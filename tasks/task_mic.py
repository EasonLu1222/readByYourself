import os
import re
import subprocess
import wavfile
from numpy.fft import fft
from playsound import playsound
from mylogger import logger
from utils import resource_path, run
from pydub import AudioSegment

wav_dir = './wav'
PADDING = ' ' * 8


def play_tone():
    playsound(resource_path(f"{wav_dir}/100Hz_to_20000Hz_mono.wav"))


def pull_recorded_sound():
    cmd = "adb devices -l"
    decoded_output = run(cmd, strip=True)
    lines = decoded_output.split('\n')[1:]
    tid_list = []   # Adb transport id list
    trp_list = []   # Test result path list
    for line in lines:
        # Sample output of "adb devices -l"
        # 0123456789ABCDEF       device usb:336855040X product:occam model:Nexus_4 device:mako transport_id:9

        match = re.search(r"transport_id:(\d+)", line)   # extract "9" from the above example
        if match:
            transport_id = match.groups()[0]
            tid_list.append(transport_id)
            wav_file_path = resource_path(f"{wav_dir}/tmp/{transport_id}.wav")
            test_result_path = resource_path(f"{wav_dir}/tmp/mic_test_result_{transport_id}")
            trp_list.append(test_result_path)

            cmd = f"adb -t {transport_id} pull /usr/share/recorded_sound.wav {wav_file_path}"
            run(cmd)

            top_n_freq_and_amp = analyze_recorded_sound(wav_file_path)

            is_duplicate = check_duplicate_channel_data(wav_file_path)
            if is_duplicate:
                test_result = 'Fail(one mic may be missing)'
            else:
                test_result = judge_fft_result(top_n_freq_and_amp)

            cmd = f'echo {test_result}'
            with open(test_result_path, "w+", encoding='utf8') as out_file:
                subprocess.call(cmd.split(' '), shell=True, stdout=out_file)

    for i, tid in enumerate(tid_list):
        push_result_to_device(tid, trp_list[i])


def check_duplicate_channel_data(wav_file_path):
    """
    This function checks whether the 2 channels of a wave file are too similar
    If so, return True
    Args:
        wav_file_path: wav file path

    Returns: bool

    """
    rtn = False
    try:
        s = AudioSegment.from_file(wav_file_path)
        ss = s.split_to_mono()
    except FileNotFoundError as e:
        logger.error(f"{PADDING}{e}")
        return True

    try:
        smp1 = ss[0].get_array_of_samples()
        smp2 = ss[1].get_array_of_samples()
    except IndexError as e:
        logger.error(f"{PADDING}{e}")
        return True

    diff_count = 0
    for i in range(len(smp1)):
        diff = abs(smp1[i] - smp2[i])
        if diff > 20:
            diff_count += 1

    if diff_count < 1000:
        rtn = True
    logger.debug(f"{PADDING}diff_count={diff_count}")

    return rtn


def analyze_recorded_sound(wav_file_path):
    """
    Apply FFT to the WAV file at wav_file_path

    Args:
        wav_file_path(str): The path of WAV file

    Returns({int:int,...}):
        A dict that maps frequency to its amplitude
    """
    rtn = []
    sample_rate, data = wavfile.read(wav_file_path)  # Load the wav data
    for channel_data in data.T:
        normalized_channel_data = [ele / 2 ** 16. for ele in channel_data]  # This is signed 16-bit track, b is now normalized on [-1,1)
        fft_data = fft(normalized_channel_data)  # Calculate fourier transform (complex numbers list)
        half_fft_data_len = int(len(fft_data) / 2)  # We only need half of the FFT list (real signal symmetry)
        data_len = len(data)
        total_seconds = data_len / sample_rate

        abs_fft = abs(fft_data[:(half_fft_data_len)])

        freq_checkpoints = [500, 1000, 10000, 19000]
        checkpoints = [int(p * total_seconds) for p in freq_checkpoints]
        peak_amplitudes = [int(abs_fft[p]) for p in checkpoints]

        rtn.append(dict(zip(freq_checkpoints, peak_amplitudes)))

    logger.info(f'{PADDING}[MicTest] Deleting {wav_file_path}')
    os.remove(wav_file_path)

    return rtn


def judge_fft_result(freq_and_amp_dict_list):
    """
    Args:
        freq_and_amp_dict({int: int,...}): A list of frequency and amplitude tuples

    Returns(str):
        'Pass' or 'Fail'
    """
    rtn = 'Pass'
    freq_amp_threshold_dict = {
        # '100': 1,
        # '300': 1,
        500: 20,
        # '700': 1,
        1000: 30,
        # '3000': 1,
        # '6000': 1,
        10000: 40,
        # '13000': 1,
        # '16000': 1,
        19000: 130,
        # '20000': 1,
    }
    logger.info(f'{PADDING}Frequency to amplitude dict: {freq_and_amp_dict_list}')
    for freq_and_amp_dict in freq_and_amp_dict_list:
        for freq in freq_amp_threshold_dict:
            amp_threshold = freq_amp_threshold_dict[freq]

            amp = freq_and_amp_dict[freq]

            if amp_threshold > amp:
                rtn = 'Fail'
                logger.error(f'{PADDING}Freq {freq} test fail, expect >{amp_threshold}, got {amp}')
                break
        if rtn == 'Fail':
            break
    return rtn


def push_result_to_device(transport_id, test_result_path):
    """

    Args:
        transport_id(str): The transport_id acquired from "adb device -l"
        test_result_path: The path to save the test result

    Returns:
    """

    file_path = "/usr/share/"
    cmd = f"adb -t {transport_id} push {test_result_path} {file_path}"
    run(cmd)

    logger.info(f'{PADDING}[MicTest] Removing {test_result_path}')
    os.remove(test_result_path)


if __name__ == '__main__':
    # with daemon.DaemonContext(working_directory=os.getcwd()):
    # play_tone()
    # pull_recorded_sound()
    # wav_file_path = '/PATH/TO/WAV'
    # r = analyze_recorded_sound(wav_file_path)
    # judge_fft_result(r)
    pass

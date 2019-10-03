import os
import re
import subprocess
from math import ceil
from scipy.fftpack import fft
from scipy.io import wavfile
from scipy.signal import find_peaks
from playsound import playsound
from subprocess import Popen, PIPE

from mylogger import logger
from utils import resource_path, get_env

wav_dir = './wav'


def play_tone():
    playsound(resource_path(f"{wav_dir}/100Hz_to_20000Hz_mono.wav"))


def pull_recorded_sound():
    cmd = "adb devices -l"
    proc = Popen(cmd.split(" "), stdout=PIPE, env=get_env(), cwd=resource_path('.'))
    output, _ = proc.communicate()
    decoded_output = output.decode('utf-8').strip()
    lines = decoded_output.split('\n')[1:]
    for line in lines:
        # Sample output of "adb devices -l"
        # 0123456789ABCDEF       device usb:336855040X product:occam model:Nexus_4 device:mako transport_id:9

        match = re.search(r"transport_id:(\d+)", line)   # extract "9" from the above example
        if match:
            transport_id = match.groups()[0]
            wav_file_path = resource_path(f"{wav_dir}/tmp/{transport_id}.wav")
            test_result_path = resource_path(f"{wav_dir}/tmp/mic_test_result_{transport_id}")

            cmd = f"adb -t {transport_id} pull /usr/share/recorded_sound.wav {wav_file_path}"
            proc = Popen(cmd.split(" "), stdout=PIPE, env=get_env(), cwd=resource_path('.'))
            proc.communicate()

            top_n_freq_and_amp = analyze_recorded_sound(wav_file_path)
            test_result = judge_fft_result(top_n_freq_and_amp)

            cmd = f'echo {test_result}'
            with open(test_result_path, "w+", encoding='utf8') as out_file:
                subprocess.call(cmd.split(' '), shell=True, stdout=out_file)

            push_result_to_device(transport_id, test_result_path)


def analyze_recorded_sound(wav_file_path):
    """
    Apply FFT to the WAV file at wav_file_path

    Args:
        wav_file_path(str): The path of WAV file

    Returns({int:int,...}):
        A dict that maps frequency to its amplitude
    """
    sample_rate, data = wavfile.read(wav_file_path)  # Load the wav data
    channel_data = data.T[1] if len(data.T) == 2 else data.T  # Detect number of channels. data.T is the transposed data
    normalized_channel_data = [ele / 2 ** 16. for ele in channel_data]  # This is signed 16-bit track, b is now normalized on [-1,1)
    fft_data = fft(normalized_channel_data)  # Calculate fourier transform (complex numbers list)
    half_fft_data_len = int(len(fft_data) / 2)  # We only need half of the FFT list (real signal symmetry)
    data_len = len(data)
    total_seconds = data_len / sample_rate

    abs_fft = abs(fft_data[:(half_fft_data_len - 1)])
    peaks, _ = find_peaks(abs_fft, height=10, width=11, distance=200)
    peak_amplitudes = [int(abs_fft[p]) for p in peaks]
    peak_freqs = [ceil(p / total_seconds) for p in peaks]

    logger.info(f'deleting {wav_file_path}')
    os.remove(wav_file_path)

    return dict(zip(peak_freqs, peak_amplitudes))


def judge_fft_result(freq_and_amp_dict):
    """
    Args:
        freq_and_amp_dict({int: int,...}): A list of frequency and amplitude tuples

    Returns(str):
        'Passed' or 'Failed'
    """
    freq_list = [100, 300, 500, 700, 1000, 3000, 6000, 10000, 13000, 16000, 19000, 20000]
    logger.info(f'Frequency to amplitude dict: {freq_and_amp_dict}')
    amp_threshold = [1] * len(freq_list)    # TODO: Have to test on multiple DUTs to adjust the criteria
    freq_amp_threshold_dict = dict(zip(freq_list, amp_threshold))
    rtn = 'Passed'

    for freq in freq_amp_threshold_dict:
        amp_threshold = freq_amp_threshold_dict[freq]
        if (freq not in freq_and_amp_dict or
                amp_threshold > freq_and_amp_dict[freq]):
            rtn = 'Failed'
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
    proc = Popen(cmd.split(" "), stdout=PIPE, env=get_env(), cwd=resource_path('.'))
    output, _ = proc.communicate()

    os.remove(test_result_path)


if __name__ == '__main__':
    # with daemon.DaemonContext(working_directory=os.getcwd()):
    # play_tone()
    pull_recorded_sound()


import numpy as np
import re
import subprocess
from scipy.fftpack import fft
from scipy.io import wavfile
from playsound import playsound
from subprocess import Popen, PIPE

from mylogger import logger

wav_dir = './wav'


def play_tone():
    playsound(f"{wav_dir}/100Hz_to_20000Hz_mono.wav")


def pull_recorded_sound():
    cmd = "adb devices -l"
    proc = Popen(cmd.split(" "), stdout=PIPE)
    output, _ = proc.communicate()
    decoded_output = output.decode('utf-8').strip()
    lines = decoded_output.split('\n')[1:]
    for line in lines:
        # Sample output of "adb devices -l"
        # 0123456789ABCDEF       device usb:336855040X product:occam model:Nexus_4 device:mako transport_id:9

        match = re.search(r"usb:(\w*)", line)   # extract "336855040X" from the above example
        if match:
            usb_id = match.groups()[0]
            wav_file_path = f"{wav_dir}/tmp/{usb_id}.wav"
            test_result_path = f"{wav_dir}/tmp/mic_test_result"

            cmd = f"adb -s usb:{usb_id} pull /usr/share/recorded_sound.wav {wav_file_path}"
            proc = Popen(cmd.split(" "), stdout=PIPE)
            proc.communicate()

            top_n_freq_and_amp = analyze_recorded_sound(wav_file_path)
            test_result = judge_fft_result(top_n_freq_and_amp)

            cmd = f'echo {test_result}'
            with open(test_result_path, "w") as out_file:
                subprocess.call(cmd.split(' '), stdout=out_file)

            push_result_to_device(usb_id, test_result_path)


def analyze_recorded_sound(wav_file_path):
    """
    Apply FFT to the WAV file at wav_file_path

    Args:
        wav_file_path(str): The path of WAV file

    Returns({int:int,...}):
        A dict that maps frequency to its amplitude
    """
    N = 12  # Top N most significant frequencies

    sample_rate, data = wavfile.read(wav_file_path)  # Load the wav data
    channel_data = data.T[1] if len(data.T) == 2 else data.T  # Detect number of channels. data.T is the transposed data
    normalized_channel_data = [ele / 2 ** 16. for ele in channel_data]  # This is signed 16-bit track, b is now normalized on [-1,1)
    fft_data = fft(normalized_channel_data)  # Calculate fourier transform (complex numbers list)
    half_fft_data_len = int(len(fft_data) / 2)  # We only need half of the FFT list (real signal symmetry)
    data_len = len(data)
    total_seconds = data_len / sample_rate

    abs_fft = abs(fft_data[:(half_fft_data_len - 1)])
    arr = np.array(abs_fft)
    top_n_indexes = np.argsort(-arr)[:N]
    vfunc = np.vectorize(lambda t: int(t / total_seconds))
    top_n_freq = vfunc(top_n_indexes)
    top_n_amp = [int(abs_fft[i]) for i in top_n_indexes]
    # print(np.sort(top_n_freq))
    print(dict(zip(top_n_freq, top_n_amp)))

    return dict(zip(top_n_freq, top_n_amp))


def judge_fft_result(freq_and_amp_dict):
    """
    Args:
        freq_and_amp_dict({int: int,...}): A list of frequency and amplitude tuples

    Returns(str):
        'Passed' or 'Failed'
    """
    freq_list = [100, 300, 500, 700, 1000, 3000, 6000, 10000, 13000, 16000, 19000, 20000]
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


def push_result_to_device(usb_id, test_result_path):
    """
    Args:
        usb_id(str): The USB ID acquired from "adb device -l"
        is_pass(bool): The mic test result
    """
    file_path = "/usr/share/"
    cmd = f"adb -s usb:{usb_id} push {test_result_path} {file_path}"
    proc = Popen(cmd.split(" "), stdout=PIPE)
    output, _ = proc.communicate()

    cmd = f"rm {test_result_path}"
    proc = Popen(cmd.split(" "), stdout=PIPE)
    output, _ = proc.communicate()


if __name__ == '__main__':
    # with daemon.DaemonContext(working_directory=os.getcwd()):
    # play_tone()
    pull_recorded_sound()


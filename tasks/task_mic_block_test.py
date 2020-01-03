import inspect
import os
import argparse
import sys
import time
from serial import Serial
from datetime import datetime
from subprocess import Popen, PIPE
from pydub import AudioSegment

from mylogger import logger

PADDING = ' ' * 8

def issue_command(serial, cmd):
    serial.write(f'{cmd}\n'.encode('utf-8'))
    lines = serial.readlines()
    lines_encoded = []
    for e in lines:
        try:
            line = e.decode('utf-8')
        except UnicodeDecodeError as ex:
            logger.info("ignored unicode error")
        except Exception as ex:
            logger.info(f"Error: {ex}")
        else:
            lines_encoded.append(line)
    return lines_encoded


def run(portname, cmd):
    with Serial(portname, baudrate=115200, timeout=0.2) as ser:
        lines = issue_command(ser, cmd)
        logger.info(lines)
    return lines


def make_experiment_dir():
    now = datetime.now().strftime('%Y%m%d')
    dir = f"./wav/experiment_{now}"
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir


def turn_off_gva():
    cmd = 'setprop ctl.stop mute_service'
    run(portname, cmd)

    cmd = '/chrome/cast_cli stop cast'
    run(portname, cmd)


def record_sound(save_path, duration):
    cmd = 'i2cget -f -y 1 0x1f 0x02'
    lines = run(portname, cmd)
    if lines[1].rstrip() == '0x01':
        logger.info("Error: the mic is muted")
        return 0

    cmd = f'arecord -Dhw:0,3 -c 2 -r 48000 -f S32_LE -d {duration} {save_path}'
    run(portname, cmd)
    return 1


def pull_result(save_path, dest_path):
    proc = Popen(['adb', 'pull', save_path, dest_path], stdout=PIPE)
    outputs, _ = proc.communicate()


def get_dbfs(wav_path, dir_path):
    s = AudioSegment.from_wav(wav_path)
    s_cut = s[-4000:]
    ss = s_cut.split_to_mono()

    with open(f'{dir_path}/test_result.txt', 'a') as f:
          f.writelines(f'{ss[0].dBFS},{ss[1].dBFS}\n')

    logger.info(f'{wav_path}\t{s.dBFS}\n')

    return s.dBFS

def mic_test(portname):
    # parser = argparse.ArgumentParser()
    # parser.add_argument('ports', help='serial com port names', type=str)
    # parser.add_argument('filename', help='filename', type=str)
    # args = parser.parse_args()
    save_path = f'/usr/share/mic_record.wav'

    dir = make_experiment_dir()

    duration = 5
    turn_off_gva()
    rtn = record_sound(save_path, duration)

    if rtn == 1:
        time.sleep(duration+1)
        pull_result(save_path, dir)
        cmd = 'rm /usr/share/mic_record.wav'
        run(portname, cmd)
        wav_path = f'{dir}/mic_record.wav'
        get_dbfs(wav_path, dir)
        result = 'Pass'
        return result
    if rtn == 0:
        result = 'Fail'
        return result

def Sensitivity_calculate():
    now = datetime.now().strftime('%Y%m%d')
    dir_path = f"./wav/experiment_{now}"
    with open(f'{dir_path}/test_result.txt', "r") as f:
        line = f.readline()
        mic_channel = line.split(",")
        line = f.readline()
        mic_block_channel = line.split(",")

    os.remove(f'{dir_path}/test_result.txt')

    channel_0_diff = float(mic_channel[0]) - float(mic_block_channel[0])
    channel_1_diff = float(mic_channel[1]) - float(mic_block_channel[1])

    logger.info(f"mic_channel[0]: {mic_channel[0]}")
    logger.info(f"mic_channel[1]: {mic_channel[1]}")
    logger.info(f"mic_block_channel[0]: {mic_block_channel[0]}")
    logger.info(f"mic_block_channel[1]: {mic_block_channel[1]}")
    logger.info(f"channel_0_diff: {channel_0_diff}")
    logger.info(f"channel_1_diff: {channel_1_diff}")

    if (abs(channel_0_diff) > float('20.0') and abs(channel_1_diff) > float('20.0')) :
        return "Pass"
    if (abs(channel_0_diff) > float('20.0') and abs(channel_1_diff) < float('20.0')) :
        return 'Fail(channel 1)'
    if (abs(channel_0_diff) < float('20.0') and abs(channel_1_diff) > float('20.0')) :
        return 'Fail(channel 0)'
    if (abs(channel_0_diff) < float('20.0') and abs(channel_1_diff) < float('20.0')) :
        return 'Fail(channel 0 and channel 1)'


if __name__ == "__main__":

    thismodule = sys.modules[__name__]

    logger.info(f'{PADDING}task_runeach start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p',
                        '--portname',
                        help='serial com port name',
                        type=str)
    parser.add_argument('-i', '--dut_idx', help='dut #number', type=int)
    parser.add_argument('-s', '--dynamic_info', help='serial id', type=str)
    parser.add_argument('funcname', help='function name', type=str)
    args = parser.parse_args()
    portname, dut_idx, dynamic_info = [
        getattr(args, e) for e in ('portname', 'dut_idx', 'dynamic_info')
    ]
    funcname = args.funcname

    logger.info(f'{PADDING}portname: {portname}')
    logger.info(f'{PADDING}dut_idx: {dut_idx}')
    logger.info(f'{PADDING}dynamic_info: {dynamic_info}')
    logger.info(f'{PADDING}args: {args}')
    logger.info(f'{PADDING}funcname: {funcname}')

    func = getattr(thismodule, funcname)
    func_args = [
        getattr(thismodule, arg) for arg in inspect.getfullargspec(func).args
    ]
    logger.info(f'{PADDING}func_args: {func_args}')

    result = func(*func_args)
    if result:
        sys.stdout.write(result)

    logger.info(f'{PADDING}task_runeach end...')
# -*- coding=utf-8 -*-
import os
import re
import sys
import json
import time
import random
import argparse
import threading
import inspect
import config

from PyQt5.QtWidgets import (QApplication, QMainWindow)

from subprocess import Popen, PIPE
from serials import issue_command, get_serial, wait_for_prompt
#  from view.loading_dialog import LoadingDialog
from utils import resource_path
from mylogger import logger

SERIAL_TIMEOUT = 0.8
PADDING = ' ' * 8


def ls_test(portname):
    with get_serial(portname, 115200, timeout=1) as ser:
        ser.reset_output_buffer()
        cmd = f'ls'
        lines = issue_command(ser, cmd)
        for e in lines:
            logger.info(e)
        return 'Pass'


def enter_burn_mode(portname, dut_idx):
    logger.debug(f'{PADDING}portname: {portname}, dut_idx: {dut_idx}')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'update')
        logger.debug(f'{PADDING}{lines}')
        result = f'Pass'
    return result


def read_pid(portname, dut_idx):
    logger.debug(f'{PADDING}portname: {portname}, dut_idx: {dut_idx}')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo usid > /sys/class/unifykeys/name',
        ]
        for cmd in cmds:
            logger.debug(f'{PADDING}cmd: {cmd}')
            issue_command(ser, cmd, False)
        lines = issue_command(ser, 'cat /sys/class/unifykeys/read')
        logger.debug(f'{PADDING}{lines}')
        response = lines[-1]
        logger.debug(f'{PADDING}response: {response}')
        if response == '/ # ':
            result = 'Fail(no pid found)'
        else:
            pid = response[:4]
            logger.debug(f'{PADDING}pid: {pid}')
            result = f'Pass({pid})'
    return result


def write_usid(dynamic_info):
    sid = dynamic_info
    logger.info(f'{PADDING}write usid')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo usid > /sys/class/unifykeys/name',
            f'echo {sid} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'{PADDING}cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.search(sid, e)
                                  for e in lines) else 'Fail'
        return result


def write_mac_wifi(dynamic_info):
    mac_wifi_addr = dynamic_info
    logger.info(f'{PADDING}write mac_wifi')
    with get_serial(portname, 115200, timeout=3) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_wifi > /sys/class/unifykeys/name',
            f'echo {mac_wifi_addr} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'{PADDING}cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.match(mac_wifi_addr, e)
                                  for e in lines) else 'Fail'
        return result


def write_mac_bt(dynamic_info):
    mac_bt_addr = dynamic_info
    logger.info(f'{PADDING}mac_bt')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_bt > /sys/class/unifykeys/name',
            f'echo {mac_bt_addr} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'{PADDING}cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.match(mac_bt_addr, e)
                                  for e in lines) else 'Fail'
        return result


def write_country_code(dynamic_info):
    ccode = dynamic_info
    logger.info(f'{PADDING}write country_code')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac > /sys/class/unifykeys/name',
            f'echo {ccode} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'{PADDING}cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.match(ccode, e)
                                  for e in lines) else 'Fail'
        return result


def write_mac_wifi(dynamic_info):
    mac_wifi_addr = dynamic_info
    logger.info(f'{PADDING}write mac_wifi')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_wifi > /sys/class/unifykeys/name',
            f'echo {mac_wifi_addr} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'{PADDING}cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.match(mac_wifi_addr, e)
                                  for e in lines) else 'Fail'
        return result


def write_mac_bt(dynamic_info):
    mac_bt_addr = dynamic_info
    logger.info(f'{PADDING}write mac_bt')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_bt > /sys/class/unifykeys/name',
            f'echo {mac_bt_addr} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'{PADDING}cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.match(mac_bt_addr, e)
                                  for e in lines) else 'Fail'
        return result


def write_country_code(dynamic_info):
    ccode = dynamic_info
    logger.info(f'{PADDING}write country_code')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac > /sys/class/unifykeys/name',
            f'echo {ccode} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'{PADDING}cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.match(ccode, e)
                                  for e in lines) else 'Fail'
        return result


def record_sound(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        wav_file_path = '/usr/share/recorded_sound.wav'
        wav_duration = 12  # In seconds

        # Start recording
        cmd = f'arecord -Dhw:0,3 -c 2 -r 48000 -f S16_LE -d {wav_duration+1} {wav_file_path}'

        logger.info(f'{PADDING}[MicTest]Recording sound and save to {wav_file_path}')
        lines = issue_command(ser, cmd)
        # TODO: Check if WAV file exists
        time.sleep(wav_duration + 2)
        return 'Pass'


def get_mic_test_result(portname):
    time.sleep(1)
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        test_result_path = '/usr/share/mic_test_result*'
        wav_file_path = '/usr/share/recorded_sound.wav'
        logger.info(f'{PADDING}[MicTest] Fetching mic test result from {test_result_path}')
        cmd = f'cat {test_result_path}'
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.match('Pass', e)
                                  for e in lines) else 'Fail'

        # Delete test result
        logger.info(f'{PADDING}[MicTest] Deleting {test_result_path}')
        cmd = f'rm {test_result_path}'
        lines = issue_command(ser, cmd)

        # Remove previously recorded file
        logger.info(f'{PADDING}[MicTest] Deleting {wav_file_path}')
        cmd = f'rm {wav_file_path}'
        lines = issue_command(ser, cmd)

        return result


def load_led_driver(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmd = f'insmod /lib/modules/4.9.113/kernel/drivers/amlogic/ledring/leds-lp50xx.ko'
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.search('probe', e) for e in lines) or any(
            re.search('File exists', e) for e in lines) else 'Fail'
        return result


def unload_led_driver(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmd = f'rmmod /lib/modules/4.9.113/kernel/drivers/amlogic/ledring/leds-lp50xx.ko'
        lines = issue_command(ser, cmd)
        result = f'Fail' if any(re.search('leds_lp50xx', e)
                                  for e in lines) else 'Pass'
        return result

def decrease_playback_volume(portname):
    logger.info(f'{PADDING}decrease_playback_volume start')
    with get_serial(portname, 115200, timeout=1) as ser:
        issue_command(ser, 'i2cset -f -y 0 0x4e 0x00 0x00;i2cset -f -y 0 0x4e 0x3d 0x60;i2cset -f -y 0 0x4e 0x3e 0x60', fetch=True)
        for e in lines:
            logger.info(f'{PADDING}{e}')
        return None

def speaker_play_1kz(portname):
    logger.info(f'{PADDING}play_1khz start')
    wav_file = '/usr/share/2ch_1khz-16b-120s_30percent.wav'
    with get_serial(portname, 115200, timeout=3) as ser:
        lines = issue_command(ser, f'aplay {wav_file}', fetch=True)
        for e in lines:
            logger.info(f'{PADDING}{e}')
        return None


def speaker_close_1kz(portname):
    logger.info(f'{PADDING}play_1khz end')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, '\x03', fetch=False)
        return None


def check_wifi_if(portname):
    with get_serial(portname, 115200, timeout=3) as ser:
        lines = issue_command(ser, 'ifconfig -a')
        result = 'Pass' if any(re.match('wlan[\d]+', e)
                                 for e in lines) else 'Fail'
        logger.info(f'{PADDING}check_wifi_if: {result}')
        return result


def check_bt(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'hciconfig hci0 up')
        lines = issue_command(ser, 'hciconfig')
        result = 'Pass' if any(re.search('UP RUNNING', e)
                                 for e in lines) else 'Fail'
        lines = issue_command(ser, 'hciconfig hci0 down')
        logger.info(f'{PADDING}has BT: {result}')
        return result


def check_cpu_cores(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /proc/cpuinfo |grep processor|wc -l')
        result = 'Pass' if any(re.match('4\r\n', e)
                                 for e in lines) else 'Fail'
        logger.info(f'{PADDING}Check CPU Cores: {result}')
        return result


def check_cpu_freq(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(
            ser, 'cat /sys/devices/system/cpu/cpufreq/policy0/cpuinfo_cur_freq')
        result = 'Pass' if any(re.match('[\d]+', e)
                                 for e in lines) else 'Fail'
        logger.info(f'{PADDING}Check CPU Freq: {result}')
        return result


def check_ddr_size(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'grep MemTotal /proc/meminfo')
        result = 'Pass' if any(
            re.match('MemTotal:[\s]+[\d]+ kB', e) for e in lines) else 'Fail'
        logger.info(f'{PADDING}DDR Size: {result}')
        return result


def check_i2c_tas5766(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser,
                              'cat /sys/class/i2c-adapter/i2c-0/0-004e/name')
        result = 'Pass' if any(re.match('tas5766m', e)
                                 for e in lines) else 'Fail'
        logger.info(f'{PADDING}has tas5766m: {result}')
        return result


def check_i2c_msp430(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser,
                              'cat /sys/class/i2c-adapter/i2c-1/1-001f/name')
        result = 'Pass' if any(re.match('msp430', e)
                                 for e in lines) else 'Fail'
        logger.info(f'{PADDING}has msp430: {result}')
        return result


def check_i2c_lp5018(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser,
                              'cat /sys/class/i2c-adapter/i2c-1/1-0028/name')
        result = 'Pass' if any(re.match('lp5018', e)
                                 for e in lines) else 'Fail'
        logger.info(f'{PADDING}has lp5018: {result}')
        return result


def hciup(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        issue_command(ser, 'hciconfig hci0 up')
        lines = issue_command(ser, 'hciconfig')
        result = 'Pass' if any(re.search('UP RUNNING', e)
                               for e in lines) else 'Fail'
        logger.info(f'{PADDING}hciup succeed: {result}')
        return result


def check_max_current(dut_idx):

    def is_file_empty(fl):
        with open(fl, 'r') as f:
            content = f.read()
            return False if content else True

    logger.info(f'{PADDING}check_max_current start')
    power_results_path = resource_path('power_results')
    while True:
        if os.path.isfile(power_results_path):
            logger.info(f'{PADDING}has power_results')
            if not is_file_empty(power_results_path):
                with open(power_results_path, 'r') as f:
                    x = json.load(f)
                    break
        else:
            logger.info(f'{PADDING}no power_results')
    result = x[str(dut_idx + 1)]
    logger.info(f'{PADDING}result: {result}')
    logger.info(f'{PADDING}check_max_current end')
    result = f'Pass({result})'
    return result


def check_something(portname):
    time.sleep(1.5)
    return random.choice(['Pass'] * 9 + ['Fail'])


def open_spdif(portname):
    logger.info(f'{PADDING}portname: {portname}')
    result = 'Pass'
    return result


def msp430_download(portname):
    time.sleep(5)
    with get_serial(portname, 115200, timeout=2) as ser:
        lines = issue_command(ser, f'/usr/share/{config.CAP_TOUCH_FW}')
        result = 'Pass' if any(
            re.search('Firmware updated without issue', e)
            for e in lines) else 'Fail'
        logger.info(f'{PADDING}msp430 fw download: {result}')
    return result


def tx_power_11n_2442mhz_ch1(portname):
    with get_serial(portname, 115200, timeout=2) as ser:
        lines = issue_command(ser, 'WifiTest4U2xxxx  11n2442-1')
        result = 'Pass' if any(
            re.search('wl pkteng_start', e) for e in lines) else 'Fail'
        logger.info(f'{PADDING}TX_POWER_11n_2442MHZ: {result}')
    return result


def tx_power_11n_2442mhz_ch2(portname):
    with get_serial(portname, 115200, timeout=2) as ser:
        lines = issue_command(ser, 'WifiTest4U2xxxx  11n2442-2')
        result = 'Pass' if any(
            re.search('wl pkteng_start', e) for e in lines) else 'Fail'
        logger.info(f'{PADDING}TX_POWER_11n_2442MHZ: {result}')
    return result


def tx_power_11ac_5500mhz_ch1(portname):
    with get_serial(portname, 115200, timeout=2) as ser:
        lines = issue_command(ser, 'WifiTest4U2xxxx  11ac5500-1')
        result = 'Pass' if any(
            re.search('wl pkteng_start', e) for e in lines) else 'Fail'
        logger.info(f'{PADDING}TX_POWER_11ac_5500MHZ: {result}')
    return result


def tx_power_11ac_5500mhz_ch2(portname):
    with get_serial(portname, 115200, timeout=2) as ser:
        lines = issue_command(ser, 'WifiTest4U2xxxx  11ac5500-2')
        result = 'Pass' if any(
            re.search('wl pkteng_start', e) for e in lines) else 'Fail'
        logger.info(f'{PADDING}TX_POWER_11ac_5500MHZ: {result}')
    return result


def read_leak_result(portname):
    logger.debug('read_leak_result')
    with open('leak_result', 'r') as f:
        result = f.readline()
    logger.debug(result)
    return result


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

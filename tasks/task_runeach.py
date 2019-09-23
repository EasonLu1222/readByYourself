# -*- coding=utf-8 -*-
import os
import re
import sys
import json
import time
import random
import argparse
import inspect
from subprocess import Popen, PIPE
from serials import issue_command, get_serial, enter_factory_image_prompt
from utils import resource_path

from mylogger import logger

SERIAL_TIMEOUT = 0.2


def enter_burn_mode(portname, dut_idx):
    logger.info(f'portname: {portname}, dut_idx: {dut_idx}')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'update')
        logger.info(lines)
        result = f'Pass'
    return result


def read_pid(portname, dut_idx):
    logger.info(f'portname: {portname}, dut_idx: {dut_idx}')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo usid > /sys/class/unifykeys/name',
        ]
        for cmd in cmds:
            logger.info(f'cmd: {cmd}')
            issue_command(ser, cmd, False)
        lines = issue_command(ser, 'cat /sys/class/unifykeys/read')
        logger.info(lines)
        response = lines[-1]
        logger.info(f'response: {response}')
        if response == '/ # ':
            result = 'Fail(no pid found)'
        else:
            pid = response[:4]
            logger.info(f'pid: {pid}')
            result = f'Pass({pid})'
    return result


def write_usid(dynamic_info):
    sid = dynamic_info
    logger.info('write usid')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo usid > /sys/class/unifykeys/name',
            f'echo {sid} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Passed' if any(re.match(sid, e) for e in lines) else 'Failed'
        return result


def write_mac_wifi(dynamic_info):
    mac_wifi_addr = dynamic_info
    logger.info('write mac_wifi')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_wifi > /sys/class/unifykeys/name',
            f'echo {mac_wifi_addr} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Passed' if any(re.match(mac_wifi_addr, e) for e in lines) else 'Failed'
        return result


def write_mac_bt(dynamic_info):
    mac_bt_addr = dynamic_info
    logger.info('write mac_bt')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_bt > /sys/class/unifykeys/name',
            f'echo {mac_bt_addr} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Passed' if any(re.match(mac_bt_addr, e) for e in lines) else 'Failed'
        return result


def write_country_code(dynamic_info):
    ccode = dynamic_info
    logger.info('write country_code')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac > /sys/class/unifykeys/name',
            f'echo {ccode} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Passed' if any(re.match(ccode, e) for e in lines) else 'Failed'
        return result


def write_mac_wifi(dynamic_info):
    mac_wifi_addr = dynamic_info
    logger.info('write mac_wifi')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_wifi > /sys/class/unifykeys/name',
            f'echo {mac_wifi_addr} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Passed' if any(re.match(mac_wifi_addr, e) for e in lines) else 'Failed'
        return result


def write_mac_bt(dynamic_info):
    mac_bt_addr = dynamic_info
    logger.info('write mac_bt')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_bt > /sys/class/unifykeys/name',
            f'echo {mac_bt_addr} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Passed' if any(re.match(mac_bt_addr, e) for e in lines) else 'Failed'
        return result


def write_country_code(dynamic_info):
    ccode = dynamic_info
    logger.info('write country_code')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac > /sys/class/unifykeys/name',
            f'echo {ccode} > /sys/class/unifykeys/write',
        ]
        for cmd in cmds:
            logger.info(f'cmd: {cmd}')
            issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Passed' if any(re.match(ccode, e) for e in lines) else 'Failed'
        return result


def record_sound(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        wav_file_path = '/usr/share/recorded_sound.wav'
        wav_duration = 12   # In seconds


        # Start recording
        cmd = f'arecord -Dhw:0,3 -c 2 -r 48000 -f S16_LE -d {wav_duration+1} {wav_file_path}'
        lines = issue_command(ser, cmd)
        # TODO: Check if WAV file exists
        time.sleep(wav_duration+2)
        return 'Passed'


def get_mic_test_result(portname):
    time.sleep(1)
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        test_result_path = '/usr/share/mic_test_result*'
        wav_file_path = '/usr/share/recorded_sound.wav'
        cmd = f'cat {test_result_path}'
        lines = issue_command(ser, cmd)
        result = f'Passed' if any(re.match('Passed', e) for e in lines) else 'Failed'

        # Delete test result
        logger.info(f"deleting {test_result_path}")
        cmd = f'rm {test_result_path}'
        lines = issue_command(ser, cmd)

        # Remove previously recorded file
        cmd = f'rm {wav_file_path}'
        lines = issue_command(ser, cmd)

        return result


def load_led_driver(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmd = f'insmod /lib/modules/4.9.113/kernel/drivers/amlogic/ledring/leds-lp50xx.ko'
        lines = issue_command(ser, cmd)
        result = f'Passed' if any(re.search('probe', e) for e in lines) or any(re.search('File exists', e) for e in lines) else 'Failed'
        return result


def unload_led_driver(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmd = f'rmmod /lib/modules/4.9.113/kernel/drivers/amlogic/ledring/leds-lp50xx.ko'
        lines = issue_command(ser, cmd)
        result = f'Failed' if any(re.search('leds_lp50xx', e) for e in lines) else 'Passed'
        return result


def speaker_play_1kz(portname):
    logger.info('play_1khz start')
    wav_file = '/usr/share/1k_30s.wav'
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        issue_command(ser, f'aplay -Dhw:0,2 {wav_file}', fetch=False)
        # TODO
        time.sleep(1)
        return None


def speaker_close_1kz(portname):
    logger.info('play_1khz end')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, '\x03', fetch=False)
        return None


def check_wifi_if(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'ifconfig -a')
        result = 'Passed' if any(re.match('wlan[\d]+', e) for e in lines) else 'Failed'
        logger.info(f'check_wifi_if: {result}')
        return result


def check_bt(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'pidof bsa_server')
        result =  'Passed' if any(re.match('[\d]+', e) for e in lines) else 'Failed'
        logger.info(f'has BT: {result}')
        return result


def check_cpu_cores(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /proc/cpuinfo |grep processor|wc -l')
        result =  'Passed' if any(re.match('4\r\n', e) for e in lines) else 'Failed'
        logger.info(f'Check CPU Cores: {result}')
        return result


def check_cpu_freq(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(
            ser, 'cat /sys/devices/system/cpu/cpufreq/policy0/cpuinfo_cur_freq')
        result =  'Passed' if any(re.match('[\d]+', e) for e in lines) else 'Failed'
        logger.info(f'Check CPU Freq: {result}')
        return result


def check_ddr_size(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'grep MemTotal /proc/meminfo')
        result =  'Passed' if any(re.match('MemTotal:[\s]+[\d]+ kB', e) for e in lines) else 'Failed'
        logger.info(f'DDR Size: {result}')
        return result


def check_i2c_tas5766(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /sys/class/i2c-adapter/i2c-0/0-004e/name')
        result =  'Passed' if any(re.match('tas5766m', e) for e in lines) else 'Failed'
        logger.info(f'has tas5766m: {result}')
        return result


def check_i2c_msp430(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /sys/class/i2c-adapter/i2c-1/1-001f/name')
        result =  'Passed' if any(re.match('msp430', e) for e in lines) else 'Failed'
        logger.info(f'has msp430: {result}')
        return result


def check_i2c_lp5018(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /sys/class/i2c-adapter/i2c-1/1-0028/name')
        result =  'Passed' if any(re.match('lp5018', e) for e in lines) else 'Failed'
        logger.info(f'has lp5018: {result}')
        return result


def hciup(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        issue_command(ser, 'hciconfig hci0 up')
        lines = issue_command(ser, 'hciconfig')
        result =  'Pass' if any(re.search('UP RUNNING', e) for e in lines) else 'Fail'
        logger.info(f'hciup succeed: {result}')
        return result


def check_max_current(dut_idx):
    def is_file_empty(fl):
        with open(fl, 'r') as f:
            content = f.read()
            return False if content else True
    logger.info(f'check_max_current start')
    power_results_path = resource_path('power_results')
    while True:
        if os.path.isfile(power_results_path):
            logger.info('has power_results')
            if not is_file_empty(power_results_path):
                with open(power_results_path, 'r') as f:
                    x = json.load(f)
                    break
        else:
            logger.info('no power_results')
    result = x[str(dut_idx + 1)]
    logger.info(f'result: {result}')
    logger.info(f'check_max_current end')
    result = f'Pass({result})'
    return result


def check_something(portname):
    time.sleep(1.5)
    return random.choice(['Pass']*9+['Fail'])


def open_spdif(portname):
    logger.info(f'portname: {portname}')
    result = 'Pass'
    return result


def msp430_download(portname):
    with get_serial(portname, 115200, timeout=2) as ser:
        lines = issue_command(ser, '/usr/share/msp430Upgrade_V05')
        result = 'Passed' if any(re.search('Firmware updated without issue', e) for e in lines) else 'Failed'
        logger.info(f'msp430 fw download: {result}')
        # wait for reboot
        issue_command(ser, 'reboot', fetch=False)
        logger.info(f'reboot')
        enter_factory_image_prompt(ser, waitwordidx=7, press_enter=True, printline=False)
        logger.info(f'wait_for_prompt done')
    return result


def tx_power_11n_2442mhz_ch1(portname):
    with get_serial(portname, 115200, timeout=2) as ser:
        lines = issue_command(ser, 'WifiTest4U2xxxx  11n2442-1')
        result = 'Passed' if any(re.search('wl pkteng_start', e) for e in lines) else 'Failed'
        logger.info(f'TX_POWER_11n_2442MHZ: {result}')
    return result


def tx_power_11n_2442mhz_ch2(portname):
    with get_serial(portname, 115200, timeout=2) as ser:
        lines = issue_command(ser, 'WifiTest4U2xxxx  11n2442-2')
        result = 'Passed' if any(re.search('wl pkteng_start', e) for e in lines) else 'Failed'
        logger.info(f'TX_POWER_11n_2442MHZ: {result}')
    return result


def tx_power_11ac_5500mhz_ch1(portname):
    with get_serial(portname, 115200, timeout=2) as ser:
        lines = issue_command(ser, 'WifiTest4U2xxxx  11ac5500-1')
        result = 'Passed' if any(re.search('wl pkteng_start', e) for e in lines) else 'Failed'
        logger.info(f'TX_POWER_11ac_5500MHZ: {result}')
    return result


def tx_power_11ac_5500mhz_ch2(portname):
    with get_serial(portname, 115200, timeout=2) as ser:
        lines = issue_command(ser, 'WifiTest4U2xxxx  11ac5500-2')
        result = 'Passed' if any(re.search('wl pkteng_start', e) for e in lines) else 'Failed'
        logger.info(f'TX_POWER_11ac_5500MHZ: {result}')
    return result


if __name__ == "__main__":

    thismodule = sys.modules[__name__]

    logger.info('task_runeach start...')
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

    logger.info(f'portname: {portname}')
    logger.info(f'dut_idx: {dut_idx}')
    logger.info(f'dynamic_info: {dynamic_info}')
    logger.info(f'args: {args}')
    logger.info(f'funcname: {funcname}')

    func = getattr(thismodule, funcname)
    func_args = [getattr(thismodule, arg) for arg in inspect.getfullargspec(func).args]
    logger.info(f'func_args: {func_args}')

    result = func(*func_args)
    if result:
        sys.stdout.write(result)

    logger.info('task_runeach end...')

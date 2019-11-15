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
from db.sqlite import write_addr, is_pid_used

SERIAL_TIMEOUT = 0.8
PADDING = ' ' * 8
type_ = lambda ex: f'<{type(ex).__name__}>'


def ls_test(portname):
    with get_serial(portname, 115200, timeout=1) as ser:
        ser.reset_output_buffer()
        cmd = f'ls'
        lines = issue_command(ser, cmd)
        for e in lines:
            logger.info(e)
        return 'Pass'


def arecord_aplay_path(portname):
    with get_serial(portname, 115200, timeout=1) as ser:
        cmd = f'arecord -Dhw:0,4 -c 2 -r 48000 -f S24_LE | aplay -Dhw:0,2 -r 48000 -f S24_LE'
        lines = issue_command(ser, cmd)
        expected = 'asoc-aml-card auge_sound: tdm playback enable'
        result = f'Pass' if any(re.search(expected, e) for e in lines) else 'Fail'
        return result


def arecord_aplay_path_audio(portname):
    with get_serial(portname, 115200, timeout=1) as ser:
        cmd = f'arecord -Dhw:0,4 -c 2 -r 48000 -f S16_LE | aplay -Dhw:0,2 -r 48000 -f S16_LE'
        lines = issue_command(ser, cmd)
        expected = 'asoc-aml-card auge_sound: tdm playback enable'
        result = f'Pass' if any(re.search(expected, e) for e in lines) else 'Fail'
        return result


def exit_aplay_path(portname):
    with get_serial(portname, 115200, timeout=1) as ser:
        lines = issue_command(ser, '\x03', fetch=False)
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
        try:
            response = lines[-1]
        except IndexError as ex:
            logger.error(f'{PADDING}{type_(ex)}, {ex}')
            return 'Fail'
        logger.debug(f'{PADDING}response: {response}')

        regex = r"\d{3}-\d{3}-\d{3}-\d{4}-\d{4}-\d{6}"
        matches = re.search(regex, response)
        if not matches:
            result = 'Fail(no pid found)'
        else:
            pid = matches.group()
            logger.debug(f'{PADDING}pid: {pid}')
            result = f'Pass({pid})'

    return result


def read_pid_dummy(portname, dut_idx):
    xxx = ['000-111-222-3333-4444-555555',
           'aaa-bbb-ccc-dddd-eeee-ffffff',
           'aa1-bbb-ccc-dddd-eeee-ffffff',
           'aa2-bbb-ccc-dddd-eeee-ffffff',
           'aa3-bbb-ccc-dddd-eeee-ffffff',
           'aa4-bbb-ccc-dddd-eeee-ffffff',
           'aa5-bbb-ccc-dddd-eeee-ffffff',
           None]
    import random
    result = random.choice(xxx)
    result = f'Pass({result})' if result else 'Fail(no pid found)'
    logger.debug(f'read_pid_dummy: {result}')
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


def write_wifi_bt_mac(dynamic_info):
    pid = None
    mac_list = dynamic_info.split(",")
    mac_wifi_addr = mac_list[0]
    mac_bt_addr = mac_list[1].replace(":", "")
    if mac_wifi_addr == "" or mac_bt_addr == "":
        return 'Fail(mac_wifi_addr or mac_wifi_addr not available)'
    logger.info(f'{PADDING}fetched mac_wifi({mac_wifi_addr}) and mac_bt({mac_bt_addr}) from db')
    with get_serial(portname, 115200, timeout=1) as ser:
        # Read product ID
        cmd = ";".join([
            'echo 1 > /sys/class/unifykeys/attach',
            'echo usid > /sys/class/unifykeys/name',
            'cat /sys/class/unifykeys/read'
        ])
        logger.debug(f'{PADDING}cmd: {cmd}')
        issue_command(ser, cmd)
        lines = issue_command(ser, 'cat /sys/class/unifykeys/read')
        logger.debug(f'{PADDING}{lines}')
        try:
            response = lines[-1]
        except IndexError as ex:
            logger.error(f'{PADDING}{type_(ex)}, {ex}')
            return "Fail(no respond when querying product ID)"

        logger.debug(f'{PADDING}response: {response}')
        regex = r"\d{3}-\d{3}-\d{3}-\d{4}-\d{4}-\d{6}"
        matches = re.search(regex, response)
        if not matches:
            return "Fail(no pid found)"
        else:
            pid = matches.group()
            logger.debug(f'{PADDING}pid: {pid}')

        # Check if pid is in db
        if is_pid_used(pid):
            return "Pass(pid exists in db)"

        # Write wifi_mac
        cmd = ";".join([
            'echo mac_wifi > /sys/class/unifykeys/name',
            f'echo {mac_wifi_addr} > /sys/class/unifykeys/write',
            "cat /sys/class/unifykeys/read"
        ])
        logger.info(f'{PADDING}cmd: {cmd}')
        issue_command(ser, cmd)
        lines = issue_command(ser, cmd)
        is_wifi_mac_written = any(re.match(mac_wifi_addr, e) for e in lines)
        if not is_wifi_mac_written:
            return "Fail(failed to write wifi_mac to DUT)"

        # Write bt_mac
        cmd = ";".join([
            'echo mac_bt > /sys/class/unifykeys/name',
            f'echo {mac_bt_addr} > /sys/class/unifykeys/write',
            "cat /sys/class/unifykeys/read"
        ])
        logger.info(f'{PADDING}cmd: {cmd}')
        lines = issue_command(ser, cmd)
        is_bt_mac_written = any(re.match(mac_bt_addr, e) for e in lines)
        if not is_bt_mac_written:
            return "Fail(failed to write bt_mac to DUT)"

        # Mark the mac_wifi and mac_bt have been used by pid
        try:
            write_addr(mac_wifi_addr, pid)
        except Exception as ex:
            logger.error(f'{PADDING}{type_(ex)}, {ex}')
            return "Fail(failed to write product ID to DB)"

        return 'Pass'


# TODO: This function should be removed when all DUTs with incorrect mac_bt are fixed at SA station
def fix_mac_bt(portname):
    """
    fix mac_bt
    "aa:bb:cc:dd:ee:ff" => "aabbccddeeff"
    """
    logger.debug(f'{PADDING}portname: {portname}')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_bt > /sys/class/unifykeys/name',
        ]
        for cmd in cmds:
            logger.debug(f'{PADDING}cmd: {cmd}')
            issue_command(ser, cmd, False)
        lines = issue_command(ser, 'cat /sys/class/unifykeys/read')
        logger.debug(f'{PADDING}{lines}')
        try:
            response = lines[-1]
        except IndexError as ex:
            logger.error(f'{PADDING}{type_(ex)}, {ex}')
            return 'Fail(fail to read old mac_bt)'
        logger.debug(f'{PADDING}response: {response}')

        regex = r"\w{2}:\w{2}:\w{2}:\w{2}:\w{2}:\w{2}"
        matches = re.search(regex, response)
        old_mac = ""
        if not matches:
            logger.debug(f'{PADDING}No old mac_bt found')
            regex = r"\w{6}#"
            matches = re.search(regex, response)
            if not matches:
                logger.debug(f'{PADDING}No mac_bt found')
                return 'Fail(no mac_bt found)'
            else:
                logger.debug(f'{PADDING}mac_bt already good')
                return 'Pass(mac_bt already good)'
        else:
            old_mac = matches.group()
            logger.debug(f'{PADDING}old_mac: {old_mac}')

        mac_bt = old_mac.replace(":", "")
        cmd = f'echo {mac_bt} > /sys/class/unifykeys/write'
        issue_command(ser, cmd, False)
        cmd = "cat /sys/class/unifykeys/read"
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.search(mac_bt, e)
                                for e in lines) else 'Fail(fail to replace old mac_bt with the correct one)'

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
    time.sleep(6)
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
        lines = issue_command(ser, 'i2cset -f -y 0 0x4e 0x00 0x00;i2cset -f -y 0 0x4e 0x3d 0x60;i2cset -f -y 0 0x4e 0x3e 0x60', fetch=True)
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

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
from datetime import datetime
from serials import issue_command, get_serial, wait_for_prompt, enter_factory_image_prompt
#  from view.loading_dialog import LoadingDialog
from utils import resource_path
from mylogger import logger
from db.sqlite import write_addr, is_pid_used, clean_tmp_flag
from config import station_json

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
        cmd = f'arecord -Dhw:0,4 -c 2 -r 48000 -f S16_LE | aplay -Dhw:0,2'
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
    with get_serial(portname, 115200, timeout=1.2) as ser:
        cmds = [
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo usid > /sys/class/unifykeys/name',
        ]
        for cmd in cmds:
            logger.debug(f'{PADDING}cmd: {cmd}')
            issue_command(ser, cmd, False)
        lines = issue_command(ser, 'cat /sys/class/unifykeys/read')
        logger.debug(f'{PADDING}{lines}')

        if len(lines) <= 0:
            logger.error(f'{PADDING}No response when querying pid')
            return 'Fail(no response when querying pid)'

        regex = r"\d{3}-\d{3}-\d{3}-\d{4}-\d{4}-\d{6}"
        result = 'Fail(no pid found)'
        for l in lines:
            matches = re.search(regex, l)
            if matches:
                pid = matches.group()
                logger.debug(f'{PADDING}pid: {pid}')
                result = f'Pass({pid})'
                break

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


def check_usid(dynamic_info):
    """
    Check if the scanned usid matches the usid in unifykeys
    Args:
        dynamic_info: Contains usid

    Returns: Pass/Fail

    """
    usid = dynamic_info
    logger.info(f'{PADDING}check usid')
    with get_serial(portname, 115200, timeout=0.8) as ser:

        cmd = ";".join([
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo usid > /sys/class/unifykeys/name',
            f'cat /sys/class/unifykeys/read'
        ])

        lines = issue_command(ser, cmd)
        regex = r"\d{3}-\d{3}-\d{3}-\d{4}-\d{4}-\d{6}"
        result = 'Fail(no pid found)'
        for l in lines:
            matches = re.search(regex, l)
            if matches:
                matched_usid = matches.group()
                logger.debug(f'{PADDING}scanned_usid: {usid}')
                logger.debug(f'{PADDING}written_usid: {matched_usid}')
                if matched_usid != usid:
                    logger.debug(f'{PADDING}matched_usid: {matched_usid}')
                    result = f'Fail(pid mismatch - {matched_usid})'
                else:
                    result = f'Pass({matched_usid})'
                break

        return result

def check_and_fix_usid(dynamic_info):
    """
    Check if the scanned usid matches the usid in unifykeys,
    Args:
        dynamic_info: Contains usid

    Returns: Pass/Fail

    """
    need_fix = False
    usid = dynamic_info
    logger.info(f'{PADDING}check usid')
    with get_serial(portname, 115200, timeout=0.4) as ser:

        cmd = ";".join([
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo usid > /sys/class/unifykeys/name',
            f'cat /sys/class/unifykeys/read'
        ])

        lines = issue_command(ser, cmd)
        regex = r"\d{3}-\d{3}-\d{3}-\d{4}-\d{4}-\d{6}"
        result = 'Fail(no pid found)'
        for l in lines:
            matches = re.search(regex, l)
            if matches:
                matched_usid = matches.group()
                logger.debug(f'{PADDING}scanned_usid: {usid}')
                logger.debug(f'{PADDING}written_usid: {matched_usid}')
                if matched_usid != usid:
                    logger.debug(f'{PADDING}matched_usid: {matched_usid}')
                    need_fix = True
                    result = f'Fail(pid mismatch - {matched_usid})'
                else:
                    result = f'Pass(pid correct:{matched_usid})'
                break

        if need_fix:
            result = 'Fail(fix pid failed)'
            cmd = ";".join([
                f'echo {usid} > /sys/class/unifykeys/write',
                f'cat /sys/class/unifykeys/read'
            ])
            lines = issue_command(ser, cmd)
            for l in lines:
                matches = re.search(regex, l)
                if matches:
                    matched_usid = matches.group()
                    logger.debug(f'{PADDING}written_usid: {matched_usid}')
                    if matched_usid == usid:
                        result = f'Pass(pid fixed:{matched_usid})'
                    break

        return result

def check_mac_wifi():
    """
    Check if Wi-Fi MAC address has the right format, and falls in the valid range

    Returns: Pass/Fail

    """
    with get_serial(portname, 115200, timeout=0.4) as ser:

        cmd = ";".join([
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_wifi > /sys/class/unifykeys/name',
            f'cat /sys/class/unifykeys/read'
        ])

        lines = issue_command(ser, cmd)
        regex = r"^c4:41:1e(?::[a-f|\d]{2}){3}"     #c4:41:1e:xx:xx:xx
        result = 'Fail(empty or invalid mac_wifi)'
        for l in lines:
            matches = re.search(regex, l)
            if matches:
                result = 'Pass'
                break

        return result


def check_mac_bt():
    """
    Check if Bluetooth MAC address has the right format, and falls in the valid range

    Returns: Pass/Fail

    """
    with get_serial(portname, 115200, timeout=0.4) as ser:

        cmd = ";".join([
            f'echo 1 > /sys/class/unifykeys/attach',
            f'echo mac_bt > /sys/class/unifykeys/name',
            f'cat /sys/class/unifykeys/read'
        ])

        lines = issue_command(ser, cmd)
        regex = r"^c4411e(?:[a-f|\d]{2}){3}"    # c4411exxxxxx
        result = 'Fail(empty or invalid mac_bt)'
        for l in lines:
            matches = re.search(regex, l)
            if matches:
                result = 'Pass'
                break

        return result


def write_usid(dynamic_info):
    usid = dynamic_info
    logger.info(f'{PADDING}write usid')
    retry_count = 0
    max_retry = 3
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:

        while True:
            cmds = [
                f'echo 1 > /sys/class/unifykeys/attach',
                f'echo usid > /sys/class/unifykeys/name',
                f'echo {usid} > /sys/class/unifykeys/write',
            ]
            issue_command(ser, ';'.join(cmds), False)
            issue_command(ser, 'echo usid > /sys/class/unifykeys/name', False)
            cmd = "cat /sys/class/unifykeys/read"
            lines = issue_command(ser, cmd)
            result = f'Pass' if any(re.search(usid, e)
                                    for e in lines) else 'Fail'
            if result == 'Pass' or retry_count > max_retry:
                break
            logger.debug(f'{PADDING}write_usid retry_count={retry_count}')
            retry_count += 1

        return result


def write_wifi_bt_mac(dynamic_info):
    pid = None
    mac_list = dynamic_info.split(",")
    mac_wifi_addr = mac_list[0]
    mac_bt_addr = mac_list[1].replace(":", "")
    if mac_wifi_addr == "" or mac_bt_addr == "":
        clean_tmp_flag()
        return 'Fail(mac_wifi_addr or mac_bt_addr not available)'
    logger.info(f'{PADDING}fetched mac_wifi({mac_wifi_addr}) and mac_bt({mac_bt_addr}) from db')
    with get_serial(portname, 115200, timeout=1.2) as ser:
        # Read product ID
        cmd = ";".join([
            'echo 1 > /sys/class/unifykeys/attach',
            'echo usid > /sys/class/unifykeys/name',
            'cat /sys/class/unifykeys/read'
        ])
        logger.debug(f'{PADDING}cmd: {cmd}')
        lines = issue_command(ser, cmd)
        logger.debug(f'{PADDING}{lines}')
        try:
            response = lines[-1]
        except IndexError as ex:
            logger.error(f'{PADDING}{type_(ex)}, {ex}')
            clean_tmp_flag()
            return "Fail(no respond when querying product ID)"

        logger.debug(f'{PADDING}response: {response}')
        regex = r"\d{3}-\d{3}-\d{3}-\d{4}-\d{4}-\d{6}"
        no_pid_found = True
        for l in lines:
            matches = re.search(regex, l)
            if matches:
                pid = matches.group()
                logger.debug(f'{PADDING}pid: {pid}')
                no_pid_found = False
                break

        if no_pid_found:
            clean_tmp_flag()
            return "Fail(no pid found)"
        else:
            pid = matches.group()
            logger.debug(f'{PADDING}pid: {pid}')

        # Check if pid is in db
        if is_pid_used(pid):
            clean_tmp_flag()
            return "Pass(pid exists in db)"

        # Write wifi_mac
        cmd = ";".join([
            'echo mac_wifi > /sys/class/unifykeys/name',
            f'echo {mac_wifi_addr} > /sys/class/unifykeys/write',
            "cat /sys/class/unifykeys/read"
        ])
        logger.info(f'{PADDING}cmd: {cmd}')
        lines = issue_command(ser, cmd)
        is_wifi_mac_written = any(re.match(mac_wifi_addr, e) for e in lines)
        if not is_wifi_mac_written:
            clean_tmp_flag()
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
            clean_tmp_flag()
            return "Fail(failed to write bt_mac to DUT)"

        # Mark the mac_wifi and mac_bt have been used by pid
        try:
            write_addr(mac_wifi_addr, pid)
            clean_tmp_flag()
        except Exception as ex:
            logger.error(f'{PADDING}{type_(ex)}, {ex}')
            return "Fail(failed to write product ID to DB)"

        return f'Pass({mac_wifi_addr})'


def reboot_and_enter_dl_mode(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        issue_command(ser, 'reboot', fetch=False)
        logger.info('enter uboot mode')
        enter_factory_image_prompt(ser, waitwordidx=0, press_enter=True, printline=False)
        logger.info('enter download mode')
        enter_factory_image_prompt(ser, waitwordidx=9, press_enter=True, printline=False)
    return 'Pass'


def sap109_downlaod(portname):
    lines = [
        'reboot mode: normal',
        '[EFUSE_MSG]keynum',
        'BULKcmd[key is_burned secure_boot_set]',
        'BULKcmd[burn_complete 3]',
        '[MSG]Pls un-plug USB line to poweroff',
    ]
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        logger.info('usb_burning_tool downloading...')
        for line in lines:
            wait_for_prompt(ser, line)
    return 'Pass'


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
        #  result = f'Pass' if any(re.match(ccode, e)
        #  for e in lines) else 'Fail'
        result = f'Pass({ccode})' if any(re.match(ccode, e)
                                         for e in lines) else 'Fail'
        return result


def record_sound(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        wav_file_path = '/usr/share/recorded_sound.wav'
        wav_duration = 12  # In seconds

        # Start recording
        cmd = f'arecord -Dhw:0,3 -c 2 -r 48000 -f S16_LE -d {wav_duration + 1} {wav_file_path}'

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
    total_retry = 0
    is_i2c_ok = False
    i2c_val = ''
    with get_serial(portname, 115200, timeout=0.4) as ser:
        while not is_i2c_ok and total_retry<5:
            time.sleep(0.03)
            cmd = f'rmmod /lib/modules/4.9.113/kernel/drivers/amlogic/ledring/leds-lp50xx.ko'
            issue_command(ser, cmd)
            time.sleep(0.03)
            cmd = f'insmod /lib/modules/4.9.113/kernel/drivers/amlogic/ledring/leds-lp50xx.ko'
            issue_command(ser, cmd)

            i2c_val = ''
            cmd = f'i2cget -f -y 1 0x28'
            time.sleep(0.03)
            lines = issue_command(ser, cmd)
            logger.error(f"{lines}")
            total_retry = total_retry + 1
            try:
                if lines[1].startswith('0x64'):
                    is_i2c_ok = True
                i2c_val = lines[1].strip()
            except Exception as e:
                is_i2c_ok = False
                logger.error(f'{PADDING}{e}')

    result = f'Pass({i2c_val})' if is_i2c_ok else f'Fail({i2c_val})'

    return result


def unload_led_driver(portname):
    with get_serial(portname, 115200, timeout=0.4) as ser:
        time.sleep(0.03)
        cmd = f'rmmod /lib/modules/4.9.113/kernel/drivers/amlogic/ledring/leds-lp50xx.ko'
        lines = issue_command(ser, cmd)
        time.sleep(0.03)
        result = f'Fail' if any(re.search('leds_lp50xx', e)
                                for e in lines) else 'Pass'
        return result


def check_mfi(portname):
    with get_serial(portname, 115200, timeout=0.4) as ser:
        cmd = f'i2cget -y 1 -f 0x10 0x00'
        lines = issue_command(ser, cmd)
        result = f'Fail' if any(re.search('read failed', e) for e in lines) else 'Pass'
        return result


def check_no_mfi(portname):
    with get_serial(portname, 115200, timeout=0.4) as ser:
        cmd = f'i2cget -y 1 -f 0x10 0x00'
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.search('read failed', e) for e in lines) else 'Fail(209 LED detected)'
        return result


def decrease_playback_volume(portname):
    logger.info(f'{PADDING}decrease_playback_volume start')
    with get_serial(portname, 115200, timeout=1) as ser:
        lines = issue_command(ser,
                              'i2cset -f -y 0 0x4e 0x00 0x00;i2cset -f -y 0 0x4e 0x3d 0x60;i2cset -f -y 0 0x4e 0x3e 0x60',
                              fetch=True)
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
    MAX_CURRENT_UPPER_LIMIT = 0.1
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
    try:
        max_current = float(x[str(dut_idx + 1)])
    except Exception as e:
        max_current = 'NaN'
        logger.error(f'{PADDING}{e}')
    logger.info(f'{PADDING}result: {max_current}')
    logger.info(f'{PADDING}check_max_current end')
    result = 'Pass' if max_current <= MAX_CURRENT_UPPER_LIMIT else 'Fail'
    result = f'{result}({max_current})'

    return result


def check_touch_fw_version(portname):
    expected_version = '0x06'
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        cmd = f'i2cget -f -y 1 0x1f 0x03'
        lines = issue_command(ser, cmd)
        result = f'Pass' if any(re.search(expected_version, e) for e in lines) else f'Fail(wrong touch fw version)'
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
    with open(resource_path('leak_result'), 'r') as f:
        result = f.readline()
    logger.debug(result)
    return result


def check_stdout(ser, prompt, timeout=86400):
    rtn = False
    start_time = datetime.now()
    while True:
        try:
            line = ser.readline().decode('utf-8').rstrip('\n')
            logger.info(f'{PADDING}{line}')
        except UnicodeDecodeError as ex:  # ignore to proceed
            logger.error(f'{PADDING}catch UnicodeDecodeError. ignore it: {ex}')
            continue

        now = datetime.now()
        if prompt in line:
            logger.info(f"found keyword: {prompt}")
            rtn = True
            break
        elif (now - start_time).seconds > timeout:
            rtn = False
            break
    return rtn


def check_boot(portname):
    rtn = 'Fail'

    with get_serial(portname, 115200, timeout=0.8) as ser:
        prompt = 'sdio debug board detected'
        check_point_1 = check_stdout(ser, prompt)
        if check_point_1:   # Test if it's the first boot
            prompt = 'start fixing up free space'       # The system pause at this line about 11 seconds
            check_point_2 = check_stdout(ser, prompt, timeout=16)
            if check_point_2:
                timeout = 36    # Timeout for first boot
            else:
                timeout = 12    # Timeout for non-first boot
            prompt = 'tee_user_mem_alloc:343: Allocate'     # The last line of a normal boot
            check_point_3 = check_stdout(ser, prompt, timeout=timeout)
            if check_point_3:
                prompt = 'tee_user_mem_free:442: Free'
                check_point_4 = check_stdout(ser, prompt, timeout=2)
                if not check_point_4:
                    rtn = 'Pass'
    return rtn


def play_ok_google():
    json_name = station_json['BootCheck']
    jsonfile = f'jsonfile/{json_name}.json'
    json_obj = json.loads(open(jsonfile, 'r', encoding='utf8').read())
    portname = json_obj["speaker_com"]
    logger.debug(f"{PADDING}speaker_com: {portname}")
    try:
        with get_serial(portname, baudrate=115200, timeout=0.2) as ser:
            # simulate press enter & ignore all the garbage
            issue_command(ser, '')
            time.sleep(5)
            try:
                cmd = ";".join([
                    'i2cset -f -y 0 0x4e 0x00 0x00',
                    'i2cset -f -y 0 0x4e 0x3d 0x40',
                    'i2cset -f -y 0 0x4e 0x3e 0x40',
                    'aplay /usr/share/ok_google_female_chloe.wav'
                ])
                lines = issue_command(ser, cmd)
                result = f'Fail(missing wav file)' if any(re.search("such file or directory", e) for e in lines) else 'Pass'
            except Exception as ex:
                logger.error(f"{ex}")
                result = 'Fail(issue_command error)'
    except Exception as ex:
        logger.error(f"{ex}")
        result = 'Fail(bad serial port)'
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

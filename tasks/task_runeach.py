# -*- coding=utf-8 -*-
import os
import re
import sys
import json
import time
import random
import argparse
import inspect
from operator import itemgetter
from serials import issue_command, get_serial

from mylogger import logger

SERIAL_TIMEOUT = 0.2


def write_usid(sid):
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
        result =  f'Passed' if any(re.match(sid, e) for e in lines) else 'Failed'
        return result
    return None
    

def speaker_play_1kz(portname):
    logger.info('play_1khz start')
    wav_file = '2ch_1khz-16b-120s.wav'
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        issue_command(ser, f'aplay /{wav_file}', fetch=False)
        return None


def speaker_close_1kz(portname):
    logger.info('play_1khz end')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, '\x03', fetch=False)
        return None


def check_wifi_if(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'pidof bsa_server')
        result =  'Passed' if any(re.match('[\d]+', e) for e in lines) else 'Failed'
        logger.info(f'check_wifi_if: {result}')
        return result
    return None


def check_bt(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'pidof bsa_server')
        result =  'Passed' if any(re.match('[\d]+', e) for e in lines) else 'Failed'
        logger.info(f'has BT: {result}')
        return result
    return None


def check_cpu_cores(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /proc/cpuinfo |grep processor|wc -l')
        result =  'Passed' if any(re.match('4\r\n', e) for e in lines) else 'Failed'
        logger.info(f'Check CPU Cores: {result}')
        return result
    return None


def check_cpu_freq(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(
            ser, 'cat /sys/devices/system/cpu/cpufreq/policy0/cpuinfo_cur_freq')
        result =  'Passed' if any(re.match('[\d]+', e) for e in lines) else 'Failed'
        logger.info(f'Check CPU Freq: {result}')
        return result
    return None


def check_ddr_size(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'grep MemTotal /proc/meminfo')
        result =  'Passed' if any(re.match('MemTotal:[\s]+[\d]+ kB', e) for e in lines) else 'Failed'
        logger.info(f'DDR Size: {result}')
        return result
    return None


def check_i2c_tas5766(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /sys/class/i2c-adapter/i2c-0/0-004e/name')
        result =  'Passed' if any(re.match('tas5766m', e) for e in lines) else 'Failed'
        logger.info(f'has tas5766m: {result}')
        return result
    return None


def check_i2c_msp430(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /sys/class/i2c-adapter/i2c-1/1-001f/name')
        result =  'Passed' if any(re.match('msp430', e) for e in lines) else 'Failed'
        logger.info(f'has msp430: {result}')
        return result
    return None


def check_i2c_lp5018(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /sys/class/i2c-adapter/i2c-1/1-0028/name')
        result =  'Passed' if any(re.match('lp5018', e) for e in lines) else 'Failed'
        logger.info(f'has lp5018: {result}')
        return result
    return None


def check_max_current(dut_idx):
    def is_file_empty(fl):
        with open(fl, 'r') as f:
            content = f.read()
            return False if content else True
    logger.info(f'check_max_current start')
    while True:
        if os.path.isfile('power_results'):
            logger.info('has power_results')
            if not is_file_empty('power_results'):
                with open('power_results', 'r') as f:
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
    return random.choice(['Pass', 'Fail'])


if __name__ == "__main__":

    thismodule = sys.modules[__name__]

    logger.info('task_runeach start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p',
                        '--portname',
                        help='serial com port name',
                        type=str)
    parser.add_argument('-i', '--dut_idx', help='dut #number', type=int)
    parser.add_argument('-s', '--sid', help='serial id', type=str)
    parser.add_argument('funcname', help='serial id', type=str)
    args = parser.parse_args()
    portname, dut_idx, sid = [
        getattr(args, e) for e in ('portname', 'dut_idx', 'sid')
    ]
    funcname = args.funcname

    logger.info(f'portname: {portname}')
    logger.info(f'dut_idx: {dut_idx}')
    logger.info(f'sid: {sid}')
    logger.info(f'args: {args}')
    logger.info(f'funcname: {funcname}')

    func = getattr(thismodule, funcname)
    func_args = [
        getattr(thismodule, arg) for arg in inspect.getargspec(func).args
    ]
    logger.info(f'func_args: {func_args}')

    result = func(*func_args)
    if result:
        sys.stdout.write(result)

    logger.info('task_runeach end...')

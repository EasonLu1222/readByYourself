# -*- coding=utf-8 -*-
import os
import re
import sys
import json
import time
import random
import argparse
from operator import itemgetter
from serials import issue_command, get_serial

from mylogger import logger

SERIAL_TIMEOUT = 0.2


funcmap = {
    'check_max_current': ['dut_index'],
    'check_cpu_freq': ['portname'],
    'speaker_play_1kz': ['portname'],
    'speaker_close_1kz': ['portname'],
}


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



def check_cpu_freq(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /sys/devices/system/cpu/cpufreq/policy0/cpuinfo_cur_freq')
        result =  'Passed' if any(re.match('[\d]+', e) for e in lines) else 'Failed'
        logger.info('Check CPU Freq: %s' % result)

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
    result = x[str(dut_idx+1)]
    logger.info(f'result: {result}')
    logger.info(f'check_max_current end')
    result = f'Pass({result})'
    return result


if __name__ == "__main__":

    thismodule = sys.modules[__name__]

    logger.info('task_runeach start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p',
                        '--portname',
                        help='serial com port name',
                        type=str)
    parser.add_argument('-i', '--dut_index', help='dut #number', type=int)
    parser.add_argument('-s', '--sid', help='serial id', type=str)
    parser.add_argument('funcname', help='serial id', type=str)
    args = parser.parse_args()
    portname, dut_index, sid = [
        getattr(args, e) for e in ('portname', 'dut_index', 'sid')
    ]
    funcname = args.funcname

    logger.info(f'portname: {portname}')
    logger.info(f'dut_index: {dut_index}')
    logger.info(f'sid: {sid}')
    logger.info(f'args: {args}')
    logger.info(f'funcname: {funcname}')

    func = getattr(thismodule, funcname)
    func_args = [getattr(thismodule, e) for e in funcmap[funcname]]
    result = func(*func_args)
    if result:
        sys.stdout.write(result)

    logger.info('task_runeach end...')

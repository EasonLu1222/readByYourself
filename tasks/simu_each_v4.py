# -*- coding=utf-8 -*-
import re
import sys
import time
import random
import argparse
from operator import itemgetter
from serials import issue_command, get_serial

from mylogger import logger

SERIAL_TIMEOUT = 0.2


def check_something(portname):
    time.sleep(1.5)
    return random.choice(['Pass', 'Fail'])


if __name__ == "__main__":
    logger.info('simu_each_v4 start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p',
                        '--portname',
                        help='serial com port name',
                        type=str)
    parser.add_argument('-i', '--dut_index', help='dut #number', type=int)
    parser.add_argument('-s', '--sid', help='serial id', type=str)
    args = parser.parse_args()
    portname, dut_index, sid = [
        getattr(args, e) for e in ('portname', 'dut_index', 'sid')
    ]
    logger.info(f'portname: {portname}')
    logger.info(f'dut_index: {dut_index}')
    logger.info(f'sid: {sid}')

    result = check_something(portname)

    logger.info(f'result: {result}')
    logger.info('simu_each_v4 end...')

    sys.stdout.write(result)

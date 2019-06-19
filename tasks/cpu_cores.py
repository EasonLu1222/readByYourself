# -*- coding=utf-8 -*-
import os
import re
import sys
import time
import serials
import argparse
from serials import issue_command, get_serial
from PyQt5.QtCore import QTimer
from threading import Timer

from mylogger import logger


SERIAL_TIMEOUT = 0.2


def check_wlan(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /proc/cpuinfo |grep processor|wc -l')
        result =  'Passed' if any(re.match('4\r\n', e) for e in lines) else 'Failed'
        logger.info('Check CPU Cores: %s' % result)

        return result
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--portname', help='serial com port name', type=str)
    args = parser.parse_args()
    portname = args.portname

    logger.info('check_CPU_Cores start')
    result = check_wlan(portname)
    logger.info('check_CPU_Cores end')
    sys.stdout.write(result)

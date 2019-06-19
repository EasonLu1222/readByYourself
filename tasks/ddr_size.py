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
        lines = issue_command(ser, 'grep MemTotal /proc/meminfo')
        result =  'Passed' if any(re.match('MemTotal:[\s]+[\d]+ kB', e) for e in lines) else 'Failed'
        logger.info('DDR Size: %s' % result)

        return result
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--portname', help='serial com port name', type=str)
    args = parser.parse_args()
    portname = args.portname

    logger.info('check_DDR_size start')
    result = check_wlan(portname)
    logger.info('check_DDR_size end')
    sys.stdout.write(result)

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
        lines = issue_command(ser, 'cat /sys/class/i2c-adapter/i2c-1/1-0028/name')
        result =  'Passed' if any(re.match('lp5018', e) for e in lines) else 'Failed'
        logger.info('has lp5018: %s' % result)

        return result
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--portname', help='serial com port name', type=str)
    args = parser.parse_args()
    portname = args.portname

    logger.info('I2C_has_lp5018 start')
    result = check_wlan(portname)
    logger.info('I2C_has_lp5018 end')
    sys.stdout.write(result)

# -*- coding=utf-8 -*-
import os
import re
import sys
import logging
import time
import serials
import argparse
from serials import issue_command, get_serial
from PyQt5.QtCore import QTimer
from threading import Timer

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][pid=%(process)d][%(message)s]')


SERIAL_TIMEOUT = 0.2


def check_wlan(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'cat /sys/class/i2c-adapter/i2c-1/1-001f/name')
        result =  'Passed' if any(re.match('msp430', e) for e in lines) else 'Failed'
        logging.info('has msp430: %s' % result)

        return result
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--portname', help='serial com port name', type=str)
    args = parser.parse_args()
    portname = args.portname

    logging.info('I2C_has_msp430 start')
    result = check_wlan(portname)
    logging.info('I2C_has_msp430 end')
    sys.stdout.write(result)

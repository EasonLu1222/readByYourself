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


SERIAL_TIMEOUT = 0.1


def check_wlan(portname):
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'ifconfig')
        has_wlan =  True if any(re.match('wlan[\d]+', e) for e in lines) else False
        logging.info('has wlan: %s' % has_wlan)
        result = 'pass' if has_wlan else 'fail'
        return result
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--portname', help='serial com port name', type=str)
    args = parser.parse_args()
    portname = args.portname

    logging.info('wifi_ping start')
    result = check_wlan(portname)
    logging.info('wifi_ping end')
    sys.stdout.write(result)

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
        lines = issue_command(ser, 'pidof bsa_server')
        has_bt =  True if any(re.match('[\d]+', e) for e in lines) else False
        logging.info('has BT: %s' % has_bt)
        result = 'pass' if has_bt else 'fail'
        return result
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--portname', help='serial com port name', type=str)
    args = parser.parse_args()
    portname = args.portname

    logging.info('BT_Ping start')
    result = check_wlan(portname)
    logging.info('BT_Ping end')
    sys.stdout.write(result)

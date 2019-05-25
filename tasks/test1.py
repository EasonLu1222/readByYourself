# -*- coding=utf-8 -*-
import os
import re
import sys
import logging
import time
import serials
from serials import issue_command, get_serial
from PyQt5.QtCore import QTimer
from threading import Timer

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][pid=%(process)d][%(message)s]')


PORT_NAME = 'COM3'
SERIAL_TIMEOUT = 0.1


def check_wlan():
    with get_serial(PORT_NAME, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, 'ifconfig')
        #  for line in lines:
            #  logging.info(line.strip())
        #  has_wlan =  True if any(re.match('wlan[\d]+', e) for e in lines) else False
        has_wlan =  True if any(re.match('swlan[\d]+', e) for e in lines) else False
        logging.info('has wlan: %s' % has_wlan)
        result = 'passed' if has_wlan else 'failed'
        return result
    return None


if __name__ == "__main__":
    logging.info('test1 start')
    result = check_wlan()
    logging.info('test1 end')
    sys.stdout.write(result)

# -*- coding=utf-8 -*-
import os
import re
import sys
import logging
import time
import serials
from serials import issue_command, ser
from PyQt5.QtCore import QTimer
from threading import Timer

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][pid=%(process)d][%(message)s]')


def check_wlan(lines):
    return True if any(re.match('wlan[\d]+', e) for e in lines) else False


if __name__ == "__main__":
    logging.info('test1 start')
    #  import time; time.sleep(1.2)
    lines = issue_command(ser, 'ifconfig')
    for line in lines:
        logging.info(line.strip())
    has_wlan = check_wlan(lines)
    logging.info('has wlan: %s' % has_wlan)
    logging.info('test1 end')
    result = 'passed' if has_wlan else 'failed'
    sys.stdout.write(result)

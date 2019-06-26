# -*- coding=utf-8 -*-
import re
import sys
import time
import random
import argparse
from serials import issue_command, get_serial

from mylogger import logger


SERIAL_TIMEOUT = 0.2


def check_something(portname):
    time.sleep(1.5)
    return random.choice(['Pass', 'Fail'])


if __name__ == "__main__":
    logger.info('simulation each1 start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--portname', help='serial com port name', type=str)
    args = parser.parse_args()
    portname = args.portname

    result = check_something(portname)
    logger.info('simulation each1 end...')

    sys.stdout.write(result)

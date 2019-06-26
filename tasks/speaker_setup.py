# -*- coding=utf-8 -*-
import re
import argparse
from serials import issue_command, get_serial

from mylogger import logger


SERIAL_TIMEOUT = 0.2


def play_1kz(portname):
    logger.info('play_1khz start')
    wav_file = '2ch_1khz-16b-120s.wav'
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        issue_command(ser, f'aplay /{wav_file}', fetch=False)
        return None


def close_1kz(portname):
    logger.info('play_1khz end')
    with get_serial(portname, 115200, timeout=SERIAL_TIMEOUT) as ser:
        lines = issue_command(ser, '\x03', fetch=False)
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--portname', help='serial com port name', type=str)
    parser.add_argument('action', help='action', type=int)
    args = parser.parse_args()
    portname = args.portname
    action = args.action

    logger.info('speaker setup start')
    if action == 1: # setup
        logger.info('setup')
        play_1kz(portname)
    elif action == 2: # teardown
        logger.info('teardown')
        close_1kz(portname)
    logger.info('speaker setup end')

# -*- coding=utf-8 -*-
import os
import re
import sys
import logging
import time
import serials
#  from serials import issue_command, ser
from serials import issue_command, get_serial
from PyQt5.QtCore import QTimer
from threading import Timer

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][pid=%(process)d][%(message)s]')




cmd = lambda brightness,num,color: \
    'echo {} > /sys/class/leds/LED{}_{}/brightness'.\
    format(brightness, num, color)


def led_all_clear(ser):
    #  print('all clear')
    for i in range(1, 5): 
        lines = issue_command(ser, cmd(0, i, 'R'))
        lines = issue_command(ser, cmd(0, i, 'G'))
        lines = issue_command(ser, cmd(0, i, 'B'))

def led_all_red(ser, b=10):
    #  print('all red')
    for i in range(1, 5): 
        lines = issue_command(ser, cmd(b, i, 'R'))
        lines = issue_command(ser, cmd(0, i, 'G'))
        lines = issue_command(ser, cmd(0, i, 'B'))


def led_all_green(ser, b=10):
    #  print('all green')
    for i in range(1, 5): 
        lines = issue_command(ser, cmd(0, i, 'R'))
        lines = issue_command(ser, cmd(b, i, 'G'))
        lines = issue_command(ser, cmd(0, i, 'B'))


def led_all_blue(ser, b=10):
    #  print('all blue')
    for i in range(1, 5): 
        lines = issue_command(ser, cmd(0, i, 'R'))
        lines = issue_command(ser, cmd(0, i, 'G'))
        lines = issue_command(ser, cmd(b, i, 'B'))


if __name__ == "__main__":
    logging.info('LED test start')
    with get_serial('COM3', 115200, 0) as ser:
        led_all_red(ser)
        time.sleep(1)
        led_all_green(ser)
        time.sleep(1)
        led_all_blue(ser)
        time.sleep(1)
        led_all_clear(ser)
        logging.info('LED test end')

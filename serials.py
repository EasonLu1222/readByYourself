# -*- coding=utf-8 -*-
import os
import logging
import time
import serial
from PyQt5.QtCore import QTimer
from threading import Timer

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][%(process)d][%(message)s]')

PORT = 'COM3'
RATE = 115200
TIMEOUT = 5


ser = serial.Serial(port=PORT,
                    baudrate=RATE,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    rtscts=False,
                    dsrdtr=False,
                    timeout=TIMEOUT)


def wait_for_prompt(serial, prompt, thread_timeout=25):
    is_timeout = False
    #  def check_timeout():
        #  nonlocal is_timeout
        #  is_timeout = True
    #  timer = Timer(thread_timeout, check_timeout)
    #  timer.setDaemon(True)
    #  timer.start()
    while True:
        if is_timeout:
            print('TIMEOUT!!!')
            break
        line = ''
        try:
            line = serial.readline().decode('utf-8').rstrip('\n')
        except UnicodeDecodeError as ex:
            logging.debug('ERR1: UnicodeDecodeError', ex)

        #  logging.info(line)
        if line.startswith(prompt):
            logging.info('get %s' % prompt)
            break


def enter_factory_image_prompt(serial):
    #  wait_for_prompt(serial, 'Starting kernel')
    wait_for_prompt(serial, 'Server is ready for client connect')
    #  wait_for_prompt(serial, '|-----bluetooth speaker is ready for connections------|')
    for _ in range(3): serial.write(os.linesep.encode('ascii'))
    #  wait_for_prompt(serial, '#')


def issue_command(serial, cmd):
    serial.write(('%s\n' % cmd).encode('utf-8'))
    lines = [e.decode('utf8') for e in serial.readlines()]
    return lines


def test_ifconfig(serial):
    t0 = time.time()
    enter_prompt(serial)
    t1 = time.time()
    print('[TIME TO ENTER PROMPT = %f]' % (t1-t0))
    serial.write('ifconfig\n'.encode('utf-8'))
    lines = serial.readlines()
    print('test_ifconfig\n', lines)
    return lines

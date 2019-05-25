# -*- coding=utf-8 -*-
import os
import logging
import time
import serial
from PyQt5.QtCore import QTimer, pyqtSignal as QSignal, QObject
from threading import Timer

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][%(process)d][%(message)s]')

PORT = 'COM3'
RATE = 115200
TIMEOUT = 1


def get_serial(port_name, baudrate, timeout):
    ser = serial.Serial(port=port_name,
                        baudrate=baudrate,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        rtscts=False,
                        dsrdtr=False,
                        timeout=timeout)
    return ser


class SerialEmit(QObject):
    serial_msg = QSignal(str)
se = SerialEmit()


def wait_for_prompt(serial, prompt, thread_timeout=25):
    while True:
        line = ''
        try:
            line = serial.readline().decode('utf-8').rstrip('\n')
        except UnicodeDecodeError as ex:
            logging.debug('ERR1: UnicodeDecodeError', ex)

        #  logging.info(line)
        #  print(line)
        se.serial_msg.emit(line.strip())
        if line.startswith(prompt):
            logging.info('get %s' % prompt)
            break


def enter_factory_image_prompt(serial):
    #  wait_for_prompt(serial, 'Starting kernel')
    wait_for_prompt(serial, 'Server is ready for client connect')
    #  wait_for_prompt(serial, '|-----bluetooth speaker is ready for connections------|')
    for _ in range(3): serial.write(os.linesep.encode('ascii'))
    #  wait_for_prompt(serial, '#')


def issue_command(serial, cmd, timeout_for_readlines=0):
    serial.write(('%s\n' % cmd).encode('utf-8'))
    #  serial.timeout = timeout_for_readlines
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

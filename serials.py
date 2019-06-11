# -*- coding=utf-8 -*-
import os
import re
import json
import logging
import time
import serial
from serial.tools.list_ports import comports
from PyQt5.QtCore import QTimer, pyqtSignal as QSignal, QObject
from threading import Timer

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][%(process)d]%(message)s')


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


def is_serial_free(port_name):
    try:
        get_serial(port_name, 115200, 1)
    except serial.serialutil.SerialException as ex:
        return False
    return True


def get_device(comport):
    matched = re.search('VID:PID=[0-9A-Z]{4}:[0-9A-Z]{4}', comport.hwid).group()
    devices = json.load(open('device.json', 'r'))
    vid_pid = matched[8:]
    device = devices[vid_pid]
    return device


def get_devices():
    devices = [{'comport': e.device,
                'hwid': e.hwid,
                'name': get_device(e)}
                for e in comports()]
    return devices


class SerialEmit(QObject):
    #  serial_msg = QSignal(str)
    serial_msg = QSignal(list)
se = SerialEmit()


def wait_for_prompt(serial, prompt, thread_timeout=25):
    portname = serial.name
    while True:
        line = ''
        try:
            line = serial.readline().decode('utf-8').rstrip('\n')
        except UnicodeDecodeError as ex:
            logging.debug('ERR1: UnicodeDecodeError', ex)

        #  print(portname, line.strip())
        se.serial_msg.emit([portname, line.strip()])
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
    logging.info('issue_command: write')
    serial.write(f'{cmd}\n'.encode('utf-8'))
    logging.info(f'issue_command: {cmd}')
    lines = [e.decode('utf-8') for e in serial.readlines()]
    for line in lines: logging.info(f'{line.rstrip()}')
    return lines

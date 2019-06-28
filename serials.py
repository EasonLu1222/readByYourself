# -*- coding=utf-8 -*-
import os
import re
import json
import time
import serial
from serial.tools.list_ports import comports
from PyQt5.QtCore import QTimer, pyqtSignal as QSignal, QObject
from threading import Timer, Thread, Event
import argparse
from queue import Queue

from mylogger import logger


def get_serial(port_name, baudrate, timeout):
    logger.info(f'===get_serial=== {port_name}')
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
        logger.error(f'error in is_serial_free: {ex}')
        return False
    return True


def get_device(comport):
    try:
        matched = re.search('VID:PID=[0-9A-Z]{4}:[0-9A-Z]{4}', comport.hwid).group()
        devices = json.load(open('device.json', 'r'))
        vid_pid = matched[8:]
        device = devices[vid_pid]
    except Exception as e:
        logger.debug("get_device failed!")
        device = ""

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
    detect_notice = QSignal(str)
se = SerialEmit()



def wait_for_prompt(serial, prompt, thread_timeout=25):
    logger.info(f'\n\nwait_for_prompt: {prompt}\n\n')
    portname = serial.name
    logger.info(f'portname: {portname}')
    logger.info(f'is_open: {serial.isOpen()}')
    while True:
        line = ''
        try:
            line = serial.readline().decode('utf-8').rstrip('\n')
            if line: print(line)
        except UnicodeDecodeError as ex:
            logger.error('ERR1: UnicodeDecodeError', ex)
            continue

        se.serial_msg.emit([portname, line.strip()])
        if line.startswith(prompt):
            logger.info('get %s' % prompt)
            break


class WaitPromptThread(Thread):
    def __init__(self, serial, prompt, q=None):
        super(WaitPromptThread, self).__init__()
        self.ser = serial
        self.prompt = prompt
        self.q = q
        self.kill = False

    def run(self):
        logger.info(f'\n\nwait_for_prompt: {self.prompt}\n\n')
        portname = self.ser.name
        logger.info(f'portname: {portname}')
        logger.info(f'is_open: {self.ser.isOpen()}')
        while not self.kill:
            line = ''
            try:
                x1 = self.ser.readline()
                x2 = x1.decode('utf-8')
                line = x2.rstrip('\n')
                #  line = self.ser.readline().decode('utf-8').rstrip('\n')
                if line: logger.info(line)
            except UnicodeDecodeError as ex:
                logger.error(f'ERR1: UnicodeDecodeError: {ex}')
                logger.error(f'x1: {x1}')
                continue

            if line.startswith(self.prompt):
                logger.info('get %s' % self.prompt)
                if self.q:
                    self.q.put(portname)
                self.ser.close()
                break
        logger.info('end of WaitPromptThread')


def check_which_port_when_poweron(ports, prompt='U-Boot', qsignal=True):
    serial_ports = [get_serial(port, 115200, 0.2) for port in ports]
    q = Queue()
    threads = {}
    for port in serial_ports:
        t = WaitPromptThread(port, prompt, q)
        threads[port.name] = t
        t.start()
    port = q.get()
    for p in ports:
        threads[p].kill = True
    print('port', port)
    if qsignal: se.detect_notice.emit(port)
    #  return port


def enter_factory_image_prompt(serial, waitwordidx=2, press_enter=True):
    waitwords = [
        'U-Boot',
        'Starting kernel',
        'usb rndis & adb start: OK',
        'Server is ready for client connect',
        '|-----bluetooth speaker is ready for connections------|',
        '#',
    ]
    wait_for_prompt(serial, waitwords[waitwordidx])
    if press_enter:
        for _ in range(3): serial.write(os.linesep.encode('ascii'))


def issue_command(serial, cmd, timeout_for_readlines=0, fetch=True):
    logger.info('issue_command: write')
    serial.write(f'{cmd}\n'.encode('utf-8'))
    logger.info(f'issue_command: {cmd}')
    if fetch:
        lines = [e.decode('utf-8') for e in serial.readlines()]
        for line in lines: logger.info(f'{line.rstrip()}')
        return lines
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--ports', help='serial com port names', type=str)
    args = parser.parse_args()
    ports = args.ports.split(',')

    print('ports', ports)
    check_which_port_when_poweron(ports)


    #  port_name = 'COM3'
    #  ser = get_serial(port_name, 115200, 0.2)
    #  enter_factory_image_prompt(ser, 0)


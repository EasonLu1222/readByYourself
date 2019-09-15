# -*- coding=utf-8 -*-
import os
import re
import json
import time
import serial
from serial.tools.list_ports import comports
import pandas as pd
from PyQt5.QtCore import pyqtSignal as QSignal, QObject, QThread
from threading import Thread
import argparse
from queue import Queue

from config import DEVICES
from mylogger import logger


type_ = lambda ex: f'<{type(ex).__name__}>'


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
        return False
    return True


def get_device(comport):
    try:
        device = None
        matched = re.search('VID:PID=[0-9A-Z]{4}:[0-9A-Z]{4}', comport.hwid)
        if not matched:
            return
        group = matched.group()
        vid_pid = group[8:]
        device, _ = DEVICES[vid_pid]
    except KeyError as ex:
        msg = (f'\n\n{type_(ex)}, {ex}'
               f'not defined in device.json.\n')
        logger.warning(msg)
    except Exception as ex:
        logger.error(f'{type_(ex)}, {ex}')
    finally:
        if not device: device = ""
    return device


def get_devices():
    devices = [{'comport': e.device,
                'hwid': e.hwid,
                'name': get_device(e),
                'sn': e.serial_number,
                }
                for e in comports()]
    return devices


def get_devices_df():
    dfes = get_devices()
    device_df = pd.DataFrame(dfes)
    return device_df


def filter_devices(devices, name, sn_numbers=None, field='comport'):
    if sn_numbers:
        filtered = [e[field] for e in [e for e in devices if e['name']==name and e['sn'] in sn_numbers]]
    else:
        filtered = [e[field] for e in [e for e in devices if e['name']==name]]
    return filtered


class SerialEmit(QObject):
    #  serial_msg = QSignal(str)
    serial_msg = QSignal(list)
    detect_notice = QSignal(str)
se = SerialEmit()


def wait_for_prompt(serial, prompt, thread_timeout=25, printline=True):
    logger.info(f'\n\nwait_for_prompt: {prompt}\n\n')
    portname = serial.name
    logger.info(f'portname: {portname}')
    logger.info(f'is_open: {serial.isOpen()}')
    while True:
        line = ''
        try:
            line = serial.readline().decode('utf-8').rstrip('\n')
            if line and printline: print(line)
        except UnicodeDecodeError as ex: # ignore to proceed
            logger.debug(f'catch UnicodeDecodeError. ignore it: {ex}')
            continue

        se.serial_msg.emit([portname, line.strip()])
        #  if line.startswith(prompt):
        if prompt in line:
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
                if line: logger.info(line)
            except UnicodeDecodeError as ex: # ignore to proceed
                logger.debug(f'x1: {x1}')
                continue

            if line.startswith(self.prompt):
                logger.info('get %s' % self.prompt)
                if self.q:
                    self.q.put(portname)
                self.ser.close()
                break
        logger.info('end of WaitPromptThread')


#  def check_which_port_when_poweron(ports, prompt='U-Boot', qsignal=True):
def check_which_port_when_poweron(ports, prompt='Starting kernel', qsignal=True):
    logger.info('check_which_port_when_poweron start')
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
    logger.info('port %s', port)
    if qsignal: se.detect_notice.emit(port)

    logger.info('close each serial start')
    for sp in serial_ports:
        sp.close()
    logger.info('close each serial end')
    logger.info('check_which_port_when_poweron end')


def enter_factory_image_prompt(serial, waitwordidx=2, press_enter=True, printline=True):
    waitwords = [
        'U-Boot',
        'Starting kernel',
        'usb rndis',
        'Server is ready for client connect',
        '|-----bluetooth speaker is ready for connections------|',
        '#',
        'aml_dai_set_bclk_ratio',
        'Initializing random number generator',
        'asoc-aml-card auge_sound: tdm playback enable',
    ]
    wait_for_prompt(serial, waitwords[waitwordidx], printline=printline)
    if press_enter:
        for _ in range(3): serial.write(os.linesep.encode('ascii'))


def issue_command(serial, cmd, timeout_for_readlines=0, fetch=True):
    logger.info('issue_command: write')
    serial.write(f'{cmd}\n'.encode('utf-8'))
    logger.info(f'issue_command: {cmd}')
    if fetch:
        lines = serial.readlines()
        lines_encoded = []
        for e in lines:
            try:
                logger.info(f'line: {e}')
                line = e.decode('utf-8')
            except UnicodeDecodeError as ex: # ignore to proceed
                logger.debug(f'catch UnicodeDecodeError. ignore it: {ex}')
            else:
                #  logger.info(f'{line.rstrip()}')
                lines_encoded.append(line)
        return lines_encoded
    else:
        return None


class BaseSerialListener(QThread):
    update_msec = 500
    if_all_ready = QSignal(bool)
    def __init__(self, *args, **kwargs):
        super(BaseSerialListener, self).__init__(*args, **kwargs)
        self.is_reading = False
        self.is_instrument_ready = False

    def get_update_ports_map(self):
        devices = get_devices()
        ports_map = {}
        for k,v in self.devices.items():

            # add below two lines will only allow comports which sn_numbers 
            # lies in jsonfile definition, but only for dut, not for instruments
            #  sn_numbers = v['sn']
            #  ports = filter_devices(devices, v['name'], sn_numbers)

            ports = filter_devices(devices, v['name'])
            ports_map[k] = ports
        return ports_map

    def update(self, devices_prev, devices):
        set_prev, set_now = set(devices_prev), set(devices)
        if set_prev != set_now:
            if set_now > set_prev:
                d = set_now - set_prev
                devices_prev.extend(list(d))
            else:
                d = set_prev - set_now
                for e in d:
                    devices_prev.remove(e)
            return True
        return False

    def port_full(self, excludes=None):
        for k,v in self.devices.items():

            if not v['name']:
                continue

            if excludes:
                for e in excludes:
                    if k==e: continue
            if len(getattr(self, f'ports_{k}')) < v['num']:
                return False
        return True

    def run(self):
        while True:
            QThread.msleep(BaseSerialListener.update_msec)
            self.is_reading = True
            ports_map = self.get_update_ports_map()
            for k in self.devices.keys():
                ports = ports_map[k]
                self_ports = getattr(self, f'ports_{k}')
                self_comports = getattr(self, f'comports_{k}')
                if self.update(self_ports, ports):
                    self_comports.emit(self_ports)
            self.is_reading = False

            if not self.is_instrument_ready and self.port_full():
                self.is_instrument_ready = True
                self.if_all_ready.emit(True)
            if self.is_instrument_ready and not self.port_full():
                self.is_instrument_ready = False
                self.if_all_ready.emit(False)

    def stop(self):
        logger.info('BaseSerialListener stop start')
        # wait 1s for list_ports to finish, is it enough or too long in order
        # not to occupy com port for subsequent test scripts
        if self.is_reading:
            QThread.msleep(1000)
        self.terminate()
        logger.info('BaseSerialListener stop end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--ports', help='serial com port names', type=str)
    args = parser.parse_args()
    ports = args.ports.split(',')

    print('ports', ports)
    check_which_port_when_poweron(ports)

# -*- coding=utf-8 -*-
import os
import re
import json
import time
import serial
from serial.tools.list_ports import comports
import pandas as pd
from PyQt5.QtCore import pyqtSignal as QSignal, QObject, QThread
from serial import SerialException
from threading import Thread
import argparse
from queue import Queue
from config import DEVICES
from mylogger import logger

type_ = lambda ex: f'<{type(ex).__name__}>'
PADDING = ' ' * 4


def get_serial(port_name, baudrate, timeout):
    #  logger.info(f'{PADDING}===get_serial=== {port_name}')
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
        serial.Serial(port_name, 115200, timeout=0.2)
    except SerialException as ex:
        logger.debug(f'{PADDING}{type_(ex)}, {ex}')
        return False
    except Exception as ex:
        logger.debug(f'{PADDING}{type_(ex)}, {ex}')
        return False
    else:
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
        msg = (f'{PADDING}{type_(ex)}, {ex}'
               f'not defined in device.json.\n')
        logger.warning(msg)
    except Exception as ex:
        logger.error(f'{PADDING}{type_(ex)}, {ex}')
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
    logger.info(f'{PADDING}wait_for_prompt: {prompt}')
    portname = serial.name
    logger.info(f'{PADDING}portname: {portname}')
    logger.info(f'{PADDING}is_open: {serial.isOpen()}')
    while True:
        line = ''
        try:
            line = serial.readline().decode('utf-8').rstrip('\n')
            # TODO: Change "logger.debug" to "print" after all stations are stable
            logger.info(f'{PADDING}{line}')
            #  if line and printline: logger.debug(f'{PADDING}{line}')
        except UnicodeDecodeError as ex: # ignore to proceed
            logger.error(f'{PADDING}catch UnicodeDecodeError. ignore it: {ex}')
            continue

        se.serial_msg.emit([portname, line.strip()])
        if prompt in line:
            logger.info(f'{PADDING}get %s' % prompt)
            break


def wait_for_prompt2(serial, empty_wait=5, printline=True):
    portname = serial.name
    logger.info(f'{PADDING}portname: {portname}')
    lines_empty = 0
    while True:
        line = ''
        try:
            line = serial.readline().decode('utf-8').rstrip('\n')
            if line=='':
                lines_empty += 1
            else:
                lines_empty = 0
            if lines_empty > empty_wait:
                serial.write(os.linesep.encode('ascii'))

                lines = issue_command(serial, 'echo 123')
                if lines:
                    if any(e.strip()=="123" for e in lines):
                        logger.info('prompt entered')
                        break
                    else:
                        continue

            if line and printline: logger.debug(f'{PADDING}{line}')
        except UnicodeDecodeError as ex: # ignore to proceed
            logger.error(f'{PADDING}catch UnicodeDecodeError. ignore it: {ex}')
            continue

        se.serial_msg.emit([portname, line.strip()])


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
        'axg_s420_v1',
        'hci0 is up',
    ]
    wait_for_prompt(serial, waitwords[waitwordidx], printline=printline)
    if press_enter:
        for _ in range(3): serial.write(os.linesep.encode('ascii'))


def issue_command(serial, cmd, fetch=True):
    serial.write(f'{cmd}\n'.encode('utf-8'))
    logger.info(f'{PADDING}issue_command: {cmd}')
    lines = serial.readlines()
    if fetch:
        lines_encoded = []
        for e in lines:
            try:
                logger.info(f'{PADDING}line: {e}')
                line = e.decode('utf-8')
            except UnicodeDecodeError as ex: # ignore to proceed
                logger.error(f'{PADDING}catch UnicodeDecodeError. ignore it: {ex}')
            except Exception as ex:
                logger.error(f'{PADDING}{type_(ex)}:{ex}')
            else:
                #  logger.info(f'{line.rstrip()}')
                lines_encoded.append(line)
        return lines_encoded
    else:
        return None


class BaseSerialListener(QThread):
    update_msec = 500
    if_all_ready = QSignal(bool)
    if_actions_ready = QSignal(bool)
    def __init__(self, *args, **kwargs):
        super(BaseSerialListener, self).__init__(*args, **kwargs)
        self.ready_to_stop = False
        self.is_instrument_ready = False

    def get_update_ports_map(self):
        devices = get_devices()
        ports_map = {}
        for k,v in self.devices.items():

            # add below two lines will only allow comports which sn_numbers
            # lies in jsonfile definition, but only for dut, not for instruments
            sn_numbers = v['sn'] if k=='dut' else None
            ports = filter_devices(devices, v['name'], sn_numbers)
            #  ports = filter_devices(devices, v['name'])

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
            if self.ready_to_stop:
                logger.debug('ready_to_stop is True!')
                self.ready_to_stop = False
                self.if_actions_ready.emit(True)
                break
            QThread.msleep(BaseSerialListener.update_msec)
            ports_map = self.get_update_ports_map()
            for k in self.devices.keys():
                ports = ports_map[k]
                self_ports = getattr(self, f'ports_{k}')
                self_comports = getattr(self, f'comports_{k}')
                if self.update(self_ports, ports):
                    self_comports.emit(self_ports)

            if not self.is_instrument_ready and self.port_full():
                self.is_instrument_ready = True
                self.if_all_ready.emit(True)
            if self.is_instrument_ready and not self.port_full():
                self.is_instrument_ready = False
                self.if_all_ready.emit(False)

    def stop(self):
        self.ready_to_stop = True

    def to_stop(self):
        self.terminate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--ports', help='serial com port names', type=str)
    args = parser.parse_args()
    ports = args.ports.split(',')

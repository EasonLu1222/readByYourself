import os
import sys
import json
import time
import pickle
import threading
import pandas as pd
import importlib
from datetime import datetime
from operator import itemgetter
from collections import defaultdict
from subprocess import Popen, PIPE
from threading import Thread

from PyQt5.QtWidgets import (QApplication, QMainWindow, QErrorMessage, QHBoxLayout,
                             QTableWidgetItem, QLabel, QTableView, QAbstractItemView,
                             QWidget, QCheckBox)
from PyQt5 import QtCore
from PyQt5.QtCore import (QSettings, QThread, Qt, QTranslator, QCoreApplication,
                          pyqtSignal as QSignal)

from PyQt5.QtGui import QFont, QColor, QPixmap

from view.pwd_dialog import PwdDialog
from view.barcode_dialog import BarcodeDialog
from view.loading_dialog import LoadingDialog

from serials import (enter_factory_image_prompt, get_serial, se, get_device,
                     get_devices, is_serial_free, check_which_port_when_poweron,
                     filter_devices, get_devices_df, BaseSerialListener)

import visa
from instrument import (update_serial, generate_instruments, PowerSupply, DMM,
                        Eloader, PowerSensor)
from ui.design3 import Ui_MainWindow
from mylogger import logger
from tasks.task_mic import play_tone

from config import (DEVICES, SERIAL_DEVICES, VISA_DEVICES,
                    SERIAL_DEVICE_NAME, VISA_DEVICE_NAME)
from utils import resource_path


INSTRUMENT_MAP = {
    'gw_powersupply': PowerSupply,
    'gw_dmm': DMM,
    'gw_eloader': Eloader,
    'ks_powersensor': PowerSensor,
}


def get_visa_devices():
    dll_32 = 'C:/Windows/System32/visa32.dll'
    rm = visa.ResourceManager(dll_32)
    resource_names = rm.list_resources()
    resource_names = [e for e in resource_names if e.startswith('USB')]
    devices = []
    for resource_name in resource_names:
        usb_idx, name, sn = get_visa_device(resource_name)
        devices.append({
            'comport': usb_idx,
            'name': name,
            'sn': sn
        })
    return devices


def get_visa_device(resource_name):
    usb_idx, vid, pid, sn, _ = resource_name.split('::')
    vid_pid = f'{vid[2:]}:{pid[2:]}'
    name, _ = DEVICES[vid_pid]
    return usb_idx, name, sn



class BaseVisaListener(QThread):
    update_msec = 500
    if_all_ready = QSignal(bool)
    def __init__(self, *args, **kwargs):
        super(BaseVisaListener, self).__init__(*args, **kwargs)
        self.is_reading = False
        self.is_instrument_ready = False

    def filter_devices(self, devices, name, field='comport'):
        filtered = [e[field] for e in [e for e in devices if e['name']==name]]
        return filtered

    def get_update_ports_map(self):
        devices = get_visa_devices()
        ports_map = {}
        for k,v in self.devices.items():
            ports = self.filter_devices(devices, v['name'])
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



class UsbPowerSensor(): comports_pws = QSignal(list)

class VisaListener(BaseVisaListener, UsbPowerSensor):
    def __init__(self, *args, **kwargs):
        devices = kwargs.pop('devices')
        super(VisaListener, self).__init__(*args, **kwargs)
        self.is_reading = False
        self.is_instrument_ready = False
        self.set_devices(devices)

    def set_devices(self, devices):
        self.devices = devices
        for k,v in devices.items():
            print('k', k, 'v', v)
            setattr(self, f'ports_{k}', [])




class ProcessListener(QThread):
    process_results = QSignal(dict)

    def __init__(self):
        super(ProcessListener, self).__init__()

    def set_process(self, processes):
        self.processes = processes

    def run(self):
        print('\n\n\nProcessListener run start!')
        outputs = {}
        for pid, proc in self.processes.items():
            output, _ = proc.communicate()
            output = output.decode('utf8')
            outputs[pid] = float(output)
        print('\n\n\nProcessListener run done!')
        self.process_results.emit(outputs)

    def stop(self):
        self.terminate()


class ComportDUT(): comports_dut = QSignal(list)
class ComportPWR(): comports_pwr = QSignal(list)
class ComportDMM(): comports_dmm = QSignal(list)
class ComportELD(): comports_eld = QSignal(list)


class SerialListener(BaseSerialListener,
                     ComportDUT, ComportPWR, ComportDMM, ComportELD):
    def __init__(self, *args, **kwargs):
        devices = kwargs.pop('devices')
        super(SerialListener, self).__init__(*args, **kwargs)
        self.is_reading = False
        self.is_instrument_ready = False
        self.set_devices(devices)

    def set_devices(self, devices):
        self.devices = devices
        for k,v in devices.items():
            setattr(self, f'ports_{k}', [])


def parse_json(jsonfile):
    x = json.loads(open(resource_path(jsonfile), 'r', encoding='utf8').read())
    groups = defaultdict(list)
    cur_group = None
    x = x['test_items']
    group_orders = []
    for e in x:
        group_name = e['group']
        if not group_name in group_orders:
            group_orders.append(group_name)
        del e['group']
        groups[group_name].append(e)
    groups = {k: groups[k] for k in group_orders}

    idx = 0
    for k, items in groups.items():
        for e in items:
            e['index'] = idx
            idx += 1
    return groups


def is_serial_ok(comports, signal_from):
    print('is_serial_ok start')
    print('comports', comports)
    print('signal_from', signal_from)
    if not all(is_serial_free(p) for p in comports()):
        print('not all serial port are free!')
        signal_from.emit(False)
        return False
    else:
        print('all serial port are free!')
        signal_from.emit(True)
        return True

def disable_power_check():
    win.power_recieved = True
    return True

def set_power_simu(win):
    win.power_recieved = True
    win.simulation = True
    return True


def dummy_com(task):
    print('\n\ndummy com!!\n\n')
    i = 100
    for name, items in task.instruments.items():
        print('name', name)
        for e in items:
            print(' e', e)
            e.com = f'COM{i}'
            i += 1
    return True


def set_power(power_process, proc_listener):
    script = 'tasks.poweron'
    for idx in range(1, 3):
        args = [str(idx)]
        proc = Popen(['python', '-m', script] + args, stdout=PIPE)
        power_process[idx] = proc
    proc_listener.set_process(power_process)
    proc_listener.start()
    return True


def enter_prompt_simu():
    def dummy(sec):
        time.sleep(sec)
    print('enter factory image prompt start')
    t0 = time.time()
    t = threading.Thread(target=dummy, args=(1.5, ))
    t.start()
    t.join()
    t1 = time.time()
    print('enter factory image prompt end')
    print('time elapsed entering prompt: %f' % (t1 - t0))
    return True


def enter_prompt(window, ser_timeout=0.2, waitwordidx=8):
    print('enter factory image prompt start')
    t0 = time.time()
    port_ser_thread = {}
    comports = window.comports
    print('enter_prompt: comports - ', comports)
    for i in window.dut_selected:
        port = comports()[i]
        print('i', i, 'port', port)
        ser = get_serial(port, 115200, ser_timeout)
        t = threading.Thread(target=enter_factory_image_prompt, args=(ser, waitwordidx))
        port_ser_thread[port] = [ser, t]
        t.start()
    for port, (ser, th) in port_ser_thread.items():
        th.join()
    t1 = time.time()
    print('enter factory image prompt end')
    print('time elapsed entering prompt: %f' % (t1 - t0))
    for port, (ser, th) in port_ser_thread.items():
        ser.close()
    return True


class Task(QThread):
    '''
    there's three types of tasks
            1. DUT Based
                a. serial port of DUTs only
                b. one process per row, one process per DUT
            2. Instrument Based
                a. serial port of instruments only
                b. one process to handle rows and duts
            3. Mixed
                a. serial port of both DUTs and instruments
                b. TBD
    '''
    task_each = QSignal(list)
    task_result = QSignal(str)
    serial_ok = QSignal(bool)
    message = QSignal(str)
    printterm_msg = QSignal(str)

    def __init__(self, json_name, json_root='jsonfile'):
        super(Task, self).__init__()
        self.json_root = json_root
        self.json_name = json_name
        self.jsonfile = f'{json_root}/{json_name}.json'
        self.base = json.loads(open(resource_path(self.jsonfile), 'r', encoding='utf8').read())
        self.groups = parse_json(self.jsonfile)
        self.action_args = list()
        self.df = self.load()
        #  self.instruments = generate_instruments(self.serial_devices, INSTRUMENT_MAP)
        self.instruments = generate_instruments(self.devices, INSTRUMENT_MAP)
        print('Task.instruments')
        for k,v in self.instruments.items():
            print(f'{k} ---> {v}')

    @property
    def serial_instruments(self):
        name_int = dict(DEVICES.values()) # {intrument_name: interface}
        filtered = {k:v for k,v in self.instruments.items() if name_int[k]=='serial'}
        serial_inst = defaultdict(list)
        serial_inst.update(filtered)
        return serial_inst

    @property
    def visa_instruments(self):
        name_int = dict(DEVICES.values()) # {intrument_name: interface}
        filtered = {k:v for k,v in self.instruments.items() if name_int[k]=='visa'}
        visa_inst = defaultdict(list)
        visa_inst.update(filtered)
        return visa_inst

    @property
    def mylist(self):
        return self.df.fillna('').values.tolist()

    @property
    def dut_num(self):
        return self.base['devices']['dut']['num']

    def load(self):
        header = self.base['header']
        header_dut = self.header_dut()
        df = pd.DataFrame(self.base['test_items'])
        self.df = df = df[header]
        for col in header_dut:
            df[col] = None
        return df

    def __len__(self):
        return len(self.groups)

    def len(self, include_hidden=True):
        if include_hidden:
            return len(self.df)
        else:
            return len(self.df[self.df['hidden'] == False])

    def __getitem__(self, key):
        return self.groups[key]

    def keys(self):
        return self.groups.keys()

    def items(self):
        return self.groups.items()

    def __iter__(self):
        for k in self.keys():
            yield k

    def each(self, index):
        x = [self[k] for k, v in self.items()]
        return sum(x, [])[index]

    def limits(self, key, idx):
        each = self[key][idx]
        min_, expect, max_ = itemgetter('min', 'expect', 'max')(each)
        return (min_, expect, max_)

    #  @property
    #  def devices(self):
        #  return self.base['devices']

    @property
    def devices(self):
        all_devices = {}
        if self.serial_devices:
            all_devices.update(self.serial_devices)
        if self.visa_devices:
            all_devices.update(self.visa_devices)
        return all_devices

    @property
    def serial_devices(self):
        devices = self.base['devices']
        serial_devices = {k:v for k,v in devices.items() if v['name'] in SERIAL_DEVICE_NAME}
        return serial_devices

    @property
    def visa_devices(self):
        devices = self.base['devices']
        visa_devices = {k:v for k,v in devices.items() if v['name'] in VISA_DEVICE_NAME}
        return visa_devices

    @property
    def behaviors(self):
        return self.base['behaviors']

    def header_dut(self, dut_names=None):
        if dut_names:
            return dut_names
        else:
            num = self.dut_num
            header = ['#%d' % e for e in list(range(1, 1 + num))]
            return header

    def header(self):
        return self.base['header']

    def header_ext(self, dut_names=None):
        header_extension = dut_names if dut_names else self.header_dut()
        return self.header() + header_extension

    def unpack_group(self, groupname):
        eachgroup = self[groupname]
        script = f'tasks.{eachgroup[0]["script"]}'
        item_len = len(eachgroup)
        index = eachgroup[0]['index']
        tasktype = eachgroup[0]['tasktype']
        args = [g['args'] for g in eachgroup]
        return eachgroup, script, index, item_len, tasktype, args

    def unpack_each(self, index):
        each = self.each(index)
        line = self.df.values[index]
        script = 'tasks.%s' % each['script']
        tasktype = each['tasktype']
        args = [str(e) for e in each['args']]if each['args'] else []
        return each, script, tasktype, args

    def rungroup(self, groupname):
        eachgroup, script, index, item_len, tasktype, args = self.unpack_group(groupname)
        print(
            f'[rungroup][script: {script}][index: {index}][len: {item_len}][args: {args}]'
        )
        limits_group = [self.limits(groupname, i) for i in range(item_len)]
        print('limits_group', limits_group)
        limits = {}
        for e in zip(*args):
            xx = {i: j for i, j in zip(e, limits_group)}
            limits.update(xx)
        print('limits', limits)
        args = {'args': args, 'limits': limits}

        #  coms = {k:[e.com for e in v] for k,v in self.instruments.items() if len(v)>0}
        coms = {}
        for k,v in self.instruments.items():
            interface = dict(DEVICES.values())[k]
            if interface == 'serial':
                com_to_extract = 'com'
            elif interface == 'visa':
                com_to_extract = 'visa_addr'
            if len(v) > 0 :
                coms.update({k: [getattr(e, com_to_extract) for e in v]})

        coms = json.dumps(coms)
        print('coms', coms)
        proc = Popen(['python', '-m', script, '-p', coms] + [json.dumps(args)], stdout=PIPE)

        return proc

    def runeach(self, row_idx, dut_idx, sid, tasktype):
        port = self.window.comports()[dut_idx]
        each, script, tasktype, args = self.unpack_each(row_idx)
        msg = (f'[runeach][script: {script}][row_idx: {row_idx}]'
               f'[dut_idx: {dut_idx}][port: {port}][sid: {sid}]'
               f'[args: {args}]')
        print(msg)
        arguments = ['python', '-m', script,
                     '-p', port,
                     '-i', str(dut_idx),
                     '-s', sid]
        if args: arguments.append(args)
        proc = Popen(arguments, stdout=PIPE)
        self.printterm_msg.emit(msg)
        return proc

    def runeachports(self, index, ports):
        '''
        Set the window background color based on the test result
        Args:
            index (int): The row index of the test item
            ports (str): The COM ports concatenated by "," e.g. "COM1,COM2"
        '''
        line = self.df.values[index]
        script = 'tasks.%s' % line[0]
        args = [str(e) for e in line[1]] if line[1] else []
        msg1 = '\n[runeachports][script: %s][index: %s][ports: %s][args: %s]' % (
            script, index, ports, args)
        print(msg1)
        self.printterm_msg.emit(msg1)

        proc = Popen(['python', '-m', script, '-pp', ports] + args, stdout=PIPE)
        outputs, _ = proc.communicate()
        if not outputs:
            print('outputs is None!!!!')
        outputs = outputs.decode('utf8')
        outputs = json.loads(outputs)
        msg2 = '[task %s][outputs: %s]' % (index, outputs)  # E.g. outputs = ['Passed', 'Failed']
        self.printterm_msg.emit(msg2)

        port_list = ports.split(',')
        for idx, output in enumerate(outputs):
            result = json.dumps({'index': index, 'port': port_list[idx], 'idx': idx, 'output': output})
            self.df.iat[index,
                        len(self.header()) +
                        self.window.dut_selected[idx]] = output
            self.task_result.emit(result)

    def register_action(self, actions):
        print('register_action')
        for e in actions:
            action, args = e['action'], e['args']
            self.action_args.append([action, args])

    def run(self):
        time_ = lambda: datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')
        self.window.show_animation_dialog.emit(True)
        t0 = time_()
        for action, args in self.action_args:
            print('run action', action, args)
            if not action(*args):
                print('return !!!!!')
                return
        QThread.msleep(500)
        self.window.show_animation_dialog.emit(False)

        get_col = lambda arr, col: map(lambda x: x[col], arr)

        c1 = len(self.header())
        #  self.df.iloc[:, c1:c1 + 2] = ""
        self.df.iloc[:, c1:c1 + self.dut_num] = ""

        for group, items in self.groups.items():
            i, next_item = items[0]['index'], items[0]
            is_auto, task_type = next_item['auto'], next_item['tasktype']
            self.task_each.emit([i, len(items)])
            if task_type == 1:
                procs = {}
                if any(self.window.port_barcodes.values()):
                    for port, barcode in self.window.port_barcodes.items():
                        if barcode:
                            dut_idx = self.window.comports().index(port)
                            proc = self.runeach(i, dut_idx, barcode, task_type)
                            procs[port] = proc
                else:
                    for dut_idx in self.window.dut_selected:
                        proc = self.runeach(i, dut_idx, '', task_type)
                        port = self.window.comports()[dut_idx]
                        print('port: ', port)
                        procs[port] = proc

                print('procs', procs)
                for j, (port, proc) in enumerate(procs.items()):
                    output, _ = proc.communicate()
                    output = output.decode('utf8')
                    msg2 = '[task %s][output: %s]' % (i, output)
                    self.printterm_msg.emit(msg2)
                    result = json.dumps({
                        'index': i,
                        'port': port,
                        'output': output
                    })
                    self.df.iat[i,
                                len(self.header()) +
                                self.window.dut_selected[j]] = output
                    print('run: result', result)

                    if not any(self.window.port_barcodes.values()):
                        script = next_item['script']
                        func = next_item['args'][0]
                        to_read_pid = (script=='task_runeach' and func=='read_pid')
                        if output.startswith('Pass') and to_read_pid:
                            pid = output[5:-1]
                            header = self.header_ext()
                            dut_i = self.window.dut_selected[j]
                            header[-self.dut_num + dut_i] = f'#{dut_i+1} - {pid}'
                            self.window.table_view.setHorizontalHeaderLabels(header)

                    self.task_result.emit(result)

            elif task_type == 2:
                proc = self.rungroup(group)
                output, _ = proc.communicate()
                output = output.decode('utf8')
                print('OUTPUT', output)
                msg2 = '[task %s][output: %s]' % ([i, i + len(items)], output)
                self.printterm_msg.emit(msg2)
                result = json.dumps({
                    'index': [i, i + len(items)],
                    'output': output
                })
                r1, r2 = i, i + len(items)
                c1 = len(self.header()) + self.window.dut_selected[0]
                c2 = c1 + len(self.window.dut_selected)
                output = json.loads(output)
                if len(self.window.dut_selected) == 1:
                    output = [[e] for e in get_col(output, self.window.dut_selected[0])]
                print('OUTPUT', output)
                self.df.iloc[r1:r2, c1:c2] = output
                self.task_result.emit(result)

            elif task_type == 3:
                selected_port_list = []
                for selected_i in self.window.dut_selected:
                    selected_port_list.append(self.window._comports_dut[selected_i])

                selected_port_str = ','.join(selected_port_list)
                self.runeachports(i, selected_port_str)

            elif task_type == 4:
                line = self.df.values[i]
                mod_name = f'tasks.{line[0]}'
                mod = importlib.import_module(mod_name)

                func_list = [str(e) for e in line[1]] if line[1] else []

                func = getattr(mod, func_list[0])
                t = Thread(target=func)
                t.start()
                r1, r2 = i, i+1
                c1 = len(self.header()) + self.window.dut_selected[0]
                c2 = c1 + len(self.window.dut_selected)
                self.df.iloc[r1:r2, c1:c2] = "Passed"

                result = json.dumps({
                    'index': i,
                    'output': "Passed"
                })
                self.task_result.emit(result)

            QThread.msleep(500)

        t1 = time_()
        self.df = self.df.fillna('')
        message = {
            'msg': 'tasks done',
            't0': t0,
            't1': t1,
        }
        self.message.emit(json.dumps(message))


class MySettings():
    lang_list = [
        'en_US',
        'zh_TW',
    ]
    def __init__(self, dut_num):
        self.settings = QSettings('FAB', 'SAP109')
        self.dut_num = dut_num
        self.update()

    def get(self, key, default, key_type):
        return self.settings.value(key, default, key_type)

    def set(self, key, value):
        self.settings.setValue(key, value)
        self.update()

    def update(self):
        for i in range(1, self.dut_num+1):
            setattr(self, f'is_fx{i}_checked',
                self.get(f'fixture_{i}', False, bool))
        self.lang_index = self.get('lang_index', 0, int)
        self.is_eng_mode_on = self.get('is_eng_mode_on', False, bool)


class MyWindow(QMainWindow, Ui_MainWindow):
    show_animation_dialog = QSignal(bool)

    def __init__(self, app, task, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.simulation = False

        logo_img = QPixmap(resource_path("./images/fit_logo.png"))
        self.logo.setPixmap(logo_img.scaled(self.logo.width(), self.logo.height(), Qt.KeepAspectRatio))

        self.pwd_dialog = PwdDialog(self)
        self.barcode_dialog = BarcodeDialog(self)
        self.barcodes = []
        self.port_barcodes = {}     # E.g. {'COM1': '1234', 'COM2': '5678'}

        self.set_task(task)
        self.settings = MySettings(dut_num=self.task.dut_num)
        self.make_checkboxes()

        self.langSelectMenu.setCurrentIndex(self.settings.lang_index)
        self.checkBoxEngMode.setChecked(self.settings.is_eng_mode_on)
        self.toggle_engineering_mode(self.settings.is_eng_mode_on)

        self._comports_dut = dict.fromkeys(range(self.task.dut_num), None)   # E.g. {0: None, 1: None}
        self._comports_pwr = []
        self._comports_dmm = []
        self._comports_eld = []
        self._comports_pws = []

        if self.task.serial_instruments:
            update_serial(self.task.serial_instruments, 'gw_powersupply', self._comports_pwr)
            update_serial(self.task.serial_instruments, 'gw_dmm', self._comports_dmm)
            update_serial(self.task.serial_instruments, 'gw_eloader', self._comports_eld)

        self.dut_layout = []
        colors = ['#edd'] * self.task.dut_num
        for i in range(self.task.dut_num):
            c = QWidget()
            c.setStyleSheet(f'background-color:{colors[i]};')
            layout = QHBoxLayout(c)
            self.hboxPorts.addWidget(c)
            self.dut_layout.append(layout)

        self.setsignal()

        #  self.ser_listener = SerialListener(devices=self.task.devices)
        self.ser_listener = SerialListener(devices=self.task.serial_devices)
        self.ser_listener.comports_dut.connect(self.ser_update)
        self.ser_listener.comports_pwr.connect(self.pwr_update)
        self.ser_listener.comports_dmm.connect(self.dmm_update)
        self.ser_listener.comports_eld.connect(self.eld_update)
        self.ser_listener.if_all_ready.connect(self.instrument_ready)
        self.ser_listener.start()
        self.serial_ready = False

        if self.task.visa_devices:
            self.visa_listener = VisaListener(devices=self.task.visa_devices)
            self.visa_listener.comports_pws.connect(self.pws_update)
            self.visa_listener.if_all_ready.connect(self.visa_instrument_ready)
            self.visa_listener.start()
            self.visa_ready = False
        else:
            self.visa_ready = True

        self.proc_listener = ProcessListener()
        self.proc_listener.process_results.connect(self.recieve_power)
        self.power_recieved = False

        self.pushButton.setEnabled(False)

        self.showMaximized()

        self.power_process = {}
        self.power_results = {}

        self.on_lang_changed(self.settings.lang_index)

        self.col_dut_start = len(self.task.header())
        self.table_hidden_row()
        self.taskdone_first = False
        self.port_autodecting = False
        self.statusBar().hide()
        self.show_animation_dialog.connect(self.toggle_loading_dialog)

    def make_checkboxes(self):
        self.checkboxes = []
        font = QFont()
        font.setFamily("Courier New")
        font.setPointSize(14)
        _translate = QtCore.QCoreApplication.translate
        cbox_text_translate = _translate('MainWindow', 'DUT')
        for i in range(1, self.task.dut_num+1):
            cbox = QCheckBox(self.container)
            cbox.setFont(font)
            self.checkboxes.append(cbox)
            self.horizontalLayout.addWidget(cbox)
            cbox.setChecked(getattr(self.settings, f'is_fx{i}_checked'))
            cbox.setText(f'{cbox_text_translate}#{i}')

    def get_checkboxes_status(self):
        status_all = [self.checkboxes[i].isChecked() for i in range(self.task.dut_num)]
        return status_all

    @property
    def logfile(self):
        now = datetime.now()
        y, m, d = now.year, now.month, now.day
        path = f'logs/{y}_{m:02d}_{d:02d}.csv'
        if not os.path.isfile(path):
            with open(path, 'w') as f:
                f.write('')
        return path

    def dummy_com(self, coms):
        self._comports_dut = coms
        self.instrument_ready(True)

    def clean_power(self):
        print('clean_power start')
        # Prevent from last crash and power supply not closed normally
        for power in self.task.instruments['gw_powersupply']:
            if not power.is_open:
                power.open_com()
            if power.ser:
                power.off()
                power.close_com()
        print('clean_power end')

    def table_hidden_row(self):
        self.rowlabel_old_new = old_new = {}
        count = 0
        for i, each in enumerate(self.task.mylist):
            is_hidden = each[4]
            if not is_hidden: count += 1
            self.table_view.setRowHidden(i, is_hidden)
            old_new[i] = count
        old_new[len(old_new)] = count + 1
        self.table_view.setVerticalHeaderLabels(str(e) for e in old_new.values())

    def recieve_power(self, process_results):
        print('recieve_power', process_results)
        self.proc_listener.stop()
        self.power_results = process_results

        with open(resource_path('power_results'), 'w+') as f:
            f.write(json.dumps(process_results))
        print('recieve_power write power_results')

        self.power_recieved = True
        if self.taskdone_first:
            self.taskdone('tasks done')

    def set_task(self, task):
        self.task = task
        self.task.window = self
        self.task_results = []
        self.table_view.set_data(self.task.mylist, self.task.header_ext())
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        widths = [1] * 3 + [100] * 2 + [150, 250] + [90] * 4 + [280] * 2
        for idx, w in zip(range(len(widths)), widths):
            self.table_view.setColumnWidth(idx, w)
        for col in [0, 1, 2, 3, 4]:
            self.table_view.setColumnHidden(col, True)
        self.table_view.setSpan(self.task.len(), 0, 1, len(self.task.header()))
        self.table_view.setItem(self.task.len(), 0, QTableWidgetItem(self.summary_text))

    def poweron(self, power):
        print('poweron start')
        print('is_open', power.is_open)
        if not power.is_open:
            print("poweron, power.com", power.com)
            print('open_com')
            power.open_com()
            print('power on')
            power.on()

    def poweroff(self, power):
        if power.ser:
            power.off()
            power.close_com()

    def clearlayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def pwr_update(self, comports):
        print('pwr_update', comports)
        self._comports_pwr = comports
        update_serial(self.task.instruments, 'gw_powersupply', comports)
        self.render_port_plot()

    def dmm_update(self, comports):
        print('dmm_update', comports)
        self._comports_dmm = comports
        update_serial(self.task.instruments, 'gw_dmm', comports)
        self.render_port_plot()

    def eld_update(self, comports):
        print('eld_update', comports)
        self._comports_eld = comports
        update_serial(self.task.instruments, 'gw_eloader', comports)
        self.render_port_plot()

    def pws_update(self, comports):
        print('pws_update', comports)
        self._comports_pws = comports
        update_serial(self.task.instruments, 'ks_powersensor', comports)
        self.render_port_plot()

    def ser_update(self, comports):
        print('ser_update', comports)
        #  dut_name, sn_numbers = itemgetter('name', 'sn')(self.task.devices['dut'])
        dut_name, sn_numbers = itemgetter('name', 'sn')(self.task.serial_devices['dut'])
        df = get_devices_df()

        if sn_numbers:
            assert len(sn_numbers) == self.task.dut_num
            if len(df)>0:
                for dut_i, sn in zip(self._comports_dut, sn_numbers):
                    df_ = df[df.sn==sn]
                    comport = df_.iat[0,0] if len(df_)==1 else None
                    self._comports_dut[dut_i] = comport
            else:
                self._comports_dut = dict.fromkeys(range(self.task.dut_num), None)
        else:
            print('dut does not have sn number')
            dict_to_nonempty_list = lambda dict_: list(filter(lambda x:x, list(dict_.values())))
            list_ = dict_to_nonempty_list(self._comports_dut)
            if len(comports) > len(list_):
                list_.extend(comports)
                x = list(dict.fromkeys(list_))
                self._comports_dut = dict(zip(range(len(x)), x))
            else:
                self._comports_dut = dict(zip(range(len(comports)), comports))

        self.barcodes = []

        for dut_i, port in self._comports_dut.items():
            if port:
                self.port_barcodes[port] = None

        print(self._comports_dut)
        self.render_port_plot()

    def render_port_plot(self):
        style_ = lambda color: """
                QLabel {
                    padding: 6px;
                    background: %s;
                    color: white;
                    border: 0;
                    border-radius: 3px;
                    outline: 0px;
                    font-family: Courier;
                    font-size: 16px;
                }""" % (color, )
        comports_map = {
            'gw_powersupply': self._comports_pwr,
            'gw_dmm': self._comports_dmm,
            'gw_eloader': self._comports_eld,
            'ks_powersensor': self._comports_pws,
        }

        for i, e in enumerate(self.dut_layout, 1):
            self.clearlayout(e)
            e.addWidget(QLabel(f'#{i}'))

        for i, port in self._comports_dut.items():
            if port:
                lb_port = QLabel(port)
                lb_port.setStyleSheet(style_('#369'))
                self.dut_layout[i].addWidget(lb_port)

        colors_inst = {
            'gw_powersupply': '#712',
            'gw_dmm': '#4a3',
            'gw_eloader': '#a31',
            'ks_powersensor': '#1a3',
        }

        for name, items in self.task.instruments.items():
            each_instruments = self.task.instruments[name]
            for i, e in enumerate(each_instruments):

                if e.interface=='serial':
                    print(f'(SERIAL!!!)[inst: {e.NAME}] [{e}] [index: {e.index}] [{i}] [{e.com}]')
                    if e.com in comports_map[name]:
                        lb_port = QLabel(e.com)
                        lb_port.setStyleSheet(style_(colors_inst[name]))
                        self.dut_layout[i].addWidget(lb_port)

                elif e.interface=='visa':
                    print(f'(VISA!!!!)[inst: {e.NAME}] [{e}] [index: {e.index}] [{i}]')
                    if comports_map[name]:
                        lb_port = QLabel(e.com)
                        lb_port.setStyleSheet(style_(colors_inst[name]))
                        self.dut_layout[i].addWidget(lb_port)

                #  lb_port.setStyleSheet(style_(colors_inst[name]))
                #  self.dut_layout[i].addWidget(lb_port)

        for i in range(self.task.dut_num):
            self.dut_layout[i].addStretch()

    def visa_instrument_ready(self, ready):
        if ready:
            self.visa_ready = True
            print('\nVISA READY\n')
        else:
            self.visa_ready = False
            self.pushButton.setEnabled(False)
            print('\nVISA NOT READY\n')

        if self.serial_ready and self.visa_ready:
            print('\n===READY===')
            self.pushButton.setEnabled(True)

    def instrument_ready(self, ready):
        if ready:
            print('\nSERIAL READY\n!')
            self.serial_ready = True
            self.clean_power()

            # order: power1,power2, dmm1
            #  instruments_to_dump = sum(self.task.instruments.values(), [])
            if self.task.serial_instruments:
                instruments_to_dump = sum(self.task.serial_instruments.values(), [])
                with open(resource_path('instruments'), 'wb') as f:
                    pickle.dump(instruments_to_dump, f)
        else:
            self.serial_ready = False
            print('\nSERIAL NOT READY\n!')

        if self.serial_ready and self.visa_ready:
            print('\n===READY===')
            self.pushButton.setEnabled(True)
        else:
            print('\n===NOT READY===')
            self.pushButton.setEnabled(False)

    def comports(self):
        comports_as_list = list(filter(lambda x:x, self._comports_dut.values()))
        return comports_as_list

    def setsignal(self):
        for i, b in enumerate(self.checkboxes, 1):
            chk_box_state_changed = lambda state, i=i: self.chk_box_fx_state_changed(state, i)
            b.stateChanged.connect(chk_box_state_changed)
        self.langSelectMenu.currentIndexChanged.connect(self.on_lang_changed)
        self.checkBoxEngMode.stateChanged.connect(self.eng_mode_state_changed)
        self.pwd_dialog.dialog_close.connect(self.on_pwd_dialog_close)
        self.barcode_dialog.barcode_entered.connect(self.on_barcode_entered)
        self.barcode_dialog.barcode_dialog_closed.connect(self.on_barcode_dialog_closed)
        self.pushButton.clicked.connect(self.btn_clicked)
        self.task.task_result.connect(self.taskrun)
        self.task.task_each.connect(self.taskeach)
        self.task.message.connect(self.taskdone)
        se.serial_msg.connect(self.printterm1)
        self.task.printterm_msg.connect(self.printterm2)
        self.task.serial_ok.connect(self.serial_ok)

    def serial_ok(self, ok):
        if ok:
            print('serial is ok!!!!')
        else:
            self.pushButton.setEnabled(True)
            print('serial is not ok!!!')

    def printterm1(self, port_msg):
        port, msg = port_msg
        msg = '[port: %s]%s' % (port, msg)
        self.edit1.appendPlainText(msg)

    def printterm2(self, msg):
        self.edit2.appendPlainText(msg)

    def taskeach(self, row_rlen):
        self.table_view.clearSelection()
        row, rowlen = row_rlen
        self.table_view.setFocusPolicy(Qt.StrongFocus)
        self.table_view.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table_view.setFocus()
        for i in range(row, row + rowlen):
            self.table_view.selectRow(i)
        self.table_view.setSelectionMode(QAbstractItemView.NoSelection)
        self.table_view.setFocusPolicy(Qt.NoFocus)

    def color_check(self, s):
        if s.startswith('Pass'):
            color = QColor(139, 195, 74)
        elif s.startswith('Fail'):
            color = QColor(255, 87, 34)
        else:
            color = QColor(255, 255, 255)
        return color

    def taskrun(self, result):
        """
        Set background color of specified table cells to indicate pass/fail

        Args:
            result: A dict with the following fields:

                index(int or [int, int]): Row or row range
                idx(int): The (idx)th DUT
                port(str): The port name, used to inference idx
                output(str): 'Passed' or 'Failed'

                e.g. {'index': 0, 'idx': 0, 'port':'COM1', 'output': 'Passed'}
        """
        ret = json.loads(result)
        row = ret['index']

        # The pass/fail result applies for the jth DUT of rows from index[0] to index[1]
        if type(row) == list:
            print('output', ret['output'])
            output = json.loads(ret['output'])
            for i in range(*row):
                for j in self.dut_selected:
                    x = output[i - row[0]][j]
                    self.table_view.setItem(i, self.col_dut_start + j, QTableWidgetItem(x))
                    self.table_view.item(i, self.col_dut_start + j).setBackground(self.color_check(x))

        # The pass/fail result applies for the jth DUT of the specified row
        elif ('port' in ret) or ('idx' in ret):
            output = str(ret['output'])
            print('runeach output', output)
            print('self.comports', self.comports()) # E.g. ['COM1', 'COM2']
            if 'port' in ret:
                port = ret['port']
                j = self.comports().index(port)
            elif 'idx' in ret:
                j = ret['idx']

            print('task %s are done, j=%s' % (row, j))
            self.table_view.setItem(row, self.col_dut_start + j, QTableWidgetItem(output))
            self.table_view.item(row, self.col_dut_start + j).setBackground(self.color_check(output))

        # The pass/fail result applies for all selected DUT of the specified row
        else:
            output = ret['output']
            for j in self.dut_selected:
                self.table_view.setItem(row, self.col_dut_start + j, QTableWidgetItem(output))
                self.table_view.item(row, self.col_dut_start + j).setBackground(self.color_check(output))


    def taskdone(self, message):
        print('taskdone start !')
        self.taskdone_first = True
        self.table_view.setSelectionMode(QAbstractItemView.NoSelection)
        msg, t0, t1 = itemgetter('msg', 't0', 't1')(json.loads(message))
        if msg.startswith('tasks done') and self.power_recieved:
            self.pushButton.setEnabled(True)
            self.ser_listener.start()
            if not self.simulation:
                for power in self.task.instruments['gw_powersupply']:
                    if not power.is_open:
                        power.open_com()
                    if power.ser:
                        power.off()
                        power.close_com()
            r = self.task.len()
            all_pass = lambda results: all(e.startswith('Pass') for e in results)

            def get_fail_list(series):
                idx = series[series.fillna('').str.startswith('Fail')].index
                d = self.task.df
                dd = d[d.index.isin(idx)]
                items = (dd['group'] + ': ' + dd['item']).values.tolist()
                indexes = [self.rowlabel_old_new[i] for i in idx]
                fail_list = ','.join([ f'#{i}({j})' for i,j in zip(indexes,items)])
                return fail_list

            d = self.task.df
            all_res = []

            dut_num = self.task.dut_num

            print('\n\n')
            print(d)
            print(d.columns)
            print(d.columns[-dut_num])

            for j, dut_i in enumerate(self.dut_selected):
                results_ = d[d.hidden == False][d.columns[-dut_num + dut_i]]
                res = 'Pass' if all_pass(results_) else 'Fail'
                fail_list = get_fail_list(d[d.columns[-dut_num+dut_i]])
                print('fail_list', fail_list)
                self.table_view.setItem(r, self.col_dut_start + dut_i, QTableWidgetItem(res))
                self.table_view.item(r, self.col_dut_start + dut_i).setBackground(self.color_check(res))
                all_res.append(res)

                df = d[d.hidden == False]
                cols1 = (df.group + ': ' + df.item).values.tolist()
                dd = pd.DataFrame(df[[d.columns[-dut_num + dut_i]]].values.T, columns=cols1)

                if self.barcodes:
                    dd.index = [self.barcodes[j]]
                dd.index.name = 'pid'

                cols2_value = {
                    'Test Pass/Fail': res,
                    'Failed Tests': fail_list,
                    'Test Start Time': t0,
                    'Test Stop Time': t1,
                    'index': dut_i+1,
                }
                dd = dd.assign(**cols2_value)[list(cols2_value) + cols1]

                with open(self.logfile, 'a') as f:
                    dd.to_csv(f, mode='a', header=f.tell()==0, sep=',')

            self.set_window_color('pass' if all(e == 'Pass' for e in all_res) else 'fail')
            self.table_view.setFocusPolicy(Qt.NoFocus)
            self.table_view.clearFocus()
            self.table_view.clearSelection()
            self.taskdone_first = False
            self.power_recieved = False

            if os.path.isfile('power_results'):
                os.remove('power_results')

    def show_barcode_dialog(self):
        print('show_barcode_dialog start')
        status_all = self.get_checkboxes_status()
        num = len(list(filter(lambda x: x == True, status_all)))
        self.barcode_dialog.set_total_barcode(num)
        if num > 0:
            self.barcode_dialog.show()
        print('show_barcode_dialog end')

    def btn_clicked(self):
        print('btn_clicked')
        self.barcodes = []
        for dut_i, port in self._comports_dut.items():
            if port:
                self.port_barcodes[port] = None
        if not any(self.get_checkboxes_status()):
            e_msg = QErrorMessage(self)
            e_msg.showMessage(self.both_fx_not_checked_err)
            return

        self.dut_selected = [i for i, x in enumerate(self.get_checkboxes_status()) if x]
        print('dut_selected', self.dut_selected)
        for i in range(self.task.len() + 1):
            for j in range(self.task.dut_num):
                self.table_view.setItem(i, self.col_dut_start + j,
                                        QTableWidgetItem(""))
        self.set_window_color('default')

        if self.task.behaviors['barcode-scan']:
            self.show_barcode_dialog()
        else:
            self.pushButton.setEnabled(False)
            self.ser_listener.stop()
            self.task.start()

    def closeEvent(self, event):
        print('closeEvent')
        for power in self.task.instruments['gw_powersupply']:
            if power.is_open:
                power.off()
        event.accept()  # let the window close

    def chk_box_fx_state_changed(self, status, idx):
        print('status', status, 'idx', idx)
        self.settings.set(f'fixture_{idx}', status == Qt.Checked)
        print(f'chk_box_fx{idx}_state_changed',
            getattr(self.settings ,f'is_fx{idx}_checked'))

    def chk_box_fx1_state_changed(self, status):
        self.settings.set("fixture_1", status == Qt.Checked)
        print('chk_box_fx1_state_changed', self.settings.is_fx1_checked)

    def chk_box_fx2_state_changed(self, status):
        self.settings.set("fixture_2", status == Qt.Checked)
        print('chk_box_fx2_state_changed', self.settings.is_fx2_checked)


    def on_pwd_dialog_close(self, is_eng_mode_on):
        if (not is_eng_mode_on):
            self.checkBoxEngMode.setChecked(False)

    def eng_mode_state_changed(self, status):
        self.toggle_engineering_mode(status == Qt.Checked)
        if (status == Qt.Checked):
            self.pwd_dialog.show()

    def toggle_engineering_mode(self, is_on):
        self.settings.set("is_eng_mode_on", is_on)
        if is_on:
            self.splitter.show()
        else:
            self.splitter.hide()

    def on_lang_changed(self, index):
        """
        When language is changed, update UI
        """
        self.settings.set("lang_index", index)
        lang_list = [f'{e}.qm' for e in self.settings.lang_list]
        app = QApplication.instance()
        translator = QTranslator()
        translator.load(resource_path(f"translate/{lang_list[index]}"))
        app.removeTranslator(translator)
        app.installTranslator(translator)
        self.retranslateUi(self)
        self.pwd_dialog.retranslateUi(self.pwd_dialog)
        self.barcode_dialog.retranslateUi(self.barcode_dialog)

    def on_barcode_entered(self, barcode):
        print(barcode)
        self.barcodes.append(barcode)

    def on_barcode_dialog_closed(self):
        """
        When the barcode(s) are ready, start testing
        """
        # Return the index of Trues. E.g.: [False, True] => [1]
        #  self.dut_selected = [i for i, x in enumerate(self.get_checkboxes_status()) if x]
        #  print('dut_selected', self.dut_selected)
        header = self.task.header_ext()
        for j, dut_i in enumerate(self.dut_selected):
            header[-self.task.dut_num + dut_i] = f'#{dut_i+1} - {self.barcodes[j]}'
            port = self._comports_dut[dut_i]
            self.port_barcodes[port] = self.barcodes[j]
        print('header', header)
        print('port_barcodes', self.port_barcodes)
        self.table_view.setHorizontalHeaderLabels(header)
        self.pushButton.setEnabled(False)
        self.ser_listener.stop()
        self.task.start()

    def toggle_loading_dialog(self, is_on=False):
        if not hasattr(self, 'loading_dialog'):
            self.loading_dialog = LoadingDialog(self)
        if is_on:
            self.loading_dialog.show()
        else:
            self.loading_dialog.done(1)

    def set_window_color(self, state="default"):
        '''
        Set the window background color based on the test result
        Args:
            state (str): "pass", "fail" or "default"
        '''
        try:
            color = {
                "pass": "#8BC34A",
                "fail": "#FF5722",
                "default": "#ECECEC"
            }[state]
        except KeyError as e:
            color = "#ECECEC"
        self.setStyleSheet(
            f"QWidget#centralwidget {{background-color:{color} }}")

    def retranslateUi(self, MyWindow):
        super().retranslateUi(self)
        _translate = QCoreApplication.translate
        self.summary_text = _translate("MainWindow", "Summary")
        self.both_fx_not_checked_err = _translate(
            "MainWindow", "At least one of the fixture should be checked")


if __name__ == "__main__":

    thismodule = sys.modules[__name__]

    STATION = 'SIMULATION'
    STATION = 'RF'
    STATION = 'MainBoard'
    STATION = 'CapTouch'
    STATION = 'LED'
    STATION = 'WPC'
    STATION = 'PowerSensor'

    app = QApplication(sys.argv)

    task_led = Task('v8_led')
    task_simu = Task('v8_simu')
    task_cap_touch = Task('v8_cap_touch')
    task_rf = Task('v8_rf')
    task_wpc = Task('v8_wpc')
    task_ps = Task('v8_power_sensor')
    task_mb = Task('v8_ftdi_total')

    map_ = {
        'MainBoard': 'mb',
        'LED': 'led',
        'SIMULATION': 'simu',
        'CapTouch': 'cap_touch',
        'RF': 'rf',
        'WPC': 'wpc',
        'PowerSensor': 'ps',
    }

    task = getattr(thismodule, f'task_{map_[STATION]}')
    win = MyWindow(app, task)

    if STATION == 'SIMULATION':
        win.dummy_com(['COM8', 'COM3'])

    actions_mb = [
        {
            'action': is_serial_ok,
            'args': (win.comports, task_mb.serial_ok),
        },
        {
            'action': set_power,
            'args': (win.power_process, win.proc_listener),
        },
        {
            'action': enter_prompt,
            'args': (win, 0.2, 7),
        },
    ]
    actions_led = [
        {
            'action': disable_power_check,
            'args': (),
        },
        {
            'action': is_serial_ok,
            'args': (win.comports, task_mb.serial_ok),
        },
        {
            'action': enter_prompt,
            'args': (win, 0.2),
        },
    ]
    actions_cap_touch = [
        {
            'action': disable_power_check,
            'args': (),
        },
        # {
        #     'action': is_serial_ok,
        #     'args': (win.comports, task_mb.serial_ok),
        # },
        # {
        #     'action': enter_prompt,
        #     'args': (win, 0.2, 7),
        # },
    ]
    actions_rf = [
        {
            'action': disable_power_check,
            'args': (),
        },
        {
            'action': is_serial_ok,
            'args': (win.comports, task_mb.serial_ok),
        },
        {
            'action': enter_prompt,
            'args': (win, 0.2),
        },
    ]
    actions_wpc = [
        {
            'action': disable_power_check,
            'args': (),
        },
        {
            'action': is_serial_ok,
            'args': (win.comports, task_mb.serial_ok),
        },
    ]
    actions_ps = [
        {
            'action': disable_power_check,
            'args': (),
        },
        {
            'action': enter_prompt,
            'args': (win, 0.2),
        },
    ]
    actions_simu = [
        {
            'action': enter_prompt_simu,
            'args': (),
        },
        {
            'action': set_power_simu,
            'args': (win,),
        },
        {
            'action': dummy_com,
            'args': (task,),
        }
    ]

    actions = getattr(thismodule, f'actions_{map_[STATION]}')
    task.register_action(actions)

    print('main end')
    app.exec_()

import os
import sys
import json
import time
import random
import pickle
import serial
import threading
from operator import itemgetter
from collections import defaultdict
from subprocess import Popen, PIPE
from threading import Thread
from PyQt5.QtWidgets import (QTableWidgetItem, QLabel, QTableView,
                             QAbstractItemView, QHBoxLayout, QWidget,
                             QProgressDialog)
from PyQt5.QtCore import (QSettings, QThread, Qt, QTranslator, QCoreApplication,
                          pyqtSignal as QSignal)
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QErrorMessage
from PyQt5.QtGui import QFont, QColor

import pandas as pd

from view.pwd_dialog import PwdDialog
from view.barcode_dialog import BarcodeDialog
from view.loading_dialog import LoadingDialog

from serial.tools.list_ports import comports
from serials import (enter_factory_image_prompt, get_serial, se, get_device,
                     get_devices, is_serial_free, check_which_port_when_poweron,
                     filter_devices, BaseSerialListener)

from instrument import update_serial, open_all, generate_instruments, PowerSupply, DMM
from ui.design3 import Ui_MainWindow

from mylogger import logger


INSTRUMENT_MAP = {
    'gw_powersupply': PowerSupply,
    'gw_dmm': DMM,
}


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


class SerialListener(BaseSerialListener, ComportDUT, ComportPWR, ComportDMM):
    def __init__(self, *args, **kwargs):
        devices = kwargs.pop('devices')
        super(SerialListener, self).__init__(*args, **kwargs)
        self.is_reading = False
        self.is_instrument_ready = False
        self.set_devices(devices)

    def set_devices(self, devices):
        self.devices = devices
        for k,v in self.devices.items():
            setattr(self, f'ports_{k}', [])


def parse_json(jsonfile):
    x = json.loads(open(jsonfile, 'r', encoding='utf8').read())
    groups = defaultdict(list)
    cur_group = None
    x = x['structure']
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
        #  self.window.pushButton.setEnabled(True)
        signal_from.emit(False)
        return False
    else:
        print('all serial port are free!')
        signal_from.emit(True)
        return True


def set_power_simu(win):
    win.power_recieved = True
    win.simulation = True
    return True


def dummy_com(task):
    print('\n\ndummy com!!\n\n')
    i = 3
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
        #  self.power_process[idx] = proc
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


def enter_prompt(comports, ser_timeout=0.2):
    print('enter factory image prompt start')
    t0 = time.time()
    port_ser_thread = {}
    print('enter_prompt: comports - ', comports)
    for port in comports():
        ser = get_serial(port, 115200, ser_timeout)
        t = Thread(target=enter_factory_image_prompt, args=(ser, ))
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
    def __init__(self, json_name, settings, json_root='jsonfile'):
        super(Task, self).__init__()
        self.json_root = json_root
        self.json_name = json_name
        self.jsonfile = f'{json_root}/{json_name}.json'
        self.settings = settings
        self.base = json.loads(open(self.jsonfile, 'r', encoding='utf8').read())
        self.groups = parse_json(self.jsonfile)
        self.action_args = list()
        self.df = self.load()
        self.mylist = self.df.fillna('').values.tolist()
        self.duts = []
        self.instruments = generate_instruments(self.devices(), INSTRUMENT_MAP)

    @property
    def dut_num(self):
        return self.devices()['dut']['num']

    def load(self):
        header = self.base['header']
        header_dut = self.header_dut()
        df = pd.DataFrame(self.base['structure'])
        self.df = df = df[header]
        for col in header_dut:
            df[col] = None
        return df

    def __len__(self):
        return len(self.groups)

    def len(self, include_hidden=True):
        if include_hidden:
            return len(self.mylist)
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

    def devices(self):
        return self.base['devices']

    def header_dut(self, dut_names=None):
        if dut_names:
            return dut_names
        else:
            #  pcs = self.base['pcs']
            num = self.devices()['dut']['num']
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
        #  args = each['args'] if each['args'] else None
        return each, script, tasktype, args

    def rungroup(self, groupname):
        eachgroup, script, index, item_len, tasktype, args = self.unpack_group(
            groupname)
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
        port_dmm = self.instruments['gw_dmm'][0].com
        proc = Popen(['python', '-m', script, '-pm', port_dmm] +
                     [json.dumps(args)],
                     stdout=PIPE)
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
        msg2 = '[task %s][outputs: %s]' % (index, outputs)
        self.printterm_msg.emit(msg2)

        for idx, output in enumerate(outputs):
            result = json.dumps({'index': index, 'idx': idx, 'output': output})
            self.task_result.emit(result)

    def register_action(self, actions):
        print('register_action')
        for e in actions:
            action, args = e['action'], e['args']
            self.action_args.append([action, args])

    def run(self):
        print('show_animation_dialog True')
        self.window.show_animation_dialog.emit(True)
        for action, args in self.action_args:
            print('run action', action, args)
            if not action(*args):
                print('return !!!!!')
                return
        print('show_animation_dialog False')
        QThread.msleep(500)
        self.window.show_animation_dialog.emit(False)

        get_col = lambda arr, col: map(lambda x: x[col], arr)

        c1 = len(self.header())
        self.df.iloc[:, c1:c1 + 2] = ""

        for group, items in self.groups.items():
            i, next_item = items[0]['index'], items[0]
            print('i', i, 'next_item', next_item)
            if len(items) > 1:
                self.task_each.emit([i, len(items)])
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
                    output = [[
                        e
                    ] for e in get_col(output, self.window.dut_selected[0])]
                print('OUTPUT', output)

                self.df.iloc[r1:r2, c1:c2] = output
                self.task_result.emit(result)
            else:
                is_auto, task_type = next_item['auto'], next_item['tasktype']
                self.task_each.emit([i, 1])
                if is_auto:
                    procs = {}
                    for dut_idx, (port, barcode) in enumerate(self.window.port_barcodes.items()):
                    #  for port, barcode in self.window.port_barcodes.items():
                        if barcode:
                            print('i', i)
                            print('dut_idx', dut_idx)
                            print('barcode', barcode)
                            print('tasktype', task_type)
                            proc = self.runeach(i, dut_idx, barcode, task_type)
                            procs[port] = proc

                    print('procs', procs)
                    for j, (port, proc) in enumerate(procs.items()):
                        print('j', j, 'port', port, 'proc', proc)
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
                        self.task_result.emit(result)
                else:
                    ports = ','.join(self.window.comports())
                    self.runeachports(i, ports)
                QThread.msleep(500)
        self.df = self.df.fillna('')
        self.message.emit('tasks done')


class Settings():
    def __init__(self, key1, key2):
        self._settings = QSettings(key1, key2)

    def get(self, key, default, key_type):
        return self._settings.value(key, default, key_type)

    def set(self, key, value):
        self._settings.setValue(key, value)
        self.update()


class MySettings(Settings):
    lang_list = [
        'en_US',
        'zh_TW',
    ]
    def __init__(self):
        super(MySettings, self).__init__('FAB', 'SAP109')
        self.update()

    def update(self):
        self.is_fx1_checked = self.get('fixture_1', False, bool)
        self.is_fx2_checked = self.get('fixture_2', False, bool)
        self.lang_index = self.get('lang_index', 0, int)
        self.is_eng_mode_on = self.get('is_eng_mode_on', False, bool)

    @property
    def lang(self, lower=False):
        language = self.lang_list[self.lang_index]
        if lower: language = language.lower()
        return language


class MyWindow(QMainWindow, Ui_MainWindow):
    show_animation_dialog = QSignal(bool)

    def __init__(self, app, task, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.logfile = 'xxx.csv'
        self.simulation = False

        self.pwd_dialog = PwdDialog(self)
        self.barcode_dialog = BarcodeDialog(self)
        self.barcodes = []
        self.port_barcodes = {}

        self.set_task(task)
        self.settings = task.settings

        # Restore UI states
        self.checkBoxFx1.setChecked(self.settings.is_fx1_checked)
        self.checkBoxFx2.setChecked(self.settings.is_fx2_checked)
        self.langSelectMenu.setCurrentIndex(self.settings.lang_index)
        self.checkBoxEngMode.setChecked(self.settings.is_eng_mode_on)
        self.toggle_engineering_mode(self.settings.is_eng_mode_on)

        self._comports_dut = []
        self._comports_pwr = []
        self._comports_dmm = []

        update_serial(self.task.instruments, 'gw_powersupply', self._comports_pwr)
        update_serial(self.task.instruments, 'gw_dmm', self._comports_dmm)

        self.dut_layout = []
        colors = ['#edd', '#edd']
        for i in range(self.task.dut_num):
            c = QWidget()
            c.setStyleSheet(f'background-color:{colors[i]};')
            layout = QHBoxLayout(c)
            self.hboxPorts.addWidget(c)
            self.dut_layout.append(layout)

        self.setsignal()

        self.ser_listener = SerialListener(devices=self.task.devices())
        self.ser_listener.comports_dut.connect(self.ser_update)
        self.ser_listener.comports_pwr.connect(self.pwr_update)
        self.ser_listener.comports_dmm.connect(self.dmm_update)
        self.ser_listener.if_all_ready.connect(self.instrument_ready)
        self.ser_listener.start()

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

    def btn_detect(self):
        self.pushDetect.setText(f'{self.push_detect_text}...')
        print("btn_detect")
        self.pushDetect.setEnabled(False)
        t = threading.Thread(target=check_which_port_when_poweron,
                             args=(self._comports_dut, ))
        t.start()

    def btn_detect_mb_after(self):
        print('btn_detect_mb_after start')
        if self.port_autodecting:
            print('port_autodecting...')
            devices = get_devices()
            print('devices', devices)

            powers = list(
                filter(lambda x: x['name'] == 'gw_powersupply', devices))
            if len(powers) == 1:
                device_power1 = powers[0]
                power1 = self.task.instruments['gw_powersupply'][0]
                print('device_power1', device_power1)
                print('power1', power1)
                power1.com = device_power1['comport']
                self.poweron(power1)
            else:
                print('please only turn on #1 power')

            t = threading.Thread(target=check_which_port_when_poweron,
                                 args=(self._comports_dut, ))
            t.start()

    def btn_detect_mb(self):
        print("btn_detect_mb start")
        self.pushDetect.setText(
            f'#1 port auto detect... please turn on the #1 powersupply')
        self.pushDetect.setEnabled(False)
        self.port_autodecting = True

    def detect_received(self, comport_when_poweron_first_dut):
        print('detect_received start')
        if self._comports_dut[0] != comport_when_poweron_first_dut:
            print('reverse comport!!!')
            self._comports_dut[0], self._comports_dut[1] = self._comports_dut[
                1], self._comports_dut[0]
        self.render_port_plot()
        self.pushDetect.setEnabled(True)
        self.port_autodecting = False
        self.clean_power()
        self.pushDetect.setText(
            f"{self.push_detect_text} ---> {comport_when_poweron_first_dut}")

    def dummy_com(self, coms):
        self._comports_dut = coms
        self.instrument_ready(True)

    def clean_power(self):
        print('clean_power start')
        # prevent from last crash and power supply not closed normally
        update_serial(self.task.instruments, 'gw_powersupply', self._comports_pwr)
        for power in self.task.instruments['gw_powersupply']:
            if not power.is_open:
                power.open_com()
            if power.ser:
                power.off()
                power.close_com()
        print('clean_power end')

    def table_hidden_row(self):
        for i, each in enumerate(self.task.mylist):
            is_hidden = each[4]
            self.table_view.setRowHidden(i, is_hidden)

    def recieve_power(self, process_results):
        print('recieve_power', process_results)
        self.proc_listener.stop()
        self.power_results = process_results

        with open('power_results', 'w+') as f:
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
        self.table_view.setItem(self.task.len(), 0,
                                QTableWidgetItem(self.summary_text))

    def update_task(self, lang_folder):
        #  mainboard_task = Task(self.task_path)
        mainboard_task = Task(
            f'{self.jsonfileroot}/{lang_folder}/{self.jsonfilename}')
        print('update_task')
        self.set_task(mainboard_task)

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
        self.btn_detect_mb_after()

    def dmm_update(self, comports):
        print('dmm_update', comports)
        self._comports_dmm = comports
        update_serial(self.task.instruments, 'gw_dmm', comports)
        self.render_port_plot()
        self.btn_detect_mb_after()

    def ser_update(self, comports):
        print('ser_update', comports)
        self._comports_dut = comports
        self.barcodes = []
        for port in self._comports_dut:
            self.port_barcodes[port] = None
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
            'gw_dmm': self._comports_dmm
        }

        for i, e in enumerate(self.dut_layout, 1):
            self.clearlayout(e)
            e.addWidget(QLabel(f'#{i}'))

        for i, port in enumerate(self._comports_dut):
            print(f'port {i}: {port}')
            lb_port = QLabel(port)
            lb_port.setStyleSheet(style_('#369'))
            self.dut_layout[i].addWidget(lb_port)

        colors_inst = {'gw_powersupply': '#712', 'gw_dmm': '#4a3'}
        for name, num in self.task.instruments.items():
            print('name', name, 'num', num)
            each_instruments = self.task.instruments[name]
            for i, e in enumerate(each_instruments):
                print(
                    f'[inst: {e.NAME}] [{e}] [index: {e.index}] [{i}] [{e.com}]'
                )

                if e.com in comports_map[name]:
                    lb_port = QLabel(e.com)
                    lb_port.setStyleSheet(style_(colors_inst[name]))
                    self.dut_layout[i].addWidget(lb_port)

        for i in range(self.task.dut_num):
            self.dut_layout[i].addStretch()

    def instrument_ready(self, ready):
        if ready:
            self.pushButton.setEnabled(True)
            print('\nREADY\n!')
            self.clean_power()

            # order: power1,power2, dmm1
            instruments_to_dump = sum(self.task.instruments.values(), [])
            with open('instruments', 'wb') as f:
                pickle.dump(instruments_to_dump, f)
        else:
            self.pushButton.setEnabled(False)
            print('\nNOT READY\n!')

    def comports(self):
        return self._comports_dut

    def setsignal(self):
        self.checkBoxFx1.stateChanged.connect(self.chk_box_fx1_state_changed)
        self.checkBoxFx2.stateChanged.connect(self.chk_box_fx2_state_changed)
        self.langSelectMenu.currentIndexChanged.connect(self.on_lang_changed)
        self.checkBoxEngMode.stateChanged.connect(self.eng_mode_state_changed)
        self.pwd_dialog.dialog_close.connect(self.on_pwd_dialog_close)
        #  self.pushDetect.clicked.connect(self.btn_detect)
        self.pushDetect.clicked.connect(self.btn_detect_mb)
        self.barcode_dialog.barcode_entered.connect(self.on_barcode_entered)
        self.barcode_dialog.barcode_dialog_closed.connect(
            self.on_barcode_dialog_closed)
        self.pushButton.clicked.connect(self.btn_clicked)
        self.task.task_result.connect(self.taskrun)
        self.task.task_each.connect(self.taskeach)
        self.task.message.connect(self.taskdone)
        se.serial_msg.connect(self.printterm1)
        se.detect_notice.connect(self.detect_received)
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
            print('taskeach selectRow', i)
            self.table_view.selectRow(i)

        self.table_view.setSelectionMode(QAbstractItemView.NoSelection)
        self.table_view.setFocusPolicy(Qt.NoFocus)

    def color_check(self, s):
        if s.startswith('Pass'):
            color = QColor(1, 255, 0)
        elif s.startswith('Fail'):
            color = QColor(255, 0, 0)
        else:
            color = QColor(255, 255, 255)
        return color

    def taskrun(self, result):
        ret = json.loads(result)
        idx = ret['index']

        if type(idx) == list:
            print('output', ret['output'])
            output = json.loads(ret['output'])

            for i in range(*idx):
                #  for j in range(self.task.dut_num):
                for j in self.dut_selected:
                    x = output[i - idx[0]][j]
                    self.table_view.setItem(i, self.col_dut_start + j,
                                            QTableWidgetItem(x))
                    self.table_view.item(i,
                                         self.col_dut_start + j).setBackground(
                                             self.color_check(x))
        else:
            output = str(ret['output'])
            print('runeach output', output)
            print('self.comports', self.comports())
            if 'port' in ret:
                port = ret['port']
                #  j = self.comports.index(port)
                j = self.comports().index(port)
            elif 'idx' in ret:
                j = ret['idx']
            print('task %s are done, j=%s' % (idx, j))
            self.table_view.setItem(idx, self.col_dut_start + j,
                                    QTableWidgetItem(output))
            self.table_view.item(idx, self.col_dut_start + j).setBackground(
                self.color_check(output))

    def taskdone(self, message):
        print('taskdone start !')
        self.taskdone_first = True
        self.table_view.setSelectionMode(QAbstractItemView.NoSelection)
        if message.startswith('tasks done') and self.power_recieved:
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
            all_pass = lambda results: all(
                e.startswith('Pass') for e in results)
            d = self.task.df
            all_res = []

            print('\n\n')
            print(d)
            print(d.columns)
            print(d.columns[-2])

            for j in self.dut_selected:
                res = 'Pass' if all_pass(
                    d[d.hidden == False][d.columns[-2 + j]]) else 'Fail'
                self.table_view.setItem(r, self.col_dut_start + j,
                                        QTableWidgetItem(res))
                self.table_view.item(r, self.col_dut_start + j).setBackground(
                    self.color_check(res))

                df = d[d.hidden == False]
                dd = pd.DataFrame(df[[d.columns[-2 + j]]].values.T)
                dd.index = [random.randint(1000, 9999)]
                dd.index.name = 'pid'
                all_res.append(res)
                with open(self.logfile, 'a') as f:
                    dd.to_csv(f, mode='a', header=f.tell() == 0, sep=',')

            self.set_window_color('pass' if all(e == 'Pass'
                                                for e in all_res) else 'fail')

            self.table_view.setFocusPolicy(Qt.NoFocus)
            self.table_view.clearFocus()
            self.table_view.clearSelection()
            self.taskdone_first = False
            self.power_recieved = False

            if os.path.isfile('power_results'):
                os.remove('power_results')

    def show_barcode_dialog(self):
        print('show_barcode_dialog start')
        s = [self.checkBoxFx1.isChecked(), self.checkBoxFx2.isChecked()]
        num = len(list(filter(lambda x: x == True, s)))
        self.barcode_dialog.set_total_barcode(num)
        if num > 0:
            self.barcode_dialog.show()
        print('show_barcode_dialog end')

    def btn_clicked(self):
        print('btn_clicked')
        self.barcodes = []
        for port in self._comports_dut:
            self.port_barcodes[port] = None
        if (not self.checkBoxFx1.isChecked()) and (
                not self.checkBoxFx2.isChecked()):
            e_msg = QErrorMessage(self)
            e_msg.showMessage(self.both_fx_not_checked_err)
            return
        self.show_barcode_dialog()
        self.set_window_color('default')
        for i in range(self.task.len() + 1):
            for j in range(self.task.dut_num):
                self.table_view.setItem(i, self.col_dut_start + j,
                                        QTableWidgetItem(""))

    def closeEvent(self, event):
        print('closeEvent')
        for power in self.task.instruments['gw_powersupply']:
            if power.is_open:
                power.off()
        event.accept()  # let the window close

    def chk_box_fx1_state_changed(self, status):
        #  self.settings.setValue("fixture_1", status == Qt.Checked)
        self.settings.set("fixture_1", status == Qt.Checked)
        print('chk_box_fx1_state_changed', self.settings.is_fx1_checked)

    def chk_box_fx2_state_changed(self, status):
        #  self.settings.setValue("fixture_2", status == Qt.Checked)
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
        #  self.settings.setValue("is_eng_mode_on", is_on)
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
        translator.load(f"translate/{lang_list[index]}")
        app.removeTranslator(translator)
        app.installTranslator(translator)
        self.retranslateUi(self)
        self.pwd_dialog.retranslateUi(self.pwd_dialog)
        self.barcode_dialog.retranslateUi(self.barcode_dialog)
        self.pushDetect.setToolTip(self.push_detect_tooltip_text)

    def on_barcode_entered(self, barcode):
        print(barcode)
        self.barcodes.append(barcode)

    def on_barcode_dialog_closed(self):
        """
        When the barcode(s) are ready, start testing
        """
        is_1 = self.settings.is_fx1_checked
        is_2 = self.settings.is_fx2_checked
        print('is_1', is_1, 'is_2', is_2)
        dut_selected = [
            w[0] for w in filter(lambda e: e[1], enumerate([is_1, is_2]))
        ]
        self.dut_selected = dut_selected
        print('dut_selected', dut_selected)

        header = self.task.header_ext()

        for j, dut_i in enumerate(dut_selected):
            header[-2 + dut_i] = f'#{dut_i+1} - {self.barcodes[j]}'
            port = self._comports_dut[dut_i]
            self.port_barcodes[port] = self.barcodes[j]
        print('header', header)
        print('port_barcodes', self.port_barcodes)

        self.table_view.setHorizontalHeaderLabels(header)

        self.pushButton.setEnabled(False)
        self.ser_listener.stop()
        self.task.start()

    def toggle_loading_dialog(self, is_on=False):
        if hasattr(self, 'loading_dialog'):
            print("has dialog")
        else:
            print("no dialog")
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
        self.push_detect_text = _translate("MainWindow", "#1 port auto detect")
        self.push_detect_tooltip_text = _translate(
            "MainWindow",
            "Press this button and power on the first DUT to calibrate the COM ports"
        )
        self.push_detect_tooltip_text = _translate(
            "MainWindow",
            "Press this button and power on the first DUT to calibrate the COM ports"
        )
        self.both_fx_not_checked_err = _translate(
            "MainWindow", "At least one of the fixture should be checked")


if __name__ == "__main__":

    thismodule = sys.modules[__name__]

    STATION = 'LED'
    STATION = 'SIMULATION'
    STATION = 'MainBoard'

    app = QApplication(sys.argv)
    mysetting = MySettings()
    #  task_mb = Task('v4_total_two_dut', mysetting)
    task_mb = Task('v4_total_test1', mysetting)
    task_led = Task('v4_led', mysetting)
    task_simu = Task('v4_total_test1', mysetting)

    map_ = {
        'MainBoard': 'mb',
        'LED': 'led',
        'SIMULATION': 'simu'
    }

    task = getattr(thismodule, f'task_{map_[STATION]}')
    win = MyWindow(app, task)

    if STATION == 'SIMULATION':
        win.dummy_com(['COM8', 'COM3'])

    actions_mb = [
        {
            'action': is_serial_ok,
            'args': (win.comports, task_mb.serial_ok)
        },
        {
            'action': set_power,
            'args': (win.power_process, win.proc_listener)
        },
        {
            'action': enter_prompt,
            'args': (win.comports, 0.2)
        },
    ]
    actions_led = [
        {
            'action': is_serial_ok,
            'args': (win.comports, task_mb.serial_ok)
        },
        {
            'action': enter_prompt,
            'args': (win.comports, 0.2)
        },
    ]
    actions_simu = [
        {
            'action': enter_prompt_simu,
            'args': ()
        },
        {
            'action': set_power_simu,
            'args': (win,)
        },
        {
            'action': dummy_com,
            'args': (task,)
        }
    ]

    actions = getattr(thismodule, f'actions_{map_[STATION]}')
    task.register_action(actions)

    print('main end')
    try:
        app.exec_()
    except Exception as ex:
        print(f'\n\ncatch!!!\n{ex}')
        raise ex


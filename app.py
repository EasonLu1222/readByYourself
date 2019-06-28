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
                             QAbstractItemView, QHBoxLayout, QWidget, QProgressDialog)
from PyQt5.QtCore import (QSettings, QThread, Qt, QTranslator, QCoreApplication,
                          pyqtSignal as QSignal)
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton
from PyQt5.QtGui import QFont, QColor

import pandas as pd

from view.myview import TableView
from view.pwd_dialog import PwdDialog
from view.barcode_dialog import BarcodeDialog
from view.loading_dialog import LoadingDialog

from serial.tools.list_ports import comports
from serials import (enter_factory_image_prompt, get_serial, se, get_device,
                     get_devices, is_serial_free, check_which_port_when_poweron)

from instrument import update_serial, open_all, generate_instruments
from ui.design3 import Ui_MainWindow

from mylogger import logger

dmm1, power1, power2 = open_all()


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


class SerialListener(QThread):
    update_msec = 500
    comports = QSignal(list)
    comports_instrument = QSignal(list)
    if_all_ready = QSignal(bool)

    def __init__(self, *args, **kwargs):
        super(SerialListener, self).__init__(*args, **kwargs)
        self.is_reading = False

        self.ports = []
        self.instruments = []
        self.is_instrument_ready = False

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

    def run(self):
        while True:
            QThread.msleep(SerialListener.update_msec)
            self.is_reading = True
            devices = get_devices()
            ports = [
                e['comport']
                for e in [e for e in devices if e['name'] == 'cygnal_cp2102']
            ]
            instruments = [
                e['comport'] for e in [
                    e for e in devices
                    if e['name'] in ['gw_powersupply', 'gw_dmm']
                ]
            ]
            self.is_reading = False

            if self.update(self.ports, ports):
                self.comports.emit(self.ports)

            # update comport of intruments
            if self.update(self.instruments, instruments):
                #  update_serial([dmm1, power1, power2])
                self.comports_instrument.emit(self.instruments)

            if not self.is_instrument_ready and len(self.instruments) == 3:
                self.is_instrument_ready = True
                self.if_all_ready.emit(True)

            if self.is_instrument_ready and len(self.instruments) < 3:
                self.is_instrument_ready = False
                self.if_all_ready.emit(False)

    def stop(self):
        # wait 1s for list_ports to finish, is it enough or too long in order
        # not to occupy com port for subsequent test scripts
        if self.is_reading:
            print('is_reading!')
            QThread.msleep(1000)
        self.terminate()


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
        t = Thread(target=enter_factory_image_prompt, args=(ser,))
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

    def __init__(self, jsonfile):
        super(Task, self).__init__()
        self.base = json.loads(open(jsonfile, 'r', encoding='utf8').read())
        self.groups = parse_json(jsonfile)
        self.action_args = list()
        self.df = self.load()
        self.mylist = self.df.fillna('').values.tolist()
        self.duts = []

    @property
    def dut_num(self):
        return int(self.base['pcs'])

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

    def instruments(self):
        return self.base['instruments']

    def header_dut(self, dut_names=None):
        if dut_names:
            return dut_names
        else:
            pcs = self.base['pcs']
            header = ['#%d' % e for e in list(range(1, 1 + pcs))]
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
        args = [str(e) for e in line[1]] if each['args'] else []
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
            xx = {i:j for i,j in zip(e,limits_group)}
            limits.update(xx)

        #  A = [{i:j for i,j in zip(each_arg, limits_group)} for each_arg in args]

        print('limits', limits)

        args = {'args': args, 'limits':limits}

        port_dmm = dmm1.com
        proc = Popen(['python', '-m', script, '-pm', port_dmm] +
                     [json.dumps(args)],
                     stdout=PIPE)
        return proc

    def runeach(self, index, port, tasktype):
        each, script, tasktype, args = self.unpack_each(index)
        msg = f'[runeach][script: {script}][index: {index}][type: {tasktype}][port: {port}][args: {args}]'
        print(msg)
        if tasktype == 1:
            proc = Popen(['python', '-m', script, '-p', port] + args,
                         stdout=PIPE)

        elif tasktype == 3:
            ports = self.window.comports()
            print(f'window.comports(): {self.window.comports()}')
            power_index = self.window.comports().index(port)+1
            print('power_index', power_index)
            args = [str(power_index)]
            proc = Popen(['python', '-m', script] + args, stdout=PIPE)

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
        for action, args in self.action_args:
            print('run action', action, args)
            if not action(*args):
                print('return !!!!!')
                return
        QThread.msleep(500)
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

                r1, r2 = i, i+len(items)
                c1, c2 = len(self.header()), len(self.header())+self.dut_num
                self.df.iloc[r1:r2,c1:c2] = json.loads(output)


                self.task_result.emit(result)
            else:
                is_auto, task_type = next_item['auto'], next_item['tasktype']
                self.task_each.emit([i, 1])


                if is_auto:
                    procs = {}
                    #  for port in self.window.comports:
                    for port in self.window.comports():
                        proc = self.runeach(i, port, task_type)
                        procs[port] = proc

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
                        self.df.iat[i,len(self.header())+j] = output
                        print('run: result', result)
                        self.task_result.emit(result)

                else:
                    #  ports = ','.join(self.window.comports)
                    ports = ','.join(self.window.comports())
                    self.runeachports(i, ports)

                QThread.msleep(500)

        self.df = self.df.fillna('')
        self.message.emit('tasks done')


class TaskSimu(Task):

    def rungroup(self, groupname):
        eachgroup, script, index, item_len, tasktype, args = self.unpack_group(
            groupname)
        print(
            f'[rungroup][script: {script}][index: {index}][len: {item_len}][args: {args}]'
        )
        port_dmm = random.choice(f'COM{random.choice([3,5,8,9,12])}')
        proc = Popen(['python', '-m', script, '-pm', port_dmm] +
                     [json.dumps(args)],
                     stdout=PIPE)
        return proc

    def runeach(self, index, port, tasktype):
        each, script, tasktype, args = self.unpack_each(index)
        if tasktype == 1:
            msg = '\n[runeach][script: %s][index: %s][port: %s][args: %s]' % (
                script, index, port, args)
            proc = Popen(['python', '-m', script, '-p', port] + args,
                         stdout=PIPE)

        elif tasktype == 3:
            msg = '\n[runeach3][script: %s][index: %s][args: %s]' % (
                script, index, args)
            x = {'COM3': 2, 'COM11': 1}  # <-- hard coded!!! To Be Modified
            args = [str(x[port])]
            proc = Popen(['python', '-m', script] + args, stdout=PIPE)

        self.printterm_msg.emit(msg)
        print(msg)
        return proc


class MyWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, app, jsonfile, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.logfile = 'xxx.csv'

        self.pwd_dialog = PwdDialog(self)
        self.barcode_dialog = BarcodeDialog(self)
        self.loading_dialog = LoadingDialog(self)

        self.jsonfileroot = 'jsonfile'
        self.jsonfilename = jsonfile

        # Read UI states from app settings
        self.settings = QSettings("FAB", "SAP109")
        is_fx1_checked = self.settings.value("fixture_1", False, type=bool)
        is_fx2_checked = self.settings.value("fixture_2", False, type=bool)
        lang_index = self.settings.value("lang_index", 0, type=int)
        is_eng_mode_on = self.settings.value("is_eng_mode_on", False, type=bool)

        # Restore UI states
        self.checkBoxFx1.setChecked(is_fx1_checked)
        self.checkBoxFx2.setChecked(is_fx2_checked)
        self.langSelectMenu.setCurrentIndex(lang_index)
        self.on_lang_changed(lang_index)
        self.checkBoxEngMode.setChecked(is_eng_mode_on)
        self.toggle_engineering_mode(is_eng_mode_on)

        self._comports = []
        self._comports_inst = []

        self.instruments = generate_instruments(self.task.instruments())
        instruments_array = sum(self.instruments.values(), [])
        update_serial(instruments_array)


        # proto for port-auto-dectect button
        self.push_detect = QPushButton()
        self.push_detect.resize(200,30)
        self.push_detect.setText("#1 port auto detect")
        self.push_detect.clicked.connect(self.btn_detect)
        self.hbox_ports.addWidget(self.push_detect)

        self.dut_layout = []
        colors = ['#edd', '#edd']
        for i in range(self.task.dut_num):
            c = QWidget()
            c.setStyleSheet(f'background-color:{colors[i]};')
            layout = QHBoxLayout(c)
            self.hbox_ports.addWidget(c)
            self.dut_layout.append(layout)

        self.setsignal()

        self.ser_listener = SerialListener()
        self.ser_listener.comports.connect(self.ser_update)
        self.ser_listener.comports_instrument.connect(self.instrument_update)
        self.ser_listener.if_all_ready.connect(self.instrument_ready)
        self.ser_listener.start()

        self.proc_listener = ProcessListener()
        self.proc_listener.process_results.connect(self.recieve_power)
        self.power_recieved = False

        self.pushButton.setEnabled(False)

        # for simulation without serial devices
        #  self.pushButtonM = QPushButton(self.centralwidget)
        #  self.pushButtonM.setText("SimulateRun")
        #  self.pushButtonM.clicked.connect(self.btn_clickedM)

        self.showMaximized()

        self.power_process = {}
        self.power_results = {}

        self.col_dut_start = len(self.task.header())
        self.table_hidden_row()
        self.clean_power()
        self.taskdone_first = False

    def btn_detect(self):
        self.push_detect.setText(f'#1 port auto detect...')
        print("btn_detect")
        self.push_detect.setEnabled(False)
        t = threading.Thread(target=check_which_port_when_poweron, args=(self._comports,))
        t.start()

    def detect_received(self, comport_when_poweron_first_dut):
        print('detect_received')
        if self._comports[0]!=comport_when_poweron_first_dut:
            print('reverse comport!!!')
            self._comports[0], self._comports[1] = self._comports[1], self._comports[0]
        self.render_port_plot()
        self.push_detect.setEnabled(True)
        self.push_detect.setText(f"#1 port auto detect ---> {comport_when_poweron_first_dut}")

    def dummy_com(self, coms):
        self._comports = coms

    def clean_power(self):
        # prevent from last crash and power supply not closed normally
        update_serial([dmm1, power1, power2])
        if not power1.is_open:
            power1.open_com()
        if not power2.is_open:
            power2.open_com()
        if power1.ser:
            power1.off()
            power1.close_com()
        if power2.ser:
            power2.off()
            power2.close_com()

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
            print('\nCCCCCC')
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

    def update_task(self, lang_folder):
        #  mainboard_task = Task(self.task_path)
        mainboard_task = Task(f'{self.jsonfileroot}/{lang_folder}/{self.jsonfilename}')
        print('update_task')
        self.set_task(mainboard_task)

    def auto_align_com_port(self):
        self._comports_inst

    def poweron(self, power):
        if not power.is_open:
            power.open_com()
            power.on()

    #  def set_power(self):
        #  script = 'tasks.poweron'
        #  for idx in range(1, 3):
            #  args = [str(idx)]
            #  proc = Popen(['python', '-m', script] + args, stdout=PIPE)
            #  self.power_process[idx] = proc
        #  self.proc_listener.set_process(self.power_process)
        #  self.proc_listener.start()

    def clearlayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def instrument_update(self, comports):
        print('instrument_update', comports)
        self._comports_inst = comports
        instruments_array = sum(self.instruments.values(), [])
        update_serial(instruments_array)

        self.render_port_plot()

    def ser_update(self, comports):
        print('ser_update', comports)
        self._comports = comports
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
                }""" % (color,)

        for i, e in enumerate(self.dut_layout, 1):
            self.clearlayout(e)
            e.addWidget(QLabel(f'#{i}'))

        for i, port in enumerate(self._comports):
            print(f'port {i}: {port}')
            lb_port = QLabel(port)
            lb_port.setStyleSheet(style_('#369'))
            self.dut_layout[i].addWidget(lb_port)

        colors_inst = {'gw_powersupply': '#712', 'gw_dmm': '#4a3'}
        for name, num in self.task.instruments().items():
            print('name', name, 'num', num)
            each_instruments = self.instruments[name]
            for i, e in enumerate(each_instruments):
                print(f'[inst: {e.NAME}] [{e}] [index: {e.index}] [{i}] [{e.com}]')
                if e.com in self._comports_inst:
                    lb_port = QLabel(e.com)
                    lb_port.setStyleSheet(style_(colors_inst[name]))
                    self.dut_layout[i].addWidget(lb_port)

        for i in range(self.task.dut_num):
            self.dut_layout[i].addStretch()

    def instrument_ready(self, ready):
        if ready:
            self.pushButton.setEnabled(True)
            print('\nREADY\n!')

            #  with open('instruments', 'wb') as f:
                #  pickle.dump([dmm1, power1, power2], f)

            # order: power1,power2, dmm1
            instruments_to_dump = sum(self.instruments.values(), [])

            with open('instruments', 'wb') as f:
                pickle.dump(instruments_to_dump, f)
        else:
            self.pushButton.setEnabled(False)
            print('\nNOT READY\n!')

    def comports(self):
        return self._comports

    def setsignal(self):
        self.checkBoxFx1.stateChanged.connect(self.chk_box_fx1_state_changed)
        self.checkBoxFx2.stateChanged.connect(self.chk_box_fx2_state_changed)
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
                for j in range(self.task.dut_num):
                    x = output[i - idx[0]][j]
                    self.table_view.setItem(i, self.col_dut_start+j,
                                            QTableWidgetItem(x))
                    self.table_view.item(i, self.col_dut_start+j).setBackground(
                        self.color_check(x))

                # DUT1
                #  x1 = output[i - idx[0]][0]
                #  self.table_view.setItem(i, self.col_dut_start,
                                        #  QTableWidgetItem(x1))
                #  self.table_view.item(i, self.col_dut_start).setBackground(
                    #  self.color_check(x1))

                # DUT2
                #  x2 = output[i - idx[0]][1]
                #  self.table_view.setItem(i, self.col_dut_start + 1,
                                        #  QTableWidgetItem(x2))
                #  self.table_view.item(i, self.col_dut_start + 1).setBackground(
                    #  self.color_check(x2))

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
        #  if message.startswith('tasks done'):
            self.pushButton.setEnabled(True)
            self.ser_listener.start()

            if not power1.is_open:
                power1.open_com()
            if not power2.is_open:
                power2.open_com()

            if power1.ser:
                power1.off()
                power1.close_com()
            if power2.ser:
                power2.off()
                power2.close_com()

            r = self.task.len()
            all_pass = lambda results: all(e.startswith('Pass') for e in results)

            d = self.task.df
            for j in range(self.task.dut_num):
                res = 'Pass' if all_pass(d[d.hidden==False][f'#{j+1}']) else 'Fail'
                self.table_view.setItem(r, self.col_dut_start + j,
                                        QTableWidgetItem(res))
                self.table_view.item(r, self.col_dut_start + j).setBackground(
                    self.color_check(res))


                df = d[d.hidden==False]
                dd = pd.DataFrame(df[[f'#{j+1}']].values.T)
                dd.index = [random.randint(1000,9999)]
                dd.index.name = 'pid'
                with open(self.logfile, 'a') as f:
                    dd.to_csv(f, mode='a', header=f.tell()==0, sep=',')


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
        num = len(list(filter(lambda x: x==True, s)))
        self.barcode_dialog.set_total_barcode(num)

        if num>0:
            self.barcode_dialog.show()
        print('show_barcode_dialog end')

    def btn_clicked(self):
        print('btn_clicked')
        self.show_barcode_dialog()

    def btn_clickedM(self):
        print('btn_clickedM')
        self.show_barcode_dialog()
        #  for i in range(len(self.task.mylist)):
            #  for j in range(2):
                #  self.table_view.setItem(i, self.col_dut_start + j,
                                        #  QTableWidgetItem(""))
        #  self.task.start()

    def closeEvent(self, event):
        print('closeEvent')
        if power1.is_open:
            power1.off()
        if power2.is_open:
            power2.off()
        event.accept()  # let the window close

    def chk_box_fx1_state_changed(self, status):
        self.settings.setValue("fixture_1", status == Qt.Checked)

    def chk_box_fx2_state_changed(self, status):
        self.settings.setValue("fixture_2", status == Qt.Checked)

    def on_pwd_dialog_close(self, is_eng_mode_on):
        if(not is_eng_mode_on):
            self.checkBoxEngMode.setChecked(False)
    
    def eng_mode_state_changed(self, status):
        self.toggle_engineering_mode(status == Qt.Checked)
        if (status == Qt.Checked):
            self.pwd_dialog.show()

    def toggle_engineering_mode(self, is_on):
        self.settings.setValue("is_eng_mode_on", is_on)
        if is_on:
            self.splitter.show()
        else:
            self.splitter.hide()

    def on_lang_changed(self, index):
        """
        When language is changed, update UI
        """
        self.settings.setValue("lang_index", index)
        lang_list = ['en_US.qm', 'zh_TW.qm']
        app = QApplication.instance()
        translator = QTranslator()
        translator.load(f"translate/{lang_list[index]}")
        app.removeTranslator(translator)
        app.installTranslator(translator)

        self.retranslateUi(self)
        self.pwd_dialog.retranslateUi(self.pwd_dialog)
        self.barcode_dialog.retranslateUi(self.barcode_dialog)
        
        # Retrieve the translated task list(json file)
        lang_folder = lang_list[index].split(".")[0]
        self.update_task(lang_folder)

    def on_barcode_entered(self, barcode):
        print(barcode)

    def on_barcode_dialog_closed(self):
        """
        When the barcode(s) are ready, start testing
        """
        for i in range(self.task.len()+1):
            for j in range(self.task.dut_num):
                self.table_view.setItem(i, self.col_dut_start + j,
                                        QTableWidgetItem(""))
        self.pushButton.setEnabled(False)
        self.ser_listener.stop()
        self.task.start()
    
    def toggle_loading_dialog(self, is_on=False):
        if is_on:
            loading_dialog.show()
        else:
            loading_dialog.done(1)
        
    def retranslateUi(self, MyWindow):
        super().retranslateUi(self)
        _translate = QCoreApplication.translate
        self.summary_text = _translate("MainWindow", "Summary")



if __name__ == "__main__":

    app = QApplication(sys.argv)

    mb_task = Task('jsonfile/v3_total_two_dut.json')
    simu_task = TaskSimu('jsonfile/v3_simu1.json')

    jsonfilename = 'v3_total_two_dut.json'
    win = MyWindow(app, jsonfilename)

    actions = [
        {
            'action': is_serial_ok,
            'args': (win.comports, mb_task.serial_ok)
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
    actions_simu = [
        {
            'action': enter_prompt_simu,
            'args': ()
        },
    ]

    win.task.register_action(actions)
    print('main end')

    # for simulated tasks
    #  win.dummy_com(['COM8', 'COM3'])

    try:
        app.exec_()
    except Exception as ex:
        print(f'\n\ncatch!!!\n{ex}')
        raise ex

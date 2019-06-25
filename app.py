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
import configparser
from subprocess import Popen, PIPE
from threading import Thread
import operator
from PyQt5.QtWidgets import (QWidget, QTableWidgetItem, QTreeView, QHeaderView,
                             QLabel, QSpacerItem, QTableView, QAbstractItemView)
from PyQt5.QtCore import (QAbstractTableModel, QModelIndex, QThread, QTimer, Qt,
                          pyqtSignal as QSignal, QRect, QItemSelectionModel)
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow, QPushButton

import pandas as pd

from view.myview import TableView
from model import TableModelTask
from ui.design3 import Ui_MainWindow
from utils import test_data, move_mainwindow_centered

from serial.tools.list_ports import comports
from serials import (enter_factory_image_prompt, get_serial, se, get_device,
                     get_devices, is_serial_free)

from instrument import update_serial, open_all

dmm1, power1, power2 = open_all()


class ProcessListener(QThread):
    process_results = QSignal(dict)

    def __init__(self):
        super(ProcessListener, self).__init__()

    def set_process(self, processes):
        self.processes = processes

    def run(self):
        outputs = {}
        for pid, proc in self.processes.items():
            output, _ = proc.communicate()
            output = output.decode('utf8')
            outputs[pid] = float(output)
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
                update_serial([dmm1, power1, power2])
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
    x = json.loads(open(jsonfile, 'r').read())
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
        t = Thread(target=enter_factory_image_prompt, args=(ser, 1))
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
    #  task_each = QSignal(int)
    task_each = QSignal(list)
    task_result = QSignal(str)
    serial_ok = QSignal(bool)
    message = QSignal(str)
    printterm_msg = QSignal(str)

    #  def __init__(self, jsonfile, mainwindow=None):
    def __init__(self, jsonfile):
        super(Task, self).__init__()
        self.base = json.loads(open(jsonfile, 'r').read())
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
        each = self.each(key, idx)
        min_, expect, max_ = itemgetter('min', 'expect', 'max')(each)
        return (min_, expect, max_)

    def instruments(self):
        self.base['instruments']

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
        port_dmm = dmm1.com
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

    def __init__(self, app, task, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.modUi()
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self._comports = []
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
        self.table_view.setItem(self.task.len(), 0, QTableWidgetItem('Summary'))

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
        self.show()

        self.power_process = {}
        self.power_results = {}

        self.col_dut_start = len(self.task.header())
        self.table_hidden_row()
        self.clean_power()
        self.taskdone_first = False

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
        self.power_recieved = True
        if self.taskdone_first:
            self.taskdone('tasks done')

    def set_power(self):
        script = 'tasks.poweron'
        for idx in range(1, 3):
            args = [str(idx)]
            proc = Popen(['python', '-m', script] + args, stdout=PIPE)
            self.power_process[idx] = proc
        self.proc_listener.set_process(self.power_process)
        self.proc_listener.start()

    def modUi(self):
        self.edit1.setStyleSheet("""
            QPlainTextEdit {
                font-family: Arial Narrow;
                font-size: 10pt;
            }
        """)
        self.edit2.setStyleSheet("""
            QPlainTextEdit {
                font-family: Arial Narrow;
                font-size: 12pt;
            }
        """)

    def clearlayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def instrument_update(self, comports):
        print('instrument_update', comports)

    def instrument_ready(self, ready):
        if ready:
            self.pushButton.setEnabled(True)
            print('\nREADY\n!')
            with open('instruments', 'wb') as f:
                pickle.dump([dmm1, power1, power2], f)
        else:
            self.pushButton.setEnabled(False)
            print('\nNOT READY\n!')

    def comports(self):
        return self._comports

    #  @comports.setter
    #  def comports(self, ports):
    #  self._comports = ports

    def ser_update(self, comports):
        print('ser_update', comports)
        self._comports = comports
        self.clearlayout(self.hbox_ports)
        for port in self._comports:
            lb_port = QLabel(port)
            lb_port.setStyleSheet("""
                QLabel {
                    padding: 6px;
                    background: #369;
                    color: white;
                    border: 0;
                    border-radius: 3px;
                    outline: 0px;
                    font-family: Courier;
                    font-size: 16px;
                }
            #  """)
            self.hbox_ports.addWidget(lb_port)
        self.hbox_ports.addStretch()

    def setsignal(self):
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
        #  if message.startswith('tasks done') and self.power_recieved:
        if message.startswith('tasks done'):
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
            all_pass = lambda results: all(e.startswith('Pass') and not e for e in results)

            for j in range(self.task.dut_num):
                res = 'Pass' if all_pass(self.task.df[f'#{j+1}']) else 'Fail'
                self.table_view.setItem(r, self.col_dut_start + j,
                                        QTableWidgetItem(res))
                self.table_view.item(r, self.col_dut_start + j).setBackground(
                    self.color_check(res))

            #  __import__('ipdb').set_trace()
            self.table_view.setFocusPolicy(Qt.NoFocus)
            self.table_view.clearFocus()
            self.table_view.clearSelection()
            self.taskdone_first = False
            self.power_recieved = False

    def btn_clickedM(self):
        for i in range(len(self.task.mylist)):
            for j in range(2):
                self.table_view.setItem(i, self.col_dut_start + j,
                                        QTableWidgetItem(""))
        self.task.start()

    def btn_clicked(self):
        print('btn_clicked')

        for i in range(self.task.len()+1):
            for j in range(self.task.dut_num):
                self.table_view.setItem(i, self.col_dut_start + j,
                                        QTableWidgetItem(""))
        self.pushButton.setEnabled(False)
        self.ser_listener.stop()
        self.task.start()

    def closeEvent(self, event):
        print('closeEvent')
        if power1.is_open:
            power1.off()
        if power2.is_open:
            power2.off()
        event.accept()  # let the window close


if __name__ == "__main__":

    app = QApplication(sys.argv)

    mb_task = Task('jsonfile/v3_total2.json')
    simu_task = TaskSimu('jsonfile/v3_simu1.json')
    TASK = mb_task

    win = MyWindow(app, TASK)

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

    ACTIONS = actions
    TASK.register_action(ACTIONS)

    # for simulated tasks
    #  win.dummy_com(['COM8', 'COM3'])

    try:
        app.exec_()
    except Exception as ex:
        print(f'\n\ncatch!!!\n{ex}')
        raise ex

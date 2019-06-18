import os
import sys
import json
import time
import random
import pickle
import serial
from collections import defaultdict
import configparser
from subprocess import Popen, PIPE
from threading import Thread
import operator
from PyQt5.QtWidgets import (QWidget, QTableWidgetItem, QTreeView, QHeaderView,
                             QLabel, QSpacerItem)
from PyQt5.QtCore import (QAbstractTableModel, QModelIndex, QThread, QTimer, Qt, QTranslator,
                          pyqtSignal as QSignal, QRect)
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow

import pandas as pd

from view.myview import TableView
from model import TableModelTask
from ui.design3 import Ui_MainWindow
from utils import test_data, move_mainwindow_centered

from serial.tools.list_ports import comports
from serials import (enter_factory_image_prompt, get_serial,
                     se, get_device, get_devices, is_serial_free)

from instrument import update_serial, power1, power2, dmm1
from ui.fixture_select_dialog_class import FixtureSelectDialog


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
            ports = [e['comport'] for e in
                    [e for e in devices if e['name']=='cygnal_cp2102']]
            instruments = [e['comport'] for e in
                [e for e in devices if e['name'] in ['gw_powersupply', 'gw_dmm']]]
            self.is_reading = False

            if self.update(self.ports, ports):
                self.comports.emit(self.ports)

            # update comport of intruments
            if self.update(self.instruments, instruments):
                update_serial([dmm1, power1, power2])
                self.comports_instrument.emit(self.instruments)

            if not self.is_instrument_ready and len(self.instruments)==3:
                self.is_instrument_ready = True
                self.if_all_ready.emit(True)

            if self.is_instrument_ready and len(self.instruments)<3:
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
        #  print(e)
        groups[group_name].append(e)
    groups = {k:groups[k] for k in group_orders}

    idx = 0
    for k,items in groups.items():
        for e in items:
            e['index'] = idx
            idx += 1
    return groups


class Task(QThread):
    task_result = QSignal(str)
    message = QSignal(str)
    printterm_msg = QSignal(str)
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
    def __init__(self, jsonfile, mainwindow=None):
        super(Task, self).__init__(mainwindow)
        self.base = json.loads(open(jsonfile, 'r').read())
        self.groups = parse_json(jsonfile)

    def load(self):
        header = self.base['header']
        header_dut = self.header_dut()
        df = pd.DataFrame(self.base['structure'])
        self.df = df = df[header]
        for col in header_dut:
            df[col] = None
        return df

    def header_dut(self, dut_names=None):
        if dut_names:
            return dut_names
        else:
            pcs = self.base['pcs']
            header = ['#%d' % e for e in list(range(1,1+pcs))]
            return header

    def header(self):
        return self.base['header']

    def header_ext(self, dut_names=None):
        header_extension = dut_names if dut_names else self.header_dut()
        return self.header() + header_extension

    def runeach1(self, index, port, to_wait=False):
        line = self.df.values[index]
        script = 'tasks.%s' % line[0]
        args = [str(e) for e in line[1]] if line[1] else []
        msg1 = '\n[runeach1][script: %s][index: %s][port: %s][args: %s]' % (script, index, port, args)
        print(msg1)
        self.printterm_msg.emit(msg1)
        proc = Popen(['python', '-m', script, '-p', port] + args, stdout=PIPE)
        return proc

    def runeach2(self, groupname):
        group = self.groups[groupname]
        script = f'tasks.{group[0]["script"]}'
        index = group[0]['index']
        item_len = len(group)
        args = [g['args'] for g in group]
        print(f'[runeach2][script: {script}][index: {index}][len: {item_len}][args: {args}]')
        port_dmm = dmm1.com
        proc = Popen(['python', '-m', script, '-pm', port_dmm] + [json.dumps(args)], stdout=PIPE)
        return proc

    def runeach3(self, index, port):
        line = self.df.values[index]
        script = 'tasks.%s' % line[0]
        args = [str(e) for e in line[1]] if line[1] else []
        msg1 = '\n[runeach3][script: %s][index: %s][args: %s]' % (script, index, args)
        print(msg1)
        x = {'COM3': 2, 'COM11': 1}
        args = [str(x[port])]
        proc = Popen(['python', '-m', script] + args, stdout=PIPE)
        return proc

    def runeachports(self, index, ports):
        line = self.df.values[index]
        script = 'tasks.%s' % line[0]
        args = [str(e) for e in line[1]] if line[1] else []
        msg1 = '\n[runeachports][script: %s][index: %s][ports: %s][args: %s]' % (script, index, ports, args)

        print(msg1)
        self.printterm_msg.emit(msg1)

        proc = Popen(['python', '-m', script, '-pp', ports] + args, stdout=PIPE)

        outputs, _ = proc.communicate()
        outputs = outputs.decode('utf8')
        outputs = json.loads(outputs)
        msg2 = '[task %s][outputs: %s]' % (index, outputs)
        self.printterm_msg.emit(msg2)

        for idx, output in enumerate(outputs):
            result = json.dumps({'index':index, 'idx': idx, 'output': output})
            self.task_result.emit(result)

    def enter_prompt(self):
        print('enter factory image prompt start')
        t0 = time.time()

        port_ser_thread = {}
        for port in self.window.comports:
            #  ser = get_serial(port, 115200, timeout=1)
            ser = get_serial(port, 115200, timeout=0.2)

            #  t = Thread(target=enter_factory_image_prompt, args=(ser,))
            t = Thread(target=enter_factory_image_prompt, args=(ser, 0))
            port_ser_thread[port] = [ser, t]
            t.start()

        for port, (ser, th) in port_ser_thread.items():
            th.join()

        t1 = time.time()
        print('enter factory image prompt end')
        print('time elapsed entering prompt: %f' % (t1-t0))

        for port, (ser, th) in port_ser_thread.items():
            ser.close()

    def run(self):
        if not all(is_serial_free(p) for p in self.window.comports):
            print('not all serial port are free!')
            self.window.pushButton.setEnabled(True)
            return
        self.enter_prompt()
        QThread.msleep(500)

        #  for i in range(len(self.df)):
        for group, items in self.groups.items():
            i = items[0]['index']
            if len(items) > 1:
                proc = self.runeach2(group)
                output, _ = proc.communicate()
                output = output.decode('utf8')
                print('OUTPUT', output)

                msg2 = '[task %s][output: %s]' % ([i, i+len(items)], output)
                self.printterm_msg.emit(msg2)
                #  result = json.dumps({'index':[i, i+len(items)], 'output': output})
                result = json.dumps({'index':[i, i+len(items)], 'output': output})
                self.task_result.emit(result)
            else:
                line = self.df.values[i]
                is_auto = bool(line[2])
                task_type=  int(line[3])

                if is_auto:
                    procs = {}
                    if task_type == 3:
                        for port in self.window.comports:
                            proc = self.runeach3(i, port)
                            procs[port] = proc
                    else:
                        for port in self.window.comports:
                            proc = self.runeach1(i, port)
                            procs[port] = proc

                    for port, proc in procs.items():
                        output, _ = proc.communicate()
                        output = output.decode('utf8')
                        print('output', output)
                        msg2 = '[task %s][output: %s]' % (i, output)
                        self.printterm_msg.emit(msg2)
                        result = json.dumps({'index':i, 'port': port, 'output': output})
                        self.task_result.emit(result)

                else:
                    ports = ','.join(self.window.comports)
                    self.runeachports(i, ports)

            QThread.msleep(500)
        self.message.emit('tasks done')


class MyWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, app, task, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.modUi()
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.comports = []

        self.task = task
        task.window = self
        self.table_model = TableModelTask(self, task)
        self.table_view.setModel(self.table_model)
        for col in [0,1,2]:
            self.table_view.setColumnHidden(col, True)

        self.setsignal()

        self.ser_listener = SerialListener()
        self.ser_listener.comports.connect(self.ser_update)
        self.ser_listener.comports_instrument.connect(self.instrument_update)
        self.ser_listener.if_all_ready.connect(self.instrument_ready)
        self.ser_listener.start()
        self.proc_listener = ProcessListener()
        self.proc_listener.process_results.connect(self.recieve_power)

        self.pushButton.setEnabled(False)
        #  self.set_power_old()

        self.showMaximized()
        self.w = FixtureSelectDialog(self)
        self.w.show()

        self.power_process = {}
        self.power_results = {}

        self.col_dut_start = 10

    #  def set_power_old(self):
        #  update_serial([power1, power2])
        #  if not power1.is_open:
            #  power1.open_com()
        #  if not power2.is_open:
            #  power2.open_com()
        #  power1.on()
        #  power2.on()

    def recieve_power(self, process_results):
        print('recieve_power', process_results)
        self.proc_listener.stop()
        self.power_results = process_results
        with open('power_results' , 'w+') as f:
            f.write(json.dumps(process_results))

    def set_power(self):
        script = 'tasks.poweron'
        for idx in range(1,3):
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


            #  for p in self.comports:
                #  print('p', p)
                #  print(is_serial_free(p))
        else:
            self.pushButton.setEnabled(False)
            print('\nNOT READY\n!')

    def ser_update(self, comports):
        print('ser_update', comports)
        self.comports = comports
        self.clearlayout(self.hbox_ports)
        for port in self.comports:
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

    def reset_model(self):
        self.table_model.reset()

    def setsignal(self):
        self.pushButton.clicked.connect(self.btn_clicked)
        self.task.task_result.connect(self.taskrun)
        self.task.message.connect(self.taskdone)
        se.serial_msg.connect(self.printterm1)
        self.task.printterm_msg.connect(self.printterm2)

    def printterm1(self, port_msg):
        port, msg = port_msg
        msg = '[port: %s]%s' % (port, msg)
        #  print(msg)
        self.edit1.appendPlainText(msg)

    def printterm2(self, msg):
        self.edit2.appendPlainText(msg)

    def taskrun(self, result):
        ret = json.loads(result)
        idx = ret['index']

        if type(idx)==list:
            output = json.loads(ret['output'])

            for i in range(*idx):
                # DUT1
                x1 = output[i-idx[0]][0]
                self.table_view.setItem(i, self.col_dut_start, QTableWidgetItem(x1))
                color1 = QColor(0,255,0) if x1.startswith('Pass') else QColor(255,0,0)
                self.table_view.item(i, self.col_dut_start).setBackground(color1)

                # DUT2
                x2 = output[i-idx[0]][1]
                self.table_view.setItem(i, self.col_dut_start+1, QTableWidgetItem(x2))
                color2 = QColor(0,255,0) if x2.startswith('Pass') else QColor(255,0,0)
                self.table_view.item(i, self.col_dut_start+1).setBackground(color2)
        else:
            output = str(ret['output'])
            self.table_view.selectRow(idx)

            if 'port' in ret:
                port = ret['port']
                j = self.comports.index(port)
            elif 'idx' in ret:
                j = ret['idx']
                # output = {True:'pass', False:'fail'}[output]

            print('task %s are done, j=%s' % (idx, j))

            self.table_view.setItem(idx, self.col_dut_start+j, QTableWidgetItem(output))
            color = QColor(0,255,0) if output.startswith('Pass') else QColor(255,0,0)
            self.table_view.item(idx,self.col_dut_start+j).setBackground(color)

    def taskdone(self, message):
        if message.startswith('tasks done'):
            print("taskdone!")
            self.pushButton.setEnabled(True)
            self.ser_listener.start()

            if not power1.is_open:
                power1.open_com()
            if not power2.is_open:
                power2.open_com()

            if power1.ser:
                power1.off()
                power1.ser.close()
            if power2.ser:
                power2.off()
                power2.ser.close()

    def btn_clicked(self):
        print('btn_clicked')
        self.reset_model()
        self.table_model.update()
        self.pushButton.setEnabled(False)
        self.ser_listener.stop()
        self.task.start()
        self.set_power()

    def closeEvent(self, event):
        try:
            if not power1.is_open:
                power1.open_com()
            if not power2.is_open:
                power2.open_com()
        except serial.serialutil.SerialException as ex:
            print('My SerialException', ex)
            raise ex
        finally:
            if power1.ser: power1.off()
            if power2.ser: power2.off()
        event.accept() # let the window close


if __name__ == "__main__":
    mainboard_task = Task('jsonfile/power_new2.json')
    #  mainboard_task = Task('jsonfile/test2.json')
    #  mainboard_task = Task('jsonfile/simulate1.json')

    app = QApplication(sys.argv)
    win = MyWindow(app, mainboard_task)
    sys.exit(app.exec_())

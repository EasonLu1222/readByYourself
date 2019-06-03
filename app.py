import os
import sys
import json
import time
import random
from subprocess import Popen, PIPE
from threading import Thread
import operator
from PyQt5.QtWidgets import (QWidget, QTableView, QTableWidgetItem, QTreeView, QHeaderView,
                             QLabel, QSpacerItem)
from PyQt5.QtCore import (QAbstractTableModel, QModelIndex, QThread, QTimer, Qt,
                          pyqtSignal as QSignal, QRect)
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow

import pandas as pd

from view.myview import TableView
from model import TableModelTask
from ui.design3 import Ui_MainWindow
from utils import test_data, move_mainwindow_centered

from serial.tools import list_ports
from serials import enter_factory_image_prompt, get_serial, se



class SerialListener(QThread):
    update_msec = 500
    comports = QSignal(list)
    def __init__(self):
        super(SerialListener, self).__init__()
        self.is_reading = False
        self.ports = []

    def run(self):
        while True:
            QThread.msleep(SerialListener.update_msec)
            self.is_reading = True
            ports = [e.device for e in list_ports.comports()]
            self.is_reading = False
            if set(ports)!=set(self.ports):
                if set(ports)>set(self.ports):
                    d = set(ports) - set(self.ports)
                    self.ports.extend(list(d))
                else:
                    d = set(self.ports) - set(ports)
                    for e in d:
                        self.ports.remove(e)
                self.comports.emit(self.ports)

    def stop(self):
        # wait 1s for list_ports to finish, is it enough or too long in order
        # not to occupy com port for subsequent test scripts
        if self.is_reading:
            print('is_reading!')
            QThread.msleep(1000)
        self.terminate()


class Task(QThread):
    task_result = QSignal(str)
    message = QSignal(str)
    printterm_msg = QSignal(str)
    def __init__(self, jsonfile, mainwindow=None):
        super(Task, self).__init__(mainwindow)
        self.base = json.loads(open(jsonfile, 'r').read())

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

    def runeach(self, index, port, to_wait=False):
        line = self.df.values[index]
        script = 'tasks.%s' % line[0]
        args = [str(e) for e in line[1]] if line[1] else []
        msg1 = '\n[runeach][script: %s][index: %s][port: %s][args: %s]' % (script, index, port, args)

        print(msg1)
        self.printterm_msg.emit(msg1)
        proc = Popen(['python', '-m', script, '-p', port] + args, stdout=PIPE)

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
            ser = get_serial(port, 115200, timeout=1)
            t = Thread(target=enter_factory_image_prompt, args=(ser,))
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
        self.enter_prompt()
        QThread.msleep(500)
        for i in range(len(self.df)):
            line = self.df.values[i]
            is_auto = bool(line[2])
            if is_auto:
                procs = {}
                for port in self.window.comports:
                    proc = self.runeach(i, port)
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

        self.setsignal()

        self.ser_listener = SerialListener()
        self.ser_listener.comports.connect(self.ser_update)
        self.ser_listener.start()

        self.showMaximized()
        self.show()

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
        print(msg)
        self.edit1.appendPlainText(msg)

    def printterm2(self, msg):
        self.edit2.appendPlainText(msg)

    def taskrun(self, result):
        ret = json.loads(result)
        idx, output = ret['index'], ret['output']
        self.table_view.selectRow(idx)

        if 'port' in ret:
            port = ret['port']
            j = self.comports.index(port)
        elif 'idx' in ret:
            j = ret['idx']
            output = {True:'pass', False:'fail'}[output]

        print('task %s are done, j=%s' % (idx, j))

        self.table_view.setItem(idx, 9+j, QTableWidgetItem(str(output)))

    def taskdone(self, message):
        if message.startswith('tasks done'):
            print("taskdone!")
            self.pushButton.setEnabled(True)
            self.ser_listener.start()

    def btn_clicked(self):
        print('btn_clicked')
        self.reset_model()
        self.pushButton.setEnabled(False)
        self.ser_listener.stop()
        self.task.start()


if __name__ == "__main__":
    mb_task = Task('jsonfile/tasks.json')

    app = QApplication(sys.argv)
    win = MyWindow(app, mb_task)
    app.exec_()

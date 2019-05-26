import os
import sys
import json
import time
import random
from subprocess import Popen, PIPE
import operator
from PyQt5.QtWidgets import (QWidget, QTableView, QTreeView, QHeaderView,
                             QLabel, QSpacerItem)
from PyQt5.QtCore import (QAbstractTableModel, QModelIndex, QThread, QTimer, Qt,
                          pyqtSignal as QSignal, QRect)
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QMainWindow

import pandas as pd

from view.myview import TableView
from model import TableModelTask
from design3 import Ui_MainWindow
from utils import test_data, move_mainwindow_centered

from serial.tools import list_ports
from serials import enter_factory_image_prompt, get_serial, se

PORTNAME = 'COM3'


def uart_ready(portnum=2):
    ports = listports()
    if len(ports)==portnum:
        return ports
    else:
        return None


class SerialListener(QThread):
    rate = 0.5
    comports = QSignal(list)
    def __init__(self):
        super(SerialListener, self).__init__()
        self.ports = []

    def run(self):
        while True:
            time.sleep(SerialListener.rate)
            ports = [e.device for e in list_ports.comports()]
            if set(ports)!=set(self.ports):
                if set(ports)>set(self.ports):
                    d = set(ports) - set(self.ports)
                    self.ports.extend(list(d))
                else:
                    d = set(self.ports) - set(ports)
                    for e in d:
                        self.ports.remove(e)
                self.comports.emit(self.ports)


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

    def runeach(self, index):
        line = self.df.values[index]
        script = 'tasks.%s' % line[0]
        args = [str(e) for e in line[1]] if line[1] else None

        print('script', script, 'args', args)
        msg1 = '[task %s][script: %s][args: %s]' % (index, script, args)
        self.printterm_msg.emit(msg1)
        if args:
            proc = Popen(['python', '-m', script] + args, stdout=PIPE)
        else:
            proc = Popen(['python', '-m', script], stdout=PIPE)
        output, _ = proc.communicate()
        output = output.decode('utf8')
        print('output', output)
        msg2 = '[task %s][output: %s]' % (index, output)
        self.printterm_msg.emit(msg2)
        result = json.dumps({'index':index, 'output': output})
        self.task_result.emit(result)
        proc.wait()

    def run(self):
        print('enter factory image prompt start')
        t0 = time.time()

        with get_serial(PORTNAME, 115200, timeout=1) as ser:
            enter_factory_image_prompt(ser)

        #  ser.close()
        t1 = time.time()
        print('time elapsed entering prompt: %f' % (t1-t0))
        for i in range(len(self.df)):
            self.runeach(i)
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
        self.table_model = TableModelTask(self, task)
        self.table_view.setModel(self.table_model)

        self.setsignal()

        self.ser_listener = SerialListener()
        self.ser_listener.comports.connect(self.ser_update)
        self.ser_listener.start()

        self.showMaximized()
        self.show()

        #  self.test()

    #  def test(self):
        #  self.timer = QTimer(self)
        #  self.timer.start(1000)
        #  self.timer.timeout.connect(self.test_timeout)

    #  def test_timeout(self):
        #  from random import randint
        #  ports = ['COM%s' % randint(3, 10) for _ in range(randint(3,6))]
        #  self.ser_update(ports)
        #  self.ser_update(['COM3', 'COM5'])

    def modUi(self):
        self.edit1.setStyleSheet("""
            QPlainTextEdit {
                font-family: Arial Narrow;
                font-size: 10pt;
            }
        """)
        self.edit2.setStyleSheet("""
            QPlainTextEdit {
                font-family: Courier;
                font-size: 14pt;
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

    def printterm1(self, msg):
        self.edit1.appendPlainText(msg)

    def printterm2(self, msg):
        self.edit2.appendPlainText(msg)

    def taskrun(self, result):
        ret = json.loads(result)
        idx, output = ret['index'], ret['output']
        print('\nrunning task %s' % idx)
        self.table_view.selectRow(idx)

        data = self.table_model.mylist
        data[idx][6] = output

    def taskdone(self, message):
        if message.startswith('tasks done'):
            print("taskdone!")
            self.pushButton.setEnabled(True)

    def btn_clicked(self):
        print('btn_clicked')
        self.reset_model()
        self.pushButton.setEnabled(False)
        self.task.start()


if __name__ == "__main__":
    mb_task = Task('tasks.json')
    app = QApplication(sys.argv)
    win = MyWindow(app, mb_task)
    #  move_mainwindow_centered(app, win)
    app.exec_()

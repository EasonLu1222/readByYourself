import os
import sys
import json
import time
import random
from subprocess import Popen, PIPE
import operator
from PyQt5.QtWidgets import (QWidget, QTableView, QTreeView, QHeaderView)
from PyQt5.QtCore import (QAbstractTableModel, QModelIndex, QThread, QTimer, Qt,
                          pyqtSignal as QSignal)
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout, QMainWindow

import pandas as pd

from view.myview import TableView
from model import TableModelTask
from design2 import Ui_MainWindow
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
    comports = QSignal(str)
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
                self.comports.emit(json.dumps(ports))


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
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.task = task
        self.table_model = TableModelTask(self, task)
        self.table_view.setModel(self.table_model)

        self.setsignal()

        self.ser_listener = SerialListener()
        self.ser_listener.comports.connect(self.ser_update)
        self.ser_listener.start()

        self.showMaximized()
        self.show()

    def modUi(self):
        #  font = QFont("Courier New", 20)
        #  self.plainTextEdit.setFont(font)
        self.edit1.setStyleSheet("""
            QPlainTextEdit {
                font-family: Courier;
                font-size: 20;
            }
        """)

    def ser_update(self, comports):
        print('ser_update', comports)

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

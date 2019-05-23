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
from design1 import Ui_MainWindow
from utils import test_data, move_mainwindow_centered

from serials import enter_factory_image_prompt, ser


class Task(QThread):
    task_result = QSignal(str)
    message = QSignal(str)
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
        if args:
            proc = Popen(['python', '-m', script] + args, stdout=PIPE)
        else:
            proc = Popen(['python', '-m', script], stdout=PIPE)
        output, _ = proc.communicate()
        output = output.decode('utf8')
        print('output', output)
        result = json.dumps({'index':index, 'output': output})
        self.task_result.emit(result)
        proc.wait()

    def run(self):
        print('enter factory image prompt start')
        t0 = time.time()
        enter_factory_image_prompt(ser)
        ser.close()
        t1 = time.time()
        print('time elapsed entering prompt: %f' % (t1-t0))
        for i in range(len(self.df)):
            self.runeach(i)
        self.message.emit('tasks done')


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, app, task, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.setGeometry(300, 200, 1200, 450)
        self.task = task
        self.table_model = TableModelTask(self, task)
        self.table_view = table_view = TableView(self.table_model)
        #  self.table_view.set_column_width([300, 300, 100, 100, 100, 100, 50, 50])

        #  self.table_view.setColumnHidden(0, True)
        #  self.table_view.setColumnHidden(1, True)
        #  self.table_view.setColumnHidden(2, True)

        self.verticalLayout_2.addWidget(table_view)
        self.setsignal()

    def reset_model(self):
        self.table_model.reset()

    def setsignal(self):
        self.pushButton.clicked.connect(self.btn_clicked)
        self.task.task_result.connect(self.taskrun)
        self.task.message.connect(self.taskdone)

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
    move_mainwindow_centered(app, win)
    win.show()
    app.exec_()

import sys
import time
import random
import operator
from PyQt5.QtWidgets import (QWidget, QTableView, QTreeView, QHeaderView)
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QTimer, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout, QMainWindow

from view.myview import TableView
from model import MyTableModel
from design1 import Ui_MainWindow
from utils import test_data, move_mainwindow_centered


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, app, data, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.setGeometry(300, 200, 1200, 450)
        header, data_list = data[0], data[1:]
        self.table_model = MyTableModel(self, data_list, header)
        self.table_view = table_view = TableView(self.table_model)
        self.table_view.set_column_width([300, 300, 100, 100, 100, 100, 50, 50])
        self.verticalLayout_2.addWidget(table_view)
        self.timer = QTimer()
        self.timer_started = False
        self.setsignal()

    def setsignal(self):
        self.pushButton.clicked.connect(self.btn_clicked)
        self.timer.timeout.connect(self.test)

    def test(self):
        print('timer test')
        data = self.table_model.mylist
        for row in range(self.table_model.rowCount(QModelIndex())):
            data[row][6] = random.randint(0,10)
            data[row][7] = random.randint(0,10)
        self.table_model.update_model(data)

    def btn_clicked(self):
        print('btn_clicked')
        if self.timer_started:
            self.timer_started = False
            self.timer.stop()
        else:
            self.timer_started = True
            self.timer.start(1000)


if __name__ == "__main__":
    data = test_data('mb.csv')
    app = QApplication(sys.argv)
    win = MyWindow(app, data)
    move_mainwindow_centered(app, win)
    win.show()
    app.exec_()

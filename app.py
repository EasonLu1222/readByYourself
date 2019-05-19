import sys
import operator
from PyQt5.QtWidgets import (QWidget, QTableView, QTreeView, QHeaderView)
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout, QMainWindow

from view.myview import TableView
from model import MyTableModel
from design1 import Ui_MainWindow


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, app, data, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.setGeometry(300, 200, 1200, 450)
        header, data_list = data[0], data[1:]
        table_model = MyTableModel(self, data_list, header)
        table_view = TableView(table_model)
        self.verticalLayout_2.addWidget(table_view)


#  class MyWindow(QWidget):
    #  def __init__(self, data, *args):
        #  QWidget.__init__(self, *args)
        #  self.setGeometry(300, 200, 1200, 450)
        #  self.setWindowTitle("SAP109 Testing")
        #  header, data_list = data[0], data[1:]
        #  table_model = MyTableModel(self, data_list, header)
        #  table_view = TableView(table_model)
        #  layout = QVBoxLayout(self)
        #  layout.addWidget(table_view)
        #  self.setLayout(layout)


def test_data(csv_file):
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    data = [e.strip().split(',') for e in lines]
    return data


def move_mainwindow_centered(app, window):
    desktop = app.desktop()
    window.move(desktop.screen().rect().center() - window.rect().center())


if __name__ == "__main__":
    data = test_data('mb.csv')
    app = QApplication(sys.argv)
    #  win = MyWindow(data)

    win = MyWindow(app, data)
    move_mainwindow_centered(app, win)
    win.show()
    app.exec_()

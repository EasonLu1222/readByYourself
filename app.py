''' ps_QAbstractTableModel_solvents.py
use PySide's QTableView and QAbstractTableModel for tabular data
sort columns by clicking on the header title
here applied to solvents commonly used in Chemistry
PySide is the official LGPL-licensed version of PyQT
tested with PySide112 and Python27/Python33 by vegaseat  15feb2013
'''
import operator
#  from PySide.QtCore import *
#  from PySide.QtGui import *

from PyQt5.QtWidgets import QWidget, QTableView, QTreeView
from PyQt5.QtCore import QAbstractTableModel, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout


class MyWindow(QWidget):
    def __init__(self, data_list, header, *args):
        QWidget.__init__(self, *args)
        # setGeometry(x_pos, y_pos, width, height)
        self.setGeometry(300, 200, 570, 450)
        self.setWindowTitle("Click on column title to sort")
        table_model = MyTableModel(self, data_list, header)
        table_view = QTableView()
        table_view.setModel(table_model)
        # set font
        font = QFont("Courier New", 14)
        table_view.setFont(font)
        # set column width to fit contents (set font first!)
        table_view.resizeColumnsToContents()
        # enable sorting
        table_view.setSortingEnabled(True)
        layout = QVBoxLayout(self)
        layout.addWidget(table_view)
        self.setLayout(layout)


class MyWindow2(QWidget):
    def __init__(self, data_list, *args):
        QWidget.__init__(self, *args)
        #  self.setGeometry(300, 200, 570, 450)
        self.setGeometry(300, 200, 1200, 450)
        self.setWindowTitle("Click on column title to sort")
        header, data_list = data[0], data[1:]
        table_model = MyTableModel(self, data_list, header)
        self.tree_view = tree_view = QTreeView()
        tree_view.setModel(table_model)
        # set font
        font = QFont("Courier New", 20)
        tree_view.setFont(font)

        # set column width to fit contents (set font first!)
        self.resizeColumnsToContents(tree_view)

        # enable sorting
        tree_view.setSortingEnabled(True)
        layout = QVBoxLayout(self)
        layout.addWidget(tree_view)
        self.setLayout(layout)

    def resizeColumnsToContents(self, tree_view):
        for i in range(tree_view.model().columnCount(tree_view)):
            tree_view.resizeColumnToContents(i)


class MyTableModel(QAbstractTableModel):

    def __init__(self, parent, mylist, header, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.mylist = mylist
        self.header = header

    def rowCount(self, parent):
        return len(self.mylist)

    def columnCount(self, parent):
        return len(self.mylist[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return self.mylist[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        #  self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.layoutAboutToBeChanged.emit()

        self.mylist = sorted(self.mylist,
            key=operator.itemgetter(col))
        if order == Qt.DescendingOrder:
            self.mylist.reverse()

        #  self.emit(SIGNAL("layoutChanged()"))
        self.layoutChanged.emit()


def test_data(csv_file):
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    data = [e.strip().split(',') for e in lines]
    return data


data = test_data('mb.csv')


if __name__ == "__main__":
    app = QApplication([])
    win = MyWindow2(data)
    win.show()
    app.exec_()

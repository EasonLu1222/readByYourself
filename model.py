

from PyQt5.QtWidgets import (QWidget, QTableView, QTreeView, QHeaderView)
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout


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

    def setData(self, index, value, role):
        print(index, value, role)
        return True

    def flags(self, index):
        #  return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled 

    def headerData(self, idx, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[idx]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return idx+1
        return None

    #  def sort(self, col, order):
        #  """sort table by given column number col"""
        #  #  self.emit(SIGNAL("layoutAboutToBeChanged()"))
        #  self.layoutAboutToBeChanged.emit()

        #  self.mylist = sorted(self.mylist,
            #  key=operator.itemgetter(col))
        #  if order == Qt.DescendingOrder:
            #  self.mylist.reverse()

        #  #  self.emit(SIGNAL("layoutChanged()"))
        #  self.layoutChanged.emit()


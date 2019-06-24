# -*- coding: utf8 -*-
from PyQt5.QtWidgets import (QHeaderView, QTableWidget, QTableWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5 import QtWidgets



class TableView(QTableWidget):
    def __init__(self, *args, **kwargs):
        super(QTableWidget, self).__init__(*args, **kwargs)
        #  self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        #  self.setFocusPolicy(Qt.StrongFocus)
        font = QFont("Courier New", 16)
        self.setFont(font)

    def set_data(self, data, header):
        nRow = len(data)
        nCol = len(data[0])
        self.setRowCount(nRow)
        self.setColumnCount(nCol)
        for r in range(0, nRow):
            for c in range(0, nCol):
                self.setItem(r,c, QTableWidgetItem(str(data[r][c])))
        self.setHorizontalHeaderLabels(header)

        #  self.header = self.task.header_ext()

        self.resizeColumnsToContents()
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

    #  def setModel(self, model):
        #  nRow = len(model.mylist)
        #  nCol = len(model.mylist[0])

        #  self.setRowCount(nRow)
        #  self.setColumnCount(nCol)

        #  for r in range(0, nRow):
            #  for c in range(0, nCol):
                #  self.setItem(r,c, QTableWidgetItem(str(model.mylist[r][c])))

        #  self.setHorizontalHeaderLabels(model.header)
        #  self.resizeColumnsToContents()
        #  self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

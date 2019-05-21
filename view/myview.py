
from PyQt5.QtWidgets import (QWidget, QTableView, QTreeView, QHeaderView)
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtWidgets import QApplication, QAbstractItemView
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5 import QtWidgets



class TableView(QTableView):
    def __init__(self, model):
        super(TableView, self).__init__()
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)

        # self.clicked.connect(self.show_cell)
        #  self.setStyleSheet("""
            #  QTableView {
                #  background-color: #646464;
                #  padding: 4px;
                #  font-size: 8pt;
                #  border-style: none;
                #  border-bottom: 1px solid #fffff8;
                #  border-right: 1px solid #fffff8;
                #  selection-background-color: qlineargradient(x1: 0, y1: 0, x2: 0.5, y2: 0.5,
                                #  stop: 0 #FF92BB, stop: 1 white);
            #  }
        #  """)
        model.view = self
        self.setModel(model)

        # set font
        font = QFont("Courier New", 16)
        self.setFont(font)

        # set column width to fit contents (set font first!)
        self.resizeColumnsToContents()

        #  self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        #  self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        #  self.setCurrentIndex(QModelIndex())

        # enable sorting
        #  self.setSortingEnabled(True)



    def set_column_width(self, widths):
        for i, w in enumerate(widths):
            self.setColumnWidth(i, w)


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
        font_header = QFont("Courier New", 20)
        font_header.setBold(True)
        tree_view.setFont(font)
        tree_view.header().setFont(font_header)
        tree_view.setAlternatingRowColors(True)

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

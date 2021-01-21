import sys

from PyQt5 import QtCore
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QPainterPath
from PyQt5.QtCore import (QSettings, Qt, QTranslator, QCoreApplication,
                          pyqtSignal as QSignal)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QErrorMessage, QHBoxLayout,
                             QTableWidgetItem, QLabel, QTableView, QAbstractItemView,
                             QWidget, QCheckBox, QPushButton, QMessageBox)
from PyQt5.uic.properties import QtWidgets

from ui.main import Ui_MainWindow


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setupUi(self)
        self.init()


    def init(self):

        dut_num = 3
        dut_layout = []
        colors = ['#edd'] * dut_num
        print(colors)
        for i in range(dut_num):
            print(dut_num)

        c = QWidget()
        c.setStyleSheet(f'background-color:{colors[i]};')
        layout = QHBoxLayout(c)
        self.hboxPorts.addWidget(c)
        dut_layout.append(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myshow = MyWindow()
    myshow.show()
    sys.exit(app.exec_())
# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design3.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from ui.design3 import Ui_MainWindow


class MainWindow(Ui_MainWindow):
    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        
    def retranslateUi(self, MainWindow):
        super().retranslateUi(self)
        _translate = QtCore.QCoreApplication.translate
        self.task_path = _translate("MainWindow", "jsonfile/test2.json")
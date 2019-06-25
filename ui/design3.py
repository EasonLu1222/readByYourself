# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui/design3.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(781, 392)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.checkBoxFx1 = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBoxFx1.setObjectName("checkBoxFx1")
        self.verticalLayout_2.addWidget(self.checkBoxFx1)
        self.checkBoxFx2 = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBoxFx2.setObjectName("checkBoxFx2")
        self.verticalLayout_2.addWidget(self.checkBoxFx2)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.langSelectMenu = QtWidgets.QComboBox(self.centralwidget)
        self.langSelectMenu.setObjectName("langSelectMenu")
        self.langSelectMenu.addItem("")
        self.langSelectMenu.addItem("")
        self.horizontalLayout_2.addWidget(self.langSelectMenu)
        self.checkBoxEngMode = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBoxEngMode.setMaximumSize(QtCore.QSize(582, 16777215))
        self.checkBoxEngMode.setObjectName("checkBoxEngMode")
        self.horizontalLayout_2.addWidget(self.checkBoxEngMode)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.hbox_ports = QtWidgets.QHBoxLayout()
        self.hbox_ports.setObjectName("hbox_ports")
        self.verticalLayout.addLayout(self.hbox_ports)
        self.splitter_2 = QtWidgets.QSplitter(self.centralwidget)
        self.splitter_2.setOrientation(QtCore.Qt.Vertical)
        self.splitter_2.setObjectName("splitter_2")
        self.table_view = TableView(self.splitter_2)
        self.table_view.setObjectName("table_view")
        self.splitter = QtWidgets.QSplitter(self.splitter_2)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.edit1 = QtWidgets.QPlainTextEdit(self.splitter)
        font = QtGui.QFont()
        font.setFamily("Arial Narrow")
        font.setPointSize(10)
        self.edit1.setFont(font)
        self.edit1.setObjectName("edit1")
        self.edit2 = QtWidgets.QPlainTextEdit(self.splitter)
        font = QtGui.QFont()
        font.setFamily("Arial Narrow")
        font.setPointSize(10)
        self.edit2.setFont(font)
        self.edit2.setObjectName("edit2")
        self.verticalLayout.addWidget(self.splitter_2)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)
        self.horizontalLayout.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.checkBoxFx1.setText(_translate("MainWindow", "Test on fixture 1"))
        self.checkBoxFx2.setText(_translate("MainWindow", "Test on fixture 2"))
        self.langSelectMenu.setItemText(0, _translate("MainWindow", "en_US"))
        self.langSelectMenu.setItemText(1, _translate("MainWindow", "zh_TW"))
        self.checkBoxEngMode.setText(_translate("MainWindow", "Engineering mode"))
        self.pushButton.setText(_translate("MainWindow", "PushButton"))


from view.myview import TableView

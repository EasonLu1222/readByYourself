# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fixture_select.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_FixtureSelectWindow(object):
    def setupUi(self, FixtureSelectWindow):
        FixtureSelectWindow.setObjectName("FixtureSelectWindow")
        FixtureSelectWindow.resize(616, 425)
        self.centralwidget = QtWidgets.QWidget(FixtureSelectWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.checkBox_3 = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox_3.setMaximumSize(QtCore.QSize(582, 16777215))
        self.checkBox_3.setObjectName("checkBox_3")
        self.horizontalLayout.addWidget(self.checkBox_3, 0, QtCore.Qt.AlignRight)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox.setObjectName("checkBox")
        self.verticalLayout_2.addWidget(self.checkBox, 0, QtCore.Qt.AlignHCenter)
        self.checkBox_2 = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBox_2.setObjectName("checkBox_2")
        self.verticalLayout_2.addWidget(self.checkBox_2, 0, QtCore.Qt.AlignHCenter)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setMinimumSize(QtCore.QSize(490, 32))
        self.pushButton.setMouseTracking(False)
        self.pushButton.setStyleSheet("")
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        FixtureSelectWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(FixtureSelectWindow)
        self.statusbar.setObjectName("statusbar")
        FixtureSelectWindow.setStatusBar(self.statusbar)

        self.retranslateUi(FixtureSelectWindow)
        QtCore.QMetaObject.connectSlotsByName(FixtureSelectWindow)

    def retranslateUi(self, FixtureSelectWindow):
        _translate = QtCore.QCoreApplication.translate
        FixtureSelectWindow.setWindowTitle(_translate("FixtureSelectWindow", "MainWindow"))
        self.checkBox_3.setText(_translate("FixtureSelectWindow", "Engineering mode"))
        self.checkBox.setText(_translate("FixtureSelectWindow", "Test on fixture1"))
        self.checkBox_2.setText(_translate("FixtureSelectWindow", "Test on fixture2"))
        self.pushButton.setText(_translate("FixtureSelectWindow", "Start"))



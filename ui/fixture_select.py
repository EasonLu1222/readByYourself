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
        self.checkBoxEngMode = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBoxEngMode.setMaximumSize(QtCore.QSize(582, 16777215))
        self.checkBoxEngMode.setObjectName("checkBoxEngMode")
        self.horizontalLayout.addWidget(self.checkBoxEngMode, 0, QtCore.Qt.AlignRight)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.checkBoxFx1 = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBoxFx1.setObjectName("checkBoxFx1")
        self.verticalLayout_2.addWidget(self.checkBoxFx1, 0, QtCore.Qt.AlignHCenter)
        self.checkBoxFx2 = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBoxFx2.setObjectName("checkBoxFx2")
        self.verticalLayout_2.addWidget(self.checkBoxFx2, 0, QtCore.Qt.AlignHCenter)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.pushButtonStart = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButtonStart.sizePolicy().hasHeightForWidth())
        self.pushButtonStart.setSizePolicy(sizePolicy)
        self.pushButtonStart.setMinimumSize(QtCore.QSize(490, 32))
        self.pushButtonStart.setMouseTracking(False)
        self.pushButtonStart.setStyleSheet("")
        self.pushButtonStart.setObjectName("pushButtonStart")
        self.verticalLayout.addWidget(self.pushButtonStart)
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
        self.checkBoxEngMode.setText(_translate("FixtureSelectWindow", "Engineering mode"))
        self.checkBoxFx1.setText(_translate("FixtureSelectWindow", "Test on fixture 1"))
        self.checkBoxFx2.setText(_translate("FixtureSelectWindow", "Test on fixture 2"))
        self.pushButtonStart.setText(_translate("FixtureSelectWindow", "Start"))



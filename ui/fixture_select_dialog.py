# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fixture_select_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_FixtureSelectDialog(object):
    def setupUi(self, FixtureSelectDialog):
        FixtureSelectDialog.setObjectName("FixtureSelectDialog")
        FixtureSelectDialog.resize(710, 235)
        self.gridLayout = QtWidgets.QGridLayout(FixtureSelectDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.checkBoxEngMode = QtWidgets.QCheckBox(FixtureSelectDialog)
        self.checkBoxEngMode.setMaximumSize(QtCore.QSize(582, 16777215))
        self.checkBoxEngMode.setObjectName("checkBoxEngMode")
        self.horizontalLayout.addWidget(self.checkBoxEngMode, 0, QtCore.Qt.AlignRight)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.checkBoxFx1 = QtWidgets.QCheckBox(FixtureSelectDialog)
        self.checkBoxFx1.setObjectName("checkBoxFx1")
        self.verticalLayout_2.addWidget(self.checkBoxFx1, 0, QtCore.Qt.AlignHCenter)
        self.checkBoxFx2 = QtWidgets.QCheckBox(FixtureSelectDialog)
        self.checkBoxFx2.setObjectName("checkBoxFx2")
        self.verticalLayout_2.addWidget(self.checkBoxFx2, 0, QtCore.Qt.AlignHCenter)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.startBtn = QtWidgets.QPushButton(FixtureSelectDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.startBtn.sizePolicy().hasHeightForWidth())
        self.startBtn.setSizePolicy(sizePolicy)
        self.startBtn.setMinimumSize(QtCore.QSize(490, 32))
        self.startBtn.setMouseTracking(False)
        self.startBtn.setStyleSheet("")
        self.startBtn.setObjectName("startBtn")
        self.verticalLayout.addWidget(self.startBtn)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(FixtureSelectDialog)
        QtCore.QMetaObject.connectSlotsByName(FixtureSelectDialog)

    def retranslateUi(self, FixtureSelectDialog):
        _translate = QtCore.QCoreApplication.translate
        FixtureSelectDialog.setWindowTitle(_translate("FixtureSelectDialog", "Dialog"))
        self.checkBoxEngMode.setText(_translate("FixtureSelectDialog", "Engineering mode"))
        self.checkBoxFx1.setText(_translate("FixtureSelectDialog", "Test on fixture 1"))
        self.checkBoxFx2.setText(_translate("FixtureSelectDialog", "Test on fixture 2"))
        self.startBtn.setText(_translate("FixtureSelectDialog", "Start"))



# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui/led_color_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LedColorDialog(object):
    def setupUi(self, LedColorDialog):
        LedColorDialog.setObjectName("LedColorDialog")
        LedColorDialog.resize(502, 240)
        self.gridLayout = QtWidgets.QGridLayout(LedColorDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.label = QtWidgets.QLabel(LedColorDialog)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(36)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(LedColorDialog)
        QtCore.QMetaObject.connectSlotsByName(LedColorDialog)

    def retranslateUi(self, LedColorDialog):
        _translate = QtCore.QCoreApplication.translate
        LedColorDialog.setWindowTitle(_translate("LedColorDialog", "Dialog"))
        self.label.setText(_translate("LedColorDialog", "Press space to proceed"))

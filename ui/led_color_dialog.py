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
        LedColorDialog.resize(320, 240)
        self.gridLayout = QtWidgets.QGridLayout(LedColorDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(LedColorDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1, QtCore.Qt.AlignHCenter)

        self.retranslateUi(LedColorDialog)
        QtCore.QMetaObject.connectSlotsByName(LedColorDialog)

    def retranslateUi(self, LedColorDialog):
        _translate = QtCore.QCoreApplication.translate
        LedColorDialog.setWindowTitle(_translate("LedColorDialog", "Dialog"))
        self.label.setText(_translate("LedColorDialog", "Press space to proceed"))

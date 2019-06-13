# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'barcode_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_BarcodeDialog(object):
    def setupUi(self, BarcodeDialog):
        BarcodeDialog.setObjectName("BarcodeDialog")
        BarcodeDialog.resize(710, 235)
        self.verticalLayout = QtWidgets.QVBoxLayout(BarcodeDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.barcodeLineEdit = QtWidgets.QLineEdit(BarcodeDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.barcodeLineEdit.sizePolicy().hasHeightForWidth())
        self.barcodeLineEdit.setSizePolicy(sizePolicy)
        self.barcodeLineEdit.setObjectName("barcodeLineEdit")
        self.horizontalLayout.addWidget(self.barcodeLineEdit)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(BarcodeDialog)
        QtCore.QMetaObject.connectSlotsByName(BarcodeDialog)

    def retranslateUi(self, BarcodeDialog):
        _translate = QtCore.QCoreApplication.translate
        BarcodeDialog.setWindowTitle(_translate("BarcodeDialog", "Barcode"))



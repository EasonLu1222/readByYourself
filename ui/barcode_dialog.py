# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui/barcode_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_BarcodeDialog(object):
    def setupUi(self, BarcodeDialog):
        BarcodeDialog.setObjectName("BarcodeDialog")
        BarcodeDialog.resize(710, 235)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(BarcodeDialog)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem1)
        self.barcodeLineEdit = QtWidgets.QLineEdit(BarcodeDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.barcodeLineEdit.sizePolicy().hasHeightForWidth())
        self.barcodeLineEdit.setSizePolicy(sizePolicy)
        self.barcodeLineEdit.setStyleSheet("")
        self.barcodeLineEdit.setObjectName("barcodeLineEdit")
        self.verticalLayout_2.addWidget(self.barcodeLineEdit)
        self.errorMsgLabel = QtWidgets.QLabel(BarcodeDialog)
        self.errorMsgLabel.setStyleSheet("color:red;margin-top:10")
        self.errorMsgLabel.setText("")
        self.errorMsgLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.errorMsgLabel.setWordWrap(False)
        self.errorMsgLabel.setObjectName("errorMsgLabel")
        self.verticalLayout_2.addWidget(self.errorMsgLabel)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem2)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.retranslateUi(BarcodeDialog)
        QtCore.QMetaObject.connectSlotsByName(BarcodeDialog)

    def retranslateUi(self, BarcodeDialog):
        _translate = QtCore.QCoreApplication.translate
        BarcodeDialog.setWindowTitle(_translate("BarcodeDialog", "Barcode"))

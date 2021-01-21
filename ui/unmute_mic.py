# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui/unmute_mic.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_UnmuteMicDialog(object):
    def setupUi(self, UnmuteMicDialog):
        UnmuteMicDialog.setObjectName("UnmuteMicDialog")
        UnmuteMicDialog.resize(594, 350)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(UnmuteMicDialog.sizePolicy().hasHeightForWidth())
        UnmuteMicDialog.setSizePolicy(sizePolicy)
        UnmuteMicDialog.setStyleSheet("QLabel[disabled=true]{\n"
"    border-radius:80px;\n"
"    background-color:#E0E0E0;\n"
"    color:#BDBDBD;\n"
"}\n"
"QLabel[disabled=false]{\n"
"    border-radius:80px;\n"
"    background-color:#FFFFFF;\n"
"    color:#000000;\n"
"}\n"
"")
        self.verticalLayout = QtWidgets.QVBoxLayout(UnmuteMicDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.b1 = QtWidgets.QLabel(UnmuteMicDialog)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b1.setFont(font)
        self.b1.setStyleSheet("")
        self.b1.setAlignment(QtCore.Qt.AlignCenter)
        self.b1.setProperty("disabled", True)
        self.b1.setObjectName("b1")
        self.horizontalLayout.addWidget(self.b1)
        self.b2 = QtWidgets.QLabel(UnmuteMicDialog)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b2.setFont(font)
        self.b2.setStyleSheet("")
        self.b2.setAlignment(QtCore.Qt.AlignCenter)
        self.b2.setProperty("disabled", True)
        self.b2.setObjectName("b2")
        self.horizontalLayout.addWidget(self.b2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.continue_button = QtWidgets.QPushButton(UnmuteMicDialog)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.continue_button.setFont(font)
        self.continue_button.setStyleSheet("QPushButton {\n"
"    color:#FFFFFF;\n"
"    padding:5px;\n"
"    border-radius:5px;\n"
"    background-color:#8BC34A;\n"
"}\n"
"QPushButton:hover:pressed {\n"
"    background-color:#689F38;\n"
"}")
        self.continue_button.setAutoDefault(False)
        self.continue_button.setObjectName("continue_button")
        self.horizontalLayout_4.addWidget(self.continue_button)
        self.horizontalLayout_4.setStretch(0, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.verticalLayout.setStretch(0, 1)

        self.retranslateUi(UnmuteMicDialog)
        QtCore.QMetaObject.connectSlotsByName(UnmuteMicDialog)

    def retranslateUi(self, UnmuteMicDialog):
        _translate = QtCore.QCoreApplication.translate
        UnmuteMicDialog.setWindowTitle(_translate("UnmuteMicDialog", "Dialog"))
        self.b1.setText(_translate("UnmuteMicDialog", "DUT1"))
        self.b1.setProperty("class", _translate("UnmuteMicDialog", "touchBtn"))
        self.b2.setText(_translate("UnmuteMicDialog", "DUT2"))
        self.b2.setProperty("class", _translate("UnmuteMicDialog", "touchBtn"))
        self.continue_button.setText(_translate("UnmuteMicDialog", "Continue"))

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui/pass_fail_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PassFailDialog(object):
    def setupUi(self, PassFailDialog):
        PassFailDialog.setObjectName("PassFailDialog")
        PassFailDialog.resize(594, 350)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PassFailDialog.sizePolicy().hasHeightForWidth())
        PassFailDialog.setSizePolicy(sizePolicy)
        PassFailDialog.setStyleSheet("QWidget[active=true]{\n"
"    border: 5px solid #8BC34A;\n"
"    border-radius: 5px;\n"
"}\n"
"QWidget[active=false]{\n"
"    border: none;\n"
"}\n"
"QWidget[disabled=true] QLabel{\n"
"    color:#BDBDBD;\n"
"}\n"
"QWidget[disabled=false] QLabel{\n"
"    color:#000000;\n"
"}\n"
"QWidget[disabled=true] QLabel[class=\"touchBtn\"]{\n"
"    border-radius:80px;\n"
"    background-color:#E0E0E0;\n"
"    color:#BDBDBD;\n"
"}\n"
"QWidget[disabled=false] QLabel[class=\"touchBtn\"]{\n"
"    border-radius:80px;\n"
"    background-color:#FFFFFF;\n"
"    color:#000000;\n"
"}\n"
"")
        self.verticalLayout = QtWidgets.QVBoxLayout(PassFailDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pass_button = QtWidgets.QPushButton(PassFailDialog)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.pass_button.setFont(font)
        self.pass_button.setStyleSheet("QPushButton {\n"
"    color:#FFFFFF;\n"
"    padding:50px;\n"
"    border-radius:5px;\n"
"    background-color:#8BC34A;\n"
"}\n"
"QPushButton:hover:pressed {\n"
"    background-color:#689F38;\n"
"}")
        self.pass_button.setAutoDefault(False)
        self.pass_button.setObjectName("pass_button")
        self.horizontalLayout.addWidget(self.pass_button)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.fail_button = QtWidgets.QPushButton(PassFailDialog)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.fail_button.setFont(font)
        self.fail_button.setStyleSheet("QPushButton {\n"
"    color:#FFFFFF;\n"
"    padding:50px;\n"
"    border-radius:5px;\n"
"    background-color:#F44336;\n"
"}\n"
"QPushButton:hover:pressed {\n"
"    background-color:#E64A19;\n"
"}")
        self.fail_button.setAutoDefault(False)
        self.fail_button.setObjectName("fail_button")
        self.horizontalLayout.addWidget(self.fail_button)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(2, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(PassFailDialog)
        QtCore.QMetaObject.connectSlotsByName(PassFailDialog)

    def retranslateUi(self, PassFailDialog):
        _translate = QtCore.QCoreApplication.translate
        PassFailDialog.setWindowTitle(_translate("PassFailDialog", "Dialog"))
        self.pass_button.setText(_translate("PassFailDialog", "PASS"))
        self.fail_button.setText(_translate("PassFailDialog", "FAIL"))

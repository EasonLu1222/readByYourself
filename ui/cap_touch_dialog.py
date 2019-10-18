# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui/cap_touch_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CapTouchDialog(object):
    def setupUi(self, CapTouchDialog):
        CapTouchDialog.setObjectName("CapTouchDialog")
        CapTouchDialog.resize(594, 350)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(CapTouchDialog.sizePolicy().hasHeightForWidth())
        CapTouchDialog.setSizePolicy(sizePolicy)
        CapTouchDialog.setStyleSheet("QWidget[active=true]{\n"
"    border: 3px solid #8BC34A;\n"
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
        self.verticalLayout = QtWidgets.QVBoxLayout(CapTouchDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.bc2 = QtWidgets.QWidget(CapTouchDialog)
        self.bc2.setAutoFillBackground(False)
        self.bc2.setStyleSheet("")
        self.bc2.setProperty("active", False)
        self.bc2.setProperty("disabled", True)
        self.bc2.setObjectName("bc2")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.bc2)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_8 = QtWidgets.QLabel(self.bc2)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.label_8.setFont(font)
        self.label_8.setStyleSheet("background:none")
        self.label_8.setAlignment(QtCore.Qt.AlignCenter)
        self.label_8.setObjectName("label_8")
        self.verticalLayout_5.addWidget(self.label_8)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.b21 = QtWidgets.QLabel(self.bc2)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b21.setFont(font)
        self.b21.setStyleSheet("")
        self.b21.setAlignment(QtCore.Qt.AlignCenter)
        self.b21.setObjectName("b21")
        self.horizontalLayout_3.addWidget(self.b21)
        self.b22 = QtWidgets.QLabel(self.bc2)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b22.setFont(font)
        self.b22.setStyleSheet("")
        self.b22.setAlignment(QtCore.Qt.AlignCenter)
        self.b22.setObjectName("b22")
        self.horizontalLayout_3.addWidget(self.b22)
        self.b23 = QtWidgets.QLabel(self.bc2)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b23.setFont(font)
        self.b23.setStyleSheet("")
        self.b23.setAlignment(QtCore.Qt.AlignCenter)
        self.b23.setObjectName("b23")
        self.horizontalLayout_3.addWidget(self.b23)
        self.b24 = QtWidgets.QLabel(self.bc2)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b24.setFont(font)
        self.b24.setStyleSheet("")
        self.b24.setAlignment(QtCore.Qt.AlignCenter)
        self.b24.setObjectName("b24")
        self.horizontalLayout_3.addWidget(self.b24)
        self.b25 = QtWidgets.QLabel(self.bc2)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b25.setFont(font)
        self.b25.setStyleSheet("")
        self.b25.setAlignment(QtCore.Qt.AlignCenter)
        self.b25.setObjectName("b25")
        self.horizontalLayout_3.addWidget(self.b25)
        self.verticalLayout_5.addLayout(self.horizontalLayout_3)
        self.verticalLayout_5.setStretch(1, 1)
        self.verticalLayout.addWidget(self.bc2)
        self.bc1 = QtWidgets.QWidget(CapTouchDialog)
        self.bc1.setStyleSheet("")
        self.bc1.setProperty("active", False)
        self.bc1.setProperty("disabled", True)
        self.bc1.setObjectName("bc1")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.bc1)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_6 = QtWidgets.QLabel(self.bc1)
        self.label_6.setMinimumSize(QtCore.QSize(527, 0))
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.label_6.setFont(font)
        self.label_6.setStyleSheet("background:none")
        self.label_6.setAlignment(QtCore.Qt.AlignCenter)
        self.label_6.setObjectName("label_6")
        self.verticalLayout_3.addWidget(self.label_6)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.b11 = QtWidgets.QLabel(self.bc1)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b11.setFont(font)
        self.b11.setStyleSheet("")
        self.b11.setAlignment(QtCore.Qt.AlignCenter)
        self.b11.setObjectName("b11")
        self.horizontalLayout.addWidget(self.b11)
        self.b12 = QtWidgets.QLabel(self.bc1)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b12.setFont(font)
        self.b12.setStyleSheet("")
        self.b12.setAlignment(QtCore.Qt.AlignCenter)
        self.b12.setObjectName("b12")
        self.horizontalLayout.addWidget(self.b12)
        self.b13 = QtWidgets.QLabel(self.bc1)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b13.setFont(font)
        self.b13.setStyleSheet("")
        self.b13.setAlignment(QtCore.Qt.AlignCenter)
        self.b13.setObjectName("b13")
        self.horizontalLayout.addWidget(self.b13)
        self.b14 = QtWidgets.QLabel(self.bc1)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b14.setFont(font)
        self.b14.setStyleSheet("")
        self.b14.setAlignment(QtCore.Qt.AlignCenter)
        self.b14.setObjectName("b14")
        self.horizontalLayout.addWidget(self.b14)
        self.b15 = QtWidgets.QLabel(self.bc1)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.b15.setFont(font)
        self.b15.setStyleSheet("")
        self.b15.setAlignment(QtCore.Qt.AlignCenter)
        self.b15.setObjectName("b15")
        self.horizontalLayout.addWidget(self.b15)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout_3.setStretch(1, 1)
        self.verticalLayout.addWidget(self.bc1)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.pass_button = QtWidgets.QPushButton(CapTouchDialog)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.pass_button.setFont(font)
        self.pass_button.setStyleSheet("QPushButton {\n"
"    color:#FFFFFF;\n"
"    cursor:pointer;\n"
"    padding:5px;\n"
"    border-radius:5px;\n"
"    background-color:#8BC34A;\n"
"}\n"
"QPushButton:hover:pressed {\n"
"    background-color:#689F38;\n"
"}")
        self.pass_button.setAutoDefault(False)
        self.pass_button.setObjectName("pass_button")
        self.horizontalLayout_4.addWidget(self.pass_button)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.fail_button = QtWidgets.QPushButton(CapTouchDialog)
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(24)
        self.fail_button.setFont(font)
        self.fail_button.setStyleSheet("QPushButton {\n"
"    color:#FFFFFF;\n"
"    padding:5px;\n"
"    border-radius:5px;\n"
"    background-color:#F44336;\n"
"}\n"
"QPushButton:hover:pressed {\n"
"    background-color:#E64A19;\n"
"}")
        self.fail_button.setAutoDefault(False)
        self.fail_button.setObjectName("fail_button")
        self.horizontalLayout_4.addWidget(self.fail_button)
        self.horizontalLayout_4.setStretch(0, 1)
        self.horizontalLayout_4.setStretch(2, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(CapTouchDialog)
        QtCore.QMetaObject.connectSlotsByName(CapTouchDialog)

    def retranslateUi(self, CapTouchDialog):
        _translate = QtCore.QCoreApplication.translate
        CapTouchDialog.setWindowTitle(_translate("CapTouchDialog", "Dialog"))
        self.label_8.setText(_translate("CapTouchDialog", "DUT2"))
        self.b21.setText(_translate("CapTouchDialog", "Mute"))
        self.b21.setProperty("class", _translate("CapTouchDialog", "touchBtn"))
        self.b22.setText(_translate("CapTouchDialog", "V+"))
        self.b22.setProperty("class", _translate("CapTouchDialog", "touchBtn"))
        self.b23.setText(_translate("CapTouchDialog", "Play"))
        self.b23.setProperty("class", _translate("CapTouchDialog", "touchBtn"))
        self.b24.setText(_translate("CapTouchDialog", "V-"))
        self.b24.setProperty("class", _translate("CapTouchDialog", "touchBtn"))
        self.b25.setText(_translate("CapTouchDialog", "BT"))
        self.b25.setProperty("class", _translate("CapTouchDialog", "touchBtn"))
        self.label_6.setText(_translate("CapTouchDialog", "DUT1"))
        self.b11.setText(_translate("CapTouchDialog", "Mute"))
        self.b11.setProperty("class", _translate("CapTouchDialog", "touchBtn"))
        self.b12.setText(_translate("CapTouchDialog", "V+"))
        self.b12.setProperty("class", _translate("CapTouchDialog", "touchBtn"))
        self.b13.setText(_translate("CapTouchDialog", "Play"))
        self.b13.setProperty("class", _translate("CapTouchDialog", "touchBtn"))
        self.b14.setText(_translate("CapTouchDialog", "V-"))
        self.b14.setProperty("class", _translate("CapTouchDialog", "touchBtn"))
        self.b15.setText(_translate("CapTouchDialog", "BT"))
        self.b15.setProperty("class", _translate("CapTouchDialog", "touchBtn"))
        self.pass_button.setText(_translate("CapTouchDialog", "PASS"))
        self.fail_button.setText(_translate("CapTouchDialog", "FAIL"))

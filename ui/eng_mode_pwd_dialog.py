# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'eng_mode_pwd_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_EngModePwdDialog(object):
    def setupUi(self, EngModePwdDialog):
        EngModePwdDialog.setObjectName("EngModePwdDialog")
        EngModePwdDialog.resize(710, 235)
        EngModePwdDialog.setMinimumSize(QtCore.QSize(0, 0))
        self.gridLayout = QtWidgets.QGridLayout(EngModePwdDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(EngModePwdDialog)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(670, 13, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_3 = QtWidgets.QLabel(EngModePwdDialog)
        self.label_3.setObjectName("label_3")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.pwdText = QtWidgets.QLineEdit(EngModePwdDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(3)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pwdText.sizePolicy().hasHeightForWidth())
        self.pwdText.setSizePolicy(sizePolicy)
        self.pwdText.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pwdText.setObjectName("pwdText")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.pwdText)
        self.verticalLayout_2.addLayout(self.formLayout_2)
        spacerItem1 = QtWidgets.QSpacerItem(670, 13, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem1)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.confirmBtn = QtWidgets.QPushButton(EngModePwdDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.confirmBtn.sizePolicy().hasHeightForWidth())
        self.confirmBtn.setSizePolicy(sizePolicy)
        self.confirmBtn.setObjectName("confirmBtn")
        self.horizontalLayout_7.addWidget(self.confirmBtn)
        self.cancelBtn = QtWidgets.QPushButton(EngModePwdDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cancelBtn.sizePolicy().hasHeightForWidth())
        self.cancelBtn.setSizePolicy(sizePolicy)
        self.cancelBtn.setObjectName("cancelBtn")
        self.horizontalLayout_7.addWidget(self.cancelBtn)
        self.verticalLayout_2.addLayout(self.horizontalLayout_7)
        self.gridLayout.addLayout(self.verticalLayout_2, 0, 0, 1, 1)

        self.retranslateUi(EngModePwdDialog)
        QtCore.QMetaObject.connectSlotsByName(EngModePwdDialog)

    def retranslateUi(self, EngModePwdDialog):
        _translate = QtCore.QCoreApplication.translate
        EngModePwdDialog.setWindowTitle(_translate("EngModePwdDialog", "Dialog"))
        self.label.setText(_translate("EngModePwdDialog", "By enabling this mode, you can force continue a failed test(if the test item is continuable)"))
        self.label_3.setText(_translate("EngModePwdDialog", "Password"))
        self.confirmBtn.setText(_translate("EngModePwdDialog", "Confirm"))
        self.cancelBtn.setText(_translate("EngModePwdDialog", "Cancel"))



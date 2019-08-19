# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui/led_result_marker_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LedResultMarkerDialog(object):
    def setupUi(self, LedResultMarkerDialog):
        LedResultMarkerDialog.setObjectName("LedResultMarkerDialog")
        LedResultMarkerDialog.resize(320, 240)
        self.gridLayout = QtWidgets.QGridLayout(LedResultMarkerDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.label_2 = QtWidgets.QLabel(LedResultMarkerDialog)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2, 0, QtCore.Qt.AlignHCenter)
        self.label = QtWidgets.QLabel(LedResultMarkerDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label, 0, QtCore.Qt.AlignHCenter)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(LedResultMarkerDialog)
        QtCore.QMetaObject.connectSlotsByName(LedResultMarkerDialog)

    def retranslateUi(self, LedResultMarkerDialog):
        _translate = QtCore.QCoreApplication.translate
        LedResultMarkerDialog.setWindowTitle(_translate("LedResultMarkerDialog", "Dialog"))
        self.label_2.setText(_translate("LedResultMarkerDialog", "Press number key to mark pass or fail"))
        self.label.setText(_translate("LedResultMarkerDialog", "Press Enter to proceed"))

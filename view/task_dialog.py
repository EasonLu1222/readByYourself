# -*- coding: utf8 -*-
import json
from PyQt5 import QtWidgets, QtCore, QtGui
from view.imglist import QCustomQWidget, ImageList

import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s][%(message)s]')


class Page(QtWidgets.QWidget):
    def __init__(self, index, img_info):
        super(Page, self).__init__()
        imglist = ImageList(img_info)
        layout = QtWidgets.QVBoxLayout()
        imglist.setCurrentRow(index)
        layout.addWidget(imglist)
        self.setLayout(layout)


class MyDialog(QtWidgets.QDialog):
    message_each = QtCore.pyqtSignal(int)
    message_end = QtCore.pyqtSignal(str)
    def __init__(self, *args, **kwargs):

        number = None
        if 'content_widget' in kwargs:
            content_widget = kwargs.pop('content_widget')
            content_widget.father = self
        if 'number' in kwargs:
            number = kwargs.pop('number')
        if 'img_info' in kwargs:
            img_info = kwargs.pop('img_info')

        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QPushButton {
                padding: 6px;
                background: #369;
                color: white;
                font-size: 33px;
                border: 0;
                border-radius: 3px;
                outline: 0px;
            }
            QPushButton:hover {
                background: #47a;
            }
            QPushButton:pressed {
                background: #58b;
            }
        """)
        self.setModal(True)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(QtCore.Qt.WindowMinimizeButtonHint, False)
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, False)

        if number:
            self.number = number
        else:
            self.number = 2
        self.pages = []
        self.idx = 0
        self.passes = {}

        self.vertical_layout = vertical_layout = QtWidgets.QVBoxLayout()
        self.setLayout(vertical_layout)



        self.content_layout = QtWidgets.QVBoxLayout() # could be almost any layout actually
        vertical_layout.addLayout(self.content_layout)

        for i in range(self.number):
            page = Page(i, img_info)
            page.setFixedHeight(300)
            self.pages.append(page)
        self.content_layout.addWidget(self.pages[0])

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        pass_button = QtWidgets.QPushButton('Passed')
        pass_button.setObjectName('pass_button')
        pass_button.clicked.connect(self.button_clicked)
        button_layout.addWidget(pass_button)
        fail_button = QtWidgets.QPushButton('Failed')
        fail_button.setObjectName('fail_button')
        fail_button.clicked.connect(self.button_clicked)
        button_layout.addWidget(fail_button)

        pass_button.setAutoDefault(False)
        pass_button.setDefault(False)
        fail_button.setAutoDefault(False)
        fail_button.setDefault(False)

        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Return), self, pass_button.click)
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Space), self, fail_button.click)

        #  content_widget = QtWidgets.QWidget()
        vertical_layout.addWidget(content_widget)

        #  self.message.connect(self.parent().xx)
        vertical_layout.addLayout(button_layout)
        self.showMaximized()
        self.show()

    def button_clicked(self):
        btn = self.sender()
        if btn.objectName() == 'pass_button':
            self.passes[self.idx] = True
        elif btn.objectName() == 'fail_button':
            self.passes[self.idx] = False

        if self.idx < self.number-1:
            page = self.pages[self.idx]
            self.content_layout.removeWidget(page)
            page.deleteLater()
            self.content_layout.addWidget(self.pages[self.idx+1])
            self.message_each.emit(self.idx)
        else:
            logging.info('button_clicked')
            result = json.dumps(self.passes)
            self.message_end.emit(result)
            self.close()
        self.idx += 1

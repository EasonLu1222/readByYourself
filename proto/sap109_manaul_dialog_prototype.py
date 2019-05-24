import json
from PyQt5 import QtWidgets, QtCore, QtGui


class Page(QtWidgets.QWidget):
    def __init__(self, index):
        super(Page, self).__init__()
        label = QtWidgets.QLabel('My Page%s' % index)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)



class MyDialog(QtWidgets.QDialog):
    message = QtCore.pyqtSignal(str)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #  self.setStyleSheet("""
            #  QPushButton:focus {
                    #  border: none;
                    #  outline: none;
            #  }
        #  """)

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

        self.number = 4
        self.pages = []
        self.idx = 0
        self.passes = {}

        vertical_layout = QtWidgets.QVBoxLayout()
        self.setLayout(vertical_layout)

        self.content_layout = QtWidgets.QVBoxLayout() # could be almost any layout actually
        vertical_layout.addLayout(self.content_layout)

        for i in range(self.number):
            content = Page(i)
            self.pages.append(content)
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
        #  QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Space), self, self.button_clicked)


        self.message.connect(self.parent().xx)

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
            content = self.pages[self.idx]
            self.content_layout.removeWidget(content)
            content.deleteLater()
            self.content_layout.addWidget(self.pages[self.idx+1])
        else:
            self.message.emit(json.dumps(self.passes))
            self.close()
        self.idx += 1



class MyWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MyWindow, self).__init__(*args, *kwargs)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.CustomizeWindowHint)
        #  self.setWindowFlag(QtCore.Qt.WindowMinimizeButtonHint, False)
        #  self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, False)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setGeometry(400,400,400,400)
        self.setWindowTitle('MyWizard Example')
        centralwidget = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(centralwidget)
        btn = QtWidgets.QPushButton('wizard show')
        layout.addWidget(btn)
        self.setCentralWidget(centralwidget)
        self.show()
        btn.clicked.connect(self.wizardshow)
        self.showMaximized()
        self.show()

    def mouseMoveEvent(self, event):
        print('.')

    def wizardshow(self):
        print('aaa')
        d = MyDialog(self)
        if d.exec_():
            print('a')
        else:
            print('b')

    def xx(self, msg):
        print('xx', msg)


app = QtWidgets.QApplication([])
win = MyWindow()
#  win = MyWizard()

app.exec_()

import json
from PyQt5 import QtWidgets, QtCore, QtGui


class Page(QtWidgets.QWidget):
    def __init__(self, index):
        super(Page, self).__init__()
        label = QtWidgets.QLabel('My Page%s' % index)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)



class ContentWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QWidget {
                background: #58b;
            }
        """)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel('TEST')
        self.setLayout(layout)
        layout.addWidget(label)


class MyDialog(QtWidgets.QDialog):
    message = QtCore.pyqtSignal(str)
    def __init__(self, *args, **kwargs):

        number = None
        if 'content_widget' in kwargs:
            content_widget = kwargs.pop('content_widget')
        if 'number' in kwargs:
            number = kwargs.pop('number')

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
            page = Page(i)
            self.pages.append(page)
        self.content_layout.addWidget(self.pages[0])

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        pass_button = QtWidgets.QPushButton('Pass')
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

        self.message.connect(self.parent().xx)
        vertical_layout.addLayout(button_layout)
        self.showMaximized()
        self.show()

    def set_content(self, widget):
        self.vertical_layout

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
        w = ContentWidget()
        d = MyDialog(self, number=2, content_widget=w)
        if d.exec_():
            print('a')
        else:
            print('b')

    def xx(self, msg):
        print('xx', msg)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    win = MyWindow()
    app.exec_()

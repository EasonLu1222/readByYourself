import sys
from ftplib import FTP
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QDialog,
                             QLabel, QWidget, QPushButton, QProgressBar)
from PyQt5.QtCore import Qt


class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.resize(600, 100)
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.progressBar = QProgressBar(self)
        self.updateStatusText = QLabel(self)
        self.verticalLayout.addWidget(self.progressBar)
        self.verticalLayout.addWidget(self.updateStatusText)

    def on_data_ready(self, data):
        print('on_data_ready', data)
        self.updateStatusText.setText(str(data))
        if data=='Status: Updated!':
            self.hide()

    def update_progress(self, value):
        self.progressBar.setValue(value)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setStyleSheet("")
        MainWindow.resize(817, 200)
        MainWindow.setCentralWidget(self.centralwidget)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.updateButton = QPushButton(self.centralwidget)
        self.verticalLayout.addWidget(self.updateButton)
        self.updateButton.clicked.connect(self.download_file)

    def download_file(self):
        self.dialog = MyDialog(self)
        self.thread = DownloadThread()
        self.thread.win = self.dialog
        self.thread.data_downloaded.connect(self.dialog.on_data_ready)
        self.thread.progress_update.connect(self.dialog.update_progress)
        self.thread.start()
        self.dialog.show()

    def on_data_ready(self, data):
        print('on_data_ready', data)
        self.updateStatusText.setText(str(data))


class DownloadThread(QtCore.QThread):
    data_downloaded = QtCore.pyqtSignal(object)
    progress_update = QtCore.pyqtSignal(int)
    def run(self):
        self.data_downloaded.emit('Status: Connecting...')
        ftp = FTP('10.228.14.92', timeout=3)
        ftp.login(user='SAP109', passwd='sapsfc')
        ftp.cwd('Belkin109/Latest_App')
        filename = 'app_20191214_1833.exe'
        self.totalsize = ftp.size(filename)
        self.dlsize = 0
        print(self.totalsize)
        self.win.progressBar.setMaximum(self.totalsize)
        self.data_downloaded.emit('Status: Downloading...')

        global localfile
        with open(filename, 'wb') as localfile:
            ftp.retrbinary('RETR ' + filename, self.file_write)
        ftp.quit()
        localfile.close()
        self.data_downloaded.emit('Status: Updated!')

    def file_write(self, data):
        global localfile
        localfile.write(data)
        dlen = len(data)
        self.dlsize += dlen
        self.progress_update.emit(self.dlsize)


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, app, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.app = app
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MyWindow(app)
    app.exec_()

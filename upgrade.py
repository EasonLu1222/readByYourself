import os
import io
import sys
import time
import glob
import errno
import psutil
import shutil
import ftplib
import hashlib
import getpass
from ftplib import FTP
from threading import Thread
from subprocess import Popen, PIPE
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import RegexMatchingEventHandler
from win32com.shell import shell, shellcon
import pythoncom
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QDialog,
                             QLabel, QWidget, QPushButton, QProgressBar)
from PyQt5.QtCore import Qt


type_ = lambda ex: f'<{type(ex).__name__}>'


# not work for nssm
EXE_DIR = os.path.abspath('.')


def get_md5(file_path):
    with open(file_path, 'rb') as file_to_check:
        data = file_to_check.read()
        md5_returned = hashlib.md5(data).hexdigest()
    return md5_returned


def wait_for_process_end(pid):
    print(f'wait for pid to stop {pid}')
    while psutil.pid_exists(pid): pass
    print(f'process {pid} is closed')
    time.sleep(1)

def delete_files(exclude_exe=None):
    print('delete_files start')

    # delete trigger file
    trigger_file = glob.glob(f'{EXE_DIR}/sap109-testing-upgrade-starting-*')
    for e in trigger_file:
        os.remove(e)

    # delete app_xxx.exe
    exefiles = glob.glob(f'{EXE_DIR}/*.exe')
    if exclude_exe:
        exefiles = [e for e in exefiles if exclude_exe not in e]
    print(f'exefiles {exefiles}')
    for exe in exefiles:
        os.remove(exe)

    # delete md5.txt
    os.remove(f'{EXE_DIR}/md5.txt')

    # delete jsonfile/
    jsondir = f'{EXE_DIR}/jsonfile'
    if os.path.isdir(jsondir):
        shutil.rmtree(jsondir)
    print('delete_files done')


def download_jsonfile(ftp):
    print('download_jsonfile start')
    ftp_path = f'/Belkin109/Latest_App/jsonfile'
    ftp.downloadFiles(ftp_path, f'{EXE_DIR}/jsonfile')
    print('download_jsonfile done')


def checkmd5(targetname, md5_expected):
    #  md5_expected = '688373fa36d4f3827fee8bef7d81e223'
    app_path = f'{EXE_DIR}/{targetname}'
    md5_actual = get_md5(app_path)
    return True if md5_actual==md5_expected else False

def create_shortcut(targetname):
    log('create_shortcut start')
    try:
        pythoncom.CoInitialize()
        print('create_shortcut')
        shortcutname = 'app.lnk'
        desktop_path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
        shortcut_path = os.path.join(desktop_path, shortcutname)
        target_path = f'{EXE_DIR}/{targetname}'
        print(f'desktop_path {desktop_path}')
        print(f'shortcut_path {shortcut_path}')
        print(f'target_path {target_path}')
        shortcut = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink,
            None,
            pythoncom.CLSCTX_INPROC_SERVER,
            shell.IID_IShellLink
        )
        shortcut.SetPath(target_path)
        shortcut.SetWorkingDirectory(EXE_DIR)
        persist_file = shortcut.QueryInterface (pythoncom.IID_IPersistFile)
        persist_file.Save(shortcut_path, 0)
    except Exception as ex:
        print(f'[ERROR]{type_(ex)}, {ex}')
    print('create_shortcut done')


class MyFtp():
    def __init__(self, cwd='/Belkin109/Latest_App'):

        # ip for office intranet
        ip = '10.228.14.92'

        # ip for production line intranet
        #  ip = '10.228.16.92'

        user, passwd = 'SAP109', 'sapsfc'
        self.ftp = FTP(ip)
        self.ftp.login(user=user, passwd=passwd)
        self.ftp.cwd(cwd)

    def size(self, filename):
        return self.ftp.size(filename)

    def retrbinary(self, cmd, callback):
        self.ftp.retrbinary(cmd, callback)

    def quit(self):
        self.ftp.quit()

    def nlst(self):
        return self.ftp.nlst()

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def downloadFiles(self, path, destination):
        interval = 0.05
        try:
            self.ftp.cwd(path)
            self.mkdir_p(destination)
            print("Created: " + destination)
            os.chdir(destination)
        except OSError as ex:
            print(f'OSError {ex}')
        except ftplib.error_perm:
            print("Error: could not change to " + path)
            sys.exit("Ending Application")

        filelist=self.ftp.nlst()
        for file in filelist:
            time.sleep(interval)
            try:
                cwd = f'{path}/{file}'
                self.ftp.cwd(cwd)
                self.downloadFiles(f'{path}/{file}', f'{destination}/{file}')

            except ftplib.error_perm:
                # this is for file download
                des = f'{destination}/{file}'
                print(f'download file: {file}')
                self.retrbinary("RETR " + file, open(des, 'wb').write)
                print(f'{file} downloaded')
        self.ftp.cwd('../')
        os.chdir('../')
        return


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
        if data=='Updated':
            self.hide()

    def update_progress(self, value):
        self.progressBar.setValue(value)


class DownloadThread(QtCore.QThread):
    data_downloaded = QtCore.pyqtSignal(object)
    progress_update = QtCore.pyqtSignal(int)
    quit = QtCore.pyqtSignal()
    def run(self):
        self.data_downloaded.emit('Status: Connecting...')
        self.ftp = MyFtp()

        # download exe & md5
        appname, md5_expected = self.download_app()
        print(f'md5_expected {md5_expected}')
        print(f'appname {appname}')

        appname = 'app_20191214_1777.exe'
        # if checksum ok, proceed
        if checkmd5(appname, md5_expected):
            print('ready to update')

            # download & overwrite jsonfile

            #  === open another process with new exe
            proc = Popen(f'{os.path.abspath(".")}/{appname}', stdout=PIPE)

            #  === close current process, emit a signal for MyWindow to quit
            self.quit.emit()

            # for new process, do following...
            #  - delete app.exe
            #  - delete md5.txt
        else:
            print('checksum error, plz download again.')

            #  === delete downloaded exe


    def download_app(self):
        exes = [e for e in self.ftp.nlst() if 'exe' in e]
        md5txts = [e for e in self.ftp.nlst() if 'md5.txt' in e]
        if len(exes)==1 and len(md5txts)==1:
            targetname, md5txt = exes[0], md5txts[0]
            self.download_file(targetname, 'Downloading...', 'Updated')
            self.download_file(md5txt, 'Downloading...', 'Updated')
            md5_expected = open(md5txt, 'r').read().strip()
        return targetname, md5_expected

    def download_file(self, filename, msg1, msg2):
        self.dlsize = 0
        self.dialog.progressBar.setMaximum(self.ftp.size(filename))
        self.data_downloaded.emit(msg1)
        self.localfile = open(filename, 'wb')
        self.ftp.retrbinary('RETR ' + filename, self.file_write)
        self.localfile.close()
        self.ftp.quit()
        self.data_downloaded.emit(msg2)

    def file_write(self, data):
        self.localfile.write(data)
        self.dlsize += len(data)
        self.progress_update.emit(self.dlsize)


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


class MyWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.show()

    def download_file(self):
        self.dialog = MyDialog(self)
        self.dialog.setModal(True)
        self.thread = DownloadThread()
        self.thread.dialog = self.dialog
        self.thread.progress_update.connect(self.dialog.update_progress)
        self.thread.data_downloaded.connect(self.dialog.on_data_ready)
        self.thread.quit.connect(self.quit)
        self.thread.start()
        self.dialog.show()

    def quit(self):
        print('MyWindow quit')
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MyWindow()
    app.exec_()

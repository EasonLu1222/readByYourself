import os
import io
import sys
import time
import glob
import errno
import socket
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
from config import (
    STATION, LOCAL_APP_PATH, FTP_DIR, TRIGGER_PREFIX,
    OFFICE_FTP_IP, FACTORY_FTP_IP, FTP_IP_USED,
)
from mylogger import logger


type_ = lambda ex: f'<{type(ex).__name__}>'


def get_md5(file_path):
    with open(file_path, 'rb') as file_to_check:
        data = file_to_check.read()
        md5_returned = hashlib.md5(data).hexdigest()
    return md5_returned


def get_appname():
    proc = psutil.Process(os.getpid())
    appname = proc.name()
    return appname


def wait_for_process_end(pid):
    logger.info(f'wait for pid to stop {pid}')
    while psutil.pid_exists(pid): pass
    logger.info(f'process {pid} is closed')
    time.sleep(1)


def delete_trigger_file():
    trigger_file = glob.glob(f'{LOCAL_APP_PATH}/{TRIGGER_PREFIX}-*')
    for e in trigger_file:
        os.remove(e)


def delete_app_exe(keep=None):
    exefiles = glob.glob(f'{LOCAL_APP_PATH}/*.exe')
    if keep:
        exefiles = [e for e in exefiles if keep not in e]
    else:
        exefiles = [e for e in exefiles if get_appname() not in e]
    logger.info(f'exefiles {exefiles}')
    for exe in exefiles:
        os.remove(exe)


def delete_md5():
    os.remove(f'{LOCAL_APP_PATH}/md5.txt')


def delete_jsonfile():
    jsondir = f'{LOCAL_APP_PATH}/jsonfile'
    if os.path.isdir(jsondir):
        shutil.rmtree(jsondir)
    os.mkdir(jsondir)
    logger.info('delete_files done')


def checkmd5(targetname, md5_expected):
    app_path = f'{LOCAL_APP_PATH}/{targetname}'
    md5_actual = get_md5(app_path)
    logger.info(f'md5_actual {md5_actual}')
    return True if md5_actual==md5_expected else False


def create_shortcut(targetname):
    logger.info('create_shortcut start')
    try:
        pythoncom.CoInitialize()
        logger.info('create_shortcut')
        shortcutname = 'app.lnk'
        desktop_path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
        shortcut_path = os.path.join(desktop_path, shortcutname)
        target_path = f'{LOCAL_APP_PATH}/{targetname}'
        logger.info(f'desktop_path {desktop_path}')
        logger.info(f'shortcut_path {shortcut_path}')
        logger.info(f'target_path {target_path}')
        shortcut = pythoncom.CoCreateInstance(
            shell.CLSID_ShellLink,
            None,
            pythoncom.CLSCTX_INPROC_SERVER,
            shell.IID_IShellLink
        )
        shortcut.SetPath(target_path)
        shortcut.SetWorkingDirectory(LOCAL_APP_PATH)
        persist_file = shortcut.QueryInterface (pythoncom.IID_IPersistFile)
        persist_file.Save(shortcut_path, 0)
    except Exception as ex:
        logger.error(f'[ERROR]{type_(ex)}, {ex}')
    logger.info('create_shortcut done')


def wait_for_process_end_if_downloading():
    triggers = glob.glob(f'{LOCAL_APP_PATH}/{TRIGGER_PREFIX}-*')
    logger.info(f'triggers {triggers}')
    if len(triggers)==1:
        x = triggers[0]
        pid = int(x[x.rfind('-')+1:])
        logger.info(f'pid {pid}')
        wait_for_process_end(pid)
        return True
    return False


class MyFtp():
    def __init__(self, cwd=FTP_DIR):
        user, passwd = 'SAP109', 'sapsfc'
        try:
            logger.info(f'ftp ip_used: {FTP_IP_USED}')
            self.ftp = None
            self.ftp = FTP(FTP_IP_USED, timeout=3)
            self.ftp.login(user=user, passwd=passwd)
            self.ftp.cwd(cwd)
        except socket.timeout as e:
            logger.error('Error: FTP connection timeout')
        except OSError as e:
            logger.error('Error: Network is unreachable')

    def cwd(self, path):
        return self.ftp.cwd(path)

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


class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        #  self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint |
                            #  ~Qt.WindowContextHelpButtonHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.resize(600, 100)
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")
        self.progressBar = QProgressBar(self)
        self.updateStatusText = QLabel(self)
        self.verticalLayout.addWidget(self.progressBar)
        self.verticalLayout.addWidget(self.updateStatusText)
        self.setWindowTitle('Upgrade...')

    def on_data_ready(self, data):
        logger.info(f'on_data_ready {data}')
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
        logger.info(f'md5_expected {md5_expected}')
        logger.info(f'appname {appname}')

        if checkmd5(appname, md5_expected):
            logger.info('============= path4 checksum ok and proceed ==============')

            # replace old jsonfile/ with new one
            delete_jsonfile()
            self.download_folder('jsonfile')

            # change station.json to current one
            with open(f'{LOCAL_APP_PATH}/jsonfile/station.json', 'w') as f:
                content = '{\n\r\t"STATION": "%s"\n\r}' % STATION
                f.write(content)

            # create shortcut
            create_shortcut(appname)

            # emit updated signal
            self.data_downloaded.emit('Updated')

            #  === open another process with new exe
            proc = Popen(f'{LOCAL_APP_PATH}/{appname}', stdout=PIPE)

            #  === close current process, emit a signal for MyWindow to quit
            self.quit.emit()
            self.ftp.quit()

            # for new process, do following...
            #  - delete old app.exe
        else:
            logger.info('checksum error, plz download again.')

            #  === delete downloaded exe
            os.remove(f'{LOCAL_APP_PATH}/{appname}')

        delete_md5()
        logger.info('end of DownloadThread.run()')

    def download_folder(self, folder):
        logger.info(f'folder {folder}')
        self.ftp.cwd(folder)
        files = self.ftp.nlst()
        self.data_downloaded.emit(f'downloading folder {folder}')
        self.dialog.progressBar.setMaximum(len(files))
        for i, filename in enumerate(files):
            with open(f'{LOCAL_APP_PATH}/jsonfile/{filename}', 'wb') as f:
                self.ftp.retrbinary('RETR ' + filename, f.write)
            self.data_downloaded.emit(f'{filename} downloaded')
            self.progress_update.emit(i)
        self.ftp.cwd('..')

    def download_app(self):
        exes = [e for e in self.ftp.nlst() if 'exe' in e]
        md5txts = [e for e in self.ftp.nlst() if 'md5.txt' in e]
        if len(exes)==1 and len(md5txts)==1:
            targetname, md5txt = exes[0], md5txts[0]
            #  targetname = f'{LOCAL_APP_PATH}/{targetname}'
            #  md5txt = f'{LOCAL_APP_PATH}/{md5txt}'

            self.data_downloaded.emit(f'Downloading {md5txt}...')
            self.download_file(md5txt)
            md5_expected = open(f'{LOCAL_APP_PATH}/{md5txt}', 'r').read().strip()
            logger.info(f'md5_expected {md5_expected}')

            self.data_downloaded.emit(f'Downloading {targetname}...')
            self.download_file(targetname)

            #  self.data_downloaded.emit('Updated')

        return targetname, md5_expected

    def download_file(self, filename):
        logger.info(f'filename {filename}')
        self.dlsize = 0
        self.dialog.progressBar.setMaximum(self.ftp.size(filename))
        self.localfile = open(f'{LOCAL_APP_PATH}/{filename}', 'wb')
        try:
            self.ftp.retrbinary('RETR ' + filename, self.file_write)
        except Exception as ex:
            logger.info(f'[ERROR]{type_(ex)}, {ex}')
            self.dialog.progressBar.setValue(0)
            #  self.dialog.hide()
        self.localfile.close()

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

        if wait_for_process_end_if_downloading():
            logger.info('============= path1 clean job at reopening app ==============')
            delete_trigger_file()
            delete_app_exe()
            return
        else:
            need_to_download_when_version_check = True
            if not need_to_download_when_version_check:
                logger.info('============= path2 check version no download ==============')
                return

        logger.info('============= path3 check version yes download ==============')
        self.dialog = MyDialog(self)
        self.dialog.setModal(True)
        self.thread = DownloadThread()
        self.thread.dialog = self.dialog
        self.thread.progress_update.connect(self.dialog.update_progress)
        self.thread.data_downloaded.connect(self.dialog.on_data_ready)
        self.thread.quit.connect(self.quit)
        self.thread.start()
        self.dialog.show()
        with open(f'{LOCAL_APP_PATH}\sap109-testing-upgrade-starting-{os.getpid()}', 'w'):
            pass

    def quit(self):
        logger.info('MyWindow quit')
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MyWindow()
    proc = psutil.Process(os.getpid())
    proc_name = proc.name()
    app.exec_()

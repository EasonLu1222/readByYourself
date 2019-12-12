import os
import io
import sys
import glob
import errno
import psutil
import shutil
import ftplib
from ftplib import FTP
from threading import Thread
import time
from subprocess import Popen
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import RegexMatchingEventHandler
import wx
import wx.lib.agw.pygauge as PG
from pubsub import pub


from win32com.shell import shell, shellcon
import pythoncom


type_ = lambda ex: f'<{type(ex).__name__}>'

EXE_DIR = 'C:/Users/zealz/SAP109_STATION'


STATION = 'AudioListen'
STATIONS = {
    "MainBoard": "Station02_MainBoard",
    "CapTouchMic": "Station03_SwBoard",
    "LED": "Station04_LedBoard",
    "RF": "Station05_BtWiFi",
    "AudioListen": "Station06_AudioListen",
    "Leak": "Station07_Leak",
    "WPC": "Station08_WPC",
    "PowerSensor": "Station09_Antenna",
    "SA": "Station10_SA",
    "AcousticListen": "Station11_AcousticListen",
    "Download": "Station12_Download",
    "BTMacFix": "StationXX_BTMacFixDownload",
}


def log(text):
    with open(f'{EXE_DIR}/log.txt', 'a+') as f:
        f.write(f'{text}\n')


#  log = print

class MyFtp():
    def __init__(self):
        ip = '10.228.14.92'
        user, passwd = 'SAP109', 'sapsfc'
        self.ftp = FTP(ip)
        self.ftp.login(user=user, passwd=passwd)

    def download(self, ftp_path, downloads_path):
        self.ftp.cwd(ftp_path)

        for file in self.ftp.nlst():
            log("Downloading..." + file)
            if not os.path.isdir(downloads_path):
                os.mkdir(downloads_path)
            self.ftp.retrbinary("RETR " + file, open(f'{downloads_path}/{file}' , 'wb').write)

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
            log("Created: " + destination)
            os.chdir(destination)
        except OSError:
            pass
        except ftplib.error_perm:
            log("Error: could not change to " + path)
            sys.exit("Ending Application")

        filelist=self.ftp.nlst()
        for file in filelist:
            time.sleep(interval)
            try:
                cwd = f'{path}/{file}'
                self.ftp.cwd(cwd)
                self.downloadFiles(f'{path}/{file}', f'{destination}/{file}')

            except ftplib.error_perm:
                des = f'{destination}/{file}'
                self.ftp.retrbinary("RETR " + file, open(des, 'wb').write)
                log(f'{file} downloaded')
        return


def wait_for_process_end(pid):
    log(f'wait for pid to stop {pid}')
    while psutil.pid_exists(pid): pass
    log(f'process {pid} is closed')
    time.sleep(1)

def step1_delete_files():
    exefiles = glob.glob(f'{EXE_DIR}/*.exe')
    jsondir = f'{EXE_DIR}/jsonfile'
    for exe in exefiles:
        os.remove(exe)
    if os.path.isdir(jsondir):
        shutil.rmtree(jsondir)
    log('step1 done')

def step2_download():
    log('step2_download')
    ftp_path = f'/Belkin109/Latest_App'
    log('prepare ftp...')
    ftp = MyFtp()
    log('ftp connected...')
    ftp.downloadFiles(ftp_path, EXE_DIR)
    log(f'ftp_path {ftp_path}')
    log(f'downloads_path {EXE_DIR}')
    target = glob.glob(f'{EXE_DIR}/*.exe')[0]
    targetname = target[target.rfind('\\')+1:]

    #  targetname ='xxx.exe'
    log(f'targetname {targetname}')
    return targetname

def step3_create_shortcut(targetname):
    try:
        pythoncom.CoInitialize()
        log('step3_create_shortcut')
        shortcutname = 'app.lnk'
        #  desktop_path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
        desktop_path = '\\\\Mac\\Home\\Desktop'
        shortcut_path = os.path.join(desktop_path, shortcutname)
        target_path = f'{EXE_DIR}/{targetname}'
        log(f'desktop_path {desktop_path}')
        log(f'shortcut_path {shortcut_path}')
        log(f'target_path {target_path}')
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
        log(f'[ERROR]{type_(ex)}, {ex}')


class FileEventHandler(RegexMatchingEventHandler):
    REGEX = [r".*sap109-testing-upgrade-starting-\d+"]
    def __init__(self):
        super().__init__(self.REGEX)
        self.to_stop = False

    def on_created(self, event):
        x = event.src_path
        pid = int(x[x.rfind('-')+1:])
        wait_for_process_end(pid)

        # doing stuff...
        try:
            step1_delete_files()
            targetname = step2_download()
            step3_create_shortcut(targetname)
        except Exception as ex:
            log(f'[ERROR]{type_(ex)}, {ex}')

        self.to_stop = True
        log('TestThread end')


class FileWatcher:
    def __init__(self, src_path):
        self.src_path = src_path
        self.handler = FileEventHandler()
        self.handler.watcher = self
        self.observer = Observer()

    def run(self):
        self.observer.schedule(self.handler, self.src_path, recursive=True)
        self.observer.start()
        log('watcher ...1')
        while not self.handler.to_stop:
            time.sleep(1)
        log('watcher ...2')
        self.observer.stop()
        self.observer.join()
        log('watcher ...3')


if __name__ == "__main__":
    '''
        this daemon program must be used with nssm on windows
        usage:
            install a service
                nssm install servcie_name path_to_the_program
            remove a service
                nssm remove servcie_name confirm
        reference: https://nssm.cc/usage
    '''

    path = f'C:\\temp'
    if not os.path.isdir(path):
        os.mkdir(path)

    pid = os.getpid()
    log(f'pid {pid}')

    watcher = FileWatcher(path)
    watcher.run()

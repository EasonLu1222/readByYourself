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
from subprocess import Popen
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from watchdog.events import RegexMatchingEventHandler
from win32com.shell import shell, shellcon
import pythoncom


type_ = lambda ex: f'<{type(ex).__name__}>'

# should work for nssm on station pc
EXE_DIR = 'D:/SAP109_STATION'
LOG_DIR = 'D:/SAP109_STATION/log.txt'

# work for nssm (on zealzel's laptop)
#  USER_PATH = 'C:/Users/zealz'
#  EXE_DIR = 'C:/Users/zealz/SAP109_STATION'
#  LOG_DIR = 'C:/Users/zealz/SAP109_STATION/log.txt'

# not work for nssm
#  USER_PATH = f'C:/Users/{getpass.getuser()}'
#  EXE_DIR = f'{USER_PATH}/SAP109_STATION'
#  LOG_DIR = f'{EXE_DIR}/log.txt'

# not work for nssm
#  USER_PATH = 'C:/Users/%s' % getpass.getuser()
#  EXE_DIR = '%s/SAP109_STATION' % USER_PATH
#  LOG_DIR = '%s/log.txt' % EXE_DIR


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
    if not os.path.isdir(EXE_DIR):
        os.makedirs(EXE_DIR)
    with open(LOG_DIR, 'a+') as f:
        f.write('%s\n' % text)


def get_md5(file_path):
    with open(file_path, 'rb') as file_to_check:
        data = file_to_check.read()
        md5_returned = hashlib.md5(data).hexdigest()
    return md5_returned


class MyFtp():
    def __init__(self):

        # ip for office intranet
        #  ip = '10.228.14.92'

        # ip for production line intranet
        ip = '10.228.16.92'

        user, passwd = 'SAP109', 'sapsfc'
        self.ftp = FTP(ip)
        self.ftp.login(user=user, passwd=passwd)

    def downloadfile(self, path, filepath):
        dirname = os.path.dirname(path)
        filename = os.path.basename(path)
        self.ftp.cwd(dirname)
        self.ftp.retrbinary(f'RETR {filename}', open(filepath, 'wb').write)

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
        except OSError as ex:
            log(f'OSError {ex}')
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
                # this is for file download
                des = f'{destination}/{file}'
                #  print(f'ftp workdir: {self.ftp.pwd()}')
                #  print(f'loc workdir: {os.getcwd()}')
                #  print(f'download file: {file}')
                #  print(f'des: {des}')
                print(f'download file: {file}')
                self.ftp.retrbinary("RETR " + file, open(des, 'wb').write)
                log(f'{file} downloaded')
        self.ftp.cwd('../')
        os.chdir('../')
        return


def wait_for_process_end(pid):
    log(f'wait for pid to stop {pid}')
    while psutil.pid_exists(pid): pass
    log(f'process {pid} is closed')
    time.sleep(1)

def delete_files(exclude_exe=None):
    log('delete_files start')

    # delete trigger file
    trigger_file = glob.glob(f'{EXE_DIR}/sap109-testing-upgrade-starting-*')
    for e in trigger_file:
        os.remove(e)

    # delete app_xxx.exe
    exefiles = glob.glob(f'{EXE_DIR}/*.exe')
    if exclude_exe:
        exefiles = [e for e in exefiles if exclude_exe not in e]
    log(f'exefiles {exefiles}')
    for exe in exefiles:
        os.remove(exe)

    # delete md5.txt
    os.remove(f'{EXE_DIR}/md5.txt')

    # delete jsonfile/
    jsondir = f'{EXE_DIR}/jsonfile'
    if os.path.isdir(jsondir):
        shutil.rmtree(jsondir)
    log('delete_files done')


def prepare_ftp():
    log('prepare ftp...')
    ftp = MyFtp()
    log('ftp connected...')
    return ftp


def download_app(ftp):
    log('download_app start')
    ftp_path = f'/Belkin109/Latest_App'
    ftp.ftp.cwd(ftp_path)
    exes = [e for e in ftp.ftp.nlst() if 'exe' in e]
    md5txts = [e for e in ftp.ftp.nlst() if 'md5.txt' in e]
    log(f'exes {exes}')
    log(f'md5txts {md5txts}')
    if len(exes)==1 and len(md5txts)==1:
        targetname, md5txt = exes[0], md5txts[0]
        ftp.downloadfile(targetname, f'{EXE_DIR}/{targetname}')
        ftp.downloadfile(md5txt, f'{EXE_DIR}/md5.txt')
        md5txt = glob.glob(f'{EXE_DIR}/md5.txt')[0]
        md5_expected = open(md5txt, 'r').read().strip()
        log(f'targetname {targetname}')
        log('download_app done')
        return targetname, md5_expected
    else:
        return None


def download_jsonfile(ftp):
    log('download_jsonfile start')
    ftp_path = f'/Belkin109/Latest_App/jsonfile'
    ftp.downloadFiles(ftp_path, f'{EXE_DIR}/jsonfile')
    log('download_jsonfile done')


def checkmd5(targetname, md5_expected):
    app_path = f'{EXE_DIR}/{targetname}'
    md5_actual = get_md5(app_path)
    return True if md5_actual==md5_expected else False

def create_shortcut(targetname):
    log('create_shortcut start')
    try:
        pythoncom.CoInitialize()
        log('create_shortcut')
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
    log('create_shortcut done')


def upgrade_task():
    ftp = prepare_ftp()
    appname, md5_expected = download_app(ftp)
    if checkmd5(appname, md5_expected):
        delete_files(appname)
        download_jsonfile(ftp)
        create_shortcut(appname)


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
            upgrade_task()
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
            deploy this py into exe
                pyinstaller --onefile simpledeploymon.py   --> simpledeploymon.exe
            move to correct directory
                on station pc
                    daemon: C:/simpledeploymon.exe
                    test-program: D:/SAP109_STATION/...
            install a service
                nssm install servcie_name path_to_the_program
            remove a service
                nssm remove servcie_name confirm
        reference: https://nssm.cc/usage
    '''

    path = f'C:\\tempp'
    if not os.path.isdir(path):
        os.mkdir(path)

    pid = os.getpid()
    log('pid: %s' % pid)

    watcher = FileWatcher(EXE_DIR)
    watcher.run()

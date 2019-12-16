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


#  def debug_step3():
    #  pythoncom.CoInitialize()
    #  try:
        #  log('.....1')
        #  x1 = shell.SHGetFolderPath
        #  log(x1)

        #  log('.....2')
        #  x2 = shellcon.CSIDL_DESKTOP
        #  log(x2)

        #  log('.....2.5')
        #  x25 = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, 0, 0)
        #  log(x25)

        #  log('.....3')
        #  x3 = shell.CLSID_ShellLink
        #  log(x3)

        #  log('.....4')
        #  x4 = shell.IID_IShellLink
        #  log(x4)

        #  log('.....5')
    #  except Exception as ex:
        #  log(f'{type_(ex)}, {ex}')


def step4_restart():
    log('step4_restart')
    wx.MessageBox('Please restart the testing program')


class TestThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.start()    # start the thread

    def run(self):
        #  log('.......debug_step3')
        #  wx.CallAfter(pub.sendMessage, "update", message='debug_step3')
        #  debug_step3()

        log('.......1')
        wx.CallAfter(pub.sendMessage, "update", message='step1')
        step1_delete_files()

        log('.......2')
        wx.CallAfter(pub.sendMessage, "update", message='step2')
        targetname = step2_download()

        log('.......3')
        wx.CallAfter(pub.sendMessage, "update", message='step3')
        step3_create_shortcut(targetname)

        log('.......4')
        wx.CallAfter(pub.sendMessage, "update", message='step4')
        step4_restart()

        pub.sendMessage('end')
        #  wx.CallAfter(pub.sendMessage, "end")
        log('TestThread end')


class FileEventHandler(RegexMatchingEventHandler):
    REGEX = [r".*sap109-testing-upgrade-starting-\d+"]
    def __init__(self):
        super().__init__(self.REGEX)
        self.to_stop = False

    def on_created(self, event):
        x = event.src_path
        pid = int(x[x.rfind('-')+1:])
        wait_for_process_end(pid)
        pub.sendMessage('set_visible')


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


class MonitorApp(wx.App):
    def __init__(self):
        wx.App.__init__(self)
        pub.subscribe(self.set_visible, 'set_visible')
        pub.subscribe(self.end, 'end')
        self.watcher = FileWatcher(path)
        self.watcher.app = self
        self.watcher.run()

    def end(self):
        log('app end start')
        self.watcher.handler.to_stop = True
        #  wx.MessageBox('Please restart the testing program')

    def set_visible(self):
        self.frame = MainFrame()
        pub.subscribe(self.frame.update, 'update')
        log('aaa')
        TestThread()
        log('bbb')
        #  try:
        self.frame.ShowModal()
        #  except Exception as ex:
            #  log(f'[ERROR]{type_(ex)}, {ex}')
        log('ccc')


class MainFrame(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, title='progress',size=(500,80))
        self.progress = wx.Gauge(self, wx.ID_ANY, 4, wx.DefaultPosition, wx.Size( 100,15 ), wx.GA_HORIZONTAL)

        #  self.progress = PG.PyGauge(self, -1, size=(100, 25), style=wx.GA_HORIZONTAL)
        #  self.progress.SetDrawValue(draw=True, drawPercent=True, font=None, colour=wx.BLACK, formatString=None)
        #  self.progress.SetBackgroundColour(wx.WHITE)
        #  self.progress.SetBorderColor(wx.BLACK)


        #  sizer = wx.BoxSizer(wx.VERTICAL)
        #  sizer.Add(self.progress, 0, wx.EXPAND)
        #  self.SetSizer(sizer)
        self.count = 0

    def update(self, message):
        log('-----------update')
        self.count += 1
        try:
            if self.count >= 4:
                log('count==4, Destroy!')
                self.Destroy()
            log('update .....2')
            self.progress.SetValue(self.count)
        except Exception as ex:
            log(f'[ERROR]{type_(ex)}, {ex}')
        log('update .....3')


if __name__ == "__main__":

    path = f'C:\\temp'
    if not os.path.isdir(path):
        os.mkdir(path)

    pid = os.getpid()
    log(f'pid {pid}')

    app = MonitorApp()
    app.MainLoop()


    #  targetname = 'app_20191211_1188.exe'
    #  print("targetname", targetname)
    #  step3_create_shortcut(targetname)

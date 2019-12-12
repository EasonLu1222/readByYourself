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


class MyFtp():
    def __init__(self):
        ip = '10.228.14.92'
        user, passwd = 'SAP109', 'sapsfc'
        self.ftp = FTP(ip)
        self.ftp.login(user=user, passwd=passwd)

    def download(self, ftp_path, downloads_path):
        self.ftp.cwd(ftp_path)

        for file in self.ftp.nlst():
            print("Downloading..." + file)
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
            print("Created: " + destination)
            os.chdir(destination)
        except OSError:
            pass
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
                des = f'{destination}/{file}'
                self.ftp.retrbinary("RETR " + file, open(des, 'wb').write)
                print(f'{file} downloaded')
        return


def wait_for_process_end(pid):
    print('wait for pid to stop', pid)
    while psutil.pid_exists(pid): pass
    print(f'process {pid} is closed')
    time.sleep(1)

def step1_delete_files():
    exefiles = glob.glob(f'{EXE_DIR}/*.exe')
    jsondir = f'{EXE_DIR}/jsonfile'
    for exe in exefiles:
        os.remove(exe)
    if os.path.isdir(jsondir):
        shutil.rmtree(jsondir)
    print('step1 done')

def step2_download():
    print('step2_download')
    ftp_path = f'/Belkin109/Latest_App'
    print('prepare ftp...')
    ftp = MyFtp()
    print('ftp connected...')
    ftp.downloadFiles(ftp_path, EXE_DIR)
    print('ftp_path', ftp_path)
    print('downloads_path', EXE_DIR)
    target = glob.glob(f'{EXE_DIR}/*.exe')[0]
    targetname = target[target.rfind('\\')+1:]

    #  targetname ='xxx.exe'
    print('targetname', targetname)
    return targetname

def step3_create_shortcut(targetname):
    from win32com.shell import shell, shellcon
    import pythoncom
    print('step3_create_shortcut')
    shortcutname = 'app.lnk'
    desktop_path = shell.SHGetFolderPath (0, shellcon.CSIDL_DESKTOP, 0, 0)
    shortcut_path = os.path.join(desktop_path, shortcutname)
    target_path = f'{EXE_DIR}/{targetname}'
    print('shortcut_path', shortcut_path)
    print('target_path', target_path)
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


def step4_restart():
    print('step4_restart')
    wx.MessageBox('Please restart the testing program')


class TestThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.start()    # start the thread

    def run(self):
        print('.......1')
        wx.CallAfter(pub.sendMessage, "update", message='step1')
        step1_delete_files()

        print('.......2')
        wx.CallAfter(pub.sendMessage, "update", message='step2')
        targetname = step2_download()

        print('.......3')
        wx.CallAfter(pub.sendMessage, "update", message='step3')
        step3_create_shortcut(targetname)

        print('.......4')
        wx.CallAfter(pub.sendMessage, "update", message='step4')
        step4_restart()

        pub.sendMessage('end')
        #  wx.CallAfter(pub.sendMessage, "end")
        print('TestThread end')


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
        print('watcher ...1')
        while not self.handler.to_stop:
            time.sleep(1)
        print('watcher ...2')
        self.observer.stop()
        self.observer.join()
        print('watcher ...3')


class MonitorApp(wx.App):
    def __init__(self):
        wx.App.__init__(self)
        pub.subscribe(self.set_visible, 'set_visible')
        pub.subscribe(self.end, 'end')
        self.watcher = FileWatcher(path)
        self.watcher.app = self
        self.watcher.run()

    def end(self):
        print('app end start')
        self.watcher.handler.to_stop = True
        #  wx.MessageBox('Please restart the testing program')

    def set_visible(self):
        self.frame = MainFrame()
        pub.subscribe(self.frame.update, 'update')
        print('aaa')
        TestThread()
        print('bbb')
        try:
            self.frame.ShowModal()
        except Exception as ex:
            print(ex)
        print('ccc')


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
        print('-----------update')
        self.count += 1
        if self.count >= 4:
            print('count==4, Destroy!')
            self.Destroy()
        self.progress.SetValue(self.count)


if __name__ == "__main__":

    path = f'C:\\temp'
    if not os.path.isdir(path):
        os.mkdir(path)

    pid = os.getpid()
    print('pid', pid)

    app = MonitorApp()
    app.MainLoop()

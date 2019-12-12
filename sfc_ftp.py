import os
import io
import sys
import time
import glob
import ftplib
import errno
from ftplib import FTP
import pandas as pd

#  station = 'Audio'
#  stations_ftp = {
    #  'SA': 'Belkin109/lk_test/SA',
    #  'RF': 'Belkin109/lk_test/RF',
    #  'PowerSensor': 'Belkin109/lk_test/PowerSensor',
    #  'WPC': 'Belkin109/lk_test/WPC',
    #  'Audio': 'Belkin109/lk_test/Audio',
#  }
#  stations_downloads = {
    #  'SA': 'downloads/SA',
    #  'RF': 'downloads/RF',
    #  'PowerSensor': 'downloads/PowerSensor',
    #  'WPC': 'downloads/WPC',
#  }

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
            print(f'downloading {file}...')
            time.sleep(interval)
            try:
                cwd = f'{path}/{file}' 
                print('cwd', cwd)
                self.ftp.cwd(cwd)
                self.downloadFiles(f'{path}/{file}', f'{destination}/{file}')

            except ftplib.error_perm:
                des = f'{destination}/{file}'
                print('des', des)
                self.ftp.retrbinary("RETR " + file, open(des, 'wb').write)
                print(f'{file} downloaded')
        return



if __name__ == "__main__":

    ftp_path = f'/Belkin109/Latest_App'
    #  downloads_path = f'{stations_downloads[station]}'
    downloads_path = f'C:/Users/zealz/temp'

    ftp = MyFtp()
    #  ftp.download(ftp_path, downloads_path)

    print('ftp_path', ftp_path)
    print('downloads_path', downloads_path)

    ftp.downloadFiles(ftp_path, downloads_path)

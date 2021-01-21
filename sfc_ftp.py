import os
import io
import sys
import time
import glob
import ftplib
import errno
from datetime import datetime
from ftplib import FTP
import pandas as pd
from config import PRODUCT, FTP_USER, FTP_PWD


stations_downloads = {
    'RF': 'downloads/RF',
    'Audio': 'downloads/Audio',
    "Leak": "downloads/Leak",
    'WPC': 'downloads/WPC',
    'PowerSensor': 'downloads/PowerSensor',
    'SA': 'downloads/SA',
    "Acoustic": "downloads/Acoustic",
    "Download": "downloads/Download",
    'MicBlock': 'downloads/MicBlock',
    "MAC_DB": "downloads/MAC_DB",
}

STATIONS = {
    "MainBoard": "Station02_MainBoard",
    "CapTouchMic": "Station03_SwBoard",
    "Led": "Station04_LedBoard",
    "RF": "Station05_BtWiFi",
    "Audio": "Station06_AudioListen",
    "Leak": "Station07_Leak",
    "WPC": "Station08_WPC",
    "PowerSensor": "Station09_Antenna",
    "SA": "Station10_SA",
    "Acoustic": "Station11_AcousticListen",
    "Download": "Station12_Download",
    "MicBlock": "Station13_MicBlock",
    "MAC_DB": "MAC_DB",
}


class MyFtp():
    def __init__(self):
        ip = '10.228.14.92'
        user, passwd = FTP_USER, FTP_PWD
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

    def downloadFiles(self, ftp_path, target_path):
        '''
            target_path must be in absolute path format
        '''
        interval = 0.01
        try:
            self.ftp.cwd(ftp_path)
            self.mkdir_p(target_path)
            print("Created: " + target_path)
            os.chdir(target_path)
        except OSError as ex:
            print(f'OSError {ex}')
        except ftplib.error_perm:
            print("Error: could not change to " + ftp_path)
            sys.exit("Ending Application")

        filelist=self.ftp.nlst()
        for file in filelist:
            time.sleep(interval)
            try:
                cwd = f'{ftp_path}/{file}'
                self.ftp.cwd(cwd)
                self.downloadFiles(f'{ftp_path}/{file}', f'{target_path}/{file}')
                self.ftp.cwd('../')

            except ftplib.error_perm:
                # this is for file download
                des = f'{target_path}/{file}'

                if not os.path.isfile(des):
                    print(f'download file: {file}', end='')
                    if "MAC_DB" in des :
                        now = datetime.now().strftime('%Y%m%d%H%M%S')
                        self.ftp.retrbinary("RETR " + file, open(f'{target_path}/{now}_{file}', 'wb').write)
                    else :
                        self.ftp.retrbinary("RETR " + file, open(des, 'wb').write)
                    print(f' ---> downloaded')
                else:
                    if "MAC_DB" in des :
                        print(f'download file: {file}', end='')
                        now = datetime.now().strftime('%Y%m%d%H%M%S')
                        self.ftp.retrbinary("RETR " + file, open(f'{target_path}/{now}_{file}', 'wb').write)
                        print(f' ---> downloaded')
                    else :
                        print(f'{des} already downloaded.')
        return


if __name__ == "__main__":

    station_to_download = ['RF', 'Audio', 'Leak', 'WPC', 'PowerSensor', 'SA', 'Acoustic', 'Download', 'MicBlock', 'MAC_DB']

    ftp = MyFtp()
    ftp_paths = [f'/Belkin{PRODUCT}/{STATIONS[sta]}' for sta in station_to_download]
    loc_paths = [f"{os.path.abspath('.')}/{stations_downloads[s]}" for s in station_to_download]
    for ftp_path, loc_path in zip(ftp_paths, loc_paths):
        print('ftp_path', ftp_path)
        print('loc_path', loc_path)
        ftp.downloadFiles(ftp_path, loc_path)

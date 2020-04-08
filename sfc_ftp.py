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
stations_ftp = {
    'RF': 'Belkin109/lk_test/RF',
    'Audio': 'Belkin109/lk_test/Audio',
    'WPC': 'Belkin109/lk_test/WPC',
    'SA': 'Belkin109/lk_test/SA',
    'PowerSensor': 'Belkin109/lk_test/PowerSensor',
}
stations_downloads = {
    'RF': 'downloads/RF',
    'Audio': 'downloads/Audio',
    'WPC': 'downloads/WPC',
    'SA': 'downloads/SA',
    'PowerSensor': 'downloads/PowerSensor',
}

STATIONS = {
    "MainBoard": "Station02_MainBoard",
    "CapTouchMic": "Station03_SwBoard",
    "LED": "Station04_LedBoard",
    "RF": "Station05_BtWiFi",
    "Audio": "Station06_AudioListen",
    "Leak": "Station07_Leak",
    "WPC": "Station08_WPC",
    "PowerSensor": "Station09_Antenna",
    "SA": "Station10_SA",
    "Acoustic": "Station11_AcousticListen",
    "Download": "Station12_Download",
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

            except ftplib.error_perm:
                # this is for file download
                des = f'{target_path}/{file}'

                if not os.path.isfile(des):
                    print(f'download file: {file}', end='')
                    self.ftp.retrbinary("RETR " + file, open(des, 'wb').write)
                    print(f' ---> downloaded')
                else:
                    print(f'{des} already downloaded.')
            self.ftp.cwd('../')
        return


if __name__ == "__main__":


    #  station_to_download = ['RF', 'Audio', 'WPC', 'SA', 'PowerSensor']
    station_to_download = ['SA']

    ftp = MyFtp()
    ftp_paths = [f'/Belkin109/{STATIONS[sta]}' for sta in station_to_download]
    loc_paths = [f"{os.path.abspath('.')}/{stations_downloads[s]}" for s in station_to_download]
    for ftp_path, loc_path in zip(ftp_paths, loc_paths):
        print('ftp_path', ftp_path)
        print('loc_path', loc_path)
        ftp.downloadFiles(ftp_path, loc_path)

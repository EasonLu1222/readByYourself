import os
import glob
from ftplib import FTP
import pandas as pd


station = 'Audio'
stations_ftp = {
    'SA': 'Belkin109/lk_test/SA',
    'RF': 'Belkin109/lk_test/RF',
    'PowerSensor': 'Belkin109/lk_test/PowerSensor',
    'WPC': 'Belkin109/lk_test/WPC',
    'Audio': 'Belkin109/lk_test/Audio',
}
stations_downloads = {
    'SA': 'downloads/SA',
    'RF': 'downloads/RF',
    'PowerSensor': 'downloads/PowerSensor',
    'WPC': 'downloads/WPC',
}


downloads_path = f'{stations_downloads[station]}'
def ftp_download(downloads_path):
    for file in ftp.nlst():
        print("Downloading..." + file)
        if not os.path.isdir(downloads_path):
            os.mkdir(downloads_path)
        ftp.retrbinary("RETR " + file, open(f'{downloads_path}/{file}' , 'wb').write)


if __name__ == "__main__":
    ip = '10.228.14.92'
    user, passwd = 'SAP109', 'sapsfc'
    ftp = FTP(ip)
    ftp.login(user=user, passwd=passwd)
    ftp.cwd(stations_ftp[station])
    ftp_download(downloads_path)

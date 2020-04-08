"""
This is a helper program to upload log files to FTP server.
Usage:
    1. Compile this script to executable with the following command:
        # pyinstaller --onefile upload_log.py
    2. Put the upload_log.exe to C:\\Program Files
    3. Open "Computer Management" and set the scheduler to run upload_log.exe periodically
        For now, the command is C:\\Program Files\\upload_log.exe C:\\SAP109_STATION
"""

import os
import argparse
import json
from ftplib import FTP, error_perm

STATIONS = [
    {
        "station": "MainBoard",
        "file_prefix": "Station02_MainBoard",
    },
    {
        "station": "CapTouchMic",
        "file_prefix": "Station03_SwBoard",
    },
    {
        "station": "LED",
        "file_prefix": "Station04_LedBoard",
    },
    {
        "station": "RF",
        "file_prefix": "Station05_BtWiFi",
    },
    {
        "station": "AudioListen",
        "file_prefix": "Station06_AudioListen",
    },
    {
        "station": "Leak",
        "file_prefix": "Station07_Leak",
    },
    {
        "station": "WPC",
        "file_prefix": "Station08_WPC",
    },
    {
        "station": "PowerSensor",
        "file_prefix": "Station09_Antenna",
    },
    {
        "station": "SA",
        "file_prefix": "Station10_SA",
    },
    {
        "station": "AcousticListen",
        "file_prefix": "Station11_AcousticListen",
    },
    {
        "station": "Download",
        "file_prefix": "Station12_Download",
    },
    {
        "station": "MicBlock",
        "file_prefix": "Station13_MicBlock",
    },
]


def create_station_folder(ftp):
    """
    Create station folders on FTP site if not exist
    """
    for station in STATIONS:
        dir = station['file_prefix']

        try:
            ftp.mkd(dir)
        except error_perm as e:
            print(f"{e}")


# def upload_log(ftp, local_log_dir='/Users/jason/Desktop/mb_test_gui'):
def upload_log(ftp, app_dir):
    station = None
    station_path = os.path.join(app_dir, 'jsonfile', 'station.json')
    with open(station_path, 'r') as f:
        station_json = json.load(f)
        station = station_json['STATION']
    if not station:
        print("Error: station.json not found")
        return

    ftp_log_dir = ''
    for station_obj in STATIONS:
        if station_obj['station'] == station:
            ftp_log_dir = station_obj['file_prefix']
            break

    if ftp_log_dir:
        ftp.cwd(ftp_log_dir)

        # Delete existing logs in FTP
        ftp_files = ftp.nlst()
        for file_name in ftp_files:
            ftp.delete(file_name)

        # Upload logs from station to FTP
        local_log_dir = os.path.join(app_dir, 'logs')
        files = os.listdir(local_log_dir)
        for file_name in files:
            if file_name.startswith('log') or file_name.endswith('csv'):
                with open(os.path.join(local_log_dir, file_name), 'rb') as f:
                    ftp.storbinary(f'STOR {file_name}', f)
        print('Upload successfully')
    else:
        print(f'Error: remote FTP directory for {station} station not found')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='app path', type=str)
    args = parser.parse_args()
    app_dir = args.path

    ftp = FTP('10.228.16.92')
    ftp.login(user='SAP109', passwd='sapsfc')
    ftp.cwd('Belkin109')

    upload_log(ftp, app_dir)

    ftp.quit()

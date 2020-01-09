"""
This is a helper program to zip and upload local folder to FTP server.
Usage:
    python upload_folder.py ZIP_NAME LOCAL_DIR REMOTE_DIR

    e.g.: python upload_folder.py klippel "C:\QC_Log_Files" "Belkin109/Station11_AcousticListen"
"""
import os
import argparse
from shutil import make_archive
from ftplib import FTP


def upload_folder(zip_name, local_path, remote_path):
    zip_path = f'{local_path}.zip'
    make_archive(local_path, 'zip', local_path)

    ftp = FTP('10.228.16.92', timeout=180)
    ftp.login(user='SAP109', passwd='sapsfc')
    ftp.cwd(remote_path)

    with open(zip_path, 'rb') as f:
        ftp.storbinary(f'STOR {zip_name}.zip', f)
    os.remove(zip_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('zip_name', help='zip name', type=str)
    parser.add_argument('local_path', help='local path', type=str)
    parser.add_argument('remote_path', help='remote path', type=str)
    args = parser.parse_args()
    zip_name = args.zip_name
    local_path = args.local_path
    remote_path = args.remote_path

    upload_folder(zip_name, local_path, remote_path)

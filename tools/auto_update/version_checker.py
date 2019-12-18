import os
import time
import socket
import sys
from ftplib import FTP
from PyQt5.QtWidgets import QApplication
from mylogger import logger
from PyQt5.QtCore import QThread, pyqtSignal
import getpass
from upgrade import FTP_DIR, MyFtp


class VersionChecker(QThread):

    version_checked = pyqtSignal(object)

    def __init__(self):
        QThread.__init__(self)

    def run(self):
        can_update = self.is_update_available()
        self.version_checked.emit(can_update)

    def is_update_available(self):
        """
        Compare the local app version with remote one(on FTP)

        Returns:
            Bool, True if a newer version exist, False otherwise
        """
        ftp = MyFtp()
        if not ftp:
            return False

        file_list = ftp.nlst()
        latest_app_name = self.get_app_name_in_dir(file_list)

        if not latest_app_name:
            logger.error("Error: latest app not found")
            return False

        try:
            file_list = os.listdir(LOCAL_APP_PATH)
        except FileNotFoundError:
            logger.error("Error: local app not found")
            return False
        current_app_name = self.get_app_name_in_dir(file_list)
        logger.info(f'Remote app name: {latest_app_name}')
        logger.info(f'Local app name : {current_app_name}')

        ftp.quit()

        can_update = latest_app_name > current_app_name
        logger.info(f"Need update: {can_update}")

        return can_update

    def get_app_name_in_dir(self, file_list):
        """
        Get the app name from the file_list
        Args:
            file_list: An array of file name

        Returns:
            app name, e.g.: app_20191212_1131.exe
        """
        latest_app_name = ''
        for file_name in file_list:
            if file_name.startswith("app") and file_name > latest_app_name:
                latest_app_name = file_name

        return latest_app_name


if __name__ == "__main__":
    app = QApplication(sys.argv)
    vc = VersionChecker()
    vc.start()
    time.sleep(4)

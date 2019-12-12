import os
import socket
from ftplib import FTP

LOCAL_APP_PATH = 'D:\\SAP109_STATION'


def check_for_update():
    """
    Compare the local app version with remote one(on FTP)

    Returns:
        Bool, True if a newer version exist, False otherwise
    """
    ftp = get_ftp()
    if not ftp:
        return False

    file_list = ftp.nlst()
    latest_app_name = get_app_name_in_dir(file_list)

    if not latest_app_name:
        print("Error: latest app not found")
        return False

    file_list = os.listdir(LOCAL_APP_PATH)
    current_app_name = get_app_name_in_dir(file_list)
    print(f'Remote app name: {latest_app_name}')
    print(f'Local app name : {current_app_name}')

    ftp.quit()

    is_update_available = latest_app_name>current_app_name
    print(f"Need update: {is_update_available}")

    return is_update_available


def get_ftp():
    """
    Connect to the FTP and navigate to the Latest_App folder
    Returns:
        ftp object
    """
    rtn = None
    try:
        ftp = FTP('10.228.14.92', timeout=3)
        ftp.login(user='SAP109', passwd='sapsfc')
        ftp.cwd('Belkin109/Latest_App')
        rtn = ftp
    except socket.timeout as e:
        print('Error: FTP connection timeout')
    except OSError as e:
        print('Error: Network is unreachable')

    return rtn


def get_app_name_in_dir(file_list):
    """
    Get the app name from the file_list
    Args:
        file_list: An array of file name

    Returns:
        app name, e.g.: app_20191212_1131.exe
    """
    latest_app_name = None
    for file_name in file_list:
        if file_name.startswith("app"):
            latest_app_name = file_name
            break

    return latest_app_name


if __name__ == "__main__":
    check_for_update()

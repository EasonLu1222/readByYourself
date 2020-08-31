"""
This is a helper program for exporting csv table containing these fields ==>(sn, mainboard id, wifi mac, bt mac)

Usage:
    1. Compile this script to executable with the following command:
        # pyinstaller --onefile sn_mac_list.py
    2. Put the sn_mac_list.exe and sn_list.txt to any folder of the SA station
    3. Open mac_importer.exe --> click "browse" --> select sn_list.txt --> click "Start"
    4. The csv file will be stored in sap109_sn_mac_list folder

Note:
    sn_list.txt contains a list of product serial number

    Sample content of sn_list.txt(ignore any tabs or spaces):
        32PA0F65A001FJ
        32PA0F65A001EE
        32PA0F67A011XY
"""
import os
import sqlite3
import re
import csv
import requests
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from gooey import Gooey, GooeyParser

PRODUCT = '109'
DB_DIR = 'C:\\db'
DB_PATH = os.path.join(DB_DIR, 'address.db')
CSV_DIR = f'sap{PRODUCT}_sn_mac_list'


@Gooey(program_name=f"SAP{PRODUCT} SN to MAC Table Generator", progress_regex=r"^progress: (\d+)%$", show_restart_button=False)
def main():
    pid_list = []
    sn_pid_dict = {}
    desc = "SN to MAC table generator "
    file_help_msg = f"Please choose a SAP{PRODUCT} sn list in txt format"
    my_cool_parser = GooeyParser(description=desc)
    my_cool_parser.add_argument("FileChooser", help=file_help_msg, widget="FileChooser")
    args = my_cool_parser.parse_args()

    sn_or_pid_list_path = args.FileChooser
    with open(sn_or_pid_list_path, 'r') as f:
        all_sn_or_pid = f.read()
        sn_or_pid_list = all_sn_or_pid.split("\n")

    sn_list = list(filter(lambda x:len(x)==14, sn_or_pid_list))
    total_sn = len(sn_list)
    pid_list = list(filter(lambda x: len(x) == 28, sn_or_pid_list))
    total_pid = len(pid_list)

    if total_sn>0:
        for i, sn in enumerate(sn_list):
            pid = find_pid_by_sn(sn)
            if pid:
                print(f"{sn} ({i+1}/{total_sn})")
                sn_pid_dict[pid] = sn
                pid_list.append(pid)
            else:
                print(f"{sn} pid not found ({i+1}/{total_sn})")
    elif total_pid>0:
        for i, pid in enumerate(pid_list):
            sn = find_sn_by_pid(pid)
            if sn:
                print(f"{sn} ({i+1}/{total_pid})")
                sn_pid_dict[pid] = sn
            else:
                print(f"{pid} sn not found ({i+1}/{total_pid})")

    gen_sn_mac_table(pid_list, sn_pid_dict)

    print('\n')
    return False


def find_pid_by_sn(sn):
    url = f'http://10.228.14.99:8{PRODUCT}/search/Query_trace.asp'
    d = {'g_search1': sn, 'Submit': 'Search'}
    r = requests.post(url, data=d)
    res = r.text

    # print(res)
    MSN = r"\d{3}-\d{3}-\d{3}-\d{4}-\d{4}-\d{6}"
    match = re.search(MSN, res)
    if match:
        pid = match.group(0)
        return pid
    else:
        return False


def find_sn_by_pid(pid):
    url = f'http://10.228.14.99:8{PRODUCT}/search/Query_trace.asp'
    d = {'g_search1': pid, 'Submit': 'Search'}
    r = requests.post(url, data=d)
    res = r.text
    soup = BeautifulSoup(res, 'html.parser')
    try:
        sn = soup.select('table')[1].find_all('tr')[1].find_all('td')[1].find('b').text
        return sn
    except:
        return False


def gen_sn_mac_table(pid_list, sn_pid_dict):
    if Path(DB_PATH).is_file():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        pid_list_str = "('"+"','".join(pid_list)+"')"
        sql = f"SELECT SN, ADDRESS_WIFI, ADDRESS_BT from ADDRESS WHERE SN IN {pid_list_str}"
        c.execute(sql)
        data = c.fetchall()
        for i in range(len(data)):
            data[i] = (sn_pid_dict[data[i][0]],) + data[i]
        if not os.path.exists(CSV_DIR):
            os.makedirs(CSV_DIR)
        now = datetime.now()
        y, m, d, h, min, sec = now.year, now.month, now.day, now.hour, now.minute, now.second
        path = f'{CSV_DIR}\{y}{m:02d}{d:02d}_{h:02d}{min:02d}{sec:02d}.csv'
        with open(path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['SN', 'Mainboard ID', 'Wi-Fi MAC', 'BT MAC'])
            writer.writerows(data)
        conn.close()
    else:
        print("DB not found")


if __name__ == '__main__':
    main()
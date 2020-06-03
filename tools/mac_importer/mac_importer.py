"""
This is a helper program for importing WiFi and BT MAC address to database which is used in SA station

Usage:
    1. Compile this script to executable with the following command:
        # pyinstaller --onefile mac_importer.py
    2. Put the mac_importer.exe and addr.txt to any folder of the SA station
    3. Open mac_importer.exe --> click "browse" --> select addr.txt --> click "Start"
    4. The MAC addressed will be imported to the database

Note:
    addr.txt contains a starting MAC in hex format, followed by the total
    amount of consecutive MAC address

    Sample content of addr.txt:
        0xc4411e79bd16,1000
"""
import os
import sqlite3
from pathlib import Path
from sqlite3 import IntegrityError, OperationalError
from gooey import Gooey, GooeyParser

DB_DIR = 'C:\\db'
DB_PATH = os.path.join(DB_DIR, 'address.db')


@Gooey(program_name="SAP109 MAC Address Importer", show_restart_button=False)
def main():
    desc = "MAC address importer"
    file_help_msg = "Name of the file you want to process"
    my_cool_parser = GooeyParser(description=desc)
    my_cool_parser.add_argument("FileChooser", help=file_help_msg, widget="FileChooser")
    args = my_cool_parser.parse_args()

    mac_range_path = args.FileChooser
    with open(mac_range_path, 'r') as f:
        mac_range = f.read()
        start_mac, range = mac_range.split(',')

    mac_list = gen_mac_list(int(start_mac, 16), int(range))
    import_addr(mac_list)
    print('\n')


def gen_mac_list(start_mac, total_mac):
    """
    Generate a consecutive list of mac addresses given the starting mac address and the total number of them
    Args:
        start_mac: e.g. 0xc4411e6a09ac
        total_mac: e.g. 1000

    Returns: ["c4:41:1e:6a:09:ac", "c4:41:1e:6a:09:ad",...]
    """
    mac_list = []
    for i in range(total_mac):
        mac = format(start_mac + i, 'x')  # Convert hex number to hex string, e.g. 0xc4411e6a09ac to "c4411e6a09ac"
        ml = [mac[i:i + 2] for i in range(0, len(mac), 2)]
        mac_str = ":".join(ml)
        mac_list.append(mac_str)
    return mac_list


def import_addr(addr_list):
    total_inserted = 0
    total_duplicated = 0

    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        print("DB folder not exist. Creating DB folder")
    else:
        print("DB folder found")

    if Path(DB_PATH).is_file():
        print("DB found")
    else:
        create_table()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print(f"Opened database successfully")

    for i in range(0, len(addr_list)):
        if (i % 2) == 0:
            try:
                c.execute(f'INSERT INTO ADDRESS (ADDRESS_WIFI,ADDRESS_BT,SN) \
					VALUES ("{addr_list[i]}", "{addr_list[i + 1]}", null )')
                total_inserted += 1
            except IntegrityError as e:
                total_duplicated += 1
    conn.commit()
    conn.close()
    print("-----------------------------------")
    print(f"Inserted: {total_inserted}\nDuplicated: {total_duplicated}\nTotal: {total_inserted + total_duplicated}")


def create_table():
    conn = sqlite3.connect(DB_PATH)
    print(f"Opened database successfully")

    c = conn.cursor()
    c.execute('''CREATE TABLE ADDRESS
        (ADDRESS_WIFI   CHAR(17)  NOT NULL UNIQUE,
        ADDRESS_BT     CHAR(17)  NOT NULL UNIQUE,
        SN             CHAR(28)  UNIQUE);''')
    conn.commit()
    print(f"Table created successfully")

    c.execute('''CREATE INDEX `` ON `ADDRESS` (
        `ADDRESS_WIFI`	ASC,
        `ADDRESS_BT`	ASC,
        `SN`	ASC);''')
    conn.commit()
    print(f"Index created successfully")
    conn.close()


if __name__ == '__main__':
    main()

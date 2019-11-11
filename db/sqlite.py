#!/usr/bin/python
import sqlite3
from sqlite3 import IntegrityError
from mylogger import logger


DB_PATH = 'C:\\db\\address.db'
PADDING = ' ' * 4


def create_table():
    conn = sqlite3.connect(DB_PATH)
    logger.debug(f"{PADDING}Opened database successfully")

    c = conn.cursor()
    c.execute('''CREATE TABLE ADDRESS
           (ADDRESS_WIFI   CHAR(17)  NOT NULL UNIQUE,
            ADDRESS_BT     CHAR(17)  NOT NULL UNIQUE,
            SN             CHAR(28)  UNIQUE);''')
    conn.commit()
    logger.debug(f"{PADDING}Table created successfully")

    c.execute('''CREATE INDEX `` ON `ADDRESS` (
    	`ADDRESS_WIFI`	ASC,
    	`ADDRESS_BT`	ASC,
    	`SN`	ASC);''')
    conn.commit()
    logger.debug(f"{PADDING}Index created successfully")
    conn.close()


def gen_mac_list(start_mac, total_mac):
    mac_list = []
    for i in range(total_mac):
        mac = format(start_mac + i, 'x')
        ml = [mac[i:i + 2] for i in range(0, len(mac), 2)]
        mac_str = ":".join(ml)
        mac_list.append(mac_str)
    return mac_list


def import_addr(addr_list):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    logger.debug(f"{PADDING}Opened database successfully")

    for i in range(0, len(addr_list)):
        if (i % 2) == 0:
            try:
                c.execute(f'INSERT INTO ADDRESS (ADDRESS_WIFI,ADDRESS_BT,SN) \
                    VALUES ("{addr_list[i]}", "{addr_list[i + 1]}", null )')
            except IntegrityError as e:
                logger.error(f"Error inserting ({addr_list[i]}, {addr_list[i + 1]}), {e}")

    conn.commit()
    logger.debug(f"{PADDING}Records created successfully")
    conn.close()


def write_addr(addr, sn):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    logger.debug(f"{PADDING}Opened database successfully")

    c.execute(f'UPDATE ADDRESS set SN = "{sn}" where ADDRESS_WIFI="{addr}"')
    conn.commit()
    logger.debug(f"{PADDING}Total number of rows updated :", conn.total_changes)
    conn.close()


def fetch_addr():
    mac_wifi = ""
    mac_bt = ""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    logger.debug(f"{PADDING}Opened database successfully")

    cursor = c.execute("SELECT ADDRESS_WIFI, ADDRESS_BT from ADDRESS where SN is null")
    result = cursor.fetchone()
    try:
        mac_wifi, mac_bt = result
        logger.debug(f"{PADDING}Operation  successfully")
    except TypeError as e:
        logger.error(f"{PADDING}Error: no WiFi or BT address available")
    conn.close()
    return f"{mac_wifi},{mac_bt}"


def is_addr_used(addr):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    logger.debug(f"{PADDING}Opened database successfully")

    cursor = c.execute(f"SELECT SN from ADDRESS where ADDRESS_WIFI={addr}")

    logger.debug(f"{PADDING}Operation done successfully")
    conn.close()


def first_run():
    start_mac = 0xc4411e6a09ac
    total_mac = 1000

    create_table()
    mac_list = gen_mac_list(start_mac, total_mac)
    import_addr(mac_list)

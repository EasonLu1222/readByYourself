#!/usr/bin/python
import os
import sqlite3                                              #SQLite
from datetime import datetime
from sqlite3 import IntegrityError, OperationalError
from mylogger import logger


DB_DIR = 'C:\\db'
DB_PATH = os.path.join(DB_DIR, 'address.db')
PADDING = ' ' * 8


def create_table():
    conn = sqlite3.connect(DB_PATH)
    logger.info(f"{PADDING}Opened database successfully")

    c = conn.cursor()
    c.execute('''CREATE TABLE ADDRESS
        (ADDRESS_WIFI   CHAR(17)  NOT NULL UNIQUE,
        ADDRESS_BT     CHAR(17)  NOT NULL UNIQUE,
        SN             CHAR(28)  UNIQUE);''')
    conn.commit()
    logger.info(f"{PADDING}Table created successfully")

    c.execute('''CREATE INDEX `` ON `ADDRESS` (
        `ADDRESS_WIFI`	ASC,
        `ADDRESS_BT`	ASC,
        `SN`	ASC);''')
    conn.commit()
    logger.info(f"{PADDING}Index created successfully")
    conn.close()


def gen_mac_list(start_mac, total_mac):
    """
    Generate a continuous list of mac addresses given the starting mac address and the total number of them
    Args:
        start_mac: e.g. 0xc4411e6a09ac
        total_mac: e.g. 1000

    Returns: ["c4:41:1e:6a:09:ac", "c4:41:1e:6a:09:ad",...]

    """

    mac_list = []
    for i in range(total_mac):
        mac = format(start_mac + i, 'x')    # Convert hex number to hex string, e.g. 0xc4411e6a09ac to "c4411e6a09ac"
        ml = [mac[i:i + 2] for i in range(0, len(mac), 2)]
        mac_str = ":".join(ml)
        mac_list.append(mac_str)
    return mac_list


def import_addr(addr_list):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    logger.info(f"{PADDING}Opened database successfully")
    for i in range(0, len(addr_list)):
        if (i % 2) == 0:
            try:
                c.execute(f'INSERT INTO ADDRESS (ADDRESS_WIFI,ADDRESS_BT,SN) \
                    VALUES ("{addr_list[i]}", "{addr_list[i + 1]}", null )')
            except IntegrityError as e:
                logger.error(f"{PADDING}Error inserting ({addr_list[i]}, {addr_list[i + 1]}), {e}")
    conn.commit()
    logger.info(f"{PADDING}Records created successfully")
    conn.close()


def write_addr(addr, sn):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    logger.info(f"{PADDING}Opened database successfully")
    c.execute(f'UPDATE ADDRESS set SN = "{sn}" where ADDRESS_WIFI="{addr}"')
    conn.commit()
    logger.info(f"{PADDING}Total number of rows updated : {conn.total_changes}")
    conn.close()


def fetch_addr():
    mac_wifi = ""
    mac_bt = ""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        logger.info(f"{PADDING}Opened database successfully")

        cursor = c.execute("SELECT ADDRESS_WIFI, ADDRESS_BT from ADDRESS where SN is null")
        result = cursor.fetchone()
        if result:
            mac_wifi = result[0]
            logger.info(mac_wifi)
            now = datetime.now().timestamp()
            c.execute(f'UPDATE ADDRESS set SN = "tmp_{now}" where ADDRESS_WIFI="{mac_wifi}"')
            conn.commit()
    except OperationalError as ex:
        logger.error(f"{PADDING}Error: {ex}")

    try:
        mac_wifi, mac_bt = result
        logger.info(f"{PADDING}Operation  successfully")
    except (TypeError, UnboundLocalError) as ex:
        logger.error(f"{PADDING}Error: no WiFi or BT address available, {ex}")
    try:
        conn.close()
    except UnboundLocalError as ex:
        logger.error(f"{PADDING}Error: failed to close connection, {ex}")
    return f"{mac_wifi},{mac_bt}"


def is_addr_used(addr):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    logger.info(f"{PADDING}Opened database successfully")
    cursor = c.execute(f"SELECT SN from ADDRESS where ADDRESS_WIFI={addr}")
    logger.info(f"{PADDING}Operation done successfully")
    conn.close()


def is_pid_used(pid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    logger.info(f"{PADDING}Opened database successfully")
    cursor = c.execute(f"SELECT COUNT(*) from ADDRESS where SN='{pid}'")
    count = cursor.fetchone()
    logger.info(f"{PADDING}Operation done successfully")
    conn.close()

    return count[0] > 0


def clean_tmp_flag():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    cursor = c.execute("UPDATE ADDRESS set sn = null where sn like 'tmp%'")
    conn.commit()
    conn.close()


def first_run():
    """
    start_mac = 0xc4411e6a09ac
    total_mac = 1000
    """
    start_mac = 0xc4411e79bd16
    total_mac = 1000

    create_table()
    mac_list = gen_mac_list(start_mac, total_mac)
    import_addr(mac_list)

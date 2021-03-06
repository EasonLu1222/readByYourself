import os
import re
import requests
import shutil
import pandas as pd
from datetime import datetime
from mylogger import logger
from requests.exceptions import ConnectTimeout
from config import SFC_URL

PADDING = ' ' * 8

UPLOAD_ENDPOINT_DICT = {
    'RF': 'add_data_RF',
    'AU': 'add_data_audio',
    'WP': 'add_data_wpc',
    'LK': 'add_data_Leak',
    'PS': 'add_data_PowerSensor',
    'SA': 'add_data_sa',
    'MS': 'add_data_MicBlock',
    'AC': 'add_data_Acoustic',
    'DL': 'add_data_download',
    'BC': 'add_data_boot',
    'GCMS': 'add_data_download'
}

CHECK_ENDPOINT_DICT = {
    'RF': 'add_check_RF',
    'AU': 'add_check_audio',
    'WP': 'add_check_wpc',
    'LK': 'add_check_Leak',
    'PS': 'add_check_PowerSensor',
    'SA': 'add_check_Sa',
    'MS': 'add_check_Micblock',
    'AC': 'add_check_Acoustic',
    'DL': 'add_check_download',
    'BC': 'add_check_boot'
}


def gen_gcms_data(post_data):
    """
    gcms stands for "工廠模式".
    This function generate dummy data for SFC
    The test data goes into Final downloads db.
    The "Station" field will be "GCMS".
    This is for the packing station(ST19) to recognize that this DUT has factory firmware inside and cannot packing.
    """
    rtn = post_data.copy()
    dummy_data = {
        'station_id': 'GCMS',
        'write_country_code': 'Pass',
        'enter_dl_mode': 'Pass',
        'press_start': 'Pass',
        'download': 'Pass',
        'press_stop': 'Pass'
    }
    rtn.update(dummy_data)
    return rtn


def send_result_to_sfc(d, sfc_station_id, msn, res, dut_num, dut_i, t0, t1):
    df = d[(d.hidden == False) & (d.sfc_name != "")]
    cols1 = (df.sfc_name).values.tolist()
    dd = pd.DataFrame(df[[d.columns[-dut_num + dut_i]]].values.T, columns=cols1)

    cols2_value = {
        'msn': '',
        'station_id': f"{sfc_station_id}{dut_i+1:02}",
        'result': res,
        'fail_list': '',
        'start_time': t0,
        'end_time': t1,
    }

    dd = dd.assign(**cols2_value)[list(cols2_value) + cols1]
    post_data = {}
    try:
        post_data = dd.to_dict('records')[0]
        if not msn:
            regex = r"\d{3}-\d{3}-\d{3}-\d{4}-\d{4}-\d{6}"
            matches = re.search(regex, post_data['read_pid'])
            if matches:
                msn = matches.group()
        if 'read_pid' in post_data:
            post_data['read_pid'] = post_data['read_pid'][:4]
        if sfc_station_id == "GCMS":
            post_data = gen_gcms_data(post_data)
        post_data['msn'] = msn
    except IndexError as ex:
        logger.error(f"{PADDING}cannot generate POST data")

    # Discard any string after the pass or fail
    fields_to_keep_value = ['write_country_code']   # The "sfc_name" in this list will not omit the test value
    for k in post_data:
        if isinstance(post_data[k], str) and re.match(r'Pass|Fail', post_data[k], re.I):
            if k not in fields_to_keep_value:
                post_data[k] = post_data[k][:4]

    endpoint = UPLOAD_ENDPOINT_DICT[sfc_station_id]
    url = f"{SFC_URL}/{endpoint}.asp"

    try:
        logger.info(f"{PADDING}Requesting {url} with data:{post_data}")
        r = requests.post(url=url, data=post_data, timeout=1)
        if r.status_code != 200:
            logger.error(f"{PADDING}The status code is{r.status_code}")
        else:
            logger.info(f"{PADDING}SFC response: {r.text}")
    except ConnectTimeout:
        logger.error(f"{PADDING}SFC server connection timeout")
    except ConnectionError:
        logger.error(f"{PADDING}SFC server connection error")
    except Exception as ex:
        logger.error(f"{PADDING}SFC request error: {ex}")


def gen_ks_sfc_csv_filename(station):
    if not station:
        return 'null.csv'
    now = datetime.now()
    ymd = now.strftime('%Y%m%d')
    hms = int(now.strftime('%H%M%S'))
    csv_filename = f'{station.lower()}_log_{ymd}_{hms}.csv'

    return csv_filename


def gen_ks_sfc_csv(d, csv_filename, station, msn, dut_num, dut_i, result):
    # d = pd.read_pickle('../led_pickle.txt')
    df = d[(d.hidden == False) & (d.sfc_name != "")]
    cols1 = (df.sfc_name).values.tolist()
    dd = pd.DataFrame(df[[d.columns[-dut_num + dut_i]]].values.T, columns=cols1)

    if station == 'MB':
        part_num = '1003SA109-600-G'
    elif station == 'CT':
        part_num = '1003MT109-600-G'
    else:
        part_num = ''

    cols2_value = {
        'part_num': part_num,
        'station': station,
        'dut_num': dut_i + 1,
        'usid': msn
    }
    dd = dd.assign(**cols2_value)[list(cols2_value) + cols1]
    dd = dd.assign(**{'result': result})

    with open(f'./logs/{csv_filename}', 'a') as f:
        dd.to_csv(f, index=False, mode='a', header=f.tell() == 0, sep=',', line_terminator='\n')


def move_ks_sfc_csv(station, csv_filename):
    if not station:
        return
    os.makedirs(f'./logs/{station.lower()}_log', exist_ok=True)
    try:
        shutil.move(f'./logs/{csv_filename}', f'./logs/{station.lower()}_log/{csv_filename}')
    except FileNotFoundError as e:
        logger.debug(f"{e}")

# gen_ks_sfc_csv(d=None, station='MB', msn='111-111-111-1111-1111-111111', dut_num=2, dut_i=1, result='Pass')
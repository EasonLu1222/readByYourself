import os
import re
import requests
import glob
import pandas as pd
from datetime import datetime
from mylogger import logger
from requests.exceptions import ConnectTimeout

PADDING = ' ' * 8

# SFC_HOST = 'http://10.228.14.99:7109'   # debug
SFC_HOST = 'http://10.228.16.99:7109'  # production

endpoint_dict = {
    'SA': 'add_data_sa',
    'WP': 'add_data_wpc',
    'AU': 'add_data_audio',
    'PS': 'add_data_PowerSensor',
    'RF': 'add_data_RF',
    'AC': 'add_data_Acoustic',
    'MS': 'add_data_MicBlock'
}


def send_result_to_sfc(d, sfc_station_id, msn, res, dut_num, dut_i, t0, t1):
# def send_result_to_sfc(d=None, sfc_station_id='SA', msn="111-111-111-1111-1111-111111", res='Pass', dut_num=1, dut_i=0, t0='2019/11/27 08:00:00', t1='2019/11/27 08:00:00'):
    # d.to_pickle('../sa_test_result.pkl')
    # d = pd.read_pickle('../led_pickle.txt')

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
        post_data['msn'] = msn
    except IndexError as ex:
        logger.error(f"{PADDING}cannot generate POST data")

    # Discard any string after the pass or fail
    for k in post_data:
        if isinstance(post_data[k], str) and re.match(r'Pass|Fail', post_data[k], re.I):
            post_data[k] = post_data[k][:4]

    endpoint = endpoint_dict[post_data['station_id'][:2]]
    url = f"{SFC_HOST}/{endpoint}.asp"

    try:
        logger.info(f"{PADDING}Requesting {url} with data:{post_data}")
        r = requests.post(url=url, data=post_data)
        if r.status_code != 200:
            logger.error(f"{PADDING}The status code is{r.status_code}")
        else:
            logger.info(f"{PADDING}SFC response: {r.text}")
    except ConnectTimeout:
        logger.error(f"{PADDING}Connection timeout")
    except ConnectionError:
        logger.error(f"{PADDING}Connection error")
    except Exception as ex:
        logger.error(f"{PADDING}SFC request error: {ex}")


def gen_ks_sfc_csv_filename():
    now = datetime.now()
    ymd = now.strftime('%Y%m%d')
    hms = int(now.strftime('%H%M%S'))
    csv_filename = f'mb_log_{ymd}_{hms}.csv'

    return csv_filename


def gen_ks_sfc_csv(d, csv_filename, station, msn, part_num, dut_num, dut_i, result):
    # d = pd.read_pickle('../led_pickle.txt')
    df = d[(d.hidden == False) & (d.sfc_name != "")]
    cols1 = (df.sfc_name).values.tolist()
    dd = pd.DataFrame(df[[d.columns[-dut_num + dut_i]]].values.T, columns=cols1)

    cols2_value = {
        'part_num': part_num,
        'station': station,
        'dut_num': dut_i + 1,
        'usid': msn

    }
    dd = dd.assign(**cols2_value)[list(cols2_value) + cols1]
    dd = dd.assign(**{'result': result})

    os.makedirs('./logs/mb_log', exist_ok=True)

    with open(f'./logs/{csv_filename}', 'a') as f:
        dd.to_csv(f, index=False, mode='a', header=f.tell() == 0, sep=',', line_terminator='\n')


# gen_ks_sfc_csv(d=None, station='MB', msn='111-111-111-1111-1111-111111', dut_num=2, dut_i=1, result='Pass')
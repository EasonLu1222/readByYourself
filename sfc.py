import re
import requests
import pandas as pd
from mylogger import logger

PADDING = ' ' * 8

SFC_HOST = 'http://10.228.14.99:7109'   # debug
# SFC_HOST = 'http://10.228.16.99'  # production

endpoint_dict = {
    'SA01': 'add_data_sa',
    'WP01': 'add_data_wpc',
    'AU01': 'add_data_audio',
    'PS01': 'add_data_PowerSensor',
    'RF01': 'add_data_RF'
}


def send_result_to_sfc(d=None, sfc_station_id='SA01', msn=None, res='Pass', dut_num=1, dut_i=0, t0='2019/11/25 08:00:00', t1='2019/11/25 08:00:00'):
    # d.to_pickle('../sa_test_result.pkl')
    d = pd.read_pickle('../sa_test_result.pkl')

    df = d[(d.hidden == False) & (d.sfc_name != "")]
    cols1 = (df.sfc_name).values.tolist()
    dd = pd.DataFrame(df[[d.columns[-dut_num + dut_i]]].values.T, columns=cols1)

    cols2_value = {
        'station_id': sfc_station_id,
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
            matches = re.search(regex, post_data['msn'])
            if matches:
                msn = matches.group()
        post_data['msn'] = msn
    except IndexError as ex:
        logger.error(f"{PADDING}cannot generate POST data")
    endpoint = endpoint_dict[post_data['station_id']]
    url = f"{SFC_HOST}/{endpoint}"

    r = requests.post(url=endpoint, data=post_data)
    logger.info(f"{PADDING}SFC respond: {r.text}")

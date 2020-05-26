import inspect
import os
import argparse
import re
import sys
import time
import json
import requests
from serial import Serial, SerialException
from datetime import datetime
from subprocess import Popen, PIPE
from pydub import AudioSegment
from requests.exceptions import ConnectTimeout
from sfc import UPLOAD_ENDPOINT_DICT, CHECK_ENDPOINT_DICT
from mylogger import logger
from config import station_json, SFC_URL

PADDING = ' ' * 8


def check_sfc(portname, dut_idx, dynamic_info):
    """
    Check if the DUT passed in previous stations or failed over 3 times
    Using the APIs provided by ACD IT
    Args:
        dynamic_info: Contains usid

    Returns: Pass/Fail

    """
    rtn = ''
    station_id, pid = dynamic_info.split(",")
    station_id = f'{station_id}{dut_idx+1:02}'

    endpoint = CHECK_ENDPOINT_DICT[station_id[:2]]
    url = f"{SFC_URL}/{endpoint}.asp"

    try:
        data = {'msn': pid, 'station_id': station_id}
        logger.info(f"{PADDING}Requesting {url} with data:{data}")
        r = requests.get(url, data=data, timeout=0.8)
        if r.status_code == 200:
            res = r.text
            if res.startswith('0') or ('Pass Exist' in res):
                rtn = f'Pass({res})'
            else:
                rtn = f'Fail({res})'
        else:
            rtn = f'Fail(network error, status:{r.status_code})'
    except ConnectTimeout:
        rtn = f'Fail(connection timeout)'
    except ConnectionError:
        rtn = f'Fail(connection error)'
    except Exception as ex:
        rtn = f'Fail(unknown network error, status:{r.status_code})'

    return rtn


if __name__ == "__main__":
    thismodule = sys.modules[__name__]

    logger.info(f'{PADDING}task_runeach start...')
    parser = argparse.ArgumentParser()
    parser.add_argument('-p',
                        '--portname',
                        help='serial com port name',
                        type=str)
    parser.add_argument('-i', '--dut_idx', help='dut #number', type=int)
    parser.add_argument('-s', '--dynamic_info', help='serial id', type=str)
    parser.add_argument('funcname', help='function name', type=str)
    args = parser.parse_args()
    portname, dut_idx, dynamic_info = [
        getattr(args, e) for e in ('portname', 'dut_idx', 'dynamic_info')
    ]
    funcname = args.funcname

    logger.info(f'{PADDING}portname: {portname}')
    logger.info(f'{PADDING}dut_idx: {dut_idx}')
    logger.info(f'{PADDING}dynamic_info: {dynamic_info}')
    logger.info(f'{PADDING}args: {args}')
    logger.info(f'{PADDING}funcname: {funcname}')

    func = getattr(thismodule, funcname)
    func_args = [
        getattr(thismodule, arg) for arg in inspect.getfullargspec(func).args
    ]
    logger.info(f'{PADDING}func_args: {func_args}')

    result = func(*func_args)
    if result:
        sys.stdout.write(result)

    logger.info(f'{PADDING}task_runeach end...')
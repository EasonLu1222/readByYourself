import json
from utils import resource_path


DEVICES = json.load(open(resource_path('device.json'), 'r'))
SERIAL_DEVICES = {k:v for k,v in DEVICES.items() if v[1]=='serial'}
VISA_DEVICES = {k:v for k,v in DEVICES.items() if v[1]=='visa'}
SERIAL_DEVICE_NAME = [e[0] for e in SERIAL_DEVICES.values()]
VISA_DEVICE_NAME = [e[0] for e in VISA_DEVICES.values()]


station_json = {
    'SIMULATION': 'v13_simu',

    # --- SMT ---
    'MainBoard': 'v13_mb',                  # pyinstaller exe  tested on clean windows
    'LED': 'v13_led',                       # pyinstaller exe  tested on clean windows
    'CapTouch': 'v13_cap_touch',            # pyinstaller exe  tested on clean windows
    'CapTouchMic': 'v13_cap_touch_mic',

    # --- FATP ---
    'SA': 'v13_sa',                         # pyinstaller exe  tested on clean windows
    'RF': 'v13_rf',
    'WPC': 'v13_wpc',                       # pyinstaller exe  tested on clean windows
    'PowerSensor': 'v13_power_sensor',      # pyinstaller exe  tested on clean windows
    'Audio': 'v13_audio',
    'Download': 'v13_download',
}

LANG_LIST = [
    'en_US',
    'zh_TW',
    'zh_CN',
    'vi'
]

CAP_TOUCH_FW = 'msp430Upgrade_V06'

STATION = json.loads(open('jsonfile/station.json', 'r').\
                     read())['STATION']

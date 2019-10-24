import json
from utils import resource_path


DEVICES = json.load(open(resource_path('device.json'), 'r'))
SERIAL_DEVICES = {k:v for k,v in DEVICES.items() if v[1]=='serial'}
VISA_DEVICES = {k:v for k,v in DEVICES.items() if v[1]=='visa'}
SERIAL_DEVICE_NAME = [e[0] for e in SERIAL_DEVICES.values()]
VISA_DEVICE_NAME = [e[0] for e in VISA_DEVICES.values()]


station_json = {
    'SIMULATION': 'v12_simu',

    # --- SMT ---
    'MainBoard': 'v12_mb',                  # pyinstaller exe  tested on clean windows
    'LED': 'v12_led',                       # pyinstaller exe  tested on clean windows
    'CapTouch': 'v12_cap_touch',            # pyinstaller exe  tested on clean windows

    # --- FATP ---
    'SA': 'v12_sa',                         # pyinstaller exe  tested on clean windows
    'RF': 'v12_rf',
    'WPC': 'v12_wpc',                       # pyinstaller exe  tested on clean windows
    'PowerSensor': 'v12_power_sensor',      # pyinstaller exe  tested on clean windows
    'Audio': 'v12_audio',
    'Download': 'v12_download',
}

LANG_LIST = [
    'en_US',
    'zh_TW',
    'zh_CN',
    'vi'
]

CAP_TOUCH_FW = 'msp430Upgrade_V06'

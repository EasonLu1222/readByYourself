import json
import getpass
from utils import resource_path


# =============== Instruments ===============
DEVICES = json.load(open(resource_path('device.json'), 'r'))
SERIAL_DEVICES = {k:v for k,v in DEVICES.items() if v[1]=='serial'}
VISA_DEVICES = {k:v for k,v in DEVICES.items() if v[1]=='visa'}
SERIAL_DEVICE_NAME = [e[0] for e in SERIAL_DEVICES.values()]
VISA_DEVICE_NAME = [e[0] for e in VISA_DEVICES.values()]


# =============== Station Related ===============
station_json = {
    'SIMULATION': 'v14_simu',

    # --- SMT ---
    'MainBoard': 'v14_mb',                  # pyinstaller exe  tested on clean windows
    'LED': 'v14_led',                       # pyinstaller exe  tested on clean windows
    'CapTouch': 'v14_cap_touch',            # pyinstaller exe  tested on clean windows
    'CapTouchMic': 'v14_cap_touch_mic',

    # --- FATP ---
    'RF': 'v14_rf',
    'Audio': 'v14_audio',
    'AudioPath': 'v14_audio_path',
    'AudioListen': 'v14_audio_listener',
    'Leak': 'v14_leak',
    'WPC': 'v14_wpc',                       # pyinstaller exe  tested on clean windows
    'PowerSensor': 'v14_power_sensor',      # pyinstaller exe  tested on clean windows
    'SA': 'v14_sa',                         # pyinstaller exe  tested on clean windows
    'Acoustic': 'v14_acoustic',
    'AcousticListen': 'v14_acoustic_listener_klippel_v1_5',
    'BTMacFix': 'v14_btmacfix',
    'Download': 'v14_download',
}
STATION = json.loads(open('jsonfile/station.json', 'r').\
                     read())['STATION']

# =============== Language ===============
LANG_LIST = [
    'en_US',
    'zh_TW',
    'zh_CN',
    'vi'
]


# =============== Acoustic Station ===============
#  KLIPPEL_PROJECT = 'SAP109 - v1.3 - DVT2 - 191209'
#  KLIPPEL_PROJECT = 'SAP109 - v1.3 - DVT2 - 191209'
KLIPPEL_PROJECT = 'SAP109-v1.5-DVT2-191214'


# =============== Acoustic Station ===============
CAP_TOUCH_FW = 'msp430Upgrade_V06'


# =============== Testing Progream Upgrade ===============
# == ftp ==
OFFICE_IP = '10.228.14.92'
FACTORY_IP = '10.228.16.92'

IP_USED = FACTORY_IP
IP_FTPDIR = {
    FACTORY_IP: '/Belkin109/Latest_App',
    OFFICE_IP: '/Belkin109/Latest_App_Test', # for test
}
FTP_DIR = IP_FTPDIR[IP_USED]

# == local ==
USER_PATH = f'C:/Users/{getpass.getuser()}'
LOCAL_APP_PATH = f'{USER_PATH}/SAP109_STATION'
TRIGGER_PREFIX = 'sap109-testing-upgrade-starting'

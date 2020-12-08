import json
import getpass
from utils import resource_path


PRODUCT = '109'

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
    'MainBoard': 'v14_mb',
    'Led': 'v14_led',
    'LedMfi': 'v14_led_mfi',
    'CapTouch': 'v14_cap_touch',
    'CapTouchMic': 'v14_cap_touch_mic',

    # --- IQC ---
    'MainBoardIqc': 'v14_mb_iqc',

    # --- FATP ---
    'RF': 'v14_rf',
    'AudioListen': 'v14_audio_listener',
    'Leak': 'v14_leak',
    'WPC': 'v14_wpc',
    'PowerSensor': 'v14_power_sensor',
    'SA': 'v14_sa',
    'MicBlock': 'v14_mic_block',
    'AcousticListen': 'v14_acoustic_listener_klippel_v2',
    'BootCheck': 'v14_boot_check',

    'Download': 'v14_download',
    'UsidFix': 'v14_usid_fix',

    # --- FATP repair ---
    'Gcms': 'v14_factory_img_download',
}
STATION = json.loads(open('jsonfile/station.json', 'r').\
                     read())['STATION']

# =============== Country Code ===============
COUNTRY_CODE = [
    'US988',    # US
    'CA2',      # Canada
    'DE30',     # EU
    'AU6',      # ANZ
    'EUP2',     # Tunisia
    'JP967',    # Japan
    'KR70',     # South Korea
]

# =============== Language ===============
LANG_LIST = [
    'en_US',
    'zh_TW',
    'zh_CN',
    'vi'
]


# =============== Acoustic Station ===============
KLIPPEL_PROJECT = 'SAP109-209 - v2 - MP - 201106'


# =============== CapTouch Station ===============
CAP_TOUCH_FW = 'msp430Upgrade_V06'


# =============== SFC System ===============
OFFICE_SFC_IP = 'http://10.228.14.99'
FACTORY_SFC_IP = 'http://10.228.16.99'

SFC_IP = FACTORY_SFC_IP

SFC_URL = f'{SFC_IP}:7{PRODUCT}'
TOTAL_MAC_URL = f'{SFC_IP}:9009/get_MacTotal_{PRODUCT}.asp?product=SAP{PRODUCT}'
GET_MAC_URL = f'{SFC_IP}:9009/get_mac_{PRODUCT}.asp?mac_type=wifi+bt&product=SAP{PRODUCT}'

# =============== Testing Program Upgrade ===============
# == ftp ==
FTP_USER = 'SAP109'
FTP_PWD = 'sapsfc'
OFFICE_FTP_IP = '10.228.14.92'
FACTORY_FTP_IP = '10.228.16.92'

FTP_IP_USED = FACTORY_FTP_IP

LATEST_APP_FOLDER = f'/Belkin{PRODUCT}/Latest_App'
LATEST_APP_TEST_FOLDER = f'/Belkin{PRODUCT}/Latest_App_Test'

IP_FTPDIR = {
    FACTORY_FTP_IP: LATEST_APP_FOLDER,
    OFFICE_FTP_IP: LATEST_APP_TEST_FOLDER, # for test
}
FTP_DIR = IP_FTPDIR[FTP_IP_USED]

# == local ==
USER_PATH = f'C:/Users/{getpass.getuser()}'
LOCAL_APP_PATH = f'{USER_PATH}/SAP{PRODUCT}_STATION'
TRIGGER_PREFIX = f'sap{PRODUCT}-testing-upgrade-starting'

import json
from utils import resource_path


DEVICES = json.load(open(resource_path('device.json'), 'r'))
SERIAL_DEVICES = {k:v for k,v in DEVICES.items() if v[1]=='serial'}
VISA_DEVICES = {k:v for k,v in DEVICES.items() if v[1]=='visa'}
SERIAL_DEVICE_NAME = [e[0] for e in SERIAL_DEVICES.values()]
VISA_DEVICE_NAME = [e[0] for e in VISA_DEVICES.values()]


station_json = {
    'SIMULATION': 'v11_simu',
    'Download': 'v11_download',
    'MainBoard': 'v11_mb',
    'LED': 'v11_led',
    'CapTouch': 'v11_cap_touch',
    'RF': 'v11_rf_wifi',
    'WPC': 'v11_wpc',
    'PowerSensor': 'v11_power_sensor',
    'Audio': 'v11_audio',
}

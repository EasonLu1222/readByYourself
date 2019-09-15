import json
from utils import resource_path


DEVICES = json.load(open(resource_path('device.json'), 'r'))
SERIAL_DEVICES = {k:v for k,v in DEVICES.items() if v[1]=='serial'}
VISA_DEVICES = {k:v for k,v in DEVICES.items() if v[1]=='visa'}
SERIAL_DEVICE_NAME = [e[0] for e in SERIAL_DEVICES.values()]
VISA_DEVICE_NAME = [e[0] for e in VISA_DEVICES.values()]


station_json = {
    'SIMULATION': 'v9_simu',
    'MainBoard': 'v9_mb_temp',
    'LED': 'v9_led',
    'CapTouch': 'v9_cap_touch',
    'RF': 'v9_rf_wifi',
    'WPC': 'v9_wpc',
    'PowerSensor': 'v9_power_sensor',
    'Audio': 'v9_audio',
}

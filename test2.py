
# -*- coding: gbk -*-
import json

from config import (DEVICES, SERIAL_DEVICES, VISA_DEVICES, SERIAL_DEVICE_NAME,
                    VISA_DEVICE_NAME, STATION, KLIPPEL_PROJECT, COUNTRY_CODE)


print(SERIAL_DEVICE_NAME)

base = json.loads(open("self.jsonfile", 'r', encoding='utf8').read())

def serial_devices(self):
    devices = self.base['devices']  # 找尋json裡的device的參數
    print(devices)
    serial_devices = {
        k: v
        for k, v in devices.items() if v['name'] in SERIAL_DEVICE_NAME
    }
    return serial_devices

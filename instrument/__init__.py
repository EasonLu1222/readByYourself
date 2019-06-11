import time
from serials import (get_serial, get_devices)
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][pid=%(process)d][%(message)s]')


POWERON = '''
    OUTPut:PROTection:CLEar
    OUTPut 0
    OUTPut:DELay:ON 0.00
    OUTPut:DELay:OFF 0.00
    OUTPut:TRIGgered 0
    VOLT 19
    CURR 3.5
    OUTPut 1
'''


POWEROFF = '''
    OUTPut:PROTection:CLEar
    OUTPut 0
'''


MEASURE_VOLT_BASE = '''
    SYST:OUTP:SEP 1
    ROUT:SCAN:FIN OFF
    ROUT:ADV ON
    SENS:DET:RATE F
    ROUT:MULT:OPEN 101,116
    ROUT:CLOSE 101
    ROUT:CLOSE 102
    ROUT:CLOSE 103
    ROUT:CLOSE 104
    ROUT:CLOSE 105
    ROUT:CLOSE 106
    ROUT:CLOSE 107
    ROUT:CLOSE 108
    ROUT:CLOSE 109
    ROUT:CLOSE 110
    ROUT:CLOSE 111
    ROUT:CLOSE 112
    ROUT:CLOSE 113
    ROUT:CLOSE 114
    ROUT:CLOSE 115
    ROUT:CLOSE 116
    ROUT:COUN 1
    ROUT:DEL 0
    TRIG:DEL 0
    ROUT:CHAN ___,1,100,0
    ROUT:FUNC OFF
    ROUT:FUNC SCAN
    FETCH?
'''


def cmd(command_constant):
    return [e.strip() for e in command_constant.strip().split('\n')]


def cmd_volt(channel):
    cmds = cmd(MEASURE_VOLT_BASE)
    cmds = [e for e in cmds if not e.startswith(f'ROUT:CLOSE {channel}')]
    for i, e in enumerate(cmds):
        if '___' in e: cmds[i] = f'ROUT:CHAN {channel},1,100,0'
    return cmds


def update_serial(instruments):
    devices = get_devices()
    for instrument in instruments:
        device = [e for e in devices if instrument.NAME in e['name']]
        instrument.com = device[0]['comport'] if device else None


class SerialInstrument():
    delay_sec = 0.01
    def __init__(self, port=None, baud=115200, timeout=2):
        if port:
            self.com = port
            self.ser = get_serial(port, baudrate=baud, timeout=timeout)
            self.is_open = True
        else:
            self.is_open = False
            self.com = None

    def open_com(self, baud=115200, timeout=2):
        if self.com:
            self.ser = get_serial(self.com, baudrate=baud, timeout=timeout)
            self.is_open = True
            return True
        else:
            return False

    def run_cmd(self, items, fetch=False):
        for item in items:
            cmd = f'{item}\n'.encode()
            self.ser.write(cmd)
            if self.delay_sec: time.sleep(self.delay_sec)
        if fetch: return self.ser.readline().decode('utf8')


class PowerSupply(SerialInstrument):
    NAME = 'gw_powersupply'
    def on(self):
        self.run_cmd(cmd(POWERON))

    def off(self):
        self.run_cmd(cmd(POWEROFF))


class DMM(SerialInstrument):
    NAME = 'gw_dmm'
    delay_sec = 0.0
    def __init__(self, *args, **kwargs):
        super(DMM, self).__init__(*args, **kwargs)

    def measure_volt(self, channel):
        while True:
            result = self.run_cmd(cmd_volt(channel), True)
            if result: 
                return float(result)


dmm = DMM()
power1 = PowerSupply()

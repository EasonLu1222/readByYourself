import time
from serials import (get_serial, get_devices)
from collections import defaultdict
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
    ROUT:FUNC SCAN
    FETCH?
'''

MEASURE_VOLT_ALL = '''
    SYST:OUTP:SEP 1
    ROUT:SCAN:FIN OFF
    ROUT:ADV ON
    SENS:DET:RATE F
    ROUT:MULT:OPEN 101,116
    ROUT:COUN 16
    ROUT:DEL 0
    TRIG:DEL 0
    ROUT:CHAN 101,1,100,0
    ROUT:CHAN 102,1,10,0
    ROUT:CHAN 103,1,10,0
    ROUT:CHAN 104,1,10,0
    ROUT:CHAN 105,1,10,0
    ROUT:CHAN 106,1,10,0
    ROUT:CHAN 107,1,10,0
    ROUT:CHAN 108,1,10,0
    ROUT:CHAN 109,1,100,0
    ROUT:CHAN 110,1,100,0
    ROUT:CHAN 111,1,100,0
    ROUT:CHAN 112,1,100,0
    ROUT:CHAN 113,1,100,0
    ROUT:CHAN 114,1,100,0
    ROUT:CHAN 115,1,100,0
    ROUT:CHAN 116,1,100,0
    ROUT:FUNC SCAN
    FETCH?
'''



MEASURE_VOLT_B = '''
    SYST:OUTP:SEP 1
    ROUT:SCAN:FIN OFF
    ROUT:ADV ON
    SENS:DET:RATE F
    ROUT:MULT:OPEN 101,116
    ROUT:COUN 1
    ROUT:DEL 0
    TRIG:DEL 0
    ROUT:FUNC SCAN
    FETCH?
'''


def cmd(command_constant):
    return [e.strip() for e in command_constant.strip().split('\n')]


def cmd_volts(channels):
    cmds = cmd(MEASURE_VOLT_B)
    idx1 = cmds.index('ROUT:MULT:OPEN 101,116')
    into1 = [f'ROUT:CLOS {e}' for e in range(101, 117) if e not in channels]
    cmds = cmds[:idx1+1] + into1 + cmds[idx1+1:]
    idx2 = cmds.index('TRIG:DEL 0')
    into2 = [f'ROUT:CHAN {e},1,100,0' for e in channels]
    cmds = cmds[:idx2+1] + into2 + cmds[idx2+1:]
    cmds[cmds.index('ROUT:COUN 1')] = f'ROUT:COUN {len(channels)}'
    for e in cmds:
        logging.info(e)
    return cmds


def cmd_volt(channel):
    cmds = cmd(MEASURE_VOLT_BASE)
    cmds = [e for e in cmds if not e.startswith(f'ROUT:CLOSE {channel}')]
    for i, e in enumerate(cmds):
        if '___' in e: cmds[i] = f'ROUT:CHAN {channel},1,100,0'
    #  idx = cmds.index('TRIG:DEL 0')
    #  cmds.insert(idx+1, f'ROUT:CHAN {channel},1,100,0')
    return cmds


#  def update_serial(instruments):
    #  devices = get_devices()
    #  for instrument in instruments:
        #  device = [e for e in devices if instrument.NAME in e['name']]
        #  instrument.com = device[0]['comport'] if device else None


def update_serial(instruments):
    devices = get_devices()
    instrument_set = set(e.NAME for e in instruments)
    for instrument_name in instrument_set:
        device = [e for e in devices if e['name']==instrument_name]
        for idx, d in enumerate(sorted(device, key=lambda x: int(x['comport'][3:])), 1):
            print(f'{instrument_name}_{idx}', d)
            each = next(filter(lambda e: e.NAME==instrument_name and e.index==idx, instruments))
            each.com = d['comport']


class SerialInstrument():
    def __init__(self, index=1, port=None, baud=115200, timeout=2, delay_sec=0.002):
        self.index = index
        self.delay_sec = delay_sec
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
        if fetch:
            result = self.ser.readline().decode('utf8')
            return result


class PowerSupply(SerialInstrument):
    NAME = 'gw_powersupply'
    def on(self):
        print('power on!')
        self.run_cmd(cmd(POWERON))

    def off(self):
        print('power off!')
        self.run_cmd(cmd(POWEROFF))


class DMM(SerialInstrument):
    NAME = 'gw_dmm'
    def measure_volt(self, channel):
        while True:
            result = self.run_cmd(cmd_volt(channel), True)
            if result:
                return float(result)

    def measure_volts(self, channels):
        result = self.run_cmd(cmd_volts(channels), True)
        logging.info(f'result: {result}')
        values = [float(e) for e in result.split(',')]
        return values

    def measure_volts_all(self):
        result = self.run_cmd(cmd(MEASURE_VOLT_ALL), True)
        values = [float(e) for e in result.split(',')]
        return values



dmm1 = DMM()
power1 = PowerSupply(1)
power2 = PowerSupply(2)
#  power1 = PowerSupply('COM8')
#  power2 = PowerSupply('COM11')

#  list(zip(range(1,17), dmm.measure_volts_all()))

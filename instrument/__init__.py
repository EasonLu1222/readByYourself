import time
from serials import (get_serial, get_devices)
from collections import defaultdict

from mylogger import logger


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
    ROUT:CHAN 110,1,10,0
    ROUT:CHAN 111,1,10,0
    ROUT:CHAN 112,1,10,0
    ROUT:CHAN 113,1,10,0
    ROUT:CHAN 114,1,10,0
    ROUT:CHAN 115,1,10,0
    ROUT:CHAN 116,1,10,0
    ROUT:FUNC SCAN
    FETCH?
'''

#  MEASURE_FREQ = '''
    #  SYST:OUTP:SEP 1
    #  ROUT:SCAN:FIN OFF
    #  ROUT:ADV ON
    #  SENS:DET:RATE F
    #  SENS:FREQ:APER 0.01
    #  ROUT:MULT:CLOS 101,116
    #  ROUT:MULT:OPEN 113,116
    #  ROUT:COUN 4
    #  ROUT:DEL 0
    #  TRIG:DEL 0
    #  ROUT:CHAN 113,8,10,0
    #  ROUT:CHAN 114,8,10,0
    #  ROUT:CHAN 115,8,10,0
    #  ROUT:CHAN 116,8,10,0
    #  ROUT:FUNC SCAN
    #  FETCH?
#  '''

MEASURE_FREQ = '''
    SYST:OUTP:SEP 1
    ROUT:SCAN:FIN OFF
    ROUT:ADV ON
    SENS:DET:RATE F
    SENS:FREQ:APER 0.01
    ROUT:MULT:CLOS 101,116
    ROUT:MULT:OPEN 107,108
    ROUT:MULT:OPEN 115,116
    ROUT:COUN 4
    ROUT:DEL 0
    TRIG:DEL 0
    ROUT:CHAN 107,8,10,0
    ROUT:CHAN 108,8,10,0
    ROUT:CHAN 115,8,10,0
    ROUT:CHAN 116,8,10,0
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
    cmds = cmds[:idx1 + 1] + into1 + cmds[idx1 + 1:]
    idx2 = cmds.index('TRIG:DEL 0')
    into2 = [f'ROUT:CHAN {e},1,100,0' for e in channels]
    cmds = cmds[:idx2 + 1] + into2 + cmds[idx2 + 1:]
    cmds[cmds.index('ROUT:COUN 1')] = f'ROUT:COUN {len(channels)}'
    for e in cmds:
        logger.info(e)
    return cmds


def cmd_volt(channel):
    cmds = cmd(MEASURE_VOLT_BASE)
    cmds = [e for e in cmds if not e.startswith(f'ROUT:CLOSE {channel}')]
    for i, e in enumerate(cmds):
        if '___' in e: cmds[i] = f'ROUT:CHAN {channel},1,100,0'
    return cmds


def update_serial(instruments):
    logger.info('update_serial start')
    devices = get_devices()
    instrument_set = set(e.NAME for e in instruments)
    for instrument_name in instrument_set:
        device = [e for e in devices if e['name'] == instrument_name]
        for idx, d in enumerate(
                sorted(device, key=lambda x: int(x['comport'][3:])), 1):
            logger.info(
                f'{instrument_name}_{idx} ---> {d["comport"]} ---> {d["hwid"]}')
            each = next(
                filter(lambda e: e.NAME == instrument_name and e.index == idx,
                       instruments))

            logger.info(f'each: {each}')
            logger.info(f'comport: {d["comport"]}')
            each.com = d['comport']


class SerialInstrument():

    def __init__(self,
                 index=1,
                 port=None,
                 baud=115200,
                 timeout=2,
                 delay_sec=0.002):
        self.index = index
        self.delay_sec = delay_sec
        if port:
            self.com = port
            self.ser = get_serial(port, baudrate=baud, timeout=timeout)
        else:
            self.com = None
            self.ser = None

    @property
    def is_open(self):
        return self.ser.isOpen() if self.ser else False

    def open_com(self, baud=115200, timeout=2):
        logger.info('in SerialInstrument: open_com 1')
        if self.com:
            logger.info('in SerialInstrument: open_com 2')
            self.ser = get_serial(self.com, baudrate=baud, timeout=timeout)
            logger.info('in SerialInstrument: open_com 3')
            return True
        else:
            return False

    def close_com(self):
        self.ser.close()
        self.ser = None

    def run_cmd(self, items, fetch=False):
        try:
            for item in items:
                cmd = f'{item}\n'.encode()
                self.ser.write(cmd)
                if self.delay_sec: time.sleep(self.delay_sec)
            if fetch:
                result = self.ser.readline().decode('utf8')
                return result
        except Exception as e:
            logger.debug("run_cmd failed!")


class PowerSupply(SerialInstrument):
    NAME = 'gw_powersupply'
    StartFetchTime = 2
    MeasureTime = 10

    def on(self):
        logger.info(f'power_{self.index}({self}) on!')
        self.run_cmd(cmd(POWERON))

    def off(self):
        logger.info(f'power_{self.index}({self}) off!')
        self.run_cmd(cmd(POWEROFF))

    def measure_current(self):
        t0 = time.perf_counter()
        elapsed = lambda: time.perf_counter() - t0
        currents = []
        while (True):
            if elapsed() >= self.StartFetchTime:
                line = self.run_cmd(['MEASure:CURRent:DC?'], True)
                #  print(line)
                if not line: continue
                result = float(line)
                currents.append(result)
            if elapsed() > self.MeasureTime:
                currents.sort(reverse=True)
                self.max_current = currents[0]
                break
        return currents


class DMM(SerialInstrument):
    NAME = 'gw_dmm'

    def measure_volt(self, channel):
        while True:
            result = self.run_cmd(cmd_volt(channel), True)
            if result:
                return float(result)

    def measure_freq(self, channel):
        result = self.run_cmd(cmd_volt(channel), True)
        if result:
            return float(result)

    def measure_volts(self, channels):
        result = self.run_cmd(cmd_volts(channels), True)
        logger.info(f'result: {result}')
        values = [float(e) for e in result.split(',')]
        return values

    #  def measure_freqs(self, channels):
        #  result = self.run_cmd(cmd_volts(channels), True)
        #  logger.info(f'result: {result}')
        #  values = [float(e) for e in result.split(',')]
        #  return values

    def measure_volts_all(self):
        result = self.run_cmd(cmd(MEASURE_VOLT_ALL), True)
        values = [float(e) for e in result.split(',')]
        return values

    def measure_freqs_all(self):
        result = self.run_cmd(cmd(MEASURE_FREQ), True)
        logger.info(f'measure_freqs_all result: {result}')
        logger.info(f'type: {type(result)}')
        values = [float(e) for e in result.split(',')]
        return values


def open_all(update_ser=False, if_open_com=False, if_poweron=False):
    dmm1 = DMM(1)
    power1 = PowerSupply(1)
    power2 = PowerSupply(2)
    instruments = [dmm1, power1, power2]
    if update_ser:
        update_serial(instruments)
    if if_open_com:
        for e in instruments:
            e.open_com() if e is not dmm1 else e.open_com(timeout=5)
    if if_poweron:
        power1.on()
        power2.on()
    return instruments


#  dmm1, power1, power2 = open_all()
#  dmm1, power1, power2 = open_all(True, True)

#  list(zip(range(1,17), dmm.measure_volts_all()))

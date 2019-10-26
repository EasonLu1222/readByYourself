import time
import json
import visa
from collections import defaultdict

from mylogger import logger
from serials import (get_serial, get_devices)
from config import (DEVICES, SERIAL_DEVICES, VISA_DEVICES,
                    SERIAL_DEVICE_NAME, VISA_DEVICE_NAME)


type_ = lambda ex: f'<{type(ex).__name__}>'


def get_visa_devices():
    #  import visa
    dll_32 = 'C:/Windows/System32/visa32.dll'
    rm = visa.ResourceManager(dll_32)
    resource_names = rm.list_resources()
    resource_names = [e for e in resource_names if e.startswith('USB')]
    devices = []
    for resource_name in resource_names:
        usb_idx, name, sn = get_visa_device(resource_name)
        devices.append({
            'comport': usb_idx,
            'name': name,
            'sn': sn
        })
    return devices


def get_visa_device(resource_name):
    usb_idx, vid, pid, sn, _ = resource_name.split('::')
    vid_pid = f'{vid[2:]}:{pid[2:]}'
    name, _ = DEVICES[vid_pid]
    return usb_idx, name, sn


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

POWER_INIT = '''
    OUTPut:PROTection:CLEar
    OUTPut 0
    OUTPut:DELay:ON 0.00
    OUTPut:DELay:OFF 0.00
    OUTPut:TRIGgered 0
    VOLT 19
    CURR 3.5
'''

POWER_START = '''
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


ELOADER_INIT = '''
    FACTory
    MODE CC
    CRANge HIGH
    VRANge HIGH
    MODE:DYNamic STAT
    CURRent:SRATe 10
    CURRent:VA 1.1
    CURRent:VB 1.1
    INPut:MODE LOAD
'''

ELOADER_START = '''
    INPut ON
'''

ELOADER_STOP = '''
    INPut OFF
'''


POWERSENSOR_INIT = '''
    SYST:PRES DEF
    INIT:CONT ON
'''


def cmd(command_constant, add_newline=True):
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
        logger.info(f'  {e}')
    return cmds


def cmd_volt(channel):
    cmds = cmd(MEASURE_VOLT_BASE)
    cmds = [e for e in cmds if not e.startswith(f'ROUT:CLOSE {channel}')]
    for i, e in enumerate(cmds):
        if '___' in e: cmds[i] = f'ROUT:CHAN {channel},1,100,0'
    return cmds


def get_ordered_comports_by_gw_idn(comports, sn_numbers):
    port_sn = {}
    for i, port in enumerate(comports):
        s = SerialInstrument(i, port)
        sn = s.gw_read_idn()
        port_sn[port] = sn
        s.close_com()
    sn_port = {v:k for k,v in port_sn.items()}
    reorderd_comports = [sn_port[sn] if sn in sn_port else None for sn in sn_numbers]
    return reorderd_comports


def update_serial(instruments, inst_type, comports):
    logger.info('    update_serial start')
    logger.info(f'    inst_type: {inst_type}')
    inst = instruments[inst_type]
    for i, e in enumerate(inst):
        e.com = None

    if inst_type=='gw_powersupply':
        sn = [e.sn for e in inst]
        comports = get_ordered_comports_by_gw_idn(comports, sn)

    for i, com in enumerate(comports):
        inst[i].com = com

    for name, items in instruments.items():
        logger.info('    name: %s', name)
        for i, e in enumerate(items):
            logger.info('    e: %s, com=%s', e, e.com)
    logger.info('    update_serial end')


class Instrument():
    @property
    def interface(self):
        filtered = [e[1] for e in DEVICES.values() if self.NAME==e[0]]
        if len(filtered)==1:
            return filtered[0]
        else:
            return 'unknown'


visa_addr = 'USB0::0x2A8D::0x2D18::MY57420015::0::INSTR'
class VisaInstrument(Instrument):
    dll_32 = 'C:/Windows/System32/visa32.dll'
    dll_64 = 'C:/Windows/System32/visa64.dll'

    #  def __init__(self, index, visa_addr=None, delay_sec=0.002):
    def __init__(self, index, sn=None, delay_sec=0.002):
        self.index = index
        vid_pid = [k for k,v in DEVICES.items() if v[0]=='ks_powersensor'][0]
        vid, pid = [f'0x{e}' for e in vid_pid.split(':')]
        self.visa_addr = '::'.join([
            f'USB{index-1}', vid, pid, sn, 'INSTR'])
        self.delay_sec = delay_sec
        #  import visa
        self.rm = visa.ResourceManager(self.dll_32)

    def open(self):
        try:
            self.dev = self.rm.open_resource(self.visa_addr)
            self.dev.timeout = 30000
            self.dev.clear()
        except Exception as ex:
            return False
        else:
            return True

    def close(self):
        self.dev.close()

    def run_cmd(self, items, fetch=False):
        try:
            for cmd in items:
                logger.info(f'    cmd: {cmd}')
                if '?' in cmd:
                    result = self.dev.query(cmd)
                else:
                    self.dev.write(cmd)
                if self.delay_sec:
                    time.sleep(self.delay_sec)
            if fetch:
                return result
        except Exception as ex:
            logger.error("    run_cmd failed!")
            logger.error(f'    {type_(ex)}, {ex}')

    def read_idn(self):
        idn = self.run_cmd(['*IDN?'], True)
        sn = idn.split(',')[2]
        return sn


class PowerSensor(VisaInstrument):
    NAME = 'ks_powersensor'
    StartFetchTime = 0
    MeasureTime = 0.3

    def init(self):
        line = self.run_cmd(cmd(POWERSENSOR_INIT), True)

    def measure_power(self, freq):
        t0 = time.perf_counter()
        elapsed = lambda: time.perf_counter() - t0
        line = self.run_cmd([f'FREQ {freq}', 'FREQ?'], True)
        powers = []
        while (True):
            if elapsed() >= self.StartFetchTime:
                line = self.run_cmd(['FETC?'], True)
                if not line: continue
                result = float(line)
                powers.append(result)
            if elapsed() > self.MeasureTime:
                self.ave_power = sum(powers)/len(powers)
                break
        return self.ave_power


class SerialInstrument(Instrument):

    def __init__(self,
                 index=1,
                 port=None,
                 sn = None,
                 baud=115200,
                 timeout=2,
                 delay_sec=0.002):
        self.index = index
        self.sn = sn
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
        logger.info('    in SerialInstrument: open_com start')
        success = False
        if self.com:
            logger.info('    get_serial start')
            self.ser = get_serial(self.com, baudrate=baud, timeout=timeout)
            logger.info('    get_serial end')
            success = True
        logger.info('    in SerialInstrument: open_com end\n')
        return success

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
            logger.debug("    run_cmd failed!")
            logger.error(f'    {type_(ex)}, {ex}')

    def gw_read_idn(self):
        idn = self.run_cmd(['*IDN?'], True) # ignore first since it's empty (just MacOS)
        idn = self.run_cmd(['*IDN?'], True)
        sn = idn.split(',')[2]
        return sn


class PowerSupply(SerialInstrument):
    NAME = 'gw_powersupply'
    StartFetchTime = 2
    MeasureTime = 10

    def init(self):
        logger.info(f'    power_{self.index}({self}) init!')
        self.run_cmd(cmd(POWER_INIT))

    def start(self):
        logger.info(f'    power_{self.index}({self}) start!')
        self.run_cmd(cmd(POWER_START))

    def on(self):
        logger.info(f'    power_{self.index}({self}) on!')
        self.run_cmd(cmd(POWERON))

    def off(self):
        logger.info(f'    power_{self.index}({self}) off!')
        self.run_cmd(cmd(POWEROFF))

    def measure_voltage(self):
        line = self.run_cmd(['MEASure:VOLTage:DC?'], True)
        volt = float(line)
        return volt

    def measure_cur(self):
        line = self.run_cmd(['MEASure:CURRent:DC?'], True)
        current = float(line)
        return current

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


class Eloader(SerialInstrument):
    NAME = 'gw_eloader'
    StartFetchTime = 2
    MeasureTime = 10

    def init(self):
        self.run_cmd(cmd(ELOADER_INIT), False)

    def start(self):
        self.run_cmd(cmd(ELOADER_START), False)

    def stop(self):
        self.run_cmd(cmd(ELOADER_STOP), False)

    def measure_voltage(self):
        line = self.run_cmd(['MEASure:VOLTage:DC?'], True)
        voltage = float(line)
        return voltage

    def measure_current(self):
        try:
            line = self.run_cmd(['MEASure:CURRent:DC?'], True)
            current = float(line)
        except ValueError as ex:
            logger.error(f'    {ex}')
            logger.error(f'    {line}')
            return None
        #  line = self.run_cmd(['MEASure:CURRent:DC?'], True)
        #  current = float(line)
        return current


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
        logger.info(f'    result: {result}')
        values = [float(e) for e in result.split(',')]
        return values

    def measure_volts_all(self):
        result = self.run_cmd(cmd(MEASURE_VOLT_ALL), True)
        values = [float(e) for e in result.split(',')]
        return values

    def measure_freqs_all(self):
        result = self.run_cmd(cmd(MEASURE_FREQ), True)
        logger.info(f'    measure_freqs_all result: {result}')
        logger.info(f'    type: {type(result)}')
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


def generate_instruments(task_devices, instrument_map):
    instruments = defaultdict(list)
    for dev, dev_info in task_devices.items():
        name, num = dev_info['name'], dev_info['num']
        sn_numbers = dev_info['sn'] if 'sn' in dev_info else None
        if name not in instrument_map.keys(): continue
        if sn_numbers: assert len(sn_numbers)==num
        for i in range(num):
            if sn_numbers:
                inst = instrument_map[name](i+1, sn=sn_numbers[i])
            else:
                inst = instrument_map[name](i+1)
            instruments[name].append(inst)
    return instruments


INSTRUMENT_MAP = {
    'gw_powersupply': PowerSupply,
    'gw_dmm': DMM,
    'gw_eloader': Eloader,
    'ks_powersensor': PowerSensor,
}


if __name__ == "__main__":
    pass

import time                                                  #引進時間模組
import json
#  import visa
from collections import defaultdict                         #用collections來定義字典內容;以供後續查找;沒有key值自定義

from mylogger import logger                                 #追蹤異常模組日誌
from serials import (get_serial, get_devices)               #引進自定義serial模組
from config import (DEVICES, SERIAL_DEVICES, VISA_DEVICES,  #引進參數檔
                    SERIAL_DEVICE_NAME, VISA_DEVICE_NAME)


type_ = lambda ex: f'<{type(ex).__name__}>'                               #用lambda定義後面函式;檢查對象類型
PADDING = ' ' * 4                                                         #4個空格

    #這個方法為利用visa32.dll找出接儀器的所有usb;得到'comport': usb_idx,  'name': name,  'sn': sn(這裡是找到多個)
def get_visa_devices():                                                   #獲得VISA的devices
    import visa
    dll_32 = 'C:/Windows/System32/visa32.dll'                             #利用visa32.dll模組
    rm = visa.ResourceManager(dll_32)                                     #為最常見的VISA操作提供導入快捷方式的模塊。
    resource_names = rm.list_resources()                                  #返回所有已連接設備匹配查詢的元組。
    resource_names = [e for e in resource_names if e.startswith('USB')]   #resource_names為所有port;檢查字串為USB開頭回傳True
    devices = []                                                          #列出devices為list
    for resource_name in resource_names:                                  #用for迴圈列出每一個usb資訊
        usb_idx, name, sn = get_visa_device(resource_name)                #由方法get_visa_device獲取resource_name得到usb_idx, name, sn
        devices.append({                                                  #增加到devices List[Dict[str, Any]] = []
            'comport': usb_idx,                                           #列出comport': usb_idx
            'name': name,                                                 #列出'name': name
            'sn': sn                                                      #列出'sn': sn
        })
    return devices


def get_visa_device(resource_name):                                      #這裡是找一個
    usb_idx, vid, pid, sn, _ = resource_name.split('::')                 #列出usb_idx, vid, pid, sn, _ ;利用::分開
    vid_pid = f'{vid[2:]}:{pid[2:]}'                                     #組合vid與pid;
    name, _ = DEVICES[vid_pid]                                           #組合vid與pid;由2組號碼查找對應的硬體資訊和通訊模式
    return usb_idx, name, sn

#=============================
#以下為command line
#=============================
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
    CORR:GAIN2 40
    CORR:GAIN2:STAT ON
    INIT:CONT ON
'''
#=======================

    #功能為刪除每具字尾所有的包括'\n', '\r', '\t',  ' ');以enter換行分開
def cmd(command_constant, add_newline=True):                            #定義cmd方法引進屬性command_constant
    return [e.strip() for e in command_constant.strip().split('\n')]    #找尋換行符號strip(rm)刪除当rm为空时，默认删除空白符（包括'\n', '\r', '\t',  ' ');split分離;都檢查每具字尾


    #組合commandline流程(MEASURE_VOLT_B)
def cmd_volts(channels):                                                #量測電壓設定
    cmds = cmd(MEASURE_VOLT_B)                                          #由MEASURE_VOLT_B設定流程引入cmds
    idx1 = cmds.index('ROUT:MULT:OPEN 101,116')                         ##設定idex1為ROUT:MULT:OPEN 101,116:第幾個4
    into1 = [f'ROUT:CLOS {e}' for e in range(101, 117) if e not in channels] #設定e為101~117;如果e的設定值不再channels裡
    cmds = cmds[:idx1 + 1] + into1 + cmds[idx1 + 1:]                    #組合
    idx2 = cmds.index('TRIG:DEL 0')                                     #定義idx2為TRIG:DEL 0
    into2 = [f'ROUT:CHAN {e},1,100,0' for e in channels]                #設定e為1,100,0;如果e的設定值不再channels裡
    cmds = cmds[:idx2 + 1] + into2 + cmds[idx2 + 1:]                    #組合
    cmds[cmds.index('ROUT:COUN 1')] = f'ROUT:COUN {len(channels)}'      #解查2者是否相等
    for e in cmds:                                                      #將cmds列出
        logger.info(f'{PADDING}{e}')                                    #列出日誌
    return cmds

    #組合commandline流程(MEASURE_VOLT_BASE)
def cmd_volt(channel):                                                    #單一電壓設定
    cmds = cmd(MEASURE_VOLT_BASE)                                         #引進設定表
    cmds = [e for e in cmds if not e.startswith(f'ROUT:CLOSE {channel}')] #e.startswith(f'ROUT:CLOSE {channel}')找出有ROUT:CLOSE {channel}字串輸出true
    for i, e in enumerate(cmds):                                          #enumerate函数用来将一个可迭代对象变成一个枚举对象
        if '___' in e: cmds[i] = f'ROUT:CHAN {channel},1,100,0'
    return cmds

    #獲得
def get_ordered_comports_by_gw_idn(comports, sn_numbers):               #獲得 comports從IDN獲取儀器序號和類型
    port_sn = {}                                                        #port_sn
    for i, port in enumerate(comports):                                 #enumerate函数用来将一个可迭代对象变成一个枚举对象
        s = SerialInstrument(i, port)                                   #使用方法SerialInstrument
        sn = s.gw_read_idn()                                            #呼叫gw_read_idn查詢儀器序號
        port_sn[port] = sn                                              #得到port儀器序號的sn碼
        s.close_com()                                                   #呼叫close_com關閉
    sn_port = {v:k for k,v in port_sn.items()}                          #列出sn_port = {v:k for k,v in 列出()}   的key和value                      #
    reorderd_comports = [sn_port[sn] if sn in sn_port else None for sn in sn_numbers]
    return reorderd_comports


def update_serial(instruments, inst_type, comports):                    #更新儀器名;更新comports
    logger.info(f'{PADDING}update_serial start')
    logger.info(f'{PADDING}inst_type: {inst_type}')
    inst = instruments[inst_type]
    for i, e in enumerate(inst):                                        #enumerate函数用来将一个可迭代对象变成一个枚举对象
        e.com = None

    if inst_type=='gw_powersupply':                                     #如果inst_type=='gw_powersupply'
        sn = [e.sn for e in inst]                                       #在inst = instruments[inst_type]
        comports = get_ordered_comports_by_gw_idn(comports, sn)         #利用通用儀器IDN得到port and sn

    for i, com in enumerate(comports):                                  #enumerate函数用来将一个可迭代对象变成一个枚举对象
        inst[i].com = com                                               #inst = instruments[inst_type]

    for name, items in instruments.items():                             #得到儀器的item為儀器名稱和通訊類型
        logger.info(f'{PADDING}name: %s', name)                         #列出日誌
        for i, e in enumerate(items):                                   #numerate函数用来将一个可迭代对象变成一个枚举对象
            logger.info(f'{PADDING}e: %s, com=%s', e, e.com)
    logger.info(f'{PADDING}update_serial end')


class Instrument():                                                      #定義物件
    @property                                                            #引進屬性
    def interface(self):                                                 #定義方法
        filtered = [e[1] for e in DEVICES.values() if self.NAME==e[0]]   #擷取devices的值;NAME為儀器名子=filtered[0];filtered[1]=通訊模式
        if len(filtered)==1:
            return filtered[0]
        else:
            return 'unknown'


#  visa_addr = 'USB0::0x2A8D::0x2D18::MY57420015::0::INSTR'
#  visa_addr = 'USB0::0x2A8D::0x2D18::MY59190011::0::INSTR'  --> U2040XA

    #針對visa儀器
class VisaInstrument(Instrument):                                       #定義一個物件
    dll_32 = 'C:/Windows/System32/visa32.dll'
    dll_64 = 'C:/Windows/System32/visa64.dll'

    #  def __init__(self, index, visa_addr=None, delay_sec=0.002):
    def __init__(self, index, sn=None, delay_sec=0.002):             #結構化引進屬性
        self.index = index                                           #index為class VisaInstrument的屬性
        vid_pid = [k for k,v in DEVICES.items() if v[0]=='ks_powersensor'][0] #對DEVICES.items()取出k和v值;如果v[0]裡面有ks_powersensor;則定為vid_pid
        vid, pid = [f'0x{e}' for e in vid_pid.split(':')]            #分離vid和pid
        self.visa_addr = '::'.join([                                 #指定::連接成新的字符;'USB0::0x2A8D::0x2D18::MY57420015::0::INSTR'
            f'USB{index-1}', vid, pid, sn, 'INSTR'])
        self.delay_sec = delay_sec                                  #定義方法
        import visa
        self.rm = visa.ResourceManager(self.dll_32)                   #透過visa32.dll引進模組=rm

        #開啟通道
    def open(self):                                                 #定義開啟方法
        try:
            self.dev = self.rm.open_resource(self.visa_addr)        #開啟通道visa_addr已經組合完畢
            self.dev.timeout = 30000                                #設定通訊timeout時間
            self.dev.clear()                                        #清除
        except Exception as ex:
            return False
        else:
            return True

        #關閉通道
    def close(self):                                                #定義關閉方法
        self.dev.close()


        #開始執行
    def run_cmd(self, items, fetch=False):                          #執行cmd
        try:
            for cmd in items:
                logger.info(f'{PADDING}cmd: {cmd}')
                if '?' in cmd:                                      #檢查內容是否有?
                    result = self.dev.query(cmd)                    #定義q序列排隊
                else:
                    self.dev.write(cmd)                             #下通訊
                if self.delay_sec:                                  #設定等待時間
                    time.sleep(self.delay_sec)
            if fetch:
                return result
        except Exception as ex:
            logger.error(f'{PADDING}run_cmd failed!')
            logger.error(f'{PADDING}{type_(ex)}, {ex}')

        #讀取儀器IDN碼
    def read_idn(self):
        idn = self.run_cmd(['*IDN?'], True)
        sn = idn.split(',')[2]
        return sn

    #定義PowerSensor
class PowerSensor(VisaInstrument):
    NAME = 'ks_powersensor'      #名稱
    StartFetchTime = 0           #開始取的時間
    MeasureTime = 0.3            #量測時間

    def init(self):
        line = self.run_cmd(cmd(POWERSENSOR_INIT), True) #定義初始方法

    def measure_power(self, freq):                       #量測power
        t0 = time.perf_counter()                         #返回性能计数器的值（以小数秒为单位）作为浮点数，即具有最高可用分辨率的时钟，以测量短持续时间
        elapsed = lambda: time.perf_counter() - t0       #定義函式(使用的時間)
        line = self.run_cmd([f'FREQ {freq}', 'FREQ?'], True)  #執行
        powers = []
        while (True):
            if elapsed() >= self.StartFetchTime:         #使用的時間>=開始擷取的時間
                line = self.run_cmd(['FETC?'], True)     #cmd下有FETC?
                if not line: continue
                result = float(line)                     #結果定義為浮點數
                powers.append(result)
            if elapsed() > self.MeasureTime:             #截取的時間大於量測的時間
                self.ave_power = sum(powers)/len(powers) #算平均能量
                break
        return self.ave_power


class SerialInstrument(Instrument):                     #定義物件SerialInstrument

    def __init__(self,                                  #結構;引進屬性;self實體化
                 index=1,                               #屬性index
                 port=None,                             #port
                 sn = None,                             #sn儀器序號
                 baud=115200,                           #通訊包瑞
                 timeout=2,                             #結束時間
                 delay_sec=0.002):                      #等待時間
        self.index = index                              #給予屬性值
        self.sn = sn                                    #給予屬性值
        self.delay_sec = delay_sec                      #等待時間
        if port:
            self.com = port                             #看port是否等於 self.com
            self.ser = get_serial(port, baudrate=baud, timeout=timeout) #引入自定義模組get_serial
        else:
            self.com = None
            self.ser = None

    @property                                               #引進屬性
    def is_open(self):                                      #查看是否打開
        return self.ser.isOpen() if self.ser else False

    def open_com(self, baud=115200, timeout=2):             #開啟通道
        logger.info(f'{PADDING}in SerialInstrument: open_com start')
        success = False
        if self.com:
            logger.info(f'{PADDING}get_serial start')
            self.ser = get_serial(self.com, baudrate=baud, timeout=timeout)
            logger.info(f'{PADDING}get_serial end')
            success = True
        logger.info(f'{PADDING}in SerialInstrument: open_com end')
        return success

    def close_com(self):                                    #關閉通到
        self.ser.close()
        self.ser = None

    def run_cmd(self, items, fetch=False):                  #執行
        try:
            for item in items:
                cmd = f'{item}\n'.encode()
                self.ser.write(cmd)
                if self.delay_sec: time.sleep(self.delay_sec)
            if fetch:
                result = self.ser.readline().decode('utf8')
                return result
        except Exception as ex:
            logger.debug(f'{PADDING}run_cmd failed!')
            logger.error(f'{PADDING}{type_(ex)} -- {ex}')

    def gw_read_idn(self):                                          #讀取儀器IDN(測試儀器連結)
        idn = self.run_cmd(['*IDN?'], True) # ignore first since it's empty (just MacOS)
        logger.debug(f'idn {idn}')
        idn = self.run_cmd(['*IDN?'], True)
        logger.debug(f'idn {idn}')
        sn = idn.split(',')[2]
        return sn

    def __repr__(self):
        return f'<{self.__class__.__name__}({self.index}, {self.sn})>'


class PowerSupply(SerialInstrument):                                #設定物件電源供應器
    NAME = 'gw_powersupply'                                         #命名
    StartFetchTime = 2                                              #開始擷取時間
    MeasureTime = 10                                                #量測時間

    def init(self):                                                 #初始
        logger.info(f'{PADDING}power_{self.index}({self}) init!')
        self.run_cmd(cmd(POWER_INIT))

    def start(self):                                                #開始
        logger.info(f'{PADDING}power_{self.index}({self}) start!')
        self.run_cmd(cmd(POWER_START))

    def on(self):                                                   #輸出電源
        logger.info(f'{PADDING}power_{self.index}({self}) on!')
        self.run_cmd(cmd(POWERON))

    def off(self):                                                  #關閉輸出
        logger.info(f'{PADDING}power_{self.index}({self}) off!')
        self.run_cmd(cmd(POWEROFF))

    def measure_voltage(self):                                      #量測電壓
        line = self.run_cmd(['MEASure:VOLTage:DC?'], True)
        volt = float(line)
        return volt

    def measure_cur(self):                                          #量測電流
        line = self.run_cmd(['MEASure:CURRent:DC?'], True)
        current = float(line)
        return current

    def measure_current(self):                                      #量測電流
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


class Eloader(SerialInstrument):                                        #
    NAME = 'gw_eloader'
    StartFetchTime = 2                                                  #開始時間
    MeasureTime = 10                                                    #量測時間

    def init(self):                                                     #初始
        logger.info(f'{PADDING}eloader_{self.index}({self}) init!')
        self.run_cmd(cmd(ELOADER_INIT), False)

    def start(self):
        logger.info(f'{PADDING}eloader_{self.index}({self}) start!')
        self.run_cmd(cmd(ELOADER_START), False)

    def stop(self):
        self.run_cmd(cmd(ELOADER_STOP), False)

    def measure_voltage(self):                                          #量測電壓
        line = self.run_cmd(['MEASure:VOLTage:DC?'], True)
        voltage = float(line)
        return voltage

    def measure_current(self):                                          #量測電流
        try:
            line = self.run_cmd(['MEASure:CURRent:DC?'], True)
            current = float(line)
        except ValueError as ex:
            logger.error(f'{PADDING}{ex}')
            logger.error(f'{PADDING}{line}')
            return None
        #  line = self.run_cmd(['MEASure:CURRent:DC?'], True)
        #  current = float(line)
        return current


class DMM(SerialInstrument):                                            #物件DMM
    NAME = 'gw_dmm'

    def measure_volt(self, channel):                                    #量測電壓
        while True:
            result = self.run_cmd(cmd_volt(channel), True)
            if result:
                return float(result)

    def measure_freq(self, channel):                                    #量測頻率
        result = self.run_cmd(cmd_volt(channel), True)
        if result:
            return float(result)

    def measure_volts(self, channels):
        result = self.run_cmd(cmd_volts(channels), True)
        logger.info(f'{PADDING}result: {result}')
        values = [float(e) for e in result.split(',')]
        return values

    def measure_volts_all(self):
        result = self.run_cmd(cmd(MEASURE_VOLT_ALL), True)
        values = [float(e) for e in result.split(',')]
        return values

    def measure_freqs_all(self):
        result = self.run_cmd(cmd(MEASURE_FREQ), True)
        logger.info(f'{PADDING}measure_freqs_all result: {result}')
        logger.info(f'{PADDING}type: {type(result)}')
        values = [float(e) for e in result.split(',')]
        return values


def open_all(update_ser=False, if_open_com=False, if_poweron=False): #打開DMM;打開PowerSupply(1);PowerSupply(2)
    dmm1 = DMM(1)
    power1 = PowerSupply(1)
    power2 = PowerSupply(2)
    instruments = [dmm1, power1, power2]

    if update_ser:                                                  #呼叫def update_ser
        update_serial(instruments)

    if if_open_com:                                                 #測試DMM通道是否開啟
        for e in instruments:
            e.open_com() if e is not dmm1 else e.open_com(timeout=5)#引進DMM方法open_com開啟通道;如果沒有開啟通道則開啟
    if if_poweron:                                                  #開啟電源供應器
        power1.on()
        power2.on()
    return instruments


def generate_instruments(task_devices, instrument_map):             #訊號產生器
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

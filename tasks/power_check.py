import sys
import json
import argparse                     #引用變數
from instrument import DMM          #儀器DMM
from mylogger import logger         #引進from mylogger import logger用來記錄引發模組異常訊息

PADDING = ' ' * 8                   #為8個空字串


def volt_in_range(channel, volt, limits):             #設定電壓範圍
    rng = limits[channel]                             #設定通道極限=rng
    if rng[0] < volt < rng[2]: # min & max            #設定範圍
        return 'Pass(%.3f)'% volt                     #rng在範圍類為Pass
    else:
        return 'Fail(%.3f)'% volt                     #rng在範圍外圍Fail


if __name__ == "__main__":                            #主程式路口，主程式名子
    logger.info('{PADDING}power_check2 start...')     #輸出日誌{PADDING}power_check2 start...
    parser = argparse.ArgumentParser()                #引用變數
    parser.add_argument('channels_limits', help='channel', type=str)  #引用變數使用對象channels_limits

    #  parser.add_argument('-pm', '--port_dmm', help='serial com port dmm', type=str)#引用變數使用對象-p', '--ports'
    parser.add_argument('-p', '--ports',
                        help='serial com port for instruments', type=str)

    args = parser.parse_args()                        #執行引用變數

    unpacked = json.loads(args.channels_limits)       #將變數轉換為json格式
    logger.info(f'{PADDING}unpacked: {unpacked}')     #紀錄由json設定的channels_limits
    channel_group = unpacked['args']                  #解析引進的變數args形成channel_group;
    limits = {int(k):v for k,v in unpacked['limits'].items()}   #將解析出來limits的key和value值

    #  port_dmm = args.port_dmm
    ports = json.loads(args.ports)                    #將變數args.ports轉換為json
    logger.info(f'{PADDING}{ports}')                  #紀錄日誌port
    port_dmm = ports['gw_dmm'][0]                     #定義port_dmm = device.json ;"2184:001A": ["gw_dmm","serial"]

    logger.info(f'{PADDING}channel_volt: {channel_group}')   #日制紀錄變數設定值
    logger.info(f'{PADDING}limits: {limits}')                #日制紀錄極限值

    # for single channel read
    dmm = DMM(port=port_dmm, timeout=0.4)                  #開始讀取儀器值
    dmm.measure_volt(101)                                  #量測電壓
    dmm.ser.close()                                        #關閉DMM

    # for multieple channels read
    dmm = DMM(port=port_dmm, timeout=2)

    logger.info(f'{PADDING}dmm.com: {dmm.com}')          #DMM通道
    logger.info(f'{PADDING}dmm.is_open: {dmm.is_open}')  #DMM是否開啟
    logger.info(f'{PADDING}dmm.ser: {dmm.ser}')

    channels = sorted(sum(channel_group, []))                   #秀出通道
    logger.info(f'{PADDING}channels: {channels}')               #日誌顯示
    logger.info(f'{PADDING}type(channels): {type(channels)}')   #日誌顯示

    dmm.measure_volt(101)                               #開始量測
    volts = dmm.measure_volts(channels)
    dmm.close_com()                                     #關閉DMM

    #  volts_passfail = [volt_in_range(ch,e) for ch, e in zip(channels, volts)]
    volts_passfail = [volt_in_range(ch, e, limits) for ch, e in zip(channels, volts)]   #確認電壓值pass or fail
    logger.info(f'{PADDING}volts measured: {volts}')                                    #紀錄現在量測值

    logger.info('{PADDING}power_check2 end...')                                         #

    channel_volt = dict(zip(channels, volts_passfail))                                  #將量測通道和電壓值壓縮列表

    results = [[channel_volt[e] for e in g]for g in channel_group]
    sys.stdout.write(json.dumps(results))                                              #寫入結果

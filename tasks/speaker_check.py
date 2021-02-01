import sys
import json                                                     #引進json格式轉換
import argparse                                                 #引進變數
from instrument import DMM                                      #引進DMM serial模塊
from mylogger import logger                                     #引進程式異常模組路徑

PADDING = ' ' * 8

    #檢測頻率是否在範圍類
def freq_in_range(channel, freq, limits):                       #檢定義方法引進屬性;channel, freq, limits
    rng = limits[channel]                                       #channel列表引進範圍
    #  if rng[0] < freq and freq < rng[2]: 
    if rng[0] < freq < rng[2]:                                  #判斷頻率
        return 'Pass(%.3f)' % freq
    else:
        return 'Fail(%.3f)' % freq


if __name__ == "__main__":
    logger.info(f'{PADDING}speaker check...')                           #日誌顯示peaker check...
    parser = argparse.ArgumentParser()                                  #引進變數架構(用來外部輸入變數);引進程式模組
    parser.add_argument('channels_limits', help='channel', type=str)    #增加引用變數channels_limits;類型為字串;提示字串為channel

    #  parser.add_argument('-pm', '--port_dmm', help='serial com port dmm', type=str)
    parser.add_argument('-p', '--ports',                                #引進選擇變數
                        help='serial com port for instruments', type=str)

    args = parser.parse_args()                                          #執行變數輸入處理

    unpacked = json.loads(args.channels_limits)                         #轉換為json格式
    logger.info(f'{PADDING}unpacked: {unpacked}')                       #日誌輸出unpacked: {unpacked}
    channel_group = unpacked['args']                                    #將變數引進channel_group
    limits = {int(k):v for k,v in unpacked['limits'].items()}           #列出json裡面的key;value

    
    #  port_dmm = args.port_dmm
    ports = json.loads(args.ports)                                      #轉換為json檔
    logger.info(f'{PADDING}{ports}')                                    #日誌輸出PADDING}{ports}
    port_dmm = ports['gw_dmm'][0]                                       #ports選取gw_dmm[0]名子;擷取port類型sreial

    logger.info(f'{PADDING}speaker check start. [channel_group: %s]' % channel_group) #輸出日誌

    # for single channel read
    dmm = DMM(port=port_dmm, timeout=0.4)                               #DMM設定開啟
    dmm.measure_volt(101)                                               #量測電壓值
    dmm.ser.close()                                                     #關閉通道

    # for multieple channels read
    dmm = DMM(port=port_dmm, timeout=5)                                 #DMM設定開啟

    logger.info(f'{PADDING}dmm.com: {dmm.com}')                         #日誌輸出COM的設定
    logger.info(f'{PADDING}dmm.is_open: {dmm.is_open}')                 #檢查是否開啟通道
    logger.info(f'{PADDING}dmm.ser: {dmm.ser}')                         #

    channels = sorted(sum(channel_group, []))
    logger.info(f'{PADDING}channels: {channels}')
    logger.info(f'{PADDING}type(channels): {type(channels)}')

    freqs = dmm.measure_freqs_all()                                     #量測頻率
    chs = list(range(107, 109)) + list(range(115, 117))                 #設定頻率範圍
    #  freqs_passfail = [freq_in_range(ch, e) for ch, e in zip(chs, freqs)]
    freqs_passfail = [freq_in_range(ch, e, limits) for ch, e in zip(channels, freqs)] #判斷頻率是否在範圍內

    logger.info(f'{PADDING}freqs: {freqs}')
    logger.info(f'{PADDING}passfail: {freqs_passfail}')

    
    channel_freq = dict(zip(channels, freqs_passfail))             #列出字典:為通道;和結果
    results = [[channel_freq[e] for e in g]for g in channel_group]

    sys.stdout.write(json.dumps(results))

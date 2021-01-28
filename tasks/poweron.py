import sys
import json
import argparse                                                 #引用變數
import pickle                                                   #實現python物件的序列化和反序列化
from mylogger import logger                                     #引進程式異常發生模組日誌
from utils import resource_path                                 #引進第3方模塊

PADDING = ' ' * 8


if __name__ == "__main__":
    logger.info(f'{PADDING}poweron start...')                   #顯示日誌poweron start...
    parser = argparse.ArgumentParser()                          #最基本的 object 起始
    parser.add_argument('power_index', help='power_index', type=int)    #引用裡面的參數power_index;類型為int
    args = parser.parse_args()                                          #執行引用
    power_index = args.power_index                                      #引用變數結果

    logger.info(f'{PADDING}power_index: {power_index}')          #顯示日誌power_index: 變數引用值

    with open(resource_path('instruments'), 'rb') as f:         #讀取instruments的資訊全部給f
        #  _, power1, power2 = pickle.load(f)
        power1, power2, _ = pickle.load(f)                      #實現python物件的序列化和反序列化(讀出的data需要反序列化)

    power = [power1, power2][power_index - 1]
    if not power.is_open:                                       #如果通道沒開啟
        logger.info(f'{PADDING}open power{power_index}!')       #秀出open power index(秀出第幾台)
        power.open_com()                                        #power supply開啟通道
        power.on()                                              #開啟power supply 輸出
        power.measure_current()                                 #量測電流值

    result = power.max_current                                  #結果為最大電流

    logger.info(f'{PADDING}result: {result}')                   #秀出日誌結果為最大電流
    sys.stdout.write(str(result))                               #寫入結果打印定向結果

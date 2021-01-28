import sys                                      #系统相关的参数和函数
import json                                     #引進json檔案模組
import time                                     #引進时间的访问和转换
import argparse                                 #引進函數變量
import random                                   #產生亂數
from instrument import DMM

from mylogger import logger                     #引進程式引發錯誤，由哪個模組造成寫成日誌


PADDING = '    '


if __name__ == "__main__":                     #程式名字;程式窗口
    logger.info(f'{PADDING}simulation group1 start...')  #日誌輸出simulation group1 start...
    parser = argparse.ArgumentParser()                   #引進變數架構
    parser.add_argument('channels', help='channels', type=str) #增加引進變數
    parser.add_argument('-pm', '--port_dmm', help='serial com port dmm', type=str) #增加選擇引進變數
    args = parser.parse_args()

    channel_group = json.loads(args.channels)             #將變數轉換為json格式
    port_dmm = args.port_dmm                              #設定port_dmm為args.port_dmm選擇引進變數
    logger.info(f'{PADDING}simulation group1 start. [channel_group: %s]' % channel_group)
    time.sleep(random.randint(1,4))                       #產生1~4之間的亂數(模擬按鍵亂數)

    logger.info(f'{PADDING}simulation group1 end...')

    results = []
    rnd = lambda: random.choice(['Pass']*9+['Fail'])      #定義函式從 ['Pass']*9+['Fail']之中回傳一個元素。如果 ['Pass']*9+['Fail']是空的，會回傳 IndexError。
    for ch in channel_group:
        results.append([rnd(), rnd()])

    sys.stdout.write(json.dumps(results))                #寫進序列以json格式


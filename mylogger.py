import os
import time
import logging
import pyclbr   #pyclbr可以掃描Python源代碼以查找類和獨立函數。有關類，方法，函數名稱和行號的信息是使用令牌化收集的，而無需導入代碼。
import bisect   #bisect --- 陣列二分演算法
from copy import copy    #copy --- 浅层 (shallow) 和深层 (deep) 复制操作
from logging.handlers import TimedRotatingFileHandler   #日誌輪轉



     #分類列出模組
class Module:                                           #定義物件Module 模組瀏覽器使用
    def __init__(self, module):                         #設定結構;引進屬性module,結構實體化self
        mod = pyclbr.readmodule_ex(module)              #返回一个基于字典的树，其中包含与模块中每个用 def 或 class 语句定义的函数和类相对应的函数和类描述器
        line2func = []                                  #宣告一個空陣列

        for classname, cls in mod.items():              #獲得模組的類因為在python中萬物都是物件，所以當我們使用Class.method()的時候，實際上的第一個引數是我們約定的cls;mod.items;字典将模块级函数和类名称映射到其描述符
            if isinstance(cls, pyclbr.Function):        #用來判斷是否為設定pyclbr.Function(類型為class)類型;
                line2func.append((cls.lineno, "<no-class>", cls.name)) #增加在line2func裡
            else:
                for methodname, start in cls.methods.items():       #獲得模組的方法
                    line2func.append((start, classname, methodname))#

        line2func.sort()
        keys = [item[0] for item in line2func]                     #列表得到key 1.內置構造函數 2.Function object 3.得到的openssl建設者 4.
        self.line2func = line2func
        self.keys = keys
        print(self.keys)


        #列出有多少模組
    def line_to_class(self, lineno):                              #列出模組有多少
        index = bisect.bisect(self.keys, lineno) - 1
        return self.line2func[index][1]

        #檢查模組是否有問題
def lookup_module(module):                                                 #檢查module是否有異常
    try:
        _module = Module(module)
    except AttributeError as ex:
        _module = None
    return _module


        #檢查模組類型是否為class
def lookup_class(module, funcname, lineno):                                #檢查否有class
    if funcname == "<module>":                                             #如果等於<module>
        return "<no-class>"                                                #則回傳為<no-class>

    try:
        module = lookup_module(module)                                     #檢查模組是否異常
        className = module.line_to_class(lineno) if module else None       #如果沒有異常為module.line_to_class(lineno)輸出模組名稱;異常則輸出None(數量)
    except IndexError as ex:                                               #如果index異常則給ex(檢查數量是否異常)
        className = None                                                   #className為None
    return className


    #日誌存檔類型設定
class MyLogFormatter(logging.Formatter):
    def format(self, record):
        record = copy(record)                                             #定義record為為複製record變數
        record.className = lookup_class(                                  #定義要記錄的物件名稱record變數引進
            record.module, record.funcName, record.lineno
        )
        if record.className:                                              #紀錄格式:模組名稱,物件名稱,功能名稱
            location = '%s.%s.%s' % (record.module, record.className, record.funcName)   #定義為record.module.record.className.record.funcName
            location = location.replace('<no-class>.', '')                #有出現的no-class字符串則用空字串代替
        else:
            location = '%s.%s' % (record.module, record.funcName)         #定義record.module.record.funcName

        msg = '%s %5s %5s %35s:%-4s %s' % (self.formatTime(record, '%m/%d %H:%M:%S'), record.levelname,
                                          record.process, location, record.lineno, record.msg)          #定義輸出訊息格式
        record.msg = msg
        return super(MyLogFormatter, self).format(record)                #繼承父類



    #日誌輪轉
def getlogger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    log_dir = 'logs'
    if not os.path.isdir(log_dir):                  #檢查檔案是否存在
        os.makedirs(log_dir, exist_ok=True)         #不存在創建



    # create console handler and set level to debug
    #創建控制台處理程序並設置調試級別
    ch1 = logging.StreamHandler()
    ch2 = TimedRotatingFileHandler(f"{log_dir}/log.txt", when="H", interval=1, backupCount=48) #日誌輪轉設定

    ch1.setLevel(logging.DEBUG)
    ch2.setLevel(logging.DEBUG)
    # create formatter
    formatter = MyLogFormatter()

    # add formatter to ch
    ch1.setFormatter(formatter)
    ch2.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch1)
    logger.addHandler(ch2)
    return logger


logger = getlogger()

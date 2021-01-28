# Fix qt import error                    #修正qt 引進的異常
# Include this file before import PyQt5 ;在引進pyqt5之前使用這個檔案
import os
import sys
import logging

    #来获取当前正在运行的应用程序的路径
def _append_run_path():                            #定義方法增加運行路徑
    if getattr(sys, 'frozen', False):              #獲得屬性frozen凍結# 判断sys中是否存在frozen变量
        pathlist = []                              #定義pathlist為一個序列

        # If the application is run as a bundle, the pyInstaller bootloader
        #如果應用程序是作為捆綁軟件運行的,pyInstaller(打包)引導程序

        # extends the sys module by a flag frozen=True and sets the app
        #通過旗標擴展sys模塊frozen=True 和設定app應用程序

        # path into variable _MEIPASS'.
        #路徑引進變量_MEIPASS
        pathlist.append(sys._MEIPASS)            #Pyinstaller 可以将资源文件一起打包到exe中，当exe在运行时，会生成一个临时文件夹，程序可通过sys._MEIPASS访问临时文件夹中的资源

        # the application exe path
        #獲得打包成應用程序的路徑;當正常的Python腳本運行時，sys.executable是已執行程序的路徑表;用來鎖定文件
        _main_app_path = os.path.dirname(sys.executable)

        #獲得的路徑表增加在pathlist序列裡
        pathlist.append(_main_app_path)

        # append to system path enviroment

        os.environ["PATH"] += os.pathsep + os.pathsep.join(pathlist)



_append_run_path()
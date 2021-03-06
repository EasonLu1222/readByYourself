import os
import sys
import json
import time
import re
import pickle
import pandas as pd
import pyautogui as pag
import fix_qt_import_error                      #用來設定打包時的臨時路徑，並設定到環境變數裡(臨時設定程序關閉既消失)，用來修正qt打包時的異常
from datetime import datetime
from operator import itemgetter
from pathlib import Path
from PyQt5 import QtCore
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QPainterPath
from PyQt5.QtCore import (QSettings, Qt, QTranslator, QCoreApplication,
                          pyqtSignal as QSignal)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QErrorMessage, QHBoxLayout,
                             QTableWidgetItem, QLabel, QTableView, QAbstractItemView,
                             QWidget, QCheckBox, QPushButton, QMessageBox)

from tasks.task_mic_block_test import sent_final_test_result_to_fixture
from view.pwd_dialog import PwdDialog
from view.barcode_dialog import BarcodeDialog
from view.loading_dialog import LoadingDialog
from core import (Task, ProcessListener, BaseVisaListener,
                  enter_prompt, enter_prompt_simu, Actions,
                 )
from serials import se, get_devices_df, BaseSerialListener
from instrument import update_serial
from utils import resource_path, QssTools, clear_tmp_folders
from ui.main import Ui_MainWindow

# for very begin before Task initialization
from iqxel import generate_jsonfile

from sfc import send_result_to_sfc, gen_ks_sfc_csv, gen_ks_sfc_csv_filename, move_ks_sfc_csv
from upgrade import (
    wait_for_process_end_if_downloading, delete_trigger_file, create_shortcut,
    delete_app_exe, MyDialog, DownloadThread,
)

#config.py 讀取jsonfile 檔裡面的 station_json 工站 STATION定義;    config.py讀取 PRODUCT定義產品類別
from config import (
    station_json, LANG_LIST, KLIPPEL_PROJECT,
    STATION, LOCAL_APP_PATH, FTP_DIR, TRIGGER_PREFIX,
    OFFICE_FTP_IP, FACTORY_FTP_IP, FTP_IP_USED, PRODUCT
)
from tools.auto_update.version_checker import VersionChecker
from mylogger import logger


class UsbPowerSensor(): comports_pws = QSignal(list)              #定義物件


pag.FAILSAFE = False    # Tell PyAutoGUI not to throw exception when the cursor is moved to the corner of screen

    #處理visa通訊相關
class VisaListener(BaseVisaListener, UsbPowerSensor):              #監聽visa，和確認usbpower
    def __init__(self, *args, **kwargs):                           #建構，定義屬性，實體化物件
        devices = kwargs.pop('devices')                            #使用.pop會刪除dic中的值
        super(VisaListener, self).__init__(*args, **kwargs)        #繼承父類屬性
        self.is_reading = False                                    #設定旗標是否正在讀為False
        self.is_instrument_ready = False                           #設定旗標儀器是否正在讀取False
        self.set_devices(devices)                                  #呼叫def device 設定device


    def set_devices(self, devices):                                #定義set_devices，裡面有一個屬性devices
        self.devices = devices                                     #self.device = device 設定屬性值
        for k,v in devices.items():                                #抓出device裡面的item，由for迴圈開始例遍
            setattr(self, f'ports_{k}', [])                        #setattr() 函数对应函数 getattr()，用于设置属性值，该属性不一定是存在的。f'ports_{k}'字串格式化，數值為[]，


class ComportDUT(): comports_dut = QSignal(list)                   #定義物件ComportDUT()
class ComportPWR(): comports_pwr = QSignal(list)                   #定義物件ComportDUT()
class ComportDMM(): comports_dmm = QSignal(list)                   #定義物件ComportDUT()
class ComportELD(): comports_eld = QSignal(list)                   #定義物件ComportDUT()


    #處理serial通訊相關
class SerialListener(BaseSerialListener,                                    #宣告一個物件，引進屬性(用來監聽串列埠)
                     ComportDUT, ComportPWR, ComportDMM, ComportELD):
    def __init__(self, *args, **kwargs):                                    #建構，定義屬性，實體化物件
        devices = kwargs.pop('devices')                                     #定義devices = kwargs為字符變數使用.pop會刪除dic中的值;讀取由config.py設定工站查詢json參數
        #print(devices)                                                      #{'dut': {'name': 'ftdi', 'num': 1, 'sn': ['AQ5IBALNA']}}
        super(SerialListener, self).__init__(*args, **kwargs)               #繼承父類屬性
        self.is_reading = False                                             #設定旗標是否正在讀為False
        self.is_instrument_ready = False                                    #設定旗標儀器是否正在讀取False
        self.set_devices(devices)                                           #呼叫def device ;將devices送到def set_devices


    def set_devices(self, devices):                                         #定義定義方法set_devices，裡面有一個屬性devices
        self.devices = devices                                              #self.device = device 設定屬性值
        for k,v in devices.items():                                         #抓出device裡面的item，由for迴圈開始例遍;濾出json裡面的item;
            setattr(self, f'ports_{k}', [])                                 #設定屬性值ports_dut []，ports_pwr []，ports_dmm []
            #print(f'ports_{k}', [])


    #讀取config來設定1.什麼產品 2.哪個工站 3.工站設定 4.是否進入工程模式
class MySettings():
    lang_list = LANG_LIST

    def __init__(self, dut_num):                                           #結構:引入屬性dut_num，self實體化
        self.settings = QSettings('FAB', f'SAP{PRODUCT}')                  #QSettings 是一個 PyQt5 提供的元件，專門用於儲存參數，可於下次讀取的時候自動載入之前設定的參數。這樣一來，我們就不用額外將參數寫成檔案了。
        self.dut_num = dut_num                                             #設定屬性
        self.update()                                                      #呼叫更新方法

    def get(self, key, default, key_type):                                 #定義get 方法 引進key, default, key_type屬性
        return self.settings.value(key, default, key_type)                 #回傳取得 self.settings = QSettings('FAB', f'SAP{PRODUCT}') 的key, default, key_type值

    def set(self, key, value):                                             #定義set 方法 引進  key, value 屬性
        self.settings.setValue(key, value)                                 #設定self.settings = QSettings('FAB', f'SAP{PRODUCT}') 的key, value值
        self.update()                                                      #呼叫更新方法

    def update(self):                                                      #定義update方法
        for i in range(1, self.dut_num+1):                                 #i由1開始最大到self.dut_num+1
            setattr(self, f'is_fx{i}_checked',                             #設定屬性:object為self = update ,name=f'is_fx{i}_checked' ,value = self.get(f'fixture_{i}', False, bool)，
                self.get(f'fixture_{i}', False, bool))                     #get的屬性為key = f'fixture_{i}', default=False, key_type=bool，設定布林值為False

        self.ccode_index = self.get('ccode_index', 0, int)                 #獲取整數值為，設定國家

        self.lang_index = self.get('lang_index', 0, int)                   #獲取整數值為，設定語系

        self.is_eng_mode_on = self.get('is_eng_mode_on', False, bool)      #獲取布林值為(初始化後更新is_eng_mode_on)


        #處理加載圖片影像
class Label(QLabel):
    def __init__(self, *args, antialiasing=True, **kwargs):                #結構:引進屬性
        super(Label, self).__init__(*args, **kwargs)                       #繼承父類承接屬性值
        self.Antialiasing = antialiasing                                   #設定最小size
        self.setMinimumSize(200, 100)                                      #設定屬性
        self.radius = 100                                                  #設定屬性
        self.target = QPixmap(self.size())                                 #設定label大小和控件一样
        self.target.fill(Qt.transparent)                                   #填充背景为透明

        # 加载图片并缩放和控件一样大
        # Qt.KeepAspectRatioByExpandingQ表示在给定矩形之外，将尺寸缩放为尽可能小的矩形，从而保持纵横比。
        # Qt.SmoothTransformationscaled 是QT自帶的影象縮放函式，Qt::SmoothTransformation可以使縮放效果更佳

        p = QPixmap(resource_path(f"./images/main_window_logo_{PRODUCT}.png")).scaled(
            170, 1, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        #使用QPainter類繪圖及坐標變換示例
        painter = QPainter(self.target)
        if self.Antialiasing:
            painter.setRenderHint(QPainter.Antialiasing, True)                #抗锯齿
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)     #提高圖像分辨率
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)       #使用pixmap平滑演算法，雙線性插值法
        painter.drawPixmap(0, 0, p)                                           #匯背景圖
        self.setPixmap(self.target)                                           #設定顯示圖片


class MyWindow(QMainWindow, Ui_MainWindow):                                      #宣告一個物件為MyWindow ，引進屬性定義
    show_animation_dialog = QSignal(bool)                                        #設定訊號槽為布林
    msg_dialog_signal = QSignal(str)                                             #設定訊號槽為字串
    show_mac_address_signal = QSignal(int,int)                                   #設定訊號槽為整數

    def __init__(self, app, task, *args):                                        #定義物件結構:引進屬性 app, task, *args ，self實體化
        super(QMainWindow, self).__init__(*args)                                 #繼承父類屬性與方法
        self.app = app                                                           #設定屬性app 在結尾=Application()
        self.desktop = app.desktop()                                             #QApplication :: desktop（）函式用於獲取QDesktopWidget的例項。用來獲取螢幕解析
        self.setupUi(self)                                                       #MainWindow中的ui就是用布局类初始化。之后在构造函数需要使用ui->setupUI(this);就可以将Ui::MainWindow中的布局应用到本地的MainWindow。
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)         #隱藏標題欄
        self.setWindowFlags(Qt.FramelessWindowHint)                              #Qt::FramelessWindowHint用来产生一个没有边框的窗口
        self.simulation = False                                                  #模擬鍵盤關閉

        clear_tmp_folders()                                                       #from utils import resource_path, QssTools, clear_tmp_folders 引用
        self.pwd_dialog = PwdDialog(self)                                         #from view.pwd_dialog import PwdDialog 引用;用來呼叫工程模式對話框
        self.barcode_dialog = BarcodeDialog(self, STATION)                        #from view.barcode_dialog import BarcodeDialog 引用;用來呼叫BarcodeDialog對話框
        self.barcodes = []                                                        #列表[]
        self.port_barcodes = {}     # E.g. {'COM1': '1234', 'COM2': '5678'}       #字典{}
        self.can_upload = {}    # E.g. {'1': False}, the key is dut_idx(0,1,...), value tells if this data should upload to SFC #值表明該數據是否應上傳到SFC 字典{}

        self.set_task(task)                                                       #呼叫下方def set_task設定任務
        self.set_appearance()                                                     #呼叫下方def set_appearance
        self.settings = MySettings(dut_num=self.task.dut_num)                     #使用上方class MySettings;MySetting在實例化的時候，會去task拿dut_num，Task定義在core.py裡，dut_num是Task去json檔裡面拿的
        self.make_checkboxes()                                                    #呼叫下方def make_checkboxes(layout checkBox)

        self.cCodeSelectMenu.setCurrentIndex(self.settings.ccode_index)           #使用介面選擇menu(顯示國家)
        self.langSelectMenu.setCurrentIndex(self.settings.lang_index)             #使用介面選擇menu(語言選擇碼)
        self.checkBoxEngMode.setChecked(self.settings.is_eng_mode_on)             #介面使用是否需要Engineering mode(進入工程模式)

        self.eng_mode_state_changed(self.settings.is_eng_mode_on)                 #呼叫設定def eng_mode_state_changed(呼叫方法檢查工程模式狀態)程式初始時檢查狀態;有檢查工程模式對話框狀態


        #用來確認serial_devices是否有設定
        if 'dut' in self.task.serial_devices:                                     #確認#['cygnal_cp2102', 'prolific', 'ftdi', 'gw_powersupply', 'gw_dmm', 'gw_eloader']讀取devices.json
            #print(self.task.serial_devices)
            self._comports_dut = dict.fromkeys(range(self.task.dut_num), None)    # E.g. {0: None, 1: None}   #fromkeys()方法從序列鍵和值設置為value來創建一個新的字典(看有幾組內容)然後列表字典
            #print(self.task.dut_num)                                              #為幾組
        else:

            #如果"dut"裡的self.task.serial_devices任務沒有找到創建空的
            self._comports_dut = {}
        #用來創建空的陣列
        self._comports_pwr = []
        self._comports_dmm = []
        self._comports_eld = []
        self._comports_pws = []

        #用來確認erial_instruments是否有設定json檔裡;如果有載入instrument裡定義的資料
        if self.task.serial_instruments:
            #print(self.task.serial_instruments)
            update_serial(self.task.serial_instruments, 'gw_powersupply', self._comports_pwr)   #在_comports_pwr裡更新內容物
            update_serial(self.task.serial_instruments, 'gw_dmm', self._comports_dmm)           #在_comports_dmm裡更新內容物
            update_serial(self.task.serial_instruments, 'gw_eloader', self._comports_eld)       #在_comports_eld裡更新內容物




        self.dut_layout = []                                                                    #新增dut_layout為
        colors = ['#edd'] * self.task.dut_num                                                   #由json得到self.task.dut_num數量去乘;色彩總共有 #000000 ~ #FFFFFF;#edd = #eedddd;16進制表示法
        #print(self.task.dut_num )
        for i in range(self.task.dut_num):                                                      #由for迴圈例遍到dut_num設定數量
            #print(self.task.dut_num)
            c = QWidget()                                                                       #QWidget 可為單一視窗也可嵌入到其他視窗內
            c.setStyleSheet(f'background-color:{colors[i]};')                                   #設定QWidget設置樣式
            #print(colors[i])
            layout = QHBoxLayout(c)                                                             #人機介面上有設定QHBoxLayout是一個類;將c = QWidget 放在QHBoxLayout裡，且等於layout
            self.hboxPorts.addWidget(c)                                                         #增加物件看有幾個c
            self.dut_layout.append(layout)                                                      #將layout附加在dut_layout裡面

        self.setsignal()                                                                        #呼叫使用def setsignal (設定)

        #  self.ser_listener = SerialListener(devices=self.task.devices)
        self.ser_listener = SerialListener(devices=self.task.serial_devices)                    #串列埠監聽
        self.ser_listener.comports_dut.connect(self.ser_update)                                 #呼叫ser_update更新各站別資訊
        self.ser_listener.comports_pwr.connect(self.pwr_update)                                 #呼叫pwr_update更新各站別資訊
        self.ser_listener.comports_dmm.connect(self.dmm_update)                                 #呼叫dmm_update更新各站別資訊
        self.ser_listener.comports_eld.connect(self.eld_update)                                 #呼叫eld_update更新各站別資訊
        self.ser_listener.if_all_ready.connect(self.instrument_ready)                           #呼叫旗標instrument_ready(用來確認所有站別是否在工作)
        self.ser_listener.if_actions_ready.connect(self.actions_ready)                          #呼叫旗標actions_ready
        self.ser_listener.start()

        self.serial_ready = False                                                               #旗標serial_ready沒有在忙碌

        if self.task.visa_devices:
            self.visa_listener = VisaListener(devices=self.task.visa_devices)
            self.visa_listener.comports_pws.connect(self.pws_update)
            self.visa_listener.if_all_ready.connect(self.visa_instrument_ready)
            self.visa_listener.start()
            self.visa_ready = False                                          #旗標visa_ready有在忙碌
        else:
            self.visa_ready = True

        self.proc_listener = ProcessListener()
        self.proc_listener.process_results.connect(self.recieve_power)
        self.power_recieved = False

        self.pushButton.setEnabled(False)

        self.power_process = {}
        self.power_results = {}

        self.on_ccode_changed(self.settings.ccode_index)
        self.on_lang_changed(self.settings.lang_index)

        self.col_dut_start = len(self.task.header())
        self.table_hidden_row()
        self.taskdone_first = False
        self.port_autodecting = False

        self.show_animation_dialog.connect(self.toggle_loading_dialog)
        self.msg_dialog_signal.connect(self.show_message_dialog)
        self.show_mac_address_signal.connect(self.show_mac_address_info)
        app.setOverrideCursor(Qt.ArrowCursor)
        self.render_port_plot()
        self.showMaximized()
        self.setGeometry(self.desktop.availableGeometry())
        self.loading_dialog = LoadingDialog(self)
        self.set_togglebutton()
        self.version_checker = VersionChecker()
        self.version_checker.version_checked.connect(self.handle_update)
        self.can_download = False
        self.download_state_check()
        self.my = pag.getActiveWindow()

    def download_state_check(self):
        logger.info('download_state_check')
        if wait_for_process_end_if_downloading():
            logger.info('============= path1 clean job at reopening app ==============')
            delete_trigger_file()
            delete_app_exe()
        self.can_download = True

    def keyPressEvent(self, event):
        if self.can_download and event.key() == Qt.Key_F2:
            logger.info('f2 pressed')
            self.version_checker.start()

    def quit(self):
        logger.info('MyWindow quit')
        time.sleep(3)
        self.close()

    def handle_update(self, need_update):
        # Remove all files in LOCAL_APP_PATH with file name start with "sap109-testing-upgrade"
        for p in Path(f"{LOCAL_APP_PATH}").glob(f"sap{PRODUCT}-testing-upgrade*"):
            p.unlink()
        if need_update:
            quit_msg = "An update is available, do you want to download it now?"
            reply = QMessageBox.question(self, 'Message', quit_msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                logger.info('============= path3 check version yes download ==============')
                self.dialog = MyDialog(self)
                self.dialog.setModal(True)
                self.thread = DownloadThread()
                self.thread.dialog = self.dialog
                self.thread.progress_update.connect(self.dialog.update_progress)
                self.thread.data_downloaded.connect(self.dialog.on_data_ready)
                self.thread.quit.connect(self.quit)
                self.thread.start()
                self.dialog.show()
                with open(f'{LOCAL_APP_PATH}/sap{PRODUCT}-testing-upgrade-starting-{os.getpid()}', 'w'):
                    pass
        else:
            logger.info('no need to update')

    def set_togglebutton(self):
        self.pushButton2 = QPushButton(self.container)
        self.pushButton2.setText('enable fetch')
        self.pushButton2.setObjectName("pushButton2")
        self.verticalLayout.addWidget(self.pushButton2)
        self.pushButton2.setCheckable(True)
        self.pushButton2.toggled.connect(self.btn2_toggled)
        self.pushButton2.setVisible(False)

    def btn2_toggled(self, state):
        if state:
            self.pushButton2.setText('fetching...')
            self.btn_clicked()
        else:
            self.pushButton2.setText('enable fetch')

    def set_layout_visible(self, layout, is_visible):
        for i in range(layout.count()):
            each_widget = layout.itemAt(i).widget()
            print(each_widget)
            if is_visible:
                each_widget.show()
            else:
                if each_widget:
                    each_widget.hide()


        #因應站別不同設計增加checkBox
    def make_checkboxes(self):                                                   #定義方法make_checkboxes
        self.checkboxes = []                                                     #設定self.checkboxes = [] 為列表
        for i in range(1, self.task.dut_num+1):                                  #由1開始到self.task.dut_num+1停止
            cbox = QCheckBox(self.container)                                     #設定QCheckBox的容器為cbox，為一個類
            self.checkboxes.append(cbox)                                         #checkboxes附加在cbox裡
            self.horizontalLayout.addWidget(cbox)                                #每個checkbox，水平對齊，
            cbox.setChecked(getattr(self.settings, f'is_fx{i}_checked'))         #設定checkbox有幾個
            cbox.setText(f'{self.cbox_text_translate}#{i}')                      #設定checkboxText顯示依照順序
            if STATION == 'MainBoard':                                           #station = MainBoard
                cbox.setChecked(True)                                            #設定為被點選
                cbox.setDisabled(True)                                           #設定被反白

    def get_checkboxes_status(self):
        status_all = [self.checkboxes[i].isChecked() for i in range(self.task.dut_num)]
        return status_all

    @property
    def logfile(self):
        now = datetime.now()
        y, m, d = now.year, now.month, now.day
        path = f'logs/{y}_{m:02d}_{d:02d}.csv'
        if not os.path.isfile(path):
            with open(path, 'w') as f:
                f.write('')
        return path

    def dummy_com(self, coms):
        self._comports_dut = coms
        self.instrument_ready(True)

    def clean_power(self):
        logger.debug('clean_power start')
        # Prevent from last crash and power supply not closed normally
        for power in self.task.instruments['gw_powersupply']:
            if not power.is_open:
                power.open_com()
            if power.ser:
                power.off()
                power.close_com()
        logger.debug('clean_power end')

    def table_hidden_row(self):
        self.rowlabel_old_new = old_new = {}
        count = 0
        for i, each in enumerate(self.task.mylist):
            is_hidden = each[4]
            if not is_hidden: count += 1
            self.table_view.setRowHidden(i, is_hidden)
            old_new[i] = count
        old_new[len(old_new)] = count + 1
        self.table_view.setVerticalHeaderLabels(str(e) for e in old_new.values())

    def recieve_power(self, process_results):
        logger.debug(f'recieve_power->process_results: {process_results}')
        self.proc_listener.stop()
        self.power_results = process_results

        with open(resource_path('power_results'), 'w+') as f:
            f.write(json.dumps(process_results))
        logger.debug('recieve_power write power_results')

        self.power_recieved = True
        if self.taskdone_first:
            self.taskdone('tasks done')

        #建立table_view task
    def set_task(self, task):                                                 #定義方法為set_task(設定任務)，引進屬性
        self.task = task                                                      #設定屬性
        self.task.window = self                                               #設定屬性
        self.task_results = []                                                #設定屬性為列表[]
        self.table_view.set_data(self.task.mylist, self.task.header_ext())    #設定ui介面的table_view 設定表頭
        self.table_view.setSelectionBehavior(QTableView.SelectRows)           #單擊某個項目時,將選擇整個行


        #介面狀態顯示
    def set_appearance(self):                                                 #定義方法set_appearance 顯示
        self.logo = Label(self.container, antialiasing=True)                  #定義屬性引用class 物件=self.logo
        self.logo.setText("")                                                 #設定為空字串
        self.logo.setObjectName("logo")                                       #設定物件名子為logo
        self.horizontalLayout_2.addWidget(self.logo)
        widths = self.task.appearance['columns_width']
        for col in self.task.appearance['columns_hidden']:
            self.table_view.setColumnHidden(col, True)                                    #設定table_view欄位隱藏
        for idx, w in zip(range(len(widths)), widths):
            self.table_view.setColumnWidth(idx, w)                                        #設定欄位寬度
        self.table_view.setStyleSheet('font: 16pt Segoe UI')                              #設置樣式表
        self.table_view.setSpan(self.task.len(), 0, 1, len(self.task.header()))           #設置表格單元的跨度為（row，column），以通過（指定的行和列的數量rowSpanCount，columnSpanCount)
        self.table_view.setItem(self.task.len(), 0, QTableWidgetItem(self.summary_text))  #新增表項
        for obj in [self, self.table_view.horizontalHeader()]:
            QssTools.set_qss_to_obj(obj)                                                  #from utils import resource_path, QssTools, clear_tmp_folders 引用
        lb1 = QLabel(f'Program version: {getattr(thismodule, "version")}')                #設定text顯示
        lb2 = QLabel(f'Station version: {self.task.base["version"]}')                     #設定text顯示
        lb1.setObjectName('lb1')                                                          #設定物件名子
        lb2.setObjectName('lb2')                                                          #設定物件名子

        #設定1.增加statusbar 2.字體居中對齊 3.設定背景顏色字體顏色字形
        for lb in [lb1, lb2]:                                                             #用for例遍做以下設定
            self.statusbar.addWidget(lb, 1)                                               #对象在底部保留一个水平条作为status bar 。 它用于显示永久或上下文状态信息。

            lb.setAlignment(QtCore.Qt.AlignCenter)                                        #設定字體居中對其

            #設定背景顏色，自行顏色(白色)，字體
            lb.setStyleSheet("QLabel#%s {background-color: #444; color: white;"
                             "font-weight: bold}" % lb.objectName())

    def poweron(self, power):
        logger.debug('poweron start')
        if not power.is_open:
            power.open_com()
            power.on()

    def poweroff(self, power):
        logger.debug('poweroff start')
        if power.ser:
            power.off()
            power.close_com()

    def clearlayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def pwr_update(self, comports):
        logger.debug(f'pwr_update {comports}')
        self._comports_pwr = comports
        update_serial(self.task.instruments, 'gw_powersupply', comports)
        self.render_port_plot()

    def dmm_update(self, comports):
        logger.debug(f'dmm_update {comports}')
        self._comports_dmm = comports
        update_serial(self.task.instruments, 'gw_dmm', comports)
        self.render_port_plot()

    def eld_update(self, comports):
        logger.debug(f'eld_update {comports}')
        self._comports_eld = comports
        update_serial(self.task.instruments, 'gw_eloader', comports)
        self.render_port_plot()

    def pws_update(self, comports):
        logger.debug(f'pws_update {comports}')
        self._comports_pws = comports
        update_serial(self.task.instruments, 'ks_powersensor', comports)
        self.render_port_plot()

    def ser_update(self, comports):                         #更新服務
        logger.debug(f'ser_update {comports}')              #更新資訊

        #  dut_name, sn_numbers = itemgetter('name', 'sn')(self.task.devices['dut'])
        dut_name, sn_numbers = itemgetter('name', 'sn')(self.task.serial_devices['dut'])
        df = get_devices_df()

        if sn_numbers:
            assert len(sn_numbers) == self.task.dut_num
            if len(df)>0:
                for dut_i, sn in zip(self._comports_dut, sn_numbers):
                    df_ = df[df.sn==sn]
                    comport = df_.iat[0,0] if len(df_)==1 else None
                    self._comports_dut[dut_i] = comport
            else:
                self._comports_dut = dict.fromkeys(range(self.task.dut_num), None)
        else:
            logger.info('dut does not have sn number')
            dict_to_nonempty_list = lambda dict_: list(filter(lambda x:x, list(dict_.values())))
            list_ = dict_to_nonempty_list(self._comports_dut)
            if len(comports) > len(list_):
                list_.extend(comports)
                x = list(dict.fromkeys(list_))
                self._comports_dut = dict(zip(range(len(x)), x))
            else:
                self._comports_dut = dict(zip(range(len(comports)), comports))

        self.barcodes = []
        for dut_i, port in self._comports_dut.items():
            if port:
                self.port_barcodes[port] = None

        logger.debug(self._comports_dut)
        self.render_port_plot()

    def render_port_plot(self):
        logger.debug(f'render_port_plot')
        comports_map = {
            'gw_powersupply': self._comports_pwr,
            'gw_dmm': self._comports_dmm,
            'gw_eloader': self._comports_eld,
            'ks_powersensor': self._comports_pws,
        }

        for i, e in enumerate(self.dut_layout, 1):
            self.clearlayout(e)
            e.addWidget(QLabel(f'#{i}'))

        lb_text = 'DUT'
        for i, port in self._comports_dut.items():
            lb_port = QLabel(lb_text)
            lb_port.setProperty('state', 'default')
            QssTools.set_qss_to_obj(lb_port)

            self.dut_layout[i].addWidget(lb_port)
            if port:
                lb_port.setText(f'{lb_text}|{port}')
                lb_port.setProperty('state', 'dut_detected')
                QssTools.set_qss_to_obj(lb_port)

        for name, items in self.task.instruments.items():
            each_instruments = self.task.instruments[name]
            for i, e in enumerate(each_instruments):
                lb_text = f'{e.__class__.__name__}'
                lb_port = QLabel(lb_text)
                lb_port.setProperty('state', 'default')
                QssTools.set_qss_to_obj(lb_port)
                self.dut_layout[i].addWidget(lb_port)

                if e.interface=='serial':
                    logger.info(f'(SERIAL!!!)[inst: {e.NAME}] [{e}] [index: {e.index}] [{i}] [{e.com}]')
                    if e.com in comports_map[name]:
                        lb_port.setText(f'{lb_text}|{e.com}')
                        lb_port.setProperty('state', f'{name}_detected')
                        QssTools.set_qss_to_obj(lb_port)

                elif e.interface=='visa':
                    logger.info(f'(VISA!!!!)[inst: {e.NAME}] [{e}] [index: {e.index}] [{i}]')
                    if comports_map[name]:
                        lb_port.setText(f'{lb_text}|{e.com}')
                        lb_port.setProperty('state', f'{name}_detected')
                        QssTools.set_qss_to_obj(lb_port)

        for i in range(self.task.dut_num):
            self.dut_layout[i].addStretch()

    def visa_instrument_ready(self, ready):
        logger.debug('visa_instrument_ready start')
        if ready:
            self.visa_ready = True
            logger.debug('VISA READY')
        else:
            self.visa_ready = False
            self.pushButton.setEnabled(False)
            logger.debug('VISA NOT READY')

        if self.serial_ready and self.visa_ready:
            logger.debug('===READY===')
            self.pushButton.setEnabled(True)
            self.actions.action_signal.emit('prepare')

    def instrument_ready(self, ready):
        logger.debug('instrument_ready start')
        if ready:
            logger.debug('SERIAL READY!')
            self.serial_ready = True
            self.clean_power()

            # order: power1,power2, dmm1
            if self.task.serial_instruments:
                instruments_to_dump = sum(self.task.serial_instruments.values(), [])
                with open(resource_path('instruments'), 'wb') as f:
                    pickle.dump(instruments_to_dump, f)
        else:
            self.serial_ready = False
            logger.debug('SERIAL NOT READY!')

        if self.serial_ready and self.visa_ready:
            logger.debug('===READY===')
            self.pushButton.setEnabled(True)
            self.actions.action_signal.emit('prepare')
        else:
            logger.debug('===NOT READY===')
            self.pushButton.setEnabled(False)

    def comports(self):
        comports_as_list = list(filter(lambda x:x, self._comports_dut.values()))
        return comports_as_list

    def get_dut_selected(self):
        return [i for i, x in enumerate(self.get_checkboxes_status()) if x]

    def setsignal(self):                                                                        #設定訊號槽

        #這個部份用來偵測新增的checkBox狀態
        for i, b in enumerate(self.checkboxes, 1):                                              #讀取jsonFile可以確定工站有幾個dut;因此 b 代表checkBox，i代表有幾個
            chk_box_state_changed = lambda state, i=i: self.chk_box_fx_state_changed(state, i)  #利用lambda function定義函式state, i=i: self.chk_box_fx_state_changed(state, i) = chk_box_state_changed
            b.stateChanged.connect(chk_box_state_changed)                                       #b已經代表為checkBox，所以觸發後會引進chk_box_state_changed

        self.cCodeSelectMenu.currentIndexChanged.connect(self.on_ccode_changed)                 #偵測人機介面改變國碼
        self.langSelectMenu.currentIndexChanged.connect(self.on_lang_changed)                   #偵測人機介面改變語言
        self.checkBoxEngMode.stateChanged.connect(self.eng_mode_state_changed)                  #偵測人機介面是否啟動工程模式
        self.pwd_dialog.dialog_close.connect(self.on_pwd_dialog_close)                          #偵測人機介面關閉工程模式對化框
        self.barcode_dialog.barcode_entered.connect(self.on_barcode_entered)                    #偵測人機介面是否進入barcode
        self.barcode_dialog.barcode_dialog_closed.connect(self.on_barcode_dialog_closed)        #偵測人機介面關閉barcode對話框
        self.pushButton.clicked.connect(self.btn_clicked)                                       #偵測人機介面pushButton
        self.task.task_result.connect(self.taskrun)                                             #
        self.task.task_each.connect(self.taskeach)
        self.task.message.connect(self.taskdone)
        se.serial_msg.connect(self.printterm1)                                                 #serial設定回傳連結
        self.task.printterm_msg.connect(self.printterm2)
        self.task.serial_ok.connect(self.serial_ok)
        self.task.adb_ok.connect(self.adb_ok)
        self.task.general_ok.connect(self.general_ok)
        self.task.trigger_snk.connect(self.soundcheck_handle)
        self.task.trigger_klippel.connect(self.klippel_handle)
        self.task.trigger_usbburntool.connect(self.usbburntool_handle)

    def soundcheck_handle(self, message):
        wins = pag.getWindowsWithTitle('soundcheck')
        win = [e for e in wins if '-' in e.title][0]
        my = pag.getActiveWindow()
        win.activate()
        time.sleep(1)
        pag.hotkey('f2')
        time.sleep(1)
        my.activate()

    def klippel_handle(self, asn):
        print('klippel_handle', 'asn', asn)
        win = pag.getWindowsWithTitle(KLIPPEL_PROJECT)[0]
        my = pag.getActiveWindow()
        time.sleep(1)
        win.maximize()
        win.activate()
        time.sleep(1)
        pag.click(127, 80)
        pag.click(127, 80)
        pag.typewrite(f'{asn}')
        pag.press('enter')
        time.sleep(1)
        pag.press('enter')
        win.minimize()
        my.activate()

    def usbburntool_handle(self, message):
        print('usb_burning_tool start/stop')
        win = pag.getWindowsWithTitle('USB_Burning_Tool')[0]
        win.maximize()
        win.activate()
        time.sleep(1)
        pag.click(1065, 95) # press start/stop button

        if message=='start':
            print('usb_burning_tool start')
        elif message == 'stop':
            print('usb_burning_tool stop')
            self.my.activate()
        time.sleep(1)

    def general_ok(self, ok):
        if not ok:
            self.pushButton.setEnabled(True)

    def serial_ok(self, ok):
        if ok:
            logger.debug('serial is ok!!!!')
        else:
            self.pushButton.setEnabled(True)
            logger.debug('serial is not ok!!!')

    def adb_ok(self, ok):
        if not ok:
            self.pushButton.setEnabled(True)

    def show_message_dialog(self, msg):
        infoBox = QMessageBox()
        infoBox.setIcon(QMessageBox.Information)
        infoBox.setText(msg)
        if STATION == 'SA':
            infoBox.setWindowTitle("Warning")
        infoBox.exec_()

    def printterm1(self, port_msg):
        port, msg = port_msg
        msg = '[port: %s]%s' % (port, msg)
        self.edit1.appendPlainText(msg)

    def printterm2(self, msg):
        self.edit2.appendPlainText(msg)

    def taskeach(self, row_rlen):
        self.table_view.clearSelection()
        row, rowlen = row_rlen
        self.table_view.setFocusPolicy(Qt.StrongFocus)
        self.table_view.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table_view.setFocus()
        for i in range(row, row + rowlen):
            self.table_view.selectRow(i)
        self.table_view.setSelectionMode(QAbstractItemView.NoSelection)
        self.table_view.setFocusPolicy(Qt.NoFocus)

    def color_check(self, s):
        if s.startswith('Pass'):
            color = QColor(139, 195, 74)
        elif s.startswith('Fail'):
            color = QColor(255, 87, 34)
        else:
            color = QColor(255, 255, 255)
        return color

    def taskrun(self, result):                                                    #taskrun任務運行當中
        logger.debug(f'taskrun result {result}')
        """
        Set background color of specified table cells to indicate pass/fail

        Args:
            result: A dict with the following fields:

                index(int or [int, int]): Row or row range
                idx(int): The (idx)th DUT
                port(str): The port name, used to inference idx
                output(str): 'Pass' or 'Fail'

                e.g. {'index': 0, 'idx': 0, 'port':'COM1', 'output': 'Pass'}
        """
        ret = json.loads(result)
        row = ret['index']

        # The pass/fail result applies for the jth DUT of rows from index[0] to index[1]
        if type(row) == list:
            output = ret['output']
            if type(output) == str:
                output = json.loads(output)
            logger.debug(f'output {output}')
            for i in range(*row):
                for j in self.dut_selected:
                    x = output[i - row[0]][j]
                    self.table_view.setItem(i, self.col_dut_start + j, QTableWidgetItem(x))
                    self.table_view.item(i, self.col_dut_start + j).setBackground(self.color_check(x))

        # The pass/fail result applies for the jth DUT of the specified row
        elif ('port' in ret) or ('idx' in ret):
            output = str(ret['output'])
            if 'port' in ret:
                port = ret['port']
                j = self.comports().index(port)
            elif 'idx' in ret:
                j = ret['idx']
            self.table_view.setItem(row, self.col_dut_start + j, QTableWidgetItem(output))
            self.table_view.item(row, self.col_dut_start + j).setBackground(self.color_check(output))

        # The pass/fail result applies for all selected DUT of the specified row
        else:
            output = ret['output']
            for j in self.dut_selected:
                self.table_view.setItem(row, self.col_dut_start + j, QTableWidgetItem(output))
                self.table_view.item(row, self.col_dut_start + j).setBackground(self.color_check(output))

    def taskdone(self, message):
        logger.debug('taskdone start !')
        self.taskdone_first = True
        self.table_view.setSelectionMode(QAbstractItemView.NoSelection)
        msg, t0, t1 = itemgetter('msg', 't0', 't1')(json.loads(message))
        if msg.startswith('tasks done') and self.power_recieved:
            self.pushButton.setEnabled(True)

            self.ser_listener.start()
            if not self.simulation:
                for power in self.task.instruments['gw_powersupply']:
                    if not power.is_open:
                        power.open_com()
                    if power.ser:
                        if STATION != 'WPC':
                            power.off()
                        power.close_com()
            r = self.task.len()
            all_pass = lambda results: all(e.startswith('Pass') for e in results)

            def get_fail_list(series):
                idx = series[series.fillna('').str.startswith('Fail')].index
                d = self.task.df
                dd = d[d.index.isin(idx)]
                items = (dd['group'] + ': ' + dd['item']).values.tolist()
                indexes = [self.rowlabel_old_new[i] for i in idx]
                fail_list = ','.join([ f'#{i}({j})' for i,j in zip(indexes,items)])
                return fail_list

            d = self.task.df
            all_res = []

            dut_num = self.task.dut_num

            sfc_station_id = self.task.sfc_station_id

            csv_filename = gen_ks_sfc_csv_filename(sfc_station_id)

            for j, dut_i in enumerate(self.dut_selected):
                results_ = d[d.hidden == False][d.columns[-dut_num + dut_i]]
                res = 'Pass' if all_pass(results_) else 'Fail'
                fail_list = get_fail_list(d[d.columns[-dut_num+dut_i]])
                logger.debug(f'fail_list {fail_list}')
                self.table_view.setItem(r, self.col_dut_start + dut_i, QTableWidgetItem(res))
                self.table_view.item(r, self.col_dut_start + dut_i).setBackground(self.color_check(res))
                all_res.append(res)

                df = d[d.hidden == False]
                cols1 = (df.group + ': ' + df.item).values.tolist()
                dd = pd.DataFrame(df[[d.columns[-dut_num + dut_i]]].values.T, columns=cols1)

                msn = None
                if self.barcodes:
                    dd.index = [self.barcodes[j]]
                    msn = self.barcodes[j]
                dd.index.name = 'pid'

                cols2_value = {
                    'Test Pass/Fail': res,
                    'Failed Tests': fail_list,
                    'Test Start Time': t0,
                    'Test Stop Time': t1,
                    'index': dut_i+1,
                }

                dd = dd.assign(**cols2_value)[list(cols2_value) + cols1]
                if sfc_station_id:
                    if sfc_station_id in ['MB', 'CT']:
                        gen_ks_sfc_csv(d, csv_filename=csv_filename, station=sfc_station_id, msn=msn, dut_num=dut_num, dut_i=dut_i, result=res)
                    else:
                        if sfc_station_id in ['WP', 'LK'] or self.can_upload[dut_i]:
                            send_result_to_sfc(d, sfc_station_id=sfc_station_id, msn=msn, res=res, dut_num=dut_num, dut_i=dut_i, t0=t0, t1=t1)

                with open(self.logfile, 'a') as f:
                    dd.to_csv(f, mode='a', header=f.tell()==0, sep=',', line_terminator='\n')

            is_all_dut_pass = all(e == 'Pass' for e in all_res)
            if sfc_station_id in ['MS']:
                sent_final_test_result_to_fixture(is_all_dut_pass)

            move_ks_sfc_csv(sfc_station_id, csv_filename)

            self.set_window_color('pass' if is_all_dut_pass else 'fail')
            self.table_view.setFocusPolicy(Qt.NoFocus)
            self.table_view.clearFocus()
            self.table_view.clearSelection()
            self.taskdone_first = False
            self.power_recieved = False

            if os.path.isfile('power_results'):
                os.remove('power_results')
        self.actions.action_signal.emit('after')

    def show_barcode_dialog(self):                                    #顯示條碼對話框
        logger.debug('show_barcode_dialog start')
        status_all = self.get_checkboxes_status()
        num = len(list(filter(lambda x: x == True, status_all)))
        self.barcode_dialog.set_total_barcode(num)
        if num > 0:
            self.barcode_dialog.show()
            self.barcode_dialog.barcodeLineEdit.clear()
        logger.debug('show_barcode_dialog end')

    def reset_port_barcodes(self):
        self.port_barcodes = {}

    def btn_clicked(self):
        logger.debug('\n')
        self.can_upload = {}
        self.barcodes = []
        for dut_i, port in self._comports_dut.items():
            self.can_upload[dut_i] = True
            if port:
                self.port_barcodes[port] = None
        if not any(self.get_checkboxes_status()):
            e_msg = QErrorMessage(self)
            e_msg.showMessage(self.both_fx_not_checked_err)
            return

        self.dut_selected = self.get_dut_selected()
        logger.debug(f'dut_selected {self.dut_selected}')
        for i in range(self.task.len() + 1):
            for j in range(self.task.dut_num):
                self.table_view.setItem(i, self.col_dut_start + j,
                                        QTableWidgetItem(""))

        header = self.task.header_ext()
        for dut_i in range(self.task.dut_num):
            header[-self.task.dut_num + dut_i] = f'#{dut_i+1}'
        self.table_view.setHorizontalHeaderLabels(header)

        self.set_window_color('default')
        if self.task.behaviors['barcode-scan']:
            self.show_barcode_dialog()
        else:
            self.pushButton.setEnabled(False)
            self.ser_listener.stop()

    def actions_ready(self):
        print('actions_ready')
        self.task.start()

    def closeEvent(self, event):
        logger.debug('closeEvent')
        for power in self.task.instruments['gw_powersupply']:
            if power.is_open:
                power.off()
        event.accept()  # let the window close

    def chk_box_fx_state_changed(self, status, idx):                       #或取新增的checkBox狀態
        #print(status)                                                      #獲取 checkBox 狀態;獲取index checkBox
        #print(idx)
        self.settings.set(f'fixture_{idx}', status == Qt.Checked)          #這裡用轉換紀錄True or False ststus狀態;
        #print(status == Qt.Checked)
        getattr(self.settings ,f'is_fx{idx}_checked')                      #得到屬性
        print("step2")

    def on_pwd_dialog_close(self, is_eng_mode_on):
        if (not is_eng_mode_on):
            self.checkBoxEngMode.setChecked(False)

    def eng_mode_state_changed(self, status):             #定義方法引進屬性status，引進狀態確認self.checkBoxEngMode.stateChanged.connect(self.eng_mode_state_changed)有勾為1;沒勾為0
        is_on = (status > 0)                              #如果(status>0)=is_on
        self.settings.set("is_eng_mode_on", is_on)        #讀取當下介面切換的狀態並觸發QSetting裡的的is_eng_mode_on;is_on並記錄
        #print(type(status))
        #print(isinstance(status, bool))
        if is_on:
            if not isinstance(status, bool):              #isinstance() 用來判斷是不是bool值;注意if not是反向;所以當為bool值時為不輸出;當不為bool值輸出;checkBox為int，記錄檔為bool
                self.pwd_dialog.show()                    #跳出工程模式對話框
            self.splitter.show()                          #main顯示splitter畫面
            if STATION == 'Download':                     #如果STATION == 'Download'
                self.cCodeSelectMenu.show()               #顯示國家選項
        else:
            self.splitter.hide()                          #隱藏分離器
            self.cCodeSelectMenu.hide()                   #隱藏國家選項

    def on_ccode_changed(self, index):
        self.settings.set("ccode_index", index)

    def on_lang_changed(self, index):
        """
        When language is changed, update UI
        """
        self.settings.set("lang_index", index)
        lang_list = [f'{e}.qm' for e in self.settings.lang_list]
        app = QApplication.instance()
        translator = QTranslator()
        translator.load(resource_path(f"translate/{lang_list[index]}"))
        app.removeTranslator(translator)
        app.installTranslator(translator)
        self.retranslateUi(self)
        self.pwd_dialog.retranslateUi(self.pwd_dialog)
        self.barcode_dialog.retranslateUi(self.barcode_dialog)

    def on_barcode_entered(self, barcode):                              #定義方法為條碼進入引進barcode屬性
        logger.info(f"Received barcode: {barcode}")                     #得到條碼回傳
        self.barcodes.append(barcode)                                   #self.barcodes = [] 為列表;得到barcodes資訊後再增加一個

    def on_barcode_dialog_closed(self):                                 #關閉條碼對話框
        """
        When the barcode(s) are ready, start testing                   #條形碼準備就緒後，開始測試
        """
        # Return the index of Trues. E.g.: [False, True] => [1]

        if STATION in ["WPC", 'AcousticListen', 'Leak', 'BootCheck']:  #這些工站時pass
            pass
        else:
            infoBox = QMessageBox()  #Message Box that doesn't run
            infoBox.setIcon(QMessageBox.Information)
            infoBox.setText("将待测物放回治具后，按回车键开始测试")
            infoBox.exec_()

        header = self.task.header_ext()
        for j, dut_i in enumerate(self.dut_selected):
            header[-self.task.dut_num + dut_i] = f'#{dut_i+1} - {self.barcodes[j]}'
            if self._comports_dut:
                port = self._comports_dut[dut_i]
                self.port_barcodes[port] = self.barcodes[j]
        self.table_view.setHorizontalHeaderLabels(header)
        self.pushButton.setEnabled(False)
        self.ser_listener.stop()

    def toggle_loading_dialog(self, is_on=False):
        if is_on:
            self.loading_dialog.show()
        else:
            self.loading_dialog.done(1)

    def set_window_color(self, state="default"):
        '''
        Set the window background color based on the test result
        Args:
            state (str): "pass", "fail" or "default"
        '''
        try:
            color = {
                "pass": "#8BC34A",
                "fail": "#FF5722",
                "default": "#ECECEC"
            }[state]
        except KeyError as e:
            color = "#ECECEC"
        self.setStyleSheet(
            f"QWidget#centralwidget {{background-color:{color} }}")

    def retranslateUi(self, MyWindow):
        super().retranslateUi(self)
        _translate = QCoreApplication.translate
        self.cbox_text_translate = _translate('MainWindow', 'DUT')
        self.summary_text = _translate("MainWindow", "Summary")
        self.both_fx_not_checked_err = _translate(
            "MainWindow", "At least one of the fixture should be checked")

    def show_mac_address_info(self, total_mac_address, remaining_mac_address):
        if STATION == 'SA':
            self.label.setVisible(True)
            self.label_2.setVisible(True)
            self.label.setText(f"Total mac addess : {total_mac_address}")
            self.label_2.setText(f"Remaining mac addess : {remaining_mac_address}")
        else:
            self.label.setVisible(False)
            self.label_2.setVisible(False)

if __name__ == "__main__":
    version = ""
    thismodule = sys.modules[__name__]

    ''' === choose one of following station ===

        STATION = 'SIMULATION'

        --- SMT ---
        STATION = 'MainBoard'
        STATION = 'CapTouch'
        STATION = 'Led'

        --- FATP ---
        STATION = 'RF'
        STATION = 'WPC'
        STATION = 'Audio'
        STATION = 'PowerSensor'
        STATION = 'Download'

    '''
    app = QApplication(sys.argv)

    if STATION == 'RF': generate_jsonfile()
    task = Task(station_json[STATION])
    if not task.base: sys.exit()

    win = MyWindow(app, task)
    actions = Actions(task)
    win.actions = actions
    actions.action_trigger('first')

    app.exec_()

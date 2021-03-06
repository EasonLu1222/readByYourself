import argparse
import json
import re
import sys
import time
import config
from json import JSONDecodeError
from subprocess import Popen, PIPE

from PyQt5.QtGui import QKeySequence, QCursor
from PyQt5.QtCore import QThread, pyqtSignal as QSignal, Qt, QSettings, QTranslator
from PyQt5.QtWidgets import QDialog, QApplication, QShortcut
from serial.serialutil import SerialException

from mylogger import logger
from serials import get_serial, issue_command
from ui.cap_touch_dialog import Ui_CapTouchDialog
from utils import get_env, resource_path, run, set_property
from config import LANG_LIST, PRODUCT

PADDING = ' ' * 8


class TouchPolling(QThread):
    '''
    This class detects which cap touch key is pressed     #這個物件測試是否被壓;透過i2c的地址去詢問
    by polling the cap touch's i2c address.
    '''
    touchSignal = QSignal(str)                            #設計一個訊號為str類型

    def __init__(self, ser, key_codes=[], parent=None):  #定義物件結構__init__;引進屬性ser, key_codes=[], parent=None;實體化self
        super(TouchPolling, self).__init__(parent)       #繼承父類
        self.ser = ser                                   #設定屬性
        self.key_codes = key_codes[:]                    #
        self.kill = False

    def run(self):
        while not self.kill:
            cmd = 'i2cget -f -y 1 0x1f 0x00'
            try:
                lines = issue_command(self.ser, cmd)
            except (AttributeError, OSError, TypeError, JSONDecodeError, SerialException):
                logger.info(f'{PADDING}TouchPolling thread terminated!')
                self.kill = True
                break
            if len(lines) > 1:
                key_code = lines[1].rstrip()
                if key_code in self.key_codes:
                    self.touchSignal.emit(key_code)
                    self.key_codes.remove(key_code)
                    if not self.key_codes:
                        break


class CapTouchDialog(QDialog, Ui_CapTouchDialog):
    def __init__(self, parent=None, portnames=[], dut_idx_list=[]):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.test_results = []
        self.dut_ptr = -1   # Point to the currently testing DUT
        self.active_port = None  # Currently testing port name
        self.ser = None  # Current serial object
        self.touchPollingThread = None
        self.portnames = portnames
        self.dut_idx_list = dut_idx_list
        self.key_codes = ['0x01', '0x02', '0x04', '0x08', '0x10']
        self.KeyStatus = 0
        self.btn_list = [
            [self.b11, self.b12, self.b13, self.b14, self.b15],
            [self.b21, self.b22, self.b23, self.b24, self.b25]
        ]
        self.key_code_to_label_map = [
            dict(zip(self.key_codes, self.btn_list[0])),
            dict(zip(self.key_codes, self.btn_list[1]))
        ]
        self.pass_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.fail_button.setCursor(QCursor(Qt.PointingHandCursor))
        # self.pass_button.clicked.connect(self.pass_clicked)
        self.fail_button.clicked.connect(self.fail_clicked)
        # QShortcut(QKeySequence(Qt.Key_Return), self, self.pass_clicked)
        QShortcut(QKeySequence(Qt.Key_Space), self, self.fail_clicked)
        self.pass_button.setVisible(False)

        self.fade_disabled_duts()

        if self.next():
            self.start_test()

    def fade_disabled_duts(self):
        if 0 in self.dut_idx_list:
            set_property(self.bc1, "disabled", False)
        if 1 in self.dut_idx_list:
            set_property(self.bc2, "disabled", False)

    def next(self):
        if len(self.dut_idx_list) > 0 and len(self.portnames) > 0:
            self.dut_ptr = self.dut_idx_list.pop(0)
            self.active_port = self.portnames.pop(0)
            return True
        else:
            return False

    def start_test(self):
        self.set_focus(dut_num=self.dut_ptr)
        self.ser = get_serial(self.active_port, 115200, 0.04)
        self.touchPollingThread = TouchPolling(self.ser, self.key_codes)
        self.touchPollingThread.touchSignal.connect(self.on_touch)
        self.touchPollingThread.start()
        logger.info(f'{PADDING}cap touch start_test')

    def set_focus(self, dut_num=0):
        set_property(self.bc1, "active", False)
        set_property(self.bc2, "active", False)
        if dut_num == 0:
            set_property(self.bc1, "active", True)
        elif dut_num == 1:
            set_property(self.bc2, "active", True)

    def clear_test(self):
        if hasattr(self, 'touchPollingThread'):
            self.touchPollingThread.kill = True
        logger.info(f'{PADDING}TouchPolling thread terminated!')
        self.KeyStatus = 0
        time.sleep(0.5)  # Wait for serial communication finish before closing serial connection
        try:
            logger.info(f'{PADDING}Closing serial port ({self.ser})')
            self.ser.close()
            logger.info(f"Serial port closed successfully ({self.ser})")
        except Exception as e:
            logger.error(f'{PADDING}Failed to close serial port ({self.ser})')
            logger.error(f'{PADDING}{e}')

    def on_touch(self, touched_key_code):
        # When cap touch button is touched, set the corresponding label's background color to yellow
        btn_label = self.key_code_to_label_map[self.dut_ptr][touched_key_code]
        btn_label.setStyleSheet('background-color: #FDD835')

        if touched_key_code == '0x01':
            self.KeyStatus |= (1 << 0)
        elif touched_key_code == '0x02':
            self.KeyStatus |= (1 << 1)
        elif touched_key_code == '0x04':
            self.KeyStatus |= (1 << 2)
        elif touched_key_code == '0x08':
            self.KeyStatus |= (1 << 3)
        elif touched_key_code == '0x10':
            self.KeyStatus |= (1 << 4)

        if self.KeyStatus == 0x1f:
            self.pass_clicked()

    def pass_clicked(self):
        self.test_results.append("Pass")
        self.handle_click()

    def fail_clicked(self):
        self.test_results.append("Fail")
        self.handle_click()

    def handle_click(self):
        self.clear_test()
        if self.next():
            self.start_test()
        else:
            sys.stdout.write(json.dumps(self.test_results))
            self.close()


def check_fw():
    # TODO: Make sure all adb devices are listed
    cmd = "adb devices -l"
    decoded_output = run(cmd, strip=True)
    lines = decoded_output.split('\n')[1:]
    for line in lines:
        match = re.search(r"transport_id:(\d+)", line)
        if match:
            transport_id = match.groups()[0]

            cmd = f"adb -t {transport_id} shell ls /usr/share/{config.CAP_TOUCH_FW}"
            outputs = run(cmd)
            match = re.search('ls:', outputs)
            if match:
                # Push the firmware from app to fixture's mainboard
                logger.info(f'{PADDING}Cap touch fw does not exist, downloading from app to fixture')
                fw_file_path = resource_path(f"./firmware/{config.CAP_TOUCH_FW}")
                cmd = f"adb -t {transport_id} push {fw_file_path} /usr/share"
                run(cmd)

                # Change firmware permission to make it executable
                cmd = f"adb -t {transport_id} shell chmod 777 /usr/share/{config.CAP_TOUCH_FW}"
                run(cmd)
            else:
                logger.info(f'{PADDING}Cap touch fw exists in fixture')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-pp', '--portnames', help='serial com port names', type=str)
    parser.add_argument('-ds', '--dutselected', help='selected duts', type=str)
    args = parser.parse_args()
    portnames = args.portnames.split(',')
    dut_idx_list = [int(idx) for idx in args.dutselected.split(',')]
    # dut_idx_list = [0, 1]
    # portnames = ['/dev/cu.usbserial-A50285BI', '/dev/cu.usbserial-22222222']

    app = QApplication(sys.argv)

    settings = QSettings('FAB', f'SAP{PRODUCT}')
    settings.lang_index = settings.value('lang_index', 0, int)
    translator = QTranslator()
    translator.load(resource_path(f"translate/{LANG_LIST[settings.lang_index]}"))
    app.removeTranslator(translator)
    app.installTranslator(translator)

    d = CapTouchDialog(portnames=portnames, dut_idx_list=dut_idx_list)
    d.showMaximized()
    sys.exit(app.exec_())

import argparse
import json
import sys
import time
from json import JSONDecodeError

from PyQt5.QtCore import QThread, pyqtSignal as QSignal, Qt, QSettings, QTranslator
from PyQt5.QtGui import QKeySequence, QCursor
from PyQt5.QtWidgets import QDialog, QApplication, QShortcut
from serial.serialutil import SerialException

from config import LANG_LIST, PRODUCT
from mylogger import logger
from serials import get_serial, issue_command
from ui.unmute_mic import Ui_UnmuteMicDialog
from utils import resource_path, set_property

PADDING = ' ' * 8


class TouchPolling(QThread):
    """
    This class detects which cap touch key is pressed
    by polling the cap touch's i2c address.
    """
    touchSignal = QSignal(str, int)
    doneSignal = QSignal(list)

    def __init__(self, ser_list=[], dut_idx_list=[], parent=None):
        super(TouchPolling, self).__init__(parent)
        self.ser_list = ser_list
        self.dut_idx_list = dut_idx_list
        self.kill = False
        self.pass_list = [False] * len(ser_list)

    def run(self):
        while not self.kill:
            cmd = 'i2cget -f -y 1 0x1f 0x02'
            for i, ser in enumerate(self.ser_list):
                try:
                    lines = issue_command(ser, cmd)
                except (AttributeError, OSError, TypeError, JSONDecodeError, SerialException) as e:
                    logger.error(f'{PADDING}TouchPolling thread terminated!\n{e}')
                    self.kill = True
                    break
                if len(lines) > 1:
                    key_code = lines[1].rstrip()
                    if key_code == '0x00' and not self.pass_list[i]:
                        self.pass_list[i] = True
                        self.touchSignal.emit(key_code, dut_idx_list[i])
                        time.sleep(0.05)
            if all(self.pass_list):
                self.kill = True
                self.doneSignal.emit(self.pass_list)
                break

        logger.info(f'{PADDING}TouchPolling thread terminated!')


class UnmuteMicDialog(QDialog, Ui_UnmuteMicDialog):
    def __init__(self, parent=None, portnames=[], dut_idx_list=[]):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.pass_list = [None]*2  # Stores a list of True/False to represent pass/fail of each DUT
        self.result_str = ''  # Json dump of pass/fail list. e.g. "['Pass', 'Fail']"
        self.ser_list = []
        self.tpt = None     # TouchPolling thread
        self.portnames = portnames
        self.dut_idx_list = dut_idx_list
        self.btn_list = [self.b1, self.b2]


        self.continue_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.continue_button.clicked.connect(self.on_done)
        QShortcut(QKeySequence(Qt.Key_Return), self, self.on_done)

        self.fade_disabled_duts()

        if len(self.dut_idx_list) > 0 and len(self.portnames) > 0:
            self.start_test()

    def fade_disabled_duts(self):
        if 0 in self.dut_idx_list:
            set_property(self.b1, "disabled", False)
            self.pass_list[0] = False
        if 1 in self.dut_idx_list:
            set_property(self.b2, "disabled", False)
            self.pass_list[1] = False

    def start_test(self):
        for i, portname in enumerate(portnames):
            ser = get_serial(portname, 115200, 0.04)
            self.ser_list.append(ser)
        self.tpt = TouchPolling(self.ser_list, self.dut_idx_list)
        self.tpt.touchSignal.connect(self.on_touch)
        self.tpt.doneSignal.connect(self.on_done)
        self.tpt.start()
        logger.info(f'{PADDING}unmute mic start_test')

    def clear_test(self):
        if hasattr(self, 'touch_polling_thread'):
            self.tpt.kill = True
        time.sleep(0.5)  # Wait for serial communication finish before closing serial connection
        for ser in self.ser_list:
            try:
                logger.info(f"{PADDING}Closing serial port ({ser})")
                ser.close()
                logger.info(f"{PADDING}Serial port closed successfully ({ser})")
            except Exception as e:
                logger.error(f"{PADDING}Failed to close serial port ({ser})\n{e}")

    def on_touch(self, touched_key_code, dut_idx):
        # When cap touch button is touched, set the corresponding label's background color to yellow
        logger.info(f'{PADDING}{touched_key_code}, {dut_idx}')
        btn_label = self.btn_list[dut_idx]
        btn_label.setStyleSheet('background-color: #FDD835')
        self.pass_list[dut_idx] = True

    def on_done(self, results=None):
        if results:
            self.pass_list = results[:]
        self.clear_test()
        self.close()

    def closeEvent(self, event):
        pass_fail_str_list = []
        for b in self.pass_list:
            if b is True:
                pass_fail_str_list.append('Pass')
            elif b is False:
                pass_fail_str_list.append('Fail')
        self.result_str = json.dumps(pass_fail_str_list)
        logger.debug(f"{PADDING}result_str={self.result_str}")
        sys.stdout.write(self.result_str)


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

    d = UnmuteMicDialog(portnames=portnames, dut_idx_list=dut_idx_list)
    d.showMaximized()
    sys.exit(app.exec_())

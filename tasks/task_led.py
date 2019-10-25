import sys
import json
import argparse
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QTranslator, QSettings
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QDialog, QLabel
from ui.led_color_dialog import Ui_LedColorDialog
from ui.led_result_marker_dialog import Ui_LedResultMarkerDialog
from serials import issue_command, get_serial
from utils import resource_path
from config import LANG_LIST

num_key_list = [
    Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5, Qt.Key_6, Qt.Key_7, Qt.Key_8, Qt.Key_9
]


class LedColorDialog(QDialog, Ui_LedColorDialog):
    def __init__(self, parent=None, ser_list=[], dut_idx_list=[]):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setWindowModality(Qt.ApplicationModal)

        self.result_dialog = LedResultMarkerDialog(dut_idx_list=dut_idx_list)
        self.ser_list = ser_list
        self.dut_idx_list = dut_idx_list    # E.g. [0, 1]
        self.color_block_list = []
        self.color_list = [  # Colors to test
            Qt.red,
            Qt.green,
            Qt.blue,
            Qt.white
        ]
        self.color_idx = -1

        for i in range(len(self.ser_list)):
            self.add_color_block()

        self.next_color()

    def keyPressEvent(self, event):
        # If Space is pressed, show next color
        if event.key() == Qt.Key_Space:
            self.next_color()
        # Ignore Esc key
        elif event.key() == Qt.Key_Escape:
            return
        else:
            super(LedColorDialog, self).keyPressEvent(event)

    def closeEvent(self, event):
        for ser in self.ser_list:
            ser.close()

    def add_color_block(self):
        """
        Add a color block to the horizontal layout.
        Each block represents a DUT(Device Under Test).
        """
        lb = QLabel()
        self.color_block_list.append(lb)
        self.horizontalLayout.addWidget(lb)

    def set_color(self, color=Qt.red):
        c = QColor(color)
        for lb in self.color_block_list:
            lb.setStyleSheet(f"background-color:{c.name()}")

    def next_color(self):
        self.color_idx += 1
        if self.color_idx < len(self.color_list):
            current_color = self.color_list[self.color_idx]
            self.set_color(color=current_color)
            self.set_led_color(color=current_color)
        else:
            self.close()
            self.result_dialog.showMaximized()

    def set_led_color(self, color=Qt.red):
        c = QColor(color)
        rgb = list(c.getRgb())[:3]
        for ser in self.ser_list:
            for i in range(1, 5):
                for j, k in enumerate(['R', 'G', 'B']):
                    cmd = f'echo {rgb[j]} > /sys/class/leds/LED{i}_{k}/brightness'
                    issue_command(ser, cmd, False)


class LedResultMarkerDialog(QDialog, Ui_LedResultMarkerDialog):
    def __init__(self, parent=None, dut_idx_list=[]):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setWindowModality(Qt.ApplicationModal)

        self.color_pass = QColor("#8BC34A")  # Green
        self.color_fail = QColor("#FF5722")  # Red
        self.color_disabled = QColor('#E0E0E0')  #Grey
        self.dut_idx_list = dut_idx_list  # Number of devices to test
        self.result_block_list = []
        self.valid_keys = [num_key_list[i] for i in dut_idx_list]
        self.pass_list = []  # Stores a list of True/False to represent pass/fail of each DUT
        self.result_str = ''   # Json dump of pass/fail list. e.g. "['Pass', 'Fail']"

        for i in range(2):
            self.add_result_block(i)

        self.set_color()

    def keyPressEvent(self, event):
        # If number key is pressed
        if event.key() in self.valid_keys:
            idx = num_key_list.index(event.key())
            self.toggle_pass_fail(self.result_block_list[idx])
        # If return key is pressed
        elif event.key() == Qt.Key_Return:
            self.close()
        # Ignore Esc key
        elif event.key() == Qt.Key_Escape:
            return
        else:
            super(LedResultMarkerDialog, self).keyPressEvent(event)

    def closeEvent(self, event):
        pass_fail_str_list = []
        for b in self.pass_list:
            if b is True:
                pass_fail_str_list.append('Passed')
            elif b is False:
                pass_fail_str_list.append('Failed')
        self.result_str = json.dumps(pass_fail_str_list)
        sys.stdout.write(self.result_str)

    def add_result_block(self, dut_idx):
        font = QtGui.QFont()
        font.setFamily("Courier New")
        font.setPointSize(36)
        lb = QLabel()
        lb.setFont(font)
        lb.setText(str(dut_idx+1))
        lb.setAlignment(Qt.AlignCenter)
        self.result_block_list.append(lb)
        self.horizontalLayout.addWidget(lb)
        if dut_idx in self.dut_idx_list:
            self.pass_list.append(True)
        else:
            self.pass_list.append(None)

    def set_color(self):
        """
        Set the color of all result blocks
        """
        for dut_idx, lb in enumerate(self.result_block_list):
            if dut_idx not in self.dut_idx_list:
                lb.setStyleSheet(f"background-color:{self.color_disabled.name()}; color:#BDBDBD")
            else:
                lb.setStyleSheet(f"background-color:{self.color_pass.name()}")

    def toggle_pass_fail(self, result_block):
        """
        Toggles the color of the result block based on the True/False value in pass_list

        Args:
            result_block: A QLabel indicating pass or fail by its background color
        """
        i = self.result_block_list.index(result_block)
        self.pass_list[i] = not self.pass_list[i]

        color = self.color_pass.name() if self.pass_list[i] else self.color_fail.name()
        result_block.setStyleSheet(f"background-color:{color}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-pp', '--portnames', help='serial com port names', type=str)
    parser.add_argument('-ds', '--dutselected', help='selected duts', type=str)
    args = parser.parse_args()
    dut_idx_list = [int(idx) for idx in args.dutselected.split(',')]
    com_list = args.portnames.split(',') if args.portnames else []
    # dut_idx_list = [0, 1]
    # com_list = ['/dev/cu.usbserial-A50285BI', '/dev/cu.usbserial-22222222']

    app = QApplication(sys.argv)

    settings = QSettings('FAB', 'SAP109')
    settings.lang_index = settings.value('lang_index', 0, int)
    translator = QTranslator()
    translator.load(resource_path(f"translate/{LANG_LIST[settings.lang_index]}"))
    app.removeTranslator(translator)
    app.installTranslator(translator)

    serial_list = []
    for com in com_list:
        s = get_serial(com, 115200, 0)
        serial_list.append(s)
    d = LedColorDialog(ser_list=serial_list, dut_idx_list=dut_idx_list)
    d.showMaximized()
    sys.exit(app.exec_())

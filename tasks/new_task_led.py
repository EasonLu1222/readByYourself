import sys
import argparse
from PyQt5.QtWidgets import QApplication, QDialog, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from ui.led_color_dialog import Ui_LedColorDialog
from serials import issue_command, get_serial
from view.led_result_marker_dialog import LedResultMarkerDialog


class LedColorDialog(QDialog, Ui_LedColorDialog):
    def __init__(self, parent=None, ser_list=[], dut_num=1):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setWindowModality(Qt.ApplicationModal)

        self.result_dialog = LedResultMarkerDialog(dut_num=dut_num)
        self.ser_list = ser_list
        self.dut_num = dut_num  # Number of devices to test
        self.color_block_list = []
        self.color_list = [  # Colors to test
            Qt.red,
            Qt.green,
            Qt.blue,
            Qt.white
        ]
        self.color_idx = -1

        for i in range(dut_num):
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
                    issue_command(ser, cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-pp', '--portnames', help='serial com port names', type=str)
    args = parser.parse_args()
    com_list = args.portnames.split(',') if args.portnames else []
    # com_list = ['/dev/cu.usbserial-00000000']

    app = QApplication(sys.argv)

    ser_list = []
    for com in com_list:
        s = get_serial(com, 115200, 0)
        ser_list.append(s)
    d = LedColorDialog(ser_list=ser_list, dut_num=len(com_list))
    d.showMaximized()
    sys.exit(app.exec_())

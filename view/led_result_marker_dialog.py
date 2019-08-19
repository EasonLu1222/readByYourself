import sys
from PyQt5.QtWidgets import QApplication, QDialog, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from ui.led_result_marker_dialog import Ui_LedResultMarkerDialog

num_key_list = [
    Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5, Qt.Key_6, Qt.Key_7, Qt.Key_8, Qt.Key_9
]


class LedResultMarkerDialog(QDialog, Ui_LedResultMarkerDialog):
    def __init__(self, parent=None, dut_num=1):
        super().__init__(parent)
        print('LedColorDialog init')
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setWindowModality(Qt.ApplicationModal)

        self.color_pass = QColor("#8BC34A")  # Green
        self.color_fail = QColor("#FF5722")  # Red
        self.dut_num = dut_num  # Number of devices to test
        self.result_block_list = []
        self.pass_list = []  # Stores a list of True/False to represent pass/fail of each DUT

        for i in range(dut_num):
            self.add_result_block(i)

        self.set_color()

    def keyPressEvent(self, event):
        # If number key is pressed
        if event.key() in num_key_list[:self.dut_num]:
            idx = num_key_list.index(event.key())
            self.toggle_pass_fail(self.result_block_list[idx])
        # If return key is pressed
        elif event.key() == Qt.Key_Return:
            print(self.pass_list)
            self.close()
        # Ignore Esc key
        elif event.key() == Qt.Key_Escape:
            return
        else:
            super(LedResultMarkerDialog, self).keyPressEvent(event)

    def add_result_block(self, dut_idx):
        lb = QLabel()
        lb.setText(str(dut_idx))
        self.result_block_list.append(lb)
        self.horizontalLayout.addWidget(lb)
        self.pass_list.append(True)

    def set_color(self):
        """
        Set the color of all result blocks
        """
        for lb in self.result_block_list:
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d = LedResultMarkerDialog(dut_num=2)
    d.showMaximized()
    app.exec_()


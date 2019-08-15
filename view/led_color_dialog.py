import sys
from PyQt5.QtWidgets import QApplication, QDialog, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from ui.led_color_dialog import Ui_LedColorDialog


class LedColorDialog(QDialog, Ui_LedColorDialog):
    def __init__(self, parent=None, dut_num=1):
        super().__init__(parent)
        print('LedColorDialog init')
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowModality(Qt.ApplicationModal)
        self.dut_num = dut_num

        for i in range(dut_num):
            self.add_color_block()

    def add_color_block(self):
        """
        Add a color block to the horizontal layout.
        Each block represents a DUT(Device Under Test).
        """
        lb = QLabel()
        lb.setStyleSheet("background-color:red")
        self.horizontalLayout.addWidget(lb)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    d = LedColorDialog(dut_num=2)
    d.show()
    app.exec_()

import sys
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import Qt, pyqtSignal
from ui.led_color_dialog import Ui_LedColorDialog


class LedColorDialog(QDialog, Ui_LedColorDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        print('LedColorDialog init')
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowModality(Qt.ApplicationModal)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    d = LedColorDialog()
    d.show()
    app.exec_()

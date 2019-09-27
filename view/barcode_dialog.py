import re
import sys

from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from ui.barcode_dialog import Ui_BarcodeDialog


class BarcodeDialog(QDialog, Ui_BarcodeDialog):
    barcode_entered = pyqtSignal(str)  # str:barcode
    barcode_dialog_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        print('BarcodeDialog init')
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowModality(Qt.ApplicationModal)
        self.barcodeLineEdit.returnPressed.connect(self.on_input_done)
        self.barcodeLineEdit.setFocus()

    def set_total_barcode(self, num):
        self.total_barcode = num

    def on_input_done(self):
        barcode = self.barcodeLineEdit.text()
        if (self.is_valid(barcode)):
            self.barcode_entered.emit(barcode)
            self.total_barcode = self.total_barcode - 1
            if (self.total_barcode <= 0):
                self.close()
            else:
                self.barcodeLineEdit.clear()
        else:
            self.barcodeLineEdit.clear()

    def is_valid(self, barcode):
        """
        Verify if the input is a valid barcode
        """
        regex = r"\d{3}-\d{3}-\d{3}-\d{4}-\d{4}-\d{6}"
        matches = re.match(regex, barcode)

        # return matches is not None
        return True

    def closeEvent(self, evnt):
        self.show_start_test_dialog()

    def show_start_test_dialog(self):
        infoBox = QMessageBox()  ##Message Box that doesn't run
        print("Im here")
        infoBox.setIcon(QMessageBox.Information)
        infoBox.setText("将待测物放回治具后，按回车键开始测试")
        infoBox.exec_()
        self.barcode_dialog_closed.emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    d = BarcodeDialog()
    d.set_total_barcode(2)
    d.show()
    sys.exit(app.exec_())
import re
import sys

from enum import Enum
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from ui.barcode_dialog import Ui_BarcodeDialog


class BarcodeRe(Enum):
    """
    Define the regular expression for different types of barcode
    """
    MSN = r"\d{3}-\d{3}-\d{3}-\d{4}-\d{4}-\d{6}"
    ASN = r'\w{14}'
    WPC = r"[\w|\d]{6}\d[\w|\d]{2}\w[\w|\d]{5}"


class BarcodeDialog(QDialog, Ui_BarcodeDialog):
    barcode_entered = pyqtSignal(str)  # str:barcode
    barcode_dialog_closed = pyqtSignal()

    def __init__(self, parent=None, station=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowModality(Qt.ApplicationModal)
        self.barcodeLineEdit.returnPressed.connect(self.on_input_done)
        self.barcodeLineEdit.setFocus()
        self.total_barcode = -1
        if station == 'WPC':
            self.regex = BarcodeRe.WPC.value
        elif station in ['AcousticListen', 'Leak']:
            self.regex = BarcodeRe.ASN.value
        else:
            self.regex = BarcodeRe.MSN.value

    def set_total_barcode(self, num):
        self.total_barcode = num

    def on_input_done(self):
        barcode = self.barcodeLineEdit.text()
        if self.is_valid(barcode):
            self.barcode_entered.emit(barcode)
            self.total_barcode = self.total_barcode - 1
            if self.total_barcode <= 0:
                self.close()
            else:
                self.barcodeLineEdit.clear()
        else:
            self.barcodeLineEdit.clear()

    def is_valid(self, barcode):
        """
        Verify if the input is a valid barcode
        """
        matches = re.match(self.regex, barcode)

        return matches is not None

    def closeEvent(self, evnt):
        self.barcode_dialog_closed.emit()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    d = BarcodeDialog()
    d.set_total_barcode(2)
    d.show()
    sys.exit(app.exec_())

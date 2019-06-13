from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, pyqtSignal
from barcode_dialog import Ui_BarcodeDialog


class BarcodeDialog(QDialog, Ui_BarcodeDialog):
    barcode_entered = pyqtSignal(str)  # str:barcode
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.barcodeLineEdit.returnPressed.connect(self.on_input_done)
        self.barcodeLineEdit.setFocus()
        
    def on_input_done(self):
        barcode = self.barcodeLineEdit.text()
        if (self.is_valid(barcode)):
            self.barcode_entered.emit(barcode)
            self.close()
        else:
            self.barcodeLineEdit.clear()
        
    def is_valid(self, barcode):
        """
        Verify if the input is a valid barcode
        """
        # TODO: Modify this when the actual barcode format is determined
        return len(barcode)==4

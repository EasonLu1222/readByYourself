from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, pyqtSignal
from ui.barcode_dialog import Ui_BarcodeDialog


class BarcodeDialog(QDialog, Ui_BarcodeDialog):
    barcode_entered = pyqtSignal(str)  # str:barcode
    barcode_dialog_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        print('BarcodeDialog init')
        self.setupUi(self)
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
        # TODO: Modify this when the actual barcode format is defined
        return len(barcode)==4
    
    def closeEvent(self, evnt):
        self.barcode_dialog_closed.emit()

        

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, pyqtSignal
from ui.barcode_dialog import Ui_BarcodeDialog


class BarcodeDialog(QDialog, Ui_BarcodeDialog):
    barcode_entered = pyqtSignal(str)  # str:barcode
    barcode_dialog_closed = pyqtSignal()
    num_of_barcode_collected = 0
    def __init__(self, parent=None, num=0):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)
        self.total_barcode = num
        self.barcodeLineEdit.returnPressed.connect(self.on_input_done)
        self.barcodeLineEdit.setFocus()
        
    def on_input_done(self):
        barcode = self.barcodeLineEdit.text()
        if (self.is_valid(barcode)):
            self.barcode_entered.emit(barcode)
            self.num_of_barcode_collected+=1
            if (self.num_of_barcode_collected >= self.total_barcode):
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
        
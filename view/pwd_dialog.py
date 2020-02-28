from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, pyqtSignal
from ui.pwd_dialog import Ui_PwdDialog


class PwdDialog(QDialog, Ui_PwdDialog):
    dialog_close = pyqtSignal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowModality(Qt.ApplicationModal)
        self.confirmBtn.clicked.connect(self.on_confirm)
        self.cancelBtn.clicked.connect(self.on_cancel)
        self.is_eng_mode_on = False

    def check_pwd(self, password):
        return password=='4321'
        
    def showEvent(self, event):
        super(PwdDialog, self).showEvent(event)
        
        # Clear the password when dialog is opened
        self.pwdText.clear()

    def on_confirm(self):
        self.is_eng_mode_on = self.check_pwd(self.pwdText.text())
        self.dialog_close.emit(self.is_eng_mode_on)
        self.close()

    def on_cancel(self):
        self.dialog_close.emit(False)
        self.close()

    def keyPressEvent(self, event):
        if event.key() is Qt.Key_Escape:
            pass



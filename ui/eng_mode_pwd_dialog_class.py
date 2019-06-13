from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, pyqtSignal
from ui.eng_mode_pwd_dialog import Ui_EngModePwdDialog


class EngModePwdDialog(QDialog, Ui_EngModePwdDialog):
    is_eng_mode_on = False
    dialog_close = pyqtSignal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)
        self.confirmBtn.clicked.connect(self.on_confirm)
        self.cancelBtn.clicked.connect(self.on_cancel)

    def on_confirm(self):
        self.is_eng_mode_on = self.check_pwd(self.pwdText.text())
        self.dialog_close.emit(self.is_eng_mode_on)
        self.close()

    def on_cancel(self):
        self.dialog_close.emit(False)
        self.close()

    def check_pwd(self, password):
        return password=='1234'
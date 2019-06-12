import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog
from PyQt5.QtCore import Qt, pyqtSignal, QSettings
from fixture_select_dialog import Ui_FixtureSelectDialog
from eng_mode_pwd_dialog import Ui_EngModePwdDialog


class FxDialog(QDialog, Ui_FixtureSelectDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.checkBoxEngMode.stateChanged.connect(self.eng_mode_state_changed)
        self.checkBoxFx1.stateChanged.connect(self.chk_box_fx1_state_changed)
        self.checkBoxFx2.stateChanged.connect(self.chk_box_fx2_state_changed)

        self.d = PwdDialog(self)
        self.d.setWindowModality(Qt.ApplicationModal)
        self.d.dialog_close.connect(self.on_dialog_close)
        self.settings = QSettings("FAB", "SAP109")
        self.checkBoxFx1.setChecked(self.settings.value("fixture_1"))
        self.checkBoxFx2.setChecked(self.settings.value("fixture_2"))

    def eng_mode_state_changed(self, status):
        if (status == Qt.Checked):
            self.d.show()

    def chk_box_fx1_state_changed(self, status):
        self.settings.setValue("fixture_1", status == Qt.Checked)

    def chk_box_fx2_state_changed(self, status):
        self.settings.setValue("fixture_2", status == Qt.Checked)

    def on_dialog_close(self, is_eng_mode_on):
        if(not is_eng_mode_on):
            self.checkBoxEngMode.setChecked(False)

class PwdDialog(QDialog, Ui_EngModePwdDialog):
    is_eng_mode_on = False
    dialog_close = pyqtSignal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

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



app = QApplication(sys.argv)
w = FxDialog()
w.show()
sys.exit(app.exec_())

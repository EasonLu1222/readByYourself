from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, QSettings
from ui.fixture_select_dialog import Ui_FixtureSelectDialog
from ui.eng_mode_pwd_dialog_class import EngModePwdDialog


class FixtureSelectDialog(QDialog, Ui_FixtureSelectDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)

        self.checkBoxEngMode.stateChanged.connect(self.eng_mode_state_changed)
        self.checkBoxFx1.stateChanged.connect(self.chk_box_fx1_state_changed)
        self.checkBoxFx2.stateChanged.connect(self.chk_box_fx2_state_changed)

        self.d = EngModePwdDialog(self)
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
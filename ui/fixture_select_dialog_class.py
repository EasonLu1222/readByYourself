from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import Qt, QSettings, QTranslator, QEvent
from ui.fixture_select_dialog import Ui_FixtureSelectDialog
from ui.eng_mode_pwd_dialog_class import EngModePwdDialog
from ui.barcode_dialog_class import BarcodeDialog


class FixtureSelectDialog(QDialog, Ui_FixtureSelectDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowModality(Qt.ApplicationModal)

        self.checkBoxEngMode.stateChanged.connect(self.eng_mode_state_changed)
        self.checkBoxFx1.stateChanged.connect(self.chk_box_fx1_state_changed)
        self.checkBoxFx2.stateChanged.connect(self.chk_box_fx2_state_changed)
        self.langSelectMenu.currentIndexChanged.connect(self.on_lang_changed)

        self.d = EngModePwdDialog(self)
        self.d.dialog_close.connect(self.on_dialog_close)
        
        self.b = BarcodeDialog(self)
        self.b.barcode_entered.connect(self.on_barcode_entered)
        self.b.barcode_dialog_closed.connect(self.on_barcode_dialog_closed)
        
        self.settings = QSettings("FAB", "SAP109")
        self.checkBoxFx1.setChecked(self.settings.value("fixture_1", False))
        self.checkBoxFx2.setChecked(self.settings.value("fixture_2", False))
        self.langSelectMenu.setCurrentIndex(self.settings.value("lang_index", 0))
        self.on_lang_changed(self.settings.value("lang_index", 0))
        self.startBtn.clicked.connect(self.on_start_clicked)
        
        self.parent().hide()

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
            
    def on_lang_changed(self, index):
        self.settings.setValue("lang_index", index)
        lang_list = ['en_US.qm', 'zh_TW.qm']
        app = QApplication.instance()
        translator = QTranslator()
        translator.load(f"translate/{lang_list[index]}")
        app.removeTranslator(translator)
        app.installTranslator(translator)
        self.retranslateUi(self)
        self.d.retranslateUi(self.d)
        self.b.retranslateUi(self.b)
        self.parent().retranslateUi(self.parent())
            
    def on_start_clicked(self):
        s = [self.settings.value("fixture_1"), self.settings.value("fixture_2")]
        num = len(list(filter(lambda x: x==True, s)))
        
        self.b.set_total_barcode(num)
        self.b.show()
        self.hide()

    def on_barcode_entered(self, barcode):
        print(barcode)
        
    def on_barcode_dialog_closed(self):
        self.parent().show()
        
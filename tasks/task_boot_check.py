import json
import sys

from PyQt5.QtCore import Qt, QSettings, QTranslator
from PyQt5.QtGui import QKeySequence, QCursor
from PyQt5.QtWidgets import QDialog, QApplication, QShortcut

from config import LANG_LIST
from ui.pass_fail_dialog import Ui_PassFailDialog
from utils import resource_path

PADDING = ' ' * 8


class PassFailDialog(QDialog, Ui_PassFailDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.test_results = []

        self.pass_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.fail_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.pass_button.clicked.connect(self.pass_clicked)
        self.fail_button.clicked.connect(self.fail_clicked)
        QShortcut(QKeySequence(Qt.Key_Return), self, self.pass_clicked)
        QShortcut(QKeySequence(Qt.Key_Space), self, self.fail_clicked)

    def pass_clicked(self):
        self.test_results.append("Pass")
        self.handle_click()

    def fail_clicked(self):
        self.test_results.append("Fail")
        self.handle_click()

    def handle_click(self):
        sys.stdout.write(json.dumps(self.test_results))
        self.close()


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-pp', '--portnames', help='serial com port names', type=str)
    # parser.add_argument('-ds', '--dutselected', help='selected duts', type=str)
    # args = parser.parse_args()
    # portnames = args.portnames.split(',')
    # dut_idx_list = [int(idx) for idx in args.dutselected.split(',')]

    # dut_idx_list = [0, 1]
    # portnames = ['/dev/cu.usbserial-A50285BI', '/dev/cu.usbserial-22222222']

    app = QApplication(sys.argv)

    settings = QSettings('FAB', 'SAP109')
    settings.lang_index = settings.value('lang_index', 0, int)
    translator = QTranslator()
    translator.load(resource_path(f"translate/{LANG_LIST[settings.lang_index]}"))
    app.removeTranslator(translator)
    app.installTranslator(translator)

    d = PassFailDialog()
    d.showMaximized()
    sys.exit(app.exec_())

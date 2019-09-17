from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMovie
from ui.loading_dialog import Ui_LoadingDialog
from utils import resource_path


class LoadingDialog(QDialog, Ui_LoadingDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        print('LoadingDialog init')
        self.setupUi(self)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        self.setWindowModality(Qt.ApplicationModal)

        self.label.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label.setText('.')
        self.label.setScaledContents(True)

        self.setWindowOpacity(0.5)

        movie = QMovie(resource_path('images/AppleLoading.gif'))
        movie.setCacheMode(QMovie.CacheAll)
        movie.setSpeed(200)
        self.label.setMovie(movie)
        movie.start()

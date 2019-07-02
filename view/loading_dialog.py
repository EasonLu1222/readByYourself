from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMovie
from ui.loading_dialog import Ui_LoadingDialog


class LoadingDialog(QDialog, Ui_LoadingDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        print('LoadingDialog init')
        self.setupUi(self)
        #  self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint |
                            #  Qt.FramelessWindowHint)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        self.setWindowModality(Qt.ApplicationModal)

        self.label.setAttribute(Qt.WA_TranslucentBackground, True)
        #  self.setStyleSheet("background:transparent;")
        self.label.setText('fuck!')
        #  self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label.setScaledContents(True)

        self.setWindowOpacity(0.5)

        #  movie = QMovie("./images/spinning_wheel.gif")
        movie = QMovie("./images/AppleLoading.gif")
        movie.setCacheMode(QMovie.CacheAll)
        movie.setSpeed(200)
        self.label.setMovie(movie)
        movie.start()

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMovie
from ui.loading_dialog import Ui_LoadingDialog


class LoadingDialog(QDialog, Ui_LoadingDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        print('LoadingDialog init')
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowModality(Qt.ApplicationModal)
        
        movie = QMovie("./images/spinning_wheel.gif")
        movie.setCacheMode(QMovie.CacheAll) 
        movie.setSpeed(100) 
        self.label.setMovie(movie)   
        movie.start()
    
    # def reject(self):
    #     pass

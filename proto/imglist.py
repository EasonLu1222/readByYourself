from PyQt5.QtCore import (
    QThread, Qt, QVariant, QObject,
    pyqtSignal as Signal, pyqtSlot as Slot,
    QAbstractItemModel, QAbstractTableModel, QAbstractListModel, QModelIndex,
    QSortFilterProxyModel,
)
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QApplication,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QComboBox,
    QTableView, QTableWidget, QLabel,
    QListView, QListWidget, QListWidgetItem,
    QAction, QWidgetAction,
    QStyledItemDelegate,
)
from PyQt5.QtGui import (
    QColor, QPixmap,
)
import sys


class QCustomQWidget(QWidget):
    def __init__ (self, parent = None):
        super(QCustomQWidget, self).__init__(parent)
        self.textQVBoxLayout = QVBoxLayout()
        self.textUpQLabel    = QLabel()
        self.textDownQLabel  = QLabel()
        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textQVBoxLayout.addWidget(self.textDownQLabel)

        self.allQVBoxLayout  = QVBoxLayout()
        self.iconQLabel      = QLabel()
        self.iconQLabel.setGeometry(0,0, 200, 200)
        self.allQVBoxLayout.addLayout(self.textQVBoxLayout, 1)
        self.allQVBoxLayout.addWidget(self.iconQLabel, 0)
        
        self.setLayout(self.allQVBoxLayout)
        # setStyleSheet
        self.textUpQLabel.setStyleSheet('''
            color: rgb(0, 0, 255);
        ''')
        self.textDownQLabel.setStyleSheet('''
            color: rgb(255, 0, 0);
        ''')

    def setTextUp (self, text):
        self.textUpQLabel.setText(text)

    def setTextDown (self, text):
        self.textDownQLabel.setText(text)

    def setIcon (self, imagePath):
        p = QPixmap(imagePath)
        w = self.iconQLabel.width()
        h = self.iconQLabel.height()
        print('w', w , 'h', h)
        self.iconQLabel.setPixmap(p.scaled(w,h,Qt.KeepAspectRatio))
        #  self.iconQLabel.setPixmap(p)
        #  self.iconQLabel.setScaledContents(True)

class ImageList(QWidget):
    def __init__ (self, img_info):
        super(ImageList, self).__init__()
        self.myQListWidget = QListWidget(self)
        self.myQListWidget.setFlow(QListWidget.LeftToRight)
        for index, name, icon in img_info:
            myQCustomQWidget = QCustomQWidget()
            myQCustomQWidget.setTextUp(index)
            myQCustomQWidget.setTextDown(name)
            myQCustomQWidget.setIcon(icon)
            myQListWidgetItem = QListWidgetItem(self.myQListWidget)
            myQListWidgetItem.setSizeHint(myQCustomQWidget.sizeHint())
            self.myQListWidget.addItem(myQListWidgetItem)
            self.myQListWidget.setItemWidget(myQListWidgetItem, myQCustomQWidget)
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.myQListWidget)


if __name__ == "__main__":

    img1 = '/Users/zealzel/Desktop/fixture_dummy1.png'
    img2 = '/Users/zealzel/Desktop/fixture_dummy2.png'
    img3 = '/Users/zealzel/Desktop/fixture_dummy1.png'
    image_info = [('No.1', 'Meyoko',  img1),
                  ('No.2', 'Nyaruko', img2),
                  ('No.3', 'Louise',  img3),]

    app = QApplication([])
    w = ImageList(image_info)
    w.show()
    sys.exit(app.exec_())

import sys
import json
import argparse
import time
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, pyqtSignal
from view import task_dialog
from serials import get_serial, issue_command
from mylogger import logger



class TouchPolling(QThread):
    '''
    This class detects which cap touch key is pressed
    by polling the cap touch's i2c address.
    '''
    touchSignal = pyqtSignal(str)
    def __init__(self, ser, key_codes = [], parent=None):
        super(TouchPolling, self).__init__(parent)
        self.ser = ser
        self.key_codes = key_codes
    
    def run(self):
        # TODO: Closing the dialog without touching all keys will cause exception 
        while True:
            cmd = 'i2cget -f -y 1 0x1f 0x00'
            lines = issue_command(self.ser, cmd)
            if len(lines)>1:
                key_code = lines[1].rstrip()
                if key_code in self.key_codes:
                    self.touchSignal.emit(key_code)
                    self.key_codes.remove(key_code)
                    if not self.key_codes:
                        break
        self.ser.close()

class ContentWidget(QtWidgets.QWidget):
    def __init__(self, portnames, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.key_codes = ['0x01', '0x02', '0x04', '0x08', '0x10']
        self.key_label_texts = ['Mute', 'V+', 'Play', 'V-', 'BT']
        self.btn_labels = []
        layout = QtWidgets.QHBoxLayout(self)

        # Create 5 labels corresponding to the 5 cap touch buttons and put them in the QHBoxLayout
        for i in range(5):
            self.btn_labels.append(QtWidgets.QLabel(self.key_label_texts[i]))
            layout.addWidget(self.btn_labels[i])
        
        # Create a map like: {'0x01': btn_label[0], '0x02': btn_label[1], ...}
        self.key_code_to_label_map = dict(zip(self.key_codes, self.btn_labels))
        self.setLayout(layout)
        
        self.iterports = iter(portnames)
        self.init_test()
        

    def init_test(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        self.all_color('#FFFFFF')
        port = next(self.iterports)
        self.ser = get_serial(port, 115200, 0.04)
        self.touchPollingThread = TouchPolling(self.ser, self.key_codes)
        self.touchPollingThread.touchSignal.connect(self.on_touch)
        self.touchPollingThread.start()
        logger.info('init_test')

    def set_signal(self):
        self.father.message_each.connect(self.init_test)
        self.father.message_end.connect(self.on_close)

    def all_color(self, color_code):
        for btn_label in self.btn_labels:
            btn_label.setStyleSheet(f'background-color: {color_code}')

    def on_touch(self, touched_key_code):
        # When cap touch button is touched, set the corresponding label's background color to yellow
        btn_label = self.key_code_to_label_map[touched_key_code]
        btn_label.setStyleSheet('background-color: #FFEB3B')

    def on_close(self, msg):
        logger.info('on_close')
        self.ser.close()
        sys.stdout.write(json.dumps(msg))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-pp', '--portnames', help='serial com port names', type=str)
    args = parser.parse_args()
    portnames = args.portnames.split(',')

    app = QtWidgets.QApplication([])
    w = ContentWidget(portnames)

    image_info = [('No.1', 'Meyoko', 'images/fixture_dummy1.png'),
                  ('No.2', 'Nyaruko', 'images/fixture_dummy2.png'),]
    d = task_dialog.MyDialog(number=len(portnames), content_widget=w, img_info=image_info)
    w.set_signal()
    app.exec_()

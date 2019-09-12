import json
from json import JSONDecodeError

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal as QSignal
from serial.serialutil import SerialException

from mylogger import logger
from serials import get_serial, issue_command


class TouchPolling(QThread):
    '''
    This class detects which cap touch key is pressed
    by polling the cap touch's i2c address.
    '''
    touchSignal = QSignal(str)

    def __init__(self, ser, key_codes = [], parent=None):
        super(TouchPolling, self).__init__(parent)
        self.ser = ser
        self.key_codes = key_codes[:]
        self.kill = False
    
    def run(self):
        while not self.kill:
            cmd = 'i2cget -f -y 1 0x1f 0x00'
            try:
                lines = issue_command(self.ser, cmd)
            except (OSError, TypeError, JSONDecodeError, SerialException):
                logger.info('TouchPolling thread terminated!')
                self.kill = True
                break
            if len(lines)>1:
                key_code = lines[1].rstrip()
                if key_code in self.key_codes:
                    self.touchSignal.emit(key_code)
                    self.key_codes.remove(key_code)
                    if not self.key_codes:
                        break
        if hasattr(self, 'ser') and self.ser.is_open:
            try:
                self.ser.close()
            except OSError:
                logger.info('TouchPolling thread terminated!')


class ContentWidget(QtWidgets.QWidget):
    runeachportResult = QSignal(str)

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
        self.clear_test()
        port = next(self.iterports)
        self.ser = get_serial(port, 115200, 0.04)
        self.touchPollingThread = TouchPolling(self.ser, self.key_codes)
        self.touchPollingThread.touchSignal.connect(self.on_touch)
        self.touchPollingThread.start()
        logger.info('init_test')
    
    def clear_test(self):
        if hasattr(self, 'touchPollingThread'):
            self.touchPollingThread.kill = True
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        self.all_color('#FFFFFF')

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
        logger.info(f'on_close {msg}')
        self.clear_test()
        self.runeachportResult.emit(json.dumps(msg))


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

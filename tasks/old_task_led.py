import sys
import json
import argparse
from PyQt5 import QtWidgets, QtCore, QtGui
from view import task_dialog
from tasks import led
from serials import get_serial

from mylogger import logger


LED_TIMEOUT = 1000

def setcolor(widget, widget_name, code):
    widget.setStyleSheet("""
        %s {
            background: %s;
        }
    """ % (widget_name, code))


class ContentWidget(QtWidgets.QWidget):
    rgb = ['#ff6e6e', '#00cc00', '#6363ff']
    cmds = [led.led_all_red, led.led_all_green, led.led_all_blue]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.idx = 0
        layout = QtWidgets.QHBoxLayout(self)

        self.leds = []
        led1 = QtWidgets.QLabel('LED')
        led2 = QtWidgets.QLabel('LED')
        led3 = QtWidgets.QLabel('LED')
        led4 = QtWidgets.QLabel('LED')
        leds = [led1, led2, led3, led4]
        self.leds.extend([led1, led2, led3, led4])
        self.all_color('#ffffff')

        layout.addWidget(led1)
        layout.addWidget(led2)
        layout.addWidget(led3)
        layout.addWidget(led4)

        self.setLayout(layout)

        self.timer = timer = QtCore.QTimer(self)
        self.timer.start(LED_TIMEOUT)

    def setports(self, portnames):
        #  print('serports start')
        self.iterports = iter(portnames)
        port = next(self.iterports)
        self.ser = get_serial(port, 115200, 0)
        #  print('serports end')

    def setsignal(self):
        self.father.message_each.connect(self.nextpage)
        self.father.message_end.connect(self.onclose)
        self.timer.timeout.connect(self.time_check)

    def all_color(self, color_code):
        for led in self.leds:
            setcolor(led, 'QWidget', color_code)

    def time_check(self):
        if self.idx >= 3:
            self.timer.stop()
            return
        logger.info('time check idx: %s' % self.idx)
        if self.idx >= 0:
            self.all_color(self.rgb[self.idx])
            self.cmds[self.idx](self.ser, 10)
        self.idx += 1

    def onclose(self, msg):
        logger.info('onclose')
        led.led_all_clear(self.ser)
        self.ser.close()
        sys.stdout.write(json.dumps(msg))

    def nextpage(self, idx):
        #  print('nextpage start')
        self.ser.close()
        self.ser = get_serial(next(self.iterports), 115200, 0)
        self.idx = 0
        logger.info('nextpage - idx:%s' % idx)
        self.all_color('#ffffff')
        led.led_all_clear(self.ser)
        self.timer = timer = QtCore.QTimer(self)
        timer.start(LED_TIMEOUT)
        timer.timeout.connect(self.time_check)
        #  print('nextpage end')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-pp', '--portnames', help='serial com port names', type=str)
    args = parser.parse_args()
    portnames = args.portnames.split(',')

    app = QtWidgets.QApplication([])
    w = ContentWidget()
    w.setports(portnames)

    img1 = 'images/fixture_dummy1.png'
    img2 = 'images/fixture_dummy2.png'
    image_info = [('No.1', 'Meyoko',  img1),
                  ('No.2', 'Nyaruko', img2),]
    #  img1 = 'images/fixture_dummy1.png'
    #  image_info = [('No.1', 'Meyoko',  img1)]
    d = task_dialog.MyDialog(number=len(portnames), content_widget=w, img_info=image_info)
    w.setsignal()
    app.exec_()

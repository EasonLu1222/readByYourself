import os
import sys
import json
import re
import pickle
import pandas as pd
from datetime import datetime
from operator import itemgetter

from PyQt5 import QtCore
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QPainterPath
from PyQt5.QtCore import (QSettings, Qt, QTranslator, QCoreApplication,
                          pyqtSignal as QSignal)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QErrorMessage, QHBoxLayout,
                             QTableWidgetItem, QLabel, QTableView, QAbstractItemView,
                             QWidget, QCheckBox, QMessageBox, QPushButton)


from view.pwd_dialog import PwdDialog
from view.barcode_dialog import BarcodeDialog
from view.loading_dialog import LoadingDialog
from core import (Task, ProcessListener, BaseVisaListener,
                  enter_prompt, enter_prompt_simu, Actions,
                 )
from serials import se, get_devices_df, BaseSerialListener
from instrument import update_serial
from utils import resource_path, QssTools
from ui.main import Ui_MainWindow
from config import station_json, LANG_LIST, STATION

# for very begin before Task initialization
from iqxel import generate_jsonfile

from mylogger import logger


class UsbPowerSensor(): comports_pws = QSignal(list)

class VisaListener(BaseVisaListener, UsbPowerSensor):
    def __init__(self, *args, **kwargs):
        devices = kwargs.pop('devices')
        super(VisaListener, self).__init__(*args, **kwargs)
        self.is_reading = False
        self.is_instrument_ready = False
        self.set_devices(devices)

    def set_devices(self, devices):
        self.devices = devices
        for k,v in devices.items():
            setattr(self, f'ports_{k}', [])


class ComportDUT(): comports_dut = QSignal(list)
class ComportPWR(): comports_pwr = QSignal(list)
class ComportDMM(): comports_dmm = QSignal(list)
class ComportELD(): comports_eld = QSignal(list)

class SerialListener(BaseSerialListener,
                     ComportDUT, ComportPWR, ComportDMM, ComportELD):
    def __init__(self, *args, **kwargs):
        devices = kwargs.pop('devices')
        super(SerialListener, self).__init__(*args, **kwargs)
        self.is_reading = False
        self.is_instrument_ready = False
        self.set_devices(devices)

    def set_devices(self, devices):
        self.devices = devices
        for k,v in devices.items():
            setattr(self, f'ports_{k}', [])


class MySettings():
    lang_list = LANG_LIST

    def __init__(self, dut_num):
        self.settings = QSettings('FAB', 'SAP109')
        self.dut_num = dut_num
        self.update()

    def get(self, key, default, key_type):
        return self.settings.value(key, default, key_type)

    def set(self, key, value):
        self.settings.setValue(key, value)
        self.update()

    def update(self):
        for i in range(1, self.dut_num+1):
            setattr(self, f'is_fx{i}_checked',
                self.get(f'fixture_{i}', False, bool))
        self.lang_index = self.get('lang_index', 0, int)
        self.is_eng_mode_on = self.get('is_eng_mode_on', False, bool)


class Label(QLabel):
    def __init__(self, *args, antialiasing=True, **kwargs):
        super(Label, self).__init__(*args, **kwargs)
        self.Antialiasing = antialiasing
        self.setMinimumSize(200, 100)
        self.radius = 100
        self.target = QPixmap(self.size())  # 大小和控件一样
        self.target.fill(Qt.transparent)  # 填充背景为透明
        p = QPixmap(resource_path("./images/fit_logo.png")).scaled(  # 加载图片并缩放和控件一样大
            170, 1, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        painter = QPainter(self.target)
        if self.Antialiasing:
            # 抗锯齿
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawPixmap(0, 0, p)
        self.setPixmap(self.target)


class MyWindow(QMainWindow, Ui_MainWindow):
    show_animation_dialog = QSignal(bool)
    msg_dialog_signal = QSignal(str)

    def __init__(self, app, task, *args):
        super(QMainWindow, self).__init__(*args)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.simulation = False

        self.pwd_dialog = PwdDialog(self)
        self.barcode_dialog = BarcodeDialog(self)
        self.barcodes = []
        self.port_barcodes = {}     # E.g. {'COM1': '1234', 'COM2': '5678'}

        self.set_task(task)
        self.set_appearance()
        self.settings = MySettings(dut_num=self.task.dut_num)
        self.make_checkboxes()

        self.langSelectMenu.setCurrentIndex(self.settings.lang_index)
        self.checkBoxEngMode.setChecked(self.settings.is_eng_mode_on)

        self.toggle_engineering_mode(self.settings.is_eng_mode_on)

        if 'dut' in self.task.serial_devices:
            self._comports_dut = dict.fromkeys(range(self.task.dut_num), None)   # E.g. {0: None, 1: None}
        else:
            self._comports_dut = {}
        self._comports_pwr = []
        self._comports_dmm = []
        self._comports_eld = []
        self._comports_pws = []

        if self.task.serial_instruments:
            update_serial(self.task.serial_instruments, 'gw_powersupply', self._comports_pwr)
            update_serial(self.task.serial_instruments, 'gw_dmm', self._comports_dmm)
            update_serial(self.task.serial_instruments, 'gw_eloader', self._comports_eld)

        self.dut_layout = []
        colors = ['#edd'] * self.task.dut_num
        for i in range(self.task.dut_num):
            c = QWidget()
            c.setStyleSheet(f'background-color:{colors[i]};')
            layout = QHBoxLayout(c)
            self.hboxPorts.addWidget(c)
            self.dut_layout.append(layout)
        self.set_hbox_visible(self.settings.is_eng_mode_on)

        self.setsignal()

        #  self.ser_listener = SerialListener(devices=self.task.devices)
        self.ser_listener = SerialListener(devices=self.task.serial_devices)
        self.ser_listener.comports_dut.connect(self.ser_update)
        self.ser_listener.comports_pwr.connect(self.pwr_update)
        self.ser_listener.comports_dmm.connect(self.dmm_update)
        self.ser_listener.comports_eld.connect(self.eld_update)
        self.ser_listener.if_all_ready.connect(self.instrument_ready)
        self.ser_listener.start()
        self.serial_ready = False

        if self.task.visa_devices:
            self.visa_listener = VisaListener(devices=self.task.visa_devices)
            self.visa_listener.comports_pws.connect(self.pws_update)
            self.visa_listener.if_all_ready.connect(self.visa_instrument_ready)
            self.visa_listener.start()
            self.visa_ready = False
        else:
            self.visa_ready = True

        self.proc_listener = ProcessListener()
        self.proc_listener.process_results.connect(self.recieve_power)
        self.power_recieved = False

        self.pushButton.setEnabled(False)

        self.power_process = {}
        self.power_results = {}

        self.on_lang_changed(self.settings.lang_index)

        self.col_dut_start = len(self.task.header())
        self.table_hidden_row()
        self.taskdone_first = False
        self.port_autodecting = False

        self.show_animation_dialog.connect(self.toggle_loading_dialog)
        self.msg_dialog_signal.connect(self.show_message_dialog)
        app.setOverrideCursor(Qt.ArrowCursor)
        self.render_port_plot()
        self.showMaximized()
        self.loading_dialog = LoadingDialog(self)
        self.set_togglebutton()

    def set_togglebutton(self):
        self.pushButton2 = QPushButton(self.container)
        self.pushButton2.setText('enable fetch')
        self.pushButton2.setObjectName("pushButton2")
        self.verticalLayout.addWidget(self.pushButton2)
        self.pushButton2.setCheckable(True)
        self.pushButton2.toggled.connect(self.btn2_toggled)
        self.pushButton2.setVisible(False)

    def btn2_toggled(self, state):
        if state:
            self.pushButton2.setText('fetching...')
            self.btn_clicked()
        else:
            self.pushButton2.setText('enable fetch')

    def set_hbox_visible(self, is_visible):
        for i in range(self.hboxPorts.count()):
            if is_visible:
                self.hboxPorts.itemAt(i).widget().show()
            else:
                self.hboxPorts.itemAt(i).widget().hide()

    def make_checkboxes(self):
        self.checkboxes = []
        for i in range(1, self.task.dut_num+1):
            cbox = QCheckBox(self.container)
            self.checkboxes.append(cbox)
            self.horizontalLayout.addWidget(cbox)
            cbox.setChecked(getattr(self.settings, f'is_fx{i}_checked'))
            cbox.setText(f'{self.cbox_text_translate}#{i}')

    def get_checkboxes_status(self):
        status_all = [self.checkboxes[i].isChecked() for i in range(self.task.dut_num)]
        return status_all

    @property
    def logfile(self):
        now = datetime.now()
        y, m, d = now.year, now.month, now.day
        path = f'logs/{y}_{m:02d}_{d:02d}.csv'
        if not os.path.isfile(path):
            with open(path, 'w') as f:
                f.write('')
        return path

    def dummy_com(self, coms):
        self._comports_dut = coms
        self.instrument_ready(True)

    def clean_power(self):
        logger.debug('clean_power start')
        # Prevent from last crash and power supply not closed normally
        for power in self.task.instruments['gw_powersupply']:
            if not power.is_open:
                power.open_com()
            if power.ser:
                power.off()
                power.close_com()
        logger.debug('clean_power end')

    def table_hidden_row(self):
        self.rowlabel_old_new = old_new = {}
        count = 0
        for i, each in enumerate(self.task.mylist):
            is_hidden = each[4]
            if not is_hidden: count += 1
            self.table_view.setRowHidden(i, is_hidden)
            old_new[i] = count
        old_new[len(old_new)] = count + 1
        self.table_view.setVerticalHeaderLabels(str(e) for e in old_new.values())

    def recieve_power(self, process_results):
        logger.debug(f'recieve_power->process_results: {process_results}')
        self.proc_listener.stop()
        self.power_results = process_results

        with open(resource_path('power_results'), 'w+') as f:
            f.write(json.dumps(process_results))
        logger.debug('recieve_power write power_results')

        self.power_recieved = True
        if self.taskdone_first:
            self.taskdone('tasks done')

    def set_task(self, task):
        self.task = task
        self.task.window = self
        self.task_results = []
        self.table_view.set_data(self.task.mylist, self.task.header_ext())
        self.table_view.setSelectionBehavior(QTableView.SelectRows)

    def set_appearance(self):
        logo_img = QPixmap(resource_path("./images/fit_logo.png"))
        self.logo = Label(self.container, antialiasing=True)
        self.logo.setText("")
        self.logo.setObjectName("logo")
        self.horizontalLayout_2.addWidget(self.logo)
        widths = self.task.appearance['columns_width']
        for col in self.task.appearance['columns_hidden']:
            self.table_view.setColumnHidden(col, True)
        for idx, w in zip(range(len(widths)), widths):
            self.table_view.setColumnWidth(idx, w)
        self.table_view.setStyleSheet('font: 16pt Segoe UI')
        self.table_view.setSpan(self.task.len(), 0, 1, len(self.task.header()))
        self.table_view.setItem(self.task.len(), 0, QTableWidgetItem(self.summary_text))
        for obj in [self, self.table_view.horizontalHeader()]:
            QssTools.set_qss_to_obj(obj)
        lb1 = QLabel(f'Program version: {getattr(thismodule, "version")}')
        lb2 = QLabel(f'Station version: {self.task.base["version"]}')
        lb1.setObjectName('lb1')
        lb2.setObjectName('lb2')
        for lb in [lb1, lb2]:
            self.statusbar.addWidget(lb, 1)
            lb.setAlignment(QtCore.Qt.AlignCenter)
            lb.setStyleSheet("QLabel#%s {background-color: #444; color: white;"
                             "font-weight: bold}" % lb.objectName())

    def poweron(self, power):
        logger.debug('poweron start')
        if not power.is_open:
            power.open_com()
            power.on()

    def poweroff(self, power):
        logger.debug('poweroff start')
        if power.ser:
            power.off()
            power.close_com()

    def clearlayout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def pwr_update(self, comports):
        logger.debug(f'pwr_update {comports}')
        self._comports_pwr = comports
        update_serial(self.task.instruments, 'gw_powersupply', comports)
        self.render_port_plot()

    def dmm_update(self, comports):
        logger.debug(f'dmm_update {comports}')
        self._comports_dmm = comports
        update_serial(self.task.instruments, 'gw_dmm', comports)
        self.render_port_plot()

    def eld_update(self, comports):
        logger.debug(f'eld_update {comports}')
        self._comports_eld = comports
        update_serial(self.task.instruments, 'gw_eloader', comports)
        self.render_port_plot()

    def pws_update(self, comports):
        logger.debug(f'pws_update {comports}')
        self._comports_pws = comports
        update_serial(self.task.instruments, 'ks_powersensor', comports)
        self.render_port_plot()

    def ser_update(self, comports):
        logger.debug(f'ser_update {comports}')
        #  dut_name, sn_numbers = itemgetter('name', 'sn')(self.task.devices['dut'])
        dut_name, sn_numbers = itemgetter('name', 'sn')(self.task.serial_devices['dut'])
        df = get_devices_df()

        if sn_numbers:
            assert len(sn_numbers) == self.task.dut_num
            if len(df)>0:
                for dut_i, sn in zip(self._comports_dut, sn_numbers):
                    df_ = df[df.sn==sn]
                    comport = df_.iat[0,0] if len(df_)==1 else None
                    self._comports_dut[dut_i] = comport
            else:
                self._comports_dut = dict.fromkeys(range(self.task.dut_num), None)
        else:
            logger.info('dut does not have sn number')
            dict_to_nonempty_list = lambda dict_: list(filter(lambda x:x, list(dict_.values())))
            list_ = dict_to_nonempty_list(self._comports_dut)
            if len(comports) > len(list_):
                list_.extend(comports)
                x = list(dict.fromkeys(list_))
                self._comports_dut = dict(zip(range(len(x)), x))
            else:
                self._comports_dut = dict(zip(range(len(comports)), comports))

        self.barcodes = []
        for dut_i, port in self._comports_dut.items():
            if port:
                self.port_barcodes[port] = None

        logger.debug(self._comports_dut)
        self.render_port_plot()

    def render_port_plot(self):
        logger.debug(f'render_port_plot')
        comports_map = {
            'gw_powersupply': self._comports_pwr,
            'gw_dmm': self._comports_dmm,
            'gw_eloader': self._comports_eld,
            'ks_powersensor': self._comports_pws,
        }

        for i, e in enumerate(self.dut_layout, 1):
            self.clearlayout(e)
            e.addWidget(QLabel(f'#{i}'))

        lb_text = 'DUT'
        for i, port in self._comports_dut.items():
            lb_port = QLabel(lb_text)
            lb_port.setProperty('state', 'default')
            QssTools.set_qss_to_obj(lb_port)

            self.dut_layout[i].addWidget(lb_port)
            if port:
                lb_port.setText(f'{lb_text}|{port}')
                lb_port.setProperty('state', 'dut_detected')
                QssTools.set_qss_to_obj(lb_port)

        for name, items in self.task.instruments.items():
            each_instruments = self.task.instruments[name]
            for i, e in enumerate(each_instruments):
                lb_text = f'{e.__class__.__name__}'
                lb_port = QLabel(lb_text)
                lb_port.setProperty('state', 'default')
                QssTools.set_qss_to_obj(lb_port)
                self.dut_layout[i].addWidget(lb_port)

                if e.interface=='serial':
                    logger.info(f'(SERIAL!!!)[inst: {e.NAME}] [{e}] [index: {e.index}] [{i}] [{e.com}]')
                    if e.com in comports_map[name]:
                        lb_port.setText(f'{lb_text}|{e.com}')
                        lb_port.setProperty('state', f'{name}_detected')
                        QssTools.set_qss_to_obj(lb_port)

                elif e.interface=='visa':
                    logger.info(f'(VISA!!!!)[inst: {e.NAME}] [{e}] [index: {e.index}] [{i}]')
                    if comports_map[name]:
                        lb_port.setText(f'{lb_text}|{e.com}')
                        lb_port.setProperty('state', f'{name}_detected')
                        QssTools.set_qss_to_obj(lb_port)

        for i in range(self.task.dut_num):
            self.dut_layout[i].addStretch()

    def visa_instrument_ready(self, ready):
        logger.debug('visa_instrument_ready start')
        if ready:
            self.visa_ready = True
            logger.debug('VISA READY')
        else:
            self.visa_ready = False
            self.pushButton.setEnabled(False)
            logger.debug('VISA NOT READY')

        if self.serial_ready and self.visa_ready:
            logger.debug('===READY===')
            self.pushButton.setEnabled(True)
            self.actions.action_signal.emit('prepare')

    def instrument_ready(self, ready):
        logger.debug('instrument_ready start')
        if ready:
            logger.debug('SERIAL READY!')
            self.serial_ready = True
            self.clean_power()

            # order: power1,power2, dmm1
            if self.task.serial_instruments:
                instruments_to_dump = sum(self.task.serial_instruments.values(), [])
                with open(resource_path('instruments'), 'wb') as f:
                    pickle.dump(instruments_to_dump, f)
        else:
            self.serial_ready = False
            logger.debug('SERIAL NOT READY!')

        if self.serial_ready and self.visa_ready:
            logger.debug('===READY===')
            self.pushButton.setEnabled(True)
            self.actions.action_signal.emit('prepare')

        else:
            logger.debug('===NOT READY===')
            self.pushButton.setEnabled(False)

    def comports(self):
        comports_as_list = list(filter(lambda x:x, self._comports_dut.values()))
        return comports_as_list

    def get_dut_selected(self):
        return [i for i, x in enumerate(self.get_checkboxes_status()) if x]

    def setsignal(self):
        for i, b in enumerate(self.checkboxes, 1):
            chk_box_state_changed = lambda state, i=i: self.chk_box_fx_state_changed(state, i)
            b.stateChanged.connect(chk_box_state_changed)
        self.langSelectMenu.currentIndexChanged.connect(self.on_lang_changed)
        self.checkBoxEngMode.stateChanged.connect(self.eng_mode_state_changed)
        self.pwd_dialog.dialog_close.connect(self.on_pwd_dialog_close)
        self.barcode_dialog.barcode_entered.connect(self.on_barcode_entered)
        self.barcode_dialog.barcode_dialog_closed.connect(self.on_barcode_dialog_closed)
        self.pushButton.clicked.connect(self.btn_clicked)
        self.task.task_result.connect(self.taskrun)
        self.task.task_each.connect(self.taskeach)
        self.task.message.connect(self.taskdone)
        se.serial_msg.connect(self.printterm1)
        self.task.printterm_msg.connect(self.printterm2)
        self.task.serial_ok.connect(self.serial_ok)
        self.task.adb_ok.connect(self.adb_ok)

    def serial_ok(self, ok):
        if ok:
            logger.debug('serial is ok!!!!')
        else:
            self.pushButton.setEnabled(True)
            logger.debug('serial is not ok!!!')

    def adb_ok(self, ok):
        if not ok:
            self.pushButton.setEnabled(True)

    def show_message_dialog(self, msg):
        # TODO: Build a dialog helper that works with the translation library
        infoBox = QMessageBox()
        infoBox.setIcon(QMessageBox.Information)
        infoBox.setText(msg)
        infoBox.exec_()

    def printterm1(self, port_msg):
        port, msg = port_msg
        msg = '[port: %s]%s' % (port, msg)
        self.edit1.appendPlainText(msg)

    def printterm2(self, msg):
        self.edit2.appendPlainText(msg)

    def taskeach(self, row_rlen):
        self.table_view.clearSelection()
        row, rowlen = row_rlen
        self.table_view.setFocusPolicy(Qt.StrongFocus)
        self.table_view.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table_view.setFocus()
        for i in range(row, row + rowlen):
            self.table_view.selectRow(i)
        self.table_view.setSelectionMode(QAbstractItemView.NoSelection)
        self.table_view.setFocusPolicy(Qt.NoFocus)

    def color_check(self, s):
        if s.startswith('Pass'):
            color = QColor(139, 195, 74)
        elif s.startswith('Fail'):
            color = QColor(255, 87, 34)
        else:
            color = QColor(255, 255, 255)
        return color

    def taskrun(self, result):
        logger.debug(f'taskrun result {result}')
        """
        Set background color of specified table cells to indicate pass/fail

        Args:
            result: A dict with the following fields:

                index(int or [int, int]): Row or row range
                idx(int): The (idx)th DUT
                port(str): The port name, used to inference idx
                output(str): 'Pass' or 'Fail'

                e.g. {'index': 0, 'idx': 0, 'port':'COM1', 'output': 'Pass'}
        """
        ret = json.loads(result)
        row = ret['index']

        # The pass/fail result applies for the jth DUT of rows from index[0] to index[1]
        if type(row) == list:
            output = ret['output']
            if type(output) == str:
                output = json.loads(output)
            logger.debug(f'output {output}')
            for i in range(*row):
                for j in self.dut_selected:
                    x = output[i - row[0]][j]
                    self.table_view.setItem(i, self.col_dut_start + j, QTableWidgetItem(x))
                    self.table_view.item(i, self.col_dut_start + j).setBackground(self.color_check(x))

        # The pass/fail result applies for the jth DUT of the specified row
        elif ('port' in ret) or ('idx' in ret):
            output = str(ret['output'])
            if 'port' in ret:
                port = ret['port']
                j = self.comports().index(port)
            elif 'idx' in ret:
                j = ret['idx']
            self.table_view.setItem(row, self.col_dut_start + j, QTableWidgetItem(output))
            self.table_view.item(row, self.col_dut_start + j).setBackground(self.color_check(output))

        # The pass/fail result applies for all selected DUT of the specified row
        else:
            output = ret['output']
            for j in self.dut_selected:
                self.table_view.setItem(row, self.col_dut_start + j, QTableWidgetItem(output))
                self.table_view.item(row, self.col_dut_start + j).setBackground(self.color_check(output))

    def taskdone(self, message):
        logger.debug('taskdone start !')
        self.taskdone_first = True
        self.table_view.setSelectionMode(QAbstractItemView.NoSelection)
        msg, t0, t1 = itemgetter('msg', 't0', 't1')(json.loads(message))
        if msg.startswith('tasks done') and self.power_recieved:
            self.pushButton.setEnabled(True)
            self.ser_listener.start()
            if not self.simulation:
                for power in self.task.instruments['gw_powersupply']:
                    if not power.is_open:
                        power.open_com()
                    if power.ser:
                        power.off()
                        power.close_com()
            r = self.task.len()
            all_pass = lambda results: all(e.startswith('Pass') for e in results)

            def get_fail_list(series):
                idx = series[series.fillna('').str.startswith('Fail')].index
                d = self.task.df
                dd = d[d.index.isin(idx)]
                items = (dd['group'] + ': ' + dd['item']).values.tolist()
                indexes = [self.rowlabel_old_new[i] for i in idx]
                fail_list = ','.join([ f'#{i}({j})' for i,j in zip(indexes,items)])
                return fail_list

            d = self.task.df
            all_res = []

            dut_num = self.task.dut_num

            print(d)
            print(d.columns)
            print(d.columns[-dut_num])

            for j, dut_i in enumerate(self.dut_selected):
                results_ = d[d.hidden == False][d.columns[-dut_num + dut_i]]
                res = 'Pass' if all_pass(results_) else 'Fail'
                fail_list = get_fail_list(d[d.columns[-dut_num+dut_i]])
                logger.debug(f'fail_list {fail_list}')
                self.table_view.setItem(r, self.col_dut_start + dut_i, QTableWidgetItem(res))
                self.table_view.item(r, self.col_dut_start + dut_i).setBackground(self.color_check(res))
                all_res.append(res)

                df = d[d.hidden == False]
                cols1 = (df.group + ': ' + df.item).values.tolist()
                dd = pd.DataFrame(df[[d.columns[-dut_num + dut_i]]].values.T, columns=cols1)

                if self.barcodes:
                    dd.index = [self.barcodes[j]]
                dd.index.name = 'pid'

                cols2_value = {
                    'Test Pass/Fail': res,
                    'Failed Tests': fail_list,
                    'Test Start Time': t0,
                    'Test Stop Time': t1,
                    'index': dut_i+1,
                }
                dd = dd.assign(**cols2_value)[list(cols2_value) + cols1]

                with open(self.logfile, 'a') as f:
                    dd.to_csv(f, mode='a', header=f.tell()==0, sep=',')

            self.set_window_color('pass' if all(e == 'Pass' for e in all_res) else 'fail')
            self.table_view.setFocusPolicy(Qt.NoFocus)
            self.table_view.clearFocus()
            self.table_view.clearSelection()
            self.taskdone_first = False
            self.power_recieved = False

            if os.path.isfile('power_results'):
                os.remove('power_results')
        self.actions.action_signal.emit('after')

    def show_barcode_dialog(self):
        logger.debug('show_barcode_dialog start')
        status_all = self.get_checkboxes_status()
        num = len(list(filter(lambda x: x == True, status_all)))
        self.barcode_dialog.set_total_barcode(num)
        if num > 0:
            self.barcode_dialog.show()
        logger.debug('show_barcode_dialog end')

    def btn_clicked(self):
        logger.debug('\n')
        self.barcodes = []
        for dut_i, port in self._comports_dut.items():
            if port:
                self.port_barcodes[port] = None
        if not any(self.get_checkboxes_status()):
            e_msg = QErrorMessage(self)
            e_msg.showMessage(self.both_fx_not_checked_err)
            return

        self.dut_selected = self.get_dut_selected()
        logger.debug(f'dut_selected {self.dut_selected}')
        for i in range(self.task.len() + 1):
            for j in range(self.task.dut_num):
                self.table_view.setItem(i, self.col_dut_start + j,
                                        QTableWidgetItem(""))
        self.set_window_color('default')
        if self.task.behaviors['barcode-scan']:
            self.show_barcode_dialog()
        else:
            self.pushButton.setEnabled(False)
            self.ser_listener.stop()
            self.task.start()

    def closeEvent(self, event):
        logger.debug('closeEvent')
        for power in self.task.instruments['gw_powersupply']:
            if power.is_open:
                power.off()
        event.accept()  # let the window close

    def chk_box_fx_state_changed(self, status, idx):
        self.settings.set(f'fixture_{idx}', status == Qt.Checked)
        getattr(self.settings ,f'is_fx{idx}_checked')

    def on_pwd_dialog_close(self, is_eng_mode_on):
        if (not is_eng_mode_on):
            self.checkBoxEngMode.setChecked(False)

    def eng_mode_state_changed(self, status):
        self.toggle_engineering_mode(status == Qt.Checked)
        if (status == Qt.Checked):
            self.pwd_dialog.show()
            self.set_hbox_visible(True)
        else:
            self.set_hbox_visible(False)

    def toggle_engineering_mode(self, is_on):
        self.settings.set("is_eng_mode_on", is_on)
        if is_on:
            self.splitter.show()
        else:
            self.splitter.hide()

    def on_lang_changed(self, index):
        """
        When language is changed, update UI
        """
        self.settings.set("lang_index", index)
        lang_list = [f'{e}.qm' for e in self.settings.lang_list]
        app = QApplication.instance()
        translator = QTranslator()
        translator.load(resource_path(f"translate/{lang_list[index]}"))
        app.removeTranslator(translator)
        app.installTranslator(translator)
        self.retranslateUi(self)
        self.pwd_dialog.retranslateUi(self.pwd_dialog)
        self.barcode_dialog.retranslateUi(self.barcode_dialog)

    def on_barcode_entered(self, barcode):
        self.barcodes.append(barcode)

    def on_barcode_dialog_closed(self):
        """
        When the barcode(s) are ready, start testing
        """
        # Return the index of Trues. E.g.: [False, True] => [1]
        header = self.task.header_ext()
        for j, dut_i in enumerate(self.dut_selected):
            header[-self.task.dut_num + dut_i] = f'#{dut_i+1} - {self.barcodes[j]}'
            port = self._comports_dut[dut_i]
            self.port_barcodes[port] = self.barcodes[j]
        self.table_view.setHorizontalHeaderLabels(header)
        self.pushButton.setEnabled(False)
        self.ser_listener.stop()
        self.task.start()

    def toggle_loading_dialog(self, is_on=False):
        if is_on:
            self.loading_dialog.show()
        else:
            self.loading_dialog.done(1)

    def set_window_color(self, state="default"):
        '''
        Set the window background color based on the test result
        Args:
            state (str): "pass", "fail" or "default"
        '''
        try:
            color = {
                "pass": "#8BC34A",
                "fail": "#FF5722",
                "default": "#ECECEC"
            }[state]
        except KeyError as e:
            color = "#ECECEC"
        self.setStyleSheet(
            f"QWidget#centralwidget {{background-color:{color} }}")

    def retranslateUi(self, MyWindow):
        super().retranslateUi(self)
        _translate = QCoreApplication.translate
        self.cbox_text_translate = _translate('MainWindow', 'DUT')
        self.summary_text = _translate("MainWindow", "Summary")
        self.both_fx_not_checked_err = _translate(
            "MainWindow", "At least one of the fixture should be checked")


if __name__ == "__main__":
    version = "0.2.2"
    thismodule = sys.modules[__name__]

    ''' === choose one of following station ===

        STATION = 'SIMULATION'

        --- SMT ---
        STATION = 'MainBoard'
        STATION = 'CapTouch'
        STATION = 'LED'

        --- FATP ---
        STATION = 'RF'
        STATION = 'WPC'
        STATION = 'Audio'
        STATION = 'PowerSensor'
        STATION = 'Download'

    '''
    app = QApplication(sys.argv)

    if STATION == 'RF': generate_jsonfile()
    task = Task(station_json[STATION])
    if not task.base: sys.exit()

    win = MyWindow(app, task)
    actions = Actions(task)
    win.actions = actions
    actions.action_trigger('first')

    app.exec_()

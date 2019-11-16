import os
import re
import time
import threading
from subprocess import Popen, PIPE
from PyQt5.QtCore import QThread, Qt, QSize
from PyQt5.QtWidgets import QHBoxLayout
from serials import is_serial_free, get_serial, issue_command, wait_for_prompt
from utils import resource_path, get_env, python_path, run, move_mainwindow_centered
from mylogger import logger

PADDING = ' ' * 4


def window_click_run(win):
    win.btn_clicked()


def wait_and_window_click_run(win, wait_sec=5):
    QThread.sleep(wait_sec)
    win.pushButton.clicked.emit()


def set_appearance(win):
    win.pushButton2.setVisible(True)
    win.pushButton.setVisible(False)


def set_acoustic_appearance(win):
    #  flags = win.windowFlags()
    #  flags &= ~Qt.FramelessWindowHint & ~Qt.WindowMaximizeButtonHint
    flags = Qt.WindowCloseButtonHint 
    win.setWindowFlags(flags)
    win.container.setVisible(False)
    win.horizontalLayout_3.addWidget(win.pushButton)
    win.horizontalLayout_3.setContentsMargins(10, 10, 10, 10)
    win.pushButton.setParent(win.centralwidget)
    win.setWindowState(Qt.WindowNoState)
    win.show()
    win.setWindowTitle('SAP109 Acoustic Enable')
    #  win.resize(1000, 50)
    #  win.setFixedSize(1000, 50)
    win.setFixedHeight(80)
    move_mainwindow_centered(win.app, win)


# for leak test
def wait_for_leak_result(win):
    win.show_animation_dialog.emit(True)
    win.loading_dialog.label_2.setText('wait for result')
    #port = win.comports()[0]
    win._comports_dut = {0: 'com1'}
    logger.debug('wait_for_leak_result')
    logger.debug(f'{PADDING}wait_for_leak_result start')

    prompt = '):'
    prompt_ok='(OK)'
    while win.pushButton2.isChecked():
        portname = win.comports()[0]
        #  logger.debug(portname)
        with get_serial(portname, 9600, timeout=0.2) as ser:
            line = ''
            try:
                line = ser.readline().decode('utf-8').rstrip('\n')
                if line: logger.debug(f'{PADDING}{line}')
            except UnicodeDecodeError as ex: # ignore to proceed
                logger.error(f'{PADDING}catch UnicodeDecodeError. ignore it: {ex}')
                continue

            if prompt in line:
                logger.info(f'{PADDING}get %s' % prompt)
                index=line.find('):')
                if prompt_ok in line:
                    leak_result = f'Pass({line[index+2:-2]})'
                    with open('leak_result', 'w') as f:
                     f.write(leak_result)
                else:
                    leak_result = f'Fail({line[index+2:-2]})'
                    with open('leak_result', 'w') as f:
                     f.write(leak_result)

                return True


    return False


def enter_prompt_simu():
    def dummy(sec):
        time.sleep(sec)

    logger.debug(f'{PADDING}enter factory image prompt start')
    t0 = time.time()
    t = threading.Thread(target=dummy, args=(1.5, ))
    t.start()
    t.join()
    t1 = time.time()
    logger.debug(f'{PADDING}enter factory image prompt end')
    logger.debug(f'{PADDING}time elapsed entering prompt: %f' % (t1 - t0))
    return True


def dummy_com_first(win, *coms):
    win._comports_dut = dict(zip(range(len(coms)), coms))
    win.instrument_ready(True)
    win.render_port_plot()
    return True


def serial_ignore_xff(window, ser_timeout=0.2):
    comports = window.comports
    for i in window.dut_selected:
        port = comports()[i]
        with get_serial(port, 115200, ser_timeout) as ser:
            # simulate press enter & ignore all the garbage
            issue_command(ser, '', False)
    return True


def press_ctrl_c(window, ser_timeout=0.2):
    comports = window.comports
    for i in window.dut_selected:
        port = comports()[i]
        with get_serial(port, 115200, ser_timeout) as ser:
            lines = issue_command(ser, '\x03', fetch=False)
    return True


def disable_power_check(win):
    win.power_recieved = True
    return True


def is_serial_ok(win, task):
    signal_from = task.serial_ok
    ports_not_free = []
    for p in win.comports():
        if not is_serial_free(p):
            logger.debug(f'    serial port {p} are not free!')
            ports_not_free.append(p)
    if len(ports_not_free)>0:
        signal_from.emit(False)
        return False
    else:
        logger.debug('    all serial port are free!')
        signal_from.emit(True)
    return True


def is_adb_ok(win, task):
    dut_selected = win.get_dut_selected
    signal_from = task.adb_ok
    print('is_adb_ok start')
    cmd = "adb start-server"
    output = run(cmd)
    cmd = "adb devices -l"
    output = run(cmd, strip=True)
    lines = output.split('\n')[1:]

    # Count the number of devices that are not offline and has transport_id
    result = sum([(not re.search('offline', l)) and (re.search('transport_id', l) is not None) for l in lines])
    ds = len(dut_selected())
    rtn = result >= ds
    if not rtn:
        print('adb devices not ready, restarting adb')
        cmd = "adb kill-server"
        run(cmd)
        cmd = "adb start-server"
        run(cmd)
        signal_from.emit(False)
    else:
        print('adb devices ready')
        signal_from.emit(True)

    return rtn


def set_power(win):
    power_process = win.power_process
    proc_listener = win.proc_listener
    script = 'tasks.poweron'
    for idx in range(1, 3):
        args = [str(idx)]

        proc = Popen([python_path(), '-m', script] + args, stdout=PIPE, env=get_env(), cwd=resource_path('.'))

        power_process[idx] = proc
    proc_listener.set_process(power_process)
    proc_listener.start()
    return True


# === STATION = SIMULATION ===

def set_power_simu(win):
    win.power_recieved = True
    win.simulation = True
    return True


def dummy_com(task):
    print('\n\ndummy com!!\n\n')
    i = 100
    for name, items in task.instruments.items():
        print('name', name)
        for e in items:
            print(' e', e)
            e.com = f'COM{i}'
            i += 1
    return True

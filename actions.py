import os
import re
import time
import threading
from subprocess import Popen, PIPE
from PyQt5.QtCore import QThread
from serials import is_serial_free, get_serial, issue_command
from utils import resource_path, get_env, python_path, run
from mylogger import logger

PADDING = ' ' * 4


def window_click_run(win):
    win.btn_clicked()


def wait_and_window_click_run(win, wait_sec=3):
    QThread.sleep(wait_sec)
    win.btn_clicked()


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


def serial_ignore_xff(window, ser_timeout=0.2):
    comports = window.comports
    for i in window.dut_selected:
        port = comports()[i]
        with get_serial(port, 115200, ser_timeout) as ser:
            # simulate press enter & ignore all the garbage
            issue_command(ser, '', False)
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

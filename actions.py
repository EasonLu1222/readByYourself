import json
import os
import re
import time
import threading
from subprocess import Popen, PIPE

import requests
from PyQt5.QtCore import QThread

from config import TOTAL_MAC_URL
from serials import is_serial_free, get_serial, issue_command
from utils import resource_path, get_env, python_path, run
from mylogger import logger
from tasks.task_sfc import check_sfc


PADDING = ' ' * 4


def window_click_run(win):
    win.btn_clicked()


def wait_and_window_click_run(win, wait_sec=5):
    QThread.sleep(wait_sec)
    win.pushButton.clicked.emit()


def set_appearance(win):
    win.pushButton2.setVisible(True)
    win.pushButton.setVisible(False)


def is_sfc_ok(win, task):
    signal_from = task.general_ok
    for barcode in win.barcodes:
        res = check_sfc("", 0, f"{task.sfc_station_id},{barcode}")

        if res.startswith('Fail'):
            win.msg_dialog_signal.emit(f"{barcode} SFC check failed! {res}")
            signal_from.emit(False)
            return False

    return True


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
    while True:
        portname = win.comports()[0]
        #  logger.debug(por
        with get_serial(portname, 9600, timeout=0.2) as ser:
            line = ''
            try:
                line0 = ser.readline()
                logger.debug(line0)
                line = line0.decode('utf-8').rstrip('\n')
                #line = ser.readline().decode('utf-8').rstrip('\n')
                if line: logger.debug(f'{PADDING}{line}')
            except UnicodeDecodeError as ex: # ignore to proceed
                logger.error(f'{PADDING}catch UnicodeDecodeError. ignore it: {ex}')
                leak_result = f'Fail(UnicodeDecodeError)'
                with open(resource_path('leak_result'), 'w') as f:
                    f.write(leak_result)

            if prompt in line:
                logger.info(f'{PADDING}get %s' % prompt)
                index=line.find('):')
                leak_value = line[index + 2:-2].strip()
                logger.debug(f'{PADDING}[Leak Debug] prompt_ok in line: {prompt_ok in line}')
                if prompt_ok in line:
                    leak_result = f'Pass({leak_value})'
                    logger.debug(f'{PADDING}[Leak Debug] in prompt_ok in line block, leak_result:{leak_result}')
                    with open(resource_path('leak_result'), 'w') as f:
                        logger.debug(f'{PADDING}[Leak Debug] writing pass result to {resource_path("leak_result")}')
                        f.write(leak_result)
                else:
                    leak_result = f'Fail({leak_value})'
                    logger.debug(f'{PADDING}[Leak Debug] not in prompt_ok in line block, leak_result:{leak_result}')
                    with open(resource_path('leak_result'), 'w') as f:
                        logger.debug(f'{PADDING}[Leak Debug] writing fail result to {resource_path("leak_result")}')
                        f.write(leak_result)

                logger.debug(f'{PADDING}[Leak Debug] return True')
                return True


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
    # TODO: Should do it the opposite way. That is, to make "disable_power_check" the default behavior,
    #  and usd "enable_power_check" in MainBoard station instead. That way, a lot of disable_power_check
    #  in jsonfile can be removed.
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
    # Force revives adb
    dut_selected = win.get_dut_selected()
    signal_from = task.adb_ok
    cmd = 'echo ff400000.dwc2_a > /sys/kernel/config/usb_gadget/amlogic/UDC'
    comports = win.comports
    adb_status = []
    for i in dut_selected:
        is_adb_alive = False
        port = comports()[i]
        with get_serial(port, 115200, 0.1) as ser:
            lines = issue_command(ser, cmd)
        if not lines:
            lines = []
        for l in lines:
            if ('USB_STATE=CONNECTED' in l) or ('resource busy' in l):
                is_adb_alive = True
                break
        adb_status.append(is_adb_alive)

    # Count the number of devices that are not offline and has transport_id
    cmd = "adb devices -l"
    output = run(cmd, strip=True)
    lines = output.split('\n')[1:]
    result = sum([(not re.search('offline', l)) and (re.search('transport_id', l) is not None) for l in lines])
    ds = len(dut_selected)
    is_adb_list_ok = result >= ds

    rtn = all(adb_status) and is_adb_list_ok
    if rtn:
        logger.debug('adb devices ready')
        signal_from.emit(True)
    else:
        logger.debug('adb devices not ready')
        signal_from.emit(False)

    return rtn


def set_power(win):
    power_process = win.power_process
    proc_listener = win.proc_listener
    script = 'tasks.poweron'
    for idx in range(1, 3):
        args = [str(idx)]

        proc = Popen([python_path(), '-m', script] + args, stdout=PIPE, env=get_env())

        power_process[idx] = proc
    proc_listener.set_process(power_process)
    proc_listener.start()
    return True


def get_remaining_addr():
    total_addr_count = 0
    remaining_addr_count = 0
    try:
        url = f'{TOTAL_MAC_URL}'
        r = requests.get(url, timeout=1)
        res_json = json.loads(r.text)
        total_addr_count = int(res_json['Data'][0]['total'])
        remaining_addr_count = int(res_json['Data'][1]['usable'])
    except Exception as e:
        logger.error(f'{e}')

    return total_addr_count, remaining_addr_count


def remaining_addr_init(win):
    total_addr_count, remaining_addr_count = get_remaining_addr()
    win.show_mac_address_signal.emit(total_addr_count, remaining_addr_count)
    return True


def remaining_addr(win):
    total_addr_count, remaining_addr_count = get_remaining_addr()

    if remaining_addr_count < 2000:
        win.msg_dialog_signal.emit(f"Remaining mac address : {remaining_addr_count} ,  less than 2000!")
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

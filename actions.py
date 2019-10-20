import os
import re
from subprocess import Popen, PIPE
from serials import is_serial_free
from utils import resource_path, get_env, python_path, run


def disable_power_check(win):
    win.power_recieved = True
    return True


def is_serial_ok(comports, signal_from):
    print('is_serial_ok start')
    print('comports', comports)
    print('signal_from', signal_from)
    if not all(is_serial_free(p) for p in comports()):
        print('not all serial port are free!')
        signal_from.emit(False)
        return False
    else:
        print('all serial port are free!')
        signal_from.emit(True)
        return True


def is_adb_ok(dut_selected):
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
    else:
        print('adb devices ready')

    return rtn


def set_power(power_process, proc_listener):
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

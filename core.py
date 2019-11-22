import os
import re
import sys
import json
import time
import inspect
import threading
import importlib
from datetime import datetime
from operator import itemgetter
from subprocess import Popen, PIPE
from collections import defaultdict
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal as QSignal
from PyQt5.QtWidgets import QMessageBox
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils import resource_path, get_env, python_path, s_
from instrument import get_visa_devices, generate_instruments, INSTRUMENT_MAP
from mylogger import logger
from config import (DEVICES, SERIAL_DEVICES, VISA_DEVICES, SERIAL_DEVICE_NAME,
                    VISA_DEVICE_NAME, STATION)
from serials import enter_factory_image_prompt, get_serial, wait_for_prompt2
from iqxel import run_iqfactrun_console
from db.sqlite import fetch_addr

from actions import (
    disable_power_check, set_power_simu, dummy_com,
    window_click_run, is_serial_ok, set_power, is_adb_ok,
    serial_ignore_xff, dummy_com_first, enter_prompt_simu,
    wait_and_window_click_run, wait_for_leak_result, set_appearance,
    press_ctrl_c, set_acoustic_appearance,
)

# for prepares
from iqxel import prepare_for_testflow_files

if STATION == 'Audio':
    from soundcheck import soundcheck_init

PADDING = ' ' * 2


def enter_prompt(window, ser_timeout=0.2, waitwordidx=8):
    logger.debug(f'{PADDING}enter factory image prompt start')
    t0 = time.time()
    port_ser_thread = {}
    comports = window.comports
    logger.debug(f'{PADDING}enter_prompt: comports -  {comports}')
    for i in window.dut_selected:
        port = comports()[i]
        ser = get_serial(port, 115200, ser_timeout)
        t = threading.Thread(target=enter_factory_image_prompt,
                             args=(ser, waitwordidx))
        port_ser_thread[port] = [ser, t]
        t.start()
    for port, (ser, th) in port_ser_thread.items():
        th.join()
    t1 = time.time()
    logger.debug(f'{PADDING}enter factory image prompt end')
    logger.debug(f'{PADDING}time elapsed entering prompt: %f' % (t1 - t0))
    for port, (ser, th) in port_ser_thread.items():
        ser.close()
    return True


def enter_prompt2(window, ser_timeout=0.2, empty_wait=5):
    logger.debug(f'{PADDING}start')
    t0 = time.time()
    port_ser_thread = {}
    comports = window.comports
    logger.debug(f'{PADDING}enter_prompt: comports -  {comports}')
    for i in window.dut_selected:
        port = comports()[i]
        ser = get_serial(port, 115200, ser_timeout)
        t = threading.Thread(target=wait_for_prompt2,
                             args=(ser, empty_wait))
        port_ser_thread[port] = [ser, t]
        t.start()
    for port, (ser, th) in port_ser_thread.items():
        th.join()
    t1 = time.time()
    logger.debug(f'{PADDING}end')
    logger.debug(f'{PADDING}time elapsed: %f' % (t1 - t0))
    for port, (ser, th) in port_ser_thread.items():
        ser.close()
    return True


def check_json_integrity(filename):
    path1 = resource_path(f'jsonfile/{filename}.json')
    path2 = os.path.join(os.path.abspath(os.path.curdir), 'jsonfile',
                         f'{filename}.json')
    logger.debug(f'{PADDING}path1 {path1}')
    logger.debug(f'{PADDING}path2 {path2}')

    def check_each_json(path):
        try:
            j = json.loads(open(path, 'r').read())
        except json.JSONDecodeError as ex:
            logger.error(f'{PADDING}==ERROR== {ex}')
            return False

        for dev, v in j['devices'].items():
            num, sn = v['num'], v['sn']
            if type(sn) != list:
                return False
            elif sn and len(sn) != num:
                return False
            del j['devices'][dev]['sn']
        return j

    j1 = check_each_json(path1)
    j2 = check_each_json(path2)
    if j1 and j2:
        if path1 == path2:
            # do not check integrity before pyinstaller deployment
            return True  # json file integrity is good
        else:
            return True if j1 == j2 else False
    else:
        return False


def parse_json(jsonfile):
    x = json.loads(open(jsonfile, 'r', encoding='utf8').read())
    groups = defaultdict(list)
    cur_group = None
    x = x['test_items']
    group_orders = []
    for e in x:
        group_name = e['group']
        if not group_name in group_orders:
            group_orders.append(group_name)
        del e['group']
        groups[group_name].append(e)
    groups = {k: groups[k] for k in group_orders}

    idx = 0
    for k, items in groups.items():
        for e in items:
            e['index'] = idx
            idx += 1
    return groups


class ProcessListener(QThread):
    process_results = QSignal(dict)

    def __init__(self):
        super(ProcessListener, self).__init__()

    def set_process(self, processes):
        self.processes = processes

    def run(self):
        outputs = {}
        for pid, proc in self.processes.items():
            output, _ = proc.communicate()
            output = output.decode('utf8')
            outputs[pid] = float(output)
        self.process_results.emit(outputs)

    def stop(self):
        self.terminate()


class BaseVisaListener(QThread):
    update_msec = 500
    if_all_ready = QSignal(bool)

    def __init__(self, *args, **kwargs):
        super(BaseVisaListener, self).__init__(*args, **kwargs)
        self.is_reading = False
        self.is_instrument_ready = False

    def filter_devices(self, devices, name, field='comport'):
        filtered = [e[field] for e in [e for e in devices if e['name'] == name]]
        return filtered

    def get_update_ports_map(self):
        devices = get_visa_devices()
        ports_map = {}
        for k, v in self.devices.items():
            ports = self.filter_devices(devices, v['name'])
            ports_map[k] = ports
        return ports_map

    def update(self, devices_prev, devices):
        set_prev, set_now = set(devices_prev), set(devices)
        if set_prev != set_now:
            if set_now > set_prev:
                d = set_now - set_prev
                devices_prev.extend(list(d))
            else:
                d = set_prev - set_now
                for e in d:
                    devices_prev.remove(e)
            return True
        return False

    def port_full(self, excludes=None):
        for k, v in self.devices.items():
            if not v['name']:
                continue

            if excludes:
                for e in excludes:
                    if k == e: continue
            if len(getattr(self, f'ports_{k}')) < v['num']:
                return False
        return True

    def run(self):
        while True:
            QThread.msleep(BaseVisaListener.update_msec)
            self.is_reading = True
            ports_map = self.get_update_ports_map()
            for k in self.devices.keys():
                ports = ports_map[k]
                self_ports = getattr(self, f'ports_{k}')
                self_comports = getattr(self, f'comports_{k}')
                if self.update(self_ports, ports):
                    self_comports.emit(self_ports)
            self.is_reading = False

            if not self.is_instrument_ready and self.port_full():
                self.is_instrument_ready = True
                self.if_all_ready.emit(True)
            if self.is_instrument_ready and not self.port_full():
                self.is_instrument_ready = False
                self.if_all_ready.emit(False)

    def stop(self):
        logger.info(f'{PADDING}BaseVisaListener stop start')
        # wait 1s for list_ports to finish, is it enough or too long in order
        # not to occupy com port for subsequent test scripts
        if self.is_reading:
            QThread.msleep(1000)
        self.terminate()
        logger.info(f'{PADDING}BaseVisaListener stop end')


class Actions(QThread):
    action_signal = QSignal(str)

    def __init__(self, task):
        super(Actions, self).__init__()
        self.task = task
        firsts, prepares, actions, afters = self.parse_action_all()
        self.actions = {}

        first = Action('first', firsts)
        prepare = Action('prepare', prepares)
        action = Action('action', actions)
        after = Action('after', afters)

        self.register_action(first, to_connect=False)
        self.register_action(prepare, to_connect=True)
        self.task.register_action(actions)
        #  self.register_action(action, to_connect=False)
        self.register_action(after, to_connect=True)

    def parse_action_all(self):
        actions_all = [
            self.parse_for_register(e)
            for e in ['firsts', 'prepares', 'actions', 'afters']
        ]
        return actions_all

    def parse_for_register(self, actions_or_prepares):
        items = self.task.base['behaviors'][actions_or_prepares]
        for e in items:
            item_name = actions_or_prepares[:-1]  # sigular not plural
            item, args = e[item_name], e['args']
            item = eval(item)
            args_parsed = []
            if args:
                for a in args:
                    if a=='win': a = 'self.task.window'
                    if a=='task': a = 'self.task'
                    if a=='thismodule': a = sys.modules['__main__']
                    try:
                        args_parsed.append(eval(a))
                    except Exception as ex:
                        args_parsed.append(a)
            e[item_name] = item
            e['args'] = args_parsed
        return items

    def register_action(self, action, to_connect=True):
        logger.debug(f'{PADDING}{action.name}')
        self.actions[action.name] = action
        if to_connect:
            self.action_signal.connect(self.action_start)
            self.actions[action.name].action_done.connect(
                getattr(self, f'{action.name}_done'))

    def prepare_done(self):
        print('prepare_done')

    def after_done(self):
        print('after_done')

    def action_start(self, action_name):
        logger.debug(f'{PADDING}action_start {action_name}')
        self.actions[action_name].start()

    def action_trigger(self, action_name):
        logger.debug(f'{PADDING}action_trigger')
        Action.trigger(self.actions[action_name].action_args)


class Action(QThread):
    action_done = QSignal()

    def __init__(self, action_name, actions):
        super(Action, self).__init__()
        self.action_args = list()
        self.name = action_name
        self.update_action(actions)

    def update_action(self, actions):
        logger.debug(f'{PADDING}{self.name}')
        for e in actions:
            action, args = e[f'{self.name}'], e['args']
            logger.debug(f'{PADDING}> {action.__name__}')
            self.action_args.append([action, args])

    @classmethod
    def trigger(cls, action_args):
        logger.debug(f'{PADDING}trigger')
        for action, args in action_args:
            aname = action.__name__
            logger.debug(f'{PADDING}run action {aname}')
            if not action(*args):
                logger.debug(f'{PADDING}{aname} is False --> return')
                return
        logger.debug(f'{PADDING}Action run end')

    def run(self):
        Action.trigger(self.action_args)
        self.action_done.emit()
        logger.debug(f'{PADDING}Action run end')


class MyHandler(FileSystemEventHandler):
    def __init__(self, ob, file_to_monitor):
        self.file = self._path(file_to_monitor)
        self.lines = self.readlines(self.file)
        #  print('lines', len(self.lines))
        self.to_stop = False
        self.result = None

    def readlines(self, file):
        with open(file) as f:
            return f.readlines()

    def _path(self, path):
        return path.replace('\\', '/')

    def on_modified(self, event):
        results = []
        if self._path(event.src_path) == self.file:
            #  print("The file is modified")
            lines = [e.strip() for e in self.readlines(self.file)]
            if len(lines) > len(self.lines):
                diff = lines[len(self.lines):]
                print('\n\n\n')
                for e in diff:
                    _, name, _, _, result, _, _ = e.strip().split('\t')
                    print('name', name, 'result', result)
                    results.append(result)
                print('\n\n\n')
                self.result = results
                self.to_stop = True
            self.lines = lines


class Task(QThread):
    '''
    there's three types of tasks
            1. DUT Based
                a. serial port of DUTs only
                b. one process per row, one process per DUT
            2. Instrument Based
                a. serial port of instruments only
                b. one process to handle rows and duts
            3. Mixed
                a. serial port of both DUTs and instruments
                b. TBD
    '''
    task_each = QSignal(list)
    task_result = QSignal(str)
    serial_ok = QSignal(bool)
    adb_ok = QSignal(bool)
    message = QSignal(str)
    printterm_msg = QSignal(str)
    show_task_dialog = QSignal(list)
    trigger_snk = QSignal(str)

    def __init__(self, json_name, json_root='jsonfile'):
        super(Task, self).__init__()
        self.json_root = json_root
        self.json_name = json_name
        self.jsonfile = f'{json_root}/{json_name}.json'
        logger.info(f'{PADDING}{self.jsonfile}')
        #  if not check_json_integrity(self.json_name):
        #  if QMessageBox.warning(None, 'Warning',
        #  'You can not change jsonfile content besides the serial numbers',
        #  QMessageBox.Yes):
        #  self.base = None
        #  return

        self.base = json.loads(open(self.jsonfile, 'r', encoding='utf8').read())
        self.groups = parse_json(self.jsonfile)
        self.action_args = list()
        self.df = self.load()
        self.instruments = generate_instruments(self.devices, INSTRUMENT_MAP)
        logger.debug(f'{PADDING}Task.instruments')
        for k, v in self.instruments.items():
            logger.debug(f'{PADDING}{k} ---> {v}')

    @property
    def serial_instruments(self):
        name_int = dict(DEVICES.values())  # {intrument_name: interface}
        filtered = {
            k: v
            for k, v in self.instruments.items() if name_int[k] == 'serial'
        }
        serial_inst = defaultdict(list)
        serial_inst.update(filtered)
        return serial_inst

    @property
    def visa_instruments(self):
        name_int = dict(DEVICES.values())  # {intrument_name: interface}
        filtered = {
            k: v
            for k, v in self.instruments.items() if name_int[k] == 'visa'
        }
        visa_inst = defaultdict(list)
        visa_inst.update(filtered)
        return visa_inst

    @property
    def mylist(self):
        return self.df.fillna('').values.tolist()

    @property
    def dut_num(self):
        return self.base['devices']['dut']['num']

    def load(self):
        header = self.base['header']
        header_dut = self.header_dut()
        df = pd.DataFrame(self.base['test_items'])
        self.df = df = df[header]
        for col in header_dut:
            df[col] = None
        return df

    def __len__(self):
        return len(self.groups)

    def len(self, include_hidden=True):
        if include_hidden:
            return len(self.df)
        else:
            return len(self.df[self.df['hidden'] == False])

    def __getitem__(self, key):
        return self.groups[key]

    def keys(self):
        return self.groups.keys()

    def items(self):
        return self.groups.items()

    def __iter__(self):
        for k in self.keys():
            yield k

    def each(self, index):
        x = [self[k] for k, v in self.items()]
        return sum(x, [])[index]

    def limits(self, key, idx):
        each = self[key][idx]
        min_, expect, max_ = itemgetter('min', 'expect', 'max')(each)
        return (min_, expect, max_)

    @property
    def devices(self):
        all_devices = {}
        if self.serial_devices:
            all_devices.update(self.serial_devices)
        if self.visa_devices:
            all_devices.update(self.visa_devices)
        return all_devices

    @property
    def serial_devices(self):
        devices = self.base['devices']
        serial_devices = {
            k: v
            for k, v in devices.items() if v['name'] in SERIAL_DEVICE_NAME
        }
        return serial_devices

    @property
    def visa_devices(self):
        devices = self.base['devices']
        visa_devices = {
            k: v
            for k, v in devices.items() if v['name'] in VISA_DEVICE_NAME
        }
        return visa_devices

    @property
    def behaviors(self):
        return self.base['behaviors']

    @property
    def appearance(self):
        return self.base['appearance']

    def header_dut(self, dut_names=None):
        if dut_names:
            return dut_names
        else:
            num = self.dut_num
            header = ['#%d' % e for e in list(range(1, 1 + num))]
            return header

    def header(self):
        return self.base['header']

    def header_ext(self, dut_names=None):
        header_extension = dut_names if dut_names else self.header_dut()
        return self.header() + header_extension

    def unpack_group(self, groupname):
        eachgroup = self[groupname]
        script = f'tasks.{eachgroup[0]["script"]}'
        item_len = len(eachgroup)
        index = eachgroup[0]['index']
        tasktype = eachgroup[0]['tasktype']
        args = [g['args'] for g in eachgroup]
        return eachgroup, script, index, item_len, tasktype, args

    def unpack_each(self, index):
        each = self.each(index)
        line = self.df.values[index]
        script = 'tasks.%s' % each['script']
        args = [str(e) for e in each['args']] if each['args'] else []
        return each, script, args

    def rungroup(self, groupname):
        eachgroup, script, index, item_len, tasktype, args = self.unpack_group(
            groupname)
        logger.debug(
            f'{PADDING}[rungroup][{s_(script)}][{s_(index)}][{s_(item_len)}][{s_(args)}]'
        )
        limits_group = [self.limits(groupname, i) for i in range(item_len)]
        limits = {}
        for e in zip(*args):
            xx = {i: j for i, j in zip(e, limits_group)}
            limits.update(xx)
        logger.debug(f'{PADDING}limits {limits}')
        args = {'args': args, 'limits': limits}

        coms = {}
        for k, v in self.instruments.items():
            interface = dict(DEVICES.values())[k]
            if interface == 'serial':
                com_to_extract = 'com'
            elif interface == 'visa':
                com_to_extract = 'visa_addr'
            if len(v) > 0:
                coms.update({k: [getattr(e, com_to_extract) for e in v]})

        coms = json.dumps(coms)

        proc = Popen([python_path(), '-m', script, '-p', coms] +
                     [json.dumps(args)],
                     stdout=PIPE,
                     env=get_env(),
                     cwd=resource_path('.'))

        return proc

    def runeach(self, row_idx, dut_idx, dynamic_info):
        port = self.window.comports()[dut_idx]
        each, script, args = self.unpack_each(row_idx)
        msg = f'{PADDING}[runeach][{s_(script)}][{s_(row_idx)}][{s_(dut_idx)}][{s_(port)}][{s_(dynamic_info)}][{s_(args)}]'
        logger.debug(msg)
        arguments = [
            python_path(), '-m', script, '-p', port, '-i',
            str(dut_idx), '-s', dynamic_info
        ]
        if args: arguments.append(args)
        proc = Popen(arguments,
                     stdout=PIPE,
                     env=get_env(),
                     cwd=resource_path('.'))
        self.printterm_msg.emit(msg)
        return proc

    def runeachports(self, index, ports):
        '''
        Set the window background color based on the test result
        Args:
            index (int): The row index of the test item
            ports (str): The COM ports concatenated by "," e.g. "COM1,COM2"
        '''
        line = self.df.values[index]
        script = 'tasks.%s' % line[0]
        args = [str(e) for e in line[1]] if line[1] else []
        msg = f'{PADDING}[rungroup][{s_(script)}][{s_(index)}][{s_(ports)}][{s_(args)}]'
        logger.debug(msg)
        self.printterm_msg.emit(msg)
        selected_duts = ','.join([str(s) for s in self.window.dut_selected
                                  ])  # E.g. '0,1'

        proc = Popen(
            [python_path(), '-m', script, '-pp', ports, '-ds', selected_duts] +
            args,
            stdout=PIPE,
            env=get_env())

        outputs, _ = proc.communicate()
        if not outputs:
            logger.warning(f'{PADDING}outputs is None!!!!')
        outputs = outputs.decode('utf8')
        outputs = json.loads(outputs)
        msg2 = '[task %s][outputs: %s]' % (
            index, outputs)  # E.g. outputs = ['Pass', 'Fail']
        self.printterm_msg.emit(msg2)

        port_list = ports.split(',')
        for idx, output in enumerate(outputs):
            result = json.dumps({
                'index': index,
                'port': port_list[idx],
                'idx': idx,
                'output': output
            })
            self.df.iat[index,
                        len(self.header()) +
                        self.window.dut_selected[idx]] = output
            self.task_result.emit(result)

    def register_action(self, actions):
        for e in actions:
            action, args = e['action'], e['args']
            logger.debug(f'{PADDING} {action}')
            self.action_args.append([action, args])

    #  def register_action(self, action, to_connect=True):
        #  logger.debug(f'register_action {action.name}')
        #  self.actions[action.name] = action
        #  if to_connect:
            #  self.action_signal.connect(self.action_start)
            #  self.actions[action.name].action_done.connect(
                #  getattr(win, f'{action.name}_done'))

    def run_task1(self, group, items):
        row_idx, next_item = items[0]['index'], items[0]
        procs = {}
        if any(self.window.port_barcodes.values()):
            for port, barcode in self.window.port_barcodes.items():
                if barcode:
                    dut_idx = self.window.comports().index(port)
                    proc = self.runeach(row_idx, dut_idx, barcode)
                    procs[port] = proc
        else:
            func = next_item['args'][0]
            dynamic_info = ''
            if func == 'write_wifi_bt_mac':
                dynamic_info = fetch_addr()
            if func == 'write_country_code':
                dynamic_info = 'CN01'

            for dut_idx in self.window.dut_selected:
                proc = self.runeach(row_idx, dut_idx, dynamic_info)
                port = self.window.comports()[dut_idx]
                procs[port] = proc

        logger.debug(f'{PADDING}procs {procs}')
        header = self.header_ext()
        for j, (port, proc) in enumerate(procs.items()):
            output, _ = proc.communicate()
            logger.critical(output)
            output = output.decode('utf8')
            msg2 = '[task %s][output: %s]' % (row_idx, output)
            self.printterm_msg.emit(msg2)
            result = json.dumps({
                'index': row_idx,
                'port': port,
                'output': output
            })
            self.df.iat[row_idx,
                        len(self.header()) +
                        self.window.dut_selected[j]] = output

            if not any(self.window.port_barcodes.values()):
                script = next_item['script']
                func = next_item['args'][0]
                to_read_pid = (script == 'task_runeach' and func.startswith('read_pid'))

                if to_read_pid:
                    if output.startswith('Pass'):
                        pid = output[5:-1]
                        dut_i = self.window.dut_selected[j]
                        header[-self.dut_num + dut_i] = f'#{dut_i+1} - {pid}'
                    elif output.startswith('Fail'):
                        pid = '0'

                    self.window.table_view.setHorizontalHeaderLabels(header)
                    self.window.barcodes.append(pid)

            self.task_result.emit(result)

    def run_task2(self, group, items):
        row = items[0]['index']
        proc = self.rungroup(group)
        output, _ = proc.communicate()
        output = output.decode('utf8')
        msg2 = '[task %s][output: %s]' % ([row, row + len(items)], output)
        self.printterm_msg.emit(msg2)
        result = json.dumps({
            'index': [row, row + len(items)],
            'output': output
        })
        r1, r2 = row, row + len(items)
        c1 = len(self.header()) + self.window.dut_selected[0]
        c2 = c1 + len(self.window.dut_selected)
        output = json.loads(output)
        get_col = lambda arr, col: map(lambda x: x[col], arr)
        if len(self.window.dut_selected) == 1:
            output = [[e] for e in get_col(output, self.window.dut_selected[0])]
        logger.debug(f'{PADDING}OUTPUT {output}')
        self.df.iloc[r1:r2, c1:c2] = output
        self.task_result.emit(result)

    def run_task3(self, group, items):
        row = items[0]['index']
        selected_port_list = []
        for selected_i in self.window.dut_selected:
            selected_port_list.append(self.window._comports_dut[selected_i])
        selected_port_str = ','.join(selected_port_list)
        self.runeachports(row, selected_port_str)

    def run_task4(self, group, items):
        row = items[0]['index']
        line = self.df.values[row]
        mod_name = f'tasks.{line[0]}'
        mod = importlib.import_module(mod_name)

        func_list = [str(e) for e in line[1]] if line[1] else []

        func = getattr(mod, func_list[0])
        t = threading.Thread(target=func)
        t.start()
        r1, r2 = row, row + 1
        c1 = len(self.header()) + self.window.dut_selected[0]
        c2 = c1 + len(self.window.dut_selected)
        self.df.iloc[r1:r2, c1:c2] = "Pass"

        result = json.dumps({'index': row, 'output': "Pass"})
        self.task_result.emit(result)

    def run_task9(self, group, items):
        row, next_item = items[0]['index'], items[0]
        obj_name, method_name = next_item['args']
        obj = getattr(sys.modules['__main__'], obj_name)
        output = getattr(obj, method_name)()
        r1, r2 = row, row + len(items)
        c1 = len(self.header()) + self.window.dut_selected[0]
        c2 = c1 + len(self.window.dut_selected)
        if len(self.window.dut_selected) == 1:
            output = [[e] for e in output]
        result = json.dumps({
            'index': [row, row + len(items)],
            'output': output
        })
        self.df.iloc[r1:r2, c1:c2] = output
        self.task_result.emit(result)

    def run_task10(self, group, items):
        from datetime import datetime
        row, next_item = items[0]['index'], items[0]

        self.trigger_snk.emit('run_sqc')

        observer = Observer()
        path = 'F:\SAP 109 DATA'
        now = datetime.now().strftime('%m-%d-%Y')
        #  filename = 'SAP109 Results 11-20-2019.txt'
        filename = f'SAP109 Results {now}.txt'
        filepath = os.path.join(path, filename)
        print('filepath', filepath)

        if not os.path.isfile(filepath):
            with open(filepath, 'w') as f:
                f.write('Time: 	Name	Margin	Unit	Result	Tolerance	Limits\n')

        event_handler = MyHandler(observer, filepath)
        observer.schedule(event_handler, path=path)
        observer.start()
        try:
            while not event_handler.to_stop:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()

        output = [e.capitalize() for e in event_handler.result]
        r1, r2 = row, row + len(items)
        c1 = len(self.header()) + self.window.dut_selected[0]
        c2 = c1 + len(self.window.dut_selected)
        if len(self.window.dut_selected) == 1:
            output = [[e] for e in output]
        result = json.dumps({
            'index': [row, row + len(items)],
            'output': output
        })
        self.df.iloc[r1:r2, c1:c2] = output
        self.task_result.emit(result)

    def run_task11(self, group, items):
        threads = {}
        for dut_idx in self.window.dut_selected:
            port = self.window.comports()[dut_idx]
            logger.debug(f'{PADDING}dut_idx:  {dut_idx}')
            logger.debug(f'{PADDING}port:  {port}')
            threads[dut_idx] = th = threading.Thread(
                target=run_iqfactrun_console,
                args=(self, dut_idx, port, group,)
            )
            th.start()
        for dut_idx, th in threads.items():
            th.join()

    def run(self):
        time_ = lambda: datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')
        self.window.show_animation_dialog.emit(True)

        #  QThread.msleep(1000)
        t0 = time_()
        for action, args in self.action_args:
            aname = action.__name__
            logger.debug(f'{PADDING}run action {aname}')
            if not action(*args):
                logger.debug(f'{PADDING}{aname} is False --> return')
                self.window.show_animation_dialog.emit(False)
                if STATION != 'Leak':
                    self.window.msg_dialog_signal.emit(f"發生錯誤({action})")

                if STATION != 'CapTouchMic':
                    self.window.ser_listener.start()
                return

        #  QThread.msleep(500)
        self.window.show_animation_dialog.emit(False)
        c1 = len(self.header())
        self.df.iloc[:, c1:c1 + self.dut_num] = ""
        for group, items in self.groups.items():
            row, next_item = items[0]['index'], items[0]
            is_auto, task_type = next_item['auto'], next_item['tasktype']
            if task_type != 11:
                self.task_each.emit([row, len(items)])
            getattr(self, f'run_task{task_type}')(group, items)
            QThread.msleep(500)

        t1 = time_()
        self.df = self.df.fillna('')
        message = {
            'msg': 'tasks done',
            't0': t0,
            't1': t1,
        }
        self.message.emit(json.dumps(message))

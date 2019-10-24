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

from utils import resource_path, get_env, python_path
from instrument import get_visa_devices, generate_instruments, INSTRUMENT_MAP
from mylogger import logger
from config import (DEVICES, SERIAL_DEVICES, VISA_DEVICES,
                    SERIAL_DEVICE_NAME, VISA_DEVICE_NAME)
from serials import enter_factory_image_prompt, get_serial
from iqxel import run_iqfactrun_console
from utils import s_


def enter_prompt_simu():
    def dummy(sec):
        time.sleep(sec)
    logger.debug('enter factory image prompt start')
    t0 = time.time()
    t = threading.Thread(target=dummy, args=(1.5, ))
    t.start()
    t.join()
    t1 = time.time()
    logger.debug('enter factory image prompt end')
    logger.debug('time elapsed entering prompt: %f' % (t1 - t0))
    return True


def enter_prompt(window, ser_timeout=0.2, waitwordidx=8):
    logger.debug('enter factory image prompt start')
    t0 = time.time()
    port_ser_thread = {}
    comports = window.comports
    logger.debug(f'enter_prompt: comports -  {comports}')
    for i in window.dut_selected:
        port = comports()[i]
        ser = get_serial(port, 115200, ser_timeout)
        t = threading.Thread(target=enter_factory_image_prompt, args=(ser, waitwordidx))
        port_ser_thread[port] = [ser, t]
        t.start()
    for port, (ser, th) in port_ser_thread.items():
        th.join()
    t1 = time.time()
    logger.debug('enter factory image prompt end')
    logger.debug('time elapsed entering prompt: %f' % (t1 - t0))
    for port, (ser, th) in port_ser_thread.items():
        ser.close()
    return True


def check_json_integrity(filename):
    path1 = resource_path(f'jsonfile/{filename}.json')
    path2 = os.path.join(os.path.abspath(os.path.curdir), 'jsonfile', f'{filename}.json')
    logger.debug(f'path1 {path1}')
    logger.debug(f'path2 {path2}')

    def check_each_json(path):
        try:
            j = json.loads(open(path, 'r').read())
        except json.JSONDecodeError as ex:
            logger.error(f'==ERROR== {ex}')
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
            return True # json file integrity is good
        else:
            return True if j1==j2 else False
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
        filtered = [e[field] for e in [e for e in devices if e['name']==name]]
        return filtered

    def get_update_ports_map(self):
        devices = get_visa_devices()
        ports_map = {}
        for k,v in self.devices.items():
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
        for k,v in self.devices.items():
            if not v['name']:
                continue

            if excludes:
                for e in excludes:
                    if k==e: continue
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
        logger.info('BaseVisaListener stop start')
        # wait 1s for list_ports to finish, is it enough or too long in order
        # not to occupy com port for subsequent test scripts
        if self.is_reading:
            QThread.msleep(1000)
        self.terminate()
        logger.info('BaseVisaListener stop end')


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

    def __init__(self, json_name, json_root='jsonfile'):
        super(Task, self).__init__()
        self.json_root = json_root
        self.json_name = json_name
        self.jsonfile = f'{json_root}/{json_name}.json'
        logger.info(self.jsonfile)
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
        logger.debug('Task.instruments')
        for k,v in self.instruments.items():
            logger.debug(f'{k} ---> {v}')

    @property
    def serial_instruments(self):
        name_int = dict(DEVICES.values()) # {intrument_name: interface}
        filtered = {k:v for k,v in self.instruments.items() if name_int[k]=='serial'}
        serial_inst = defaultdict(list)
        serial_inst.update(filtered)
        return serial_inst

    @property
    def visa_instruments(self):
        name_int = dict(DEVICES.values()) # {intrument_name: interface}
        filtered = {k:v for k,v in self.instruments.items() if name_int[k]=='visa'}
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
        serial_devices = {k:v for k,v in devices.items() if v['name'] in SERIAL_DEVICE_NAME}
        return serial_devices

    @property
    def visa_devices(self):
        devices = self.base['devices']
        visa_devices = {k:v for k,v in devices.items() if v['name'] in VISA_DEVICE_NAME}
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
        args = [str(e) for e in each['args']]if each['args'] else []
        return each, script, args

    def rungroup(self, groupname):
        eachgroup, script, index, item_len, tasktype, args = self.unpack_group(groupname)
        logger.debug(f'[rungroup][{s_(script)}][{s_(index)}][{s_(item_len)}][{s_(args)}]')
        limits_group = [self.limits(groupname, i) for i in range(item_len)]
        limits = {}
        for e in zip(*args):
            xx = {i: j for i, j in zip(e, limits_group)}
            limits.update(xx)
        logger.debug(f'limits {limits}')
        args = {'args': args, 'limits': limits}

        coms = {}
        for k,v in self.instruments.items():
            interface = dict(DEVICES.values())[k]
            if interface == 'serial':
                com_to_extract = 'com'
            elif interface == 'visa':
                com_to_extract = 'visa_addr'
            if len(v) > 0 :
                coms.update({k: [getattr(e, com_to_extract) for e in v]})

        coms = json.dumps(coms)

        proc = Popen([python_path(), '-m', script, '-p', coms] + [json.dumps(args)], stdout=PIPE, env=get_env(), cwd=resource_path('.'))

        return proc

    def runeach(self, row_idx, dut_idx, dynamic_info):
        port = self.window.comports()[dut_idx]
        each, script, args = self.unpack_each(row_idx)
        msg = f'[runeach][{s_(script)}][{s_(row_idx)}][{s_(dut_idx)}][{s_(port)}][{s_(dynamic_info)}][{s_(args)}]'
        logger.debug(msg)
        arguments = [python_path(), '-m', script,
                     '-p', port,
                     '-i', str(dut_idx),
                     '-s', dynamic_info]
        if args: arguments.append(args)
        proc = Popen(arguments, stdout=PIPE, env=get_env(), cwd=resource_path('.'))
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
        msg = f'[rungroup][{s_(script)}][{s_(index)}][{s_(ports)}][{s_(args)}]'
        logger.debug(msg)
        self.printterm_msg.emit(msg)
        selected_duts = ','.join([str(s) for s in self.window.dut_selected])    # E.g. '0,1'

        proc = Popen([python_path(), '-m', script, '-pp', ports, '-ds', selected_duts] + args, stdout=PIPE, env=get_env())

        outputs, _ = proc.communicate()
        if not outputs:
            logger.warning('outputs is None!!!!')
        outputs = outputs.decode('utf8')
        outputs = json.loads(outputs)
        msg2 = '[task %s][outputs: %s]' % (index, outputs)  # E.g. outputs = ['Passed', 'Failed']
        self.printterm_msg.emit(msg2)

        port_list = ports.split(',')
        for idx, output in enumerate(outputs):
            result = json.dumps({'index': index, 'port': port_list[idx], 'idx': idx, 'output': output})
            self.df.iat[index,
                        len(self.header()) +
                        self.window.dut_selected[idx]] = output
            self.task_result.emit(result)

    def register_action(self, actions):
        logger.debug('register_action')
        for e in actions:
            action, args = e['action'], e['args']
            self.action_args.append([action, args])

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
            if (func == 'write_mac_wifi'):
                dynamic_info = 'fa:23:34:89:45:22'
            if (func == 'write_mac_bt'):
                dynamic_info = 'fa:8f:ca:52:f3:38'
            if (func == 'write_country_code'):
                dynamic_info = 'CN01'

            for dut_idx in self.window.dut_selected:
                proc = self.runeach(row_idx, dut_idx, dynamic_info)
                port = self.window.comports()[dut_idx]
                procs[port] = proc

        logger.debug(f'procs {procs}')
        for j, (port, proc) in enumerate(procs.items()):
            output, _ = proc.communicate()
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
                to_read_pid = (script=='task_runeach' and func=='read_pid')
                if output.startswith('Pass') and to_read_pid:
                    pid = output[5:-1]
                    header = self.header_ext()
                    dut_i = self.window.dut_selected[j]
                    header[-self.dut_num + dut_i] = f'#{dut_i+1} - {pid}'
                    self.window.table_view.setHorizontalHeaderLabels(header)
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
        logger.debug(f'OUTPUT {output}')
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
        r1, r2 = row, row+1
        c1 = len(self.header()) + self.window.dut_selected[0]
        c2 = c1 + len(self.window.dut_selected)
        self.df.iloc[r1:r2, c1:c2] = "Passed"

        result = json.dumps({
            'index': row,
            'output': "Passed"
        })
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

    def run_task11(self, group, items):
        threads = {}
        for dut_idx in self.window.dut_selected:
            port = self.window.comports()[dut_idx]
            logger.debug(f'dut_idx:  {dut_idx}')
            logger.debug(f'port:  {port}')
            threads[dut_idx] = th = threading.Thread(target=run_iqfactrun_console,
                                                args=(self, dut_idx, port, group,))
            th.start()
        for dut_idx, th in threads.items():
            th.join()

    def run(self):
        time_ = lambda: datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')
        self.window.show_animation_dialog.emit(True)
        t0 = time_()

        for action, args in self.action_args:
            logger.debug(f'run action {action} {args}')
            if not action(*args):
                logger.debug('return !!!!!')
                self.window.show_animation_dialog.emit(False)
                self.window.msg_dialog_signal.emit(f"發生錯誤({action})")
                return

        QThread.msleep(500)
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

import os
import sys
import json
import time
import threading
import importlib
from datetime import datetime
from operator import itemgetter
from subprocess import Popen, PIPE
from collections import defaultdict
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal as QSignal
from PyQt5.QtWidgets import QMessageBox

from utils import resource_path, get_env
from instrument import  get_visa_devices, generate_instruments, INSTRUMENT_MAP
from mylogger import logger
from config import (DEVICES, SERIAL_DEVICES, VISA_DEVICES,
                    SERIAL_DEVICE_NAME, VISA_DEVICE_NAME)
from serials import enter_factory_image_prompt, get_serial, filter_devices


def enter_prompt_simu():
    def dummy(sec):
        time.sleep(sec)
    print('enter factory image prompt start')
    t0 = time.time()
    t = threading.Thread(target=dummy, args=(1.5, ))
    t.start()
    t.join()
    t1 = time.time()
    print('enter factory image prompt end')
    print('time elapsed entering prompt: %f' % (t1 - t0))
    return True


def enter_prompt(window, ser_timeout=0.2, waitwordidx=8):
    print('enter factory image prompt start')
    t0 = time.time()
    port_ser_thread = {}
    comports = window.comports
    print('enter_prompt: comports - ', comports)
    for i in window.dut_selected:
        port = comports()[i]
        print('i', i, 'port', port)
        ser = get_serial(port, 115200, ser_timeout)
        t = threading.Thread(target=enter_factory_image_prompt, args=(ser, waitwordidx))
        port_ser_thread[port] = [ser, t]
        t.start()
    for port, (ser, th) in port_ser_thread.items():
        th.join()
    t1 = time.time()
    print('enter factory image prompt end')
    print('time elapsed entering prompt: %f' % (t1 - t0))
    for port, (ser, th) in port_ser_thread.items():
        ser.close()
    return True


def check_json_integrity(filename):
    path1 = resource_path(f'jsonfile/{filename}.json')
    path2 = os.path.join(os.path.abspath(os.path.curdir), 'jsonfile', f'{filename}.json')
    print('path1', path1)
    print('path2', path2)

    def check_each_json(path):
        try:
            j = json.loads(open(path, 'r').read())
        except json.JSONDecodeError as ex:
            print('==ERROR==', ex)
            return False

        for dev, v in j['devices'].items():
            print('dev', dev)
            print('v', v)
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
            print('j1', j1['devices'])
            print('j2', j2['devices'])
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
        print('\n\n\nProcessListener run start!')
        outputs = {}
        for pid, proc in self.processes.items():
            output, _ = proc.communicate()
            output = output.decode('utf8')
            outputs[pid] = float(output)
        print('\n\n\nProcessListener run done!')
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
    message = QSignal(str)
    printterm_msg = QSignal(str)
    show_task_dialog = QSignal(list)

    def __init__(self, json_name, json_root='jsonfile'):
        super(Task, self).__init__()
        self.pause = False
        self.json_root = json_root
        self.json_name = json_name
        self.jsonfile = resource_path(f'{json_root}/{json_name}.json')
        logger.info(self.jsonfile)
        if not check_json_integrity(self.json_name):
            if QMessageBox.warning(None, 'Warning',
                   'You can not change jsonfile content besides the serial numbers',
                   QMessageBox.Yes):
                self.base = None
                return

        self.base = json.loads(open(self.jsonfile, 'r', encoding='utf8').read())
        self.groups = parse_json(self.jsonfile)
        self.action_args = list()
        self.df = self.load()
        self.instruments = generate_instruments(self.devices, INSTRUMENT_MAP)
        print('Task.instruments')
        for k,v in self.instruments.items():
            print(f'{k} ---> {v}')

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
        tasktype = each['tasktype']
        args = [str(e) for e in each['args']]if each['args'] else []
        return each, script, tasktype, args

    def rungroup(self, groupname):
        eachgroup, script, index, item_len, tasktype, args = self.unpack_group(groupname)
        print(
            f'[rungroup][script: {script}][index: {index}][len: {item_len}][args: {args}]'
        )
        limits_group = [self.limits(groupname, i) for i in range(item_len)]
        print('limits_group', limits_group)
        limits = {}
        for e in zip(*args):
            xx = {i: j for i, j in zip(e, limits_group)}
            limits.update(xx)
        print('limits', limits)
        args = {'args': args, 'limits': limits}

        #  coms = {k:[e.com for e in v] for k,v in self.instruments.items() if len(v)>0}
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
        print('coms', coms)
        proc = Popen(['python', '-m', script, '-p', coms] + [json.dumps(args)], stdout=PIPE, env=get_env(), cwd=resource_path('.'))

        return proc

    def runeach(self, row_idx, dut_idx, sid, tasktype):
        port = self.window.comports()[dut_idx]
        each, script, tasktype, args = self.unpack_each(row_idx)
        msg = (f'[runeach][script: {script}][row_idx: {row_idx}]'
               f'[dut_idx: {dut_idx}][port: {port}][sid: {sid}]'
               f'[args: {args}]')
        print(msg)
        arguments = ['python', '-m', script,
                     '-p', port,
                     '-i', str(dut_idx),
                     '-s', sid]
        if args: arguments.append(args)

        proc = Popen(arguments, stdout=PIPE, env=get_env(), cwd=resource_path('.'))

        self.printterm_msg.emit(msg)
        return proc

    def run_iqfactrun_console(self, dut_idx, port, groupname):
        print('run_iqfactrun_console start')
        eachgroup, script, index, item_len, tasktype, args = self.unpack_group(groupname)
        print(
            f'[run_iqfactrun_console][eachgroup: {eachgroup}][script: {script}][index: {index}][len: {item_len}][args: {args}]'
        )
        workdir = (f'C:/LitePoint/IQfact_plus/'
                   f'IQfact+_BRCM_43xx_COM_Golden_3.3.2.Eng18_Lock/bin{dut_idx+1}/')
        exe = 'IQfactRun_Console.exe'
        script1 = 'FIT_TEST_Sample_Flow.txt'
        script2 = 'FIT_TEST_BT_Sample_Flow.txt'
        print(f'workdir: {workdir}')
        def run():
            process = Popen([f'{workdir}{exe}', '-RUN', f'{workdir}{script1}', '-exit'],
                         stdout=PIPE, cwd=workdir, shell=True)
            #  process = Popen([f'{workdir}{exe}', '-RUN', f'{workdir}{script2}', '-exit'],
                         #  stdout=PIPE, cwd=workdir, shell=True)
            ended = False
            while True:
                line = process.stdout.readline()
                line = line.decode('utf8').rstrip()
                if 'In This Run' in line:
                    ended = True
                if ended and not line:
                    break
                yield line
        items = [e['item'] for e in eachgroup]
        processing_item = False
        item_idx = 0
        pattern1 = '[\d]{1,4}\.%s' % items[0]
        pattern2 = '[\d]{1,4}\..+_____'
        print('pattern1', pattern1)
        print('pattern2', pattern2)

        items_lines = []
        for line in run():
            print(line)
            matched = re.search(pattern1, line)
            matched2 = re.search(pattern2, line)
            if matched:
                if not processing_item:
                    print('pattern1 found [case1]')
                    processing_item = True
                    self.task_each.emit([index, 1])
                    index += 1
                    item_idx += 1
            elif processing_item:
                if matched2:
                    print('pattern2 found')
                    processing_item = False
                    output = 'Pass'
                    for e in items_lines:
                        if '--- [Failed]' in e:
                            err_msg = [e for e in items_lines if e.startswith('ERROR_MESSAGE')][0]
                            err_msg = err_msg.split(':')[1].strip()
                            output = f'Fail({err_msg})'
                            break
                    self.df.iat[index-1, len(self.header()) + dut_idx] = output

                    result = json.dumps({
                        'index': index-1,
                        'port': port,
                        'output': output
                    })
                    self.task_result.emit(result)
                    items_lines = []

                    # change pattern
                    if item_idx < len(items):
                        pattern1 = '[\d]{1,4}\.%s' % items[item_idx]
                        print('change pattern1!!!!!', pattern1)

                    if re.search(pattern1, line):
                        print('pattern1 found [case2]')
                        processing_item = True
                        self.task_each.emit([index, 1])
                        index += 1
                        item_idx += 1
                else:
                    items_lines.append(line)

        print('run_iqfactrun_console end')

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
        msg1 = '\n[runeachports][script: %s][index: %s][ports: %s][args: %s]' % (
            script, index, ports, args)
        print(msg1)
        self.printterm_msg.emit(msg1)

        proc = Popen(['python', '-m', script, '-pp', ports] + args, stdout=PIPE, env=get_env())
        outputs, _ = proc.communicate()
        if not outputs:
            print('outputs is None!!!!')
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
        print('register_action')
        for e in actions:
            action, args = e['action'], e['args']
            self.action_args.append([action, args])

    def run(self):
        time_ = lambda: datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')
        self.window.show_animation_dialog.emit(True)
        t0 = time_()
        for action, args in self.action_args:
            print('run action', action, args)
            if not action(*args):
                print('return !!!!!')
                return
        QThread.msleep(500)
        self.window.show_animation_dialog.emit(False)

        get_col = lambda arr, col: map(lambda x: x[col], arr)

        c1 = len(self.header())
        self.df.iloc[:, c1:c1 + self.dut_num] = ""

        for group, items in self.groups.items():
            i, next_item = items[0]['index'], items[0]
            is_auto, task_type = next_item['auto'], next_item['tasktype']
            if task_type != 11:
                self.task_each.emit([i, len(items)])

            if task_type == 1:
                procs = {}
                if any(self.window.port_barcodes.values()):
                    for port, barcode in self.window.port_barcodes.items():
                        if barcode:
                            dut_idx = self.window.comports().index(port)
                            proc = self.runeach(i, dut_idx, barcode, task_type)
                            procs[port] = proc
                else:
                    for dut_idx in self.window.dut_selected:
                        proc = self.runeach(i, dut_idx, '', task_type)
                        port = self.window.comports()[dut_idx]
                        print('port: ', port)
                        procs[port] = proc

                print('procs', procs)
                for j, (port, proc) in enumerate(procs.items()):
                    output, _ = proc.communicate()
                    output = output.decode('utf8')
                    msg2 = '[task %s][output: %s]' % (i, output)
                    self.printterm_msg.emit(msg2)
                    result = json.dumps({
                        'index': i,
                        'port': port,
                        'output': output
                    })
                    self.df.iat[i,
                                len(self.header()) +
                                self.window.dut_selected[j]] = output
                    print('run: result', result)

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

            elif task_type == 11:
                threads = {}
                for dut_idx in self.window.dut_selected:
                    port = self.window.comports()[dut_idx]
                    print('dut_idx: ', dut_idx)
                    print('port: ', port)
                    threads[dut_idx] = th = threading.Thread(target=self.run_iqfactrun_console,
                                                        args=(dut_idx, port, group,))
                    th.start()
                for dut_idx, th in threads.items():
                    th.join()

            elif task_type == 2:
                proc = self.rungroup(group)
                output, _ = proc.communicate()
                output = output.decode('utf8')
                print('OUTPUT', output)
                msg2 = '[task %s][output: %s]' % ([i, i + len(items)], output)
                self.printterm_msg.emit(msg2)
                result = json.dumps({
                    'index': [i, i + len(items)],
                    'output': output
                })
                r1, r2 = i, i + len(items)
                c1 = len(self.header()) + self.window.dut_selected[0]
                c2 = c1 + len(self.window.dut_selected)
                output = json.loads(output)
                if len(self.window.dut_selected) == 1:
                    output = [[e] for e in get_col(output, self.window.dut_selected[0])]
                print('OUTPUT', output)
                self.df.iloc[r1:r2, c1:c2] = output
                self.task_result.emit(result)

            elif task_type == 3:
                selected_port_list = []
                for selected_i in self.window.dut_selected:
                    selected_port_list.append(self.window._comports_dut[selected_i])

                selected_port_str = ','.join(selected_port_list)
                self.runeachports(i, selected_port_str)

            elif task_type == 4:
                line = self.df.values[i]
                mod_name = f'tasks.{line[0]}'
                mod = importlib.import_module(mod_name)

                func_list = [str(e) for e in line[1]] if line[1] else []

                func = getattr(mod, func_list[0])
                t = threading.Thread(target=func)
                t.start()
                r1, r2 = i, i+1
                c1 = len(self.header()) + self.window.dut_selected[0]
                c2 = c1 + len(self.window.dut_selected)
                self.df.iloc[r1:r2, c1:c2] = "Passed"

                result = json.dumps({
                    'index': i,
                    'output': "Passed"
                })
                self.task_result.emit(result)


            elif task_type == 9:
                obj_name, method_name = next_item['args']
                #  obj = getattr(thismodule, obj_name)
                obj = getattr(sys.modules['__main__'], obj_name)
                output = getattr(obj, method_name)()
                r1, r2 = i, i + len(items)
                c1 = len(self.header()) + self.window.dut_selected[0]
                c2 = c1 + len(self.window.dut_selected)
                if len(self.window.dut_selected) == 1:
                    output = [[e] for e in output]
                result = json.dumps({
                    'index': [i, i + len(items)],
                    'output': output
                })
                self.df.iloc[r1:r2, c1:c2] = output
                self.task_result.emit(result)

            elif task_type == 40:
                # Cap touch
                self.pause = True
                self.show_task_dialog.emit([i, task_type])

            while self.pause:
                QThread.msleep(100)

            QThread.msleep(500)

        t1 = time_()
        self.df = self.df.fillna('')
        message = {
            'msg': 'tasks done',
            't0': t0,
            't1': t1,
        }
        self.message.emit(json.dumps(message))

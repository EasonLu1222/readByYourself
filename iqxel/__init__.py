import os
import re
import json
import shutil
from subprocess import Popen, PIPE
from utils import s_, resource_path

from mylogger import logger


SOURCE_TF = 'FAB_Test_Flow.txt'
iqfact_v18_workdir = 'C:/LitePoint/IQfact_plus/IQfact+_BRCM_43xx_COM_Golden_3.3.2.Eng18_Lock'
iqfact_v19_workdir = 'C:/LitePoint/IQfact_plus/IQfact+_BRCM_43xx_COM_Golden_3.3.2.Eng19_Lock'


def iqxel_workdir():
    if os.path.exists(iqfact_v18_workdir):
        return 'IQfact+_BRCM_43xx_COM_Golden_3.3.2.Eng18_Lock'
    elif os.path.exists(iqfact_v19_workdir):
        return 'IQfact+_BRCM_43xx_COM_Golden_3.3.2.Eng19_Lock'


def iqxel_ver():
    if os.path.exists(iqfact_v18_workdir):
        return 18
    elif os.path.exists(iqfact_v19_workdir):
        return 19


def run_iqfactrun_console(task, dut_idx, port, groupname):
    logger.debug('    run_iqfactrun_console start')
    eachgroup, script, index, item_len, tasktype, args = task.unpack_group(groupname)
    logger.debug(f'    [run_iqfactrun_console][{s_(eachgroup)}][{s_(script)}][{s_(index)}][{s_(item_len)}][{s_(args)}]')
    workdir = f'C:/LitePoint/IQfact_plus/{iqxel_workdir()}/bin{dut_idx+1}/'

    iqxel_dir = os.path.join(os.path.abspath(os.path.curdir), 'iqxel')
    script_dir = os.path.abspath(os.path.curdir)
    script_path = os.path.join(workdir, f'FAB_Test_Flow.txt')
    exe = 'IQfactRun_Console.exe'
    #  exe_winpty = os.path.join(iqxel_dir, 'winpty.exe')
    exe_winpty = resource_path('iqxel/winpty.exe')
    logger.debug('    exe_winpty', exe_winpty)
    def run():
        # clean log
        try:
            shutil.rmtree(f'{workdir}LOG')
        except OSError as e:
            logger.error(f'    {e}')
        else:
            os.mkdir(f'{workdir}LOG')

        process = Popen([exe_winpty, "-Xallow-non-tty", "-Xplain",
                         f'{workdir}{exe}', '-RUN', f'{script_path}', '-exit'],
                        stdout=PIPE, stdin=PIPE, shell=True, cwd=workdir)
        #  process = Popen([f'{workdir}{exe}', '-RUN', f'{script_path}', '-exit'],
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
    pattern3 = '--------------------------------------------------------------------'
    items_lines = []
    for line in run():
        logger.debug(f'    {line}')
        matched = re.search(pattern1, line)
        matched2 = re.search(pattern2, line)
        matched3 = re.search(pattern3, line)
        if matched:
            if not processing_item:
                logger.debug('    pattern1 found [case1]')
                processing_item = True
                task.task_each.emit([index, 1])
                index += 1
                item_idx += 1
        elif processing_item:
            if matched2 or matched3:
                processing_item = False
                output = 'Pass'
                for e in items_lines:
                    if '--- [Failed]' in e:
                        err_msg = [e for e in items_lines if e.startswith('ERROR_MESSAGE')][0]
                        err_msg = err_msg.split(':')[1].strip()
                        output = f'Fail({err_msg})'
                        break
                task.df.iat[index-1, len(task.header()) + dut_idx] = output
                result = json.dumps({
                    'index': index-1,
                    'port': port,
                    'output': output
                })
                task.task_result.emit(result)
                items_lines = []

                if matched2:
                    logger.debug('    pattern2 found')
                    # change pattern
                    if item_idx < len(items):
                        pattern1 = '[\d]{1,4}\.%s' % items[item_idx]
                        logger.debug(f'    change pattern1!!!!! {pattern1}')
                    if re.search(pattern1, line):
                        logger.debug('    pattern1 found [case2]')
                        processing_item = True
                        task.task_each.emit([index, 1])
                        index += 1
                        item_idx += 1
                elif matched3:
                    pattern1 = 'DO NOT FIND ANY PATTERN'
                    logger.debug(f'    change pattern1!!!!! {pattern1}')
                    logger.debug('    pattern3 found')
            else:
                items_lines.append(line)
    logger.debug('    run_iqfactrun_console end')


def generate_jsonfile():
    source_json = 'v13_rf_base'
    target_json = os.path.join('jsonfile', 'v13_rf.json')
    from core import Task
    each = lambda item: {
        "group": "RF",
        "hidden": False,
        "tasktype": 11,
        "item": item,
        "script": None,
        "args": None,
        "auto": True,
        "min": None,
        "expect": None,
        "max": None,
        "unit": None
    }
    j = Task(source_json).base

    #  source_tf = resource_path(os.path.join('iqxel', SOURCE_TF))
    source_tf = os.path.join('iqxel', SOURCE_TF)

    logger.debug(f'    source_tf {source_tf}')

    wifi, bt = parse_testflow(source_tf)
    j['test_items'] = [each(item) for item in wifi + bt]
    with open(target_json, 'w') as f:
        f.write(json.dumps(j, indent=4))
    return j


def parse_testflow(filepath):
    with open(filepath, 'r') as f:
        lines_ = f.readlines()
    wifi_line_idx = [i for i,e in enumerate(lines_) if e.startswith('WIFI_11AC')][0]
    bt_line_idx = [i for i,e in enumerate(lines_) if e.startswith('BT')][0]
    wifi_lines = lines_[wifi_line_idx+1:bt_line_idx]
    bt_lines = lines_[bt_line_idx+1:]
    wifi_items = parse_testflow_wifi_or_bt(wifi_lines)
    bt_items = parse_testflow_wifi_or_bt(bt_lines)
    wifi_item_names = list(wifi_items.keys())
    bt_item_names = list(bt_items.keys())
    return wifi_item_names, bt_item_names


def parse_testflow_wifi_or_bt(lines_):
    setup_items = [
        'CONNECT_IQ_TESTER',
        'GLOBAL_SETTINGS',
        'LOAD_PATH_LOSS_TABLE',
        'INSERT_DUT',
        'INITIALIZE_DUT',
        'REMOVE_DUT',
        'DISCONNECT_IQ_TESTER',
    ]
    strips = lambda v: [e.strip() for e in v]
    lines = [(i, e.rstrip()) for i, e in enumerate(lines_)]
    lines_no_idx = [e.rstrip() for e in lines_]
    x = [(i, e) for i, e in lines if e.startswith('\t') and e.count('\t') == 1]
    name_items = [
        [e.strip(),
            strips(lines_no_idx[i2+1:x[i1+1][0]]) if i1<len(x)-1
            else strips(lines_no_idx[i2+1:])]
        for i1, (i2, e) in enumerate(x)
    ]
    parsed = {}
    for name, items in name_items:
        if name.endswith('ALWAYS_SKIP'):
            continue
        if name in ['TX_MULTI_VERIFICATION', 'RX_VERIFY_PER']:
            item_dict = parse_testflow_items(items)
            v1 = item_dict['>BSS_FREQ_MHZ_PRIMARY [Integer]']
            v2 = item_dict['>DATA_RATE [String]']

            if iqxel_ver() == 18:
                v_ = ' '
            elif iqxel_ver() == 19:
                v_ = ' ' + item_dict['>PACKET_FORMAT [String]'] + ' '

            v3 = item_dict['>BSS_BANDWIDTH [String]']
            t_or_r = name[0]
            v4 = [item_dict[f'>{t_or_r}X{i} [Integer]'] for i in range(1, 5)].index(1)+1

            name = f'{name}  {v1} {v2}{v_}{v3} {t_or_r}X{v4}'
            parsed[name] = items
        elif re.search('[TR]X_(BDR|EDR|LE)', name):
            item_dict = parse_testflow_items(items)
            v1 = item_dict['>FREQ_MHZ [Integer]']
            v2 = item_dict['>PACKET_TYPE [String]']
            name = f'{name}  {v1} {v2}'
        parsed[name] = items

    # IQfact+_BRCM_43xx_COM_Golden_3.3.2.Eng18_Lock
    'TX_MULTI_VERIFICATION  2412 CCK-11 BW-20 TX1'
    'RX_VERIFY_PER  2412 DSSS-1 BW-20 RX1'

    '>BSS_FREQ_MHZ_PRIMARY [Integer]  = 2412',
    '>DATA_RATE [String]  = CCK-11'
    '>BSS_BANDWIDTH [String]  = BW-20',
    '>T(R)X1 [Integer]  = 1',
    '>T(R)X2 [Integer]  = 0',
    '>T(R)X3 [Integer]  = 0',
    '>T(R)X4 [Integer]  = 0',

    'T(R)X_BDR|T(R)X_EDR|T(R)X_LE  2402 1DH1'
    '>FREQ_MHZ [Integer]  = 2402',
    '>PACKET_TYPE [String]  = 1DH1',

    # IQfact+_BRCM_43xx_COM_Golden_3.3.2.Eng19_Lock
    'TX_MULTI_VERIFICATION  2412 CCK-11 NON_HT BW-20 TX1'
    'RX_VERIFY_PER  2412 DSSS-1 NON_HT BW-20 RX1'

    '>BSS_FREQ_MHZ_PRIMARY [Integer]  = 2412',
    '>DATA_RATE [String]  = CCK-11'
    '>PACKET_FORMAT [String]  = NON_HT'
    '>BSS_BANDWIDTH [String]  = BW-20',
    '>T(R)X1 [Integer]  = 1',
    '>T(R)X2 [Integer]  = 0',
    '>T(R)X3 [Integer]  = 0',
    '>T(R)X4 [Integer]  = 0',

    'T(R)X_BDR|T(R)X_EDR|T(R)X_LE  2402 1DH1'
    '>FREQ_MHZ [Integer]  = 2402',
    '>PACKET_TYPE [String]  = 1DH1',

    return parsed


def item_split(item):
    name, value = [e.strip() for e in item.split('=')]
    return name, value


def item_type(item):
    matched = re.search('\[(.+)\]', item)
    return matched.groups()[0] if matched else None


def parse_value(item):
    name, value = item_split(item)
    itemtype = item_type(item)
    _ = {'Integer': int, 'Double': float, 'String': str}
    if name.startswith('>'):
        value = _[itemtype](value)
    elif name.startswith('<'):
        value = [_[itemtype](e) if e else None for e in value[1:-1].split(',')]
    return value


def parse_testflow_items(items):
    item_dict = {}
    for item in items:
        if item.startswith('#'): # this is comment
            pass
        else:
            name, value = item_split(item)
            item_dict[name] = parse_value(item)
    return item_dict


def prepare_for_testflow_files(win):
    match_s1 = r"\t\t>APP_ID \[Integer]  = \d"
    match_s2 = r"\t\t>IQTESTER_MODULE_01 \[String]  = 192.168.100.254:A"
    match_s3 = r"\t\t>VSA_PORT \[Integer]  = \d"
    match_s4 = r"\t\t>VSG_PORT \[Integer]  = \d"
    match_s5 = r"\t\t>CONNECTION_STRING \[String]  = com"
    match_s6 = r"\t\t>CONNECTION_NAME \[String]  = com"
    source_tf = os.path.join('iqxel', SOURCE_TF)
    appid = 4

    for dut_idx, port in win._comports_dut.items():
        workdir = f'C:/LitePoint/IQfact_plus/{iqxel_workdir()}/bin{dut_idx+1}/'
        dest_tf = os.path.join(workdir, f'FAB_Test_Flow.txt')
        with open(source_tf, 'r') as f, open(dest_tf, 'w') as f2:
            for line in f.readlines():
                if re.search(match_s1, line):
                    # APP_ID
                    old_str = line
                    l = line.split()
                    replace_str = f'\t\t{l[0]} {l[1]}  {l[2]} {dut_idx+appid}\n'
                    appid += 1
                    line = line.replace(old_str, replace_str)
                    print(line, end='')
                elif re.search(match_s2, line):
                    # IQTESTER_MODULE_01
                    if (dut_idx+1) != 2:
                        iqtester = '192.168.100.254:A'
                    else:
                        iqtester = '192.168.100.254:B'
                    old_str = line
                    l = line.split()
                    replace_str = f'\t\t{l[0]} {l[1]}  {l[2]} {iqtester}\n'
                    line = line.replace(old_str, replace_str)
                    print(line, end='')
                elif re.search(match_s3, line):
                    # VSA_PORT
                    if (dut_idx+1) != 3:
                        vsaport = '2'
                    else:
                        vsaport = '3'
                    old_str = line
                    l = line.split()
                    replace_str = f'\t\t{l[0]} {l[1]}  {l[2]} {vsaport}\n'
                    line = line.replace(old_str, replace_str)
                    print(line, end='')
                elif re.search(match_s4, line):
                    # VSG_PORT
                    if (dut_idx+1) != 3:
                        vsgport = '2'
                    else:
                        vsgport = '3'
                    old_str = line
                    l = line.split()
                    replace_str = f'\t\t{l[0]} {l[1]}  {l[2]} {vsgport}\n'
                    line = line.replace(old_str, replace_str)
                    print(line, end='')
                elif re.search(match_s5, line):
                    # CONNECTION_STRING
                    old_str = line
                    l = line.split()
                    replace_str = f'\t\t{l[0]} {l[1]}  {l[2]} {port}\n'
                    line = line.replace(old_str, replace_str)
                    print(line, end='')
                elif re.search(match_s6, line):
                    # CONNECTION_NAME
                    old_str = line
                    l = line.split()
                    replace_str = f'\t\t{l[0]} {l[1]}  {l[2]} {port}\n'
                    line = line.replace(old_str, replace_str)
                    print(line, end='')
                f2.write(line)
        print('-----------------------------------------------------------')

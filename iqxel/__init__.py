import os
import re
import json
import shutil
from subprocess import Popen, PIPE
from utils import s_


def run_iqfactrun_console(task, dut_idx, port, groupname):
    print('run_iqfactrun_console start')
    eachgroup, script, index, item_len, tasktype, args = task.unpack_group(groupname)
    print(f'[run_iqfactrun_console][{s_(eachgroup)}][{s_(script)}][{s_(index)}][{s_(item_len)}][{s_(args)}]')
    workdir = (f'C:/LitePoint/IQfact_plus/'
               #  f'IQfact+_BRCM_43xx_COM_Golden_3.3.2.Eng18_Lock/bin{dut_idx+1}/')
               f'IQfact+_BRCM_43xx_COM_Golden_3.3.2.Eng19_Lock/bin{dut_idx+1}/')

    iqxel_dir = os.path.join(os.path.abspath(os.path.curdir), 'iqxel')
    script_dir = os.path.abspath(os.path.curdir)
    script_path = os.path.join(workdir, f'FAB_Test_Flow.txt')
    exe = 'IQfactRun_Console.exe'
    exe_winpty = os.path.join(iqxel_dir, 'winpty.exe')
    def run():
        # clean log
        try:
            shutil.rmtree(f'{workdir}LOG')
        except OSError as e:
            print(e)
        else:
            #  print(f'The directory ({workdir}LOG) is deleted successfully')
            os.mkdir(f'{workdir}LOG')

        process = Popen([exe_winpty, "-Xallow-non-tty", "-Xplain",
                         f'{workdir}{exe}', '-RUN', f'{script_path}', '-exit'],
                        stdout=PIPE, stdin=PIPE, shell=True, cwd=workdir)
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
        print(line)
        matched = re.search(pattern1, line)
        matched2 = re.search(pattern2, line)
        matched3 = re.search(pattern3, line)
        if matched:
            if not processing_item:
                print('pattern1 found [case1]')
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
                    print('pattern2 found')
                    # change pattern
                    if item_idx < len(items):
                        pattern1 = '[\d]{1,4}\.%s' % items[item_idx]
                        print('change pattern1!!!!!', pattern1)
                    if re.search(pattern1, line):
                        print('pattern1 found [case2]')
                        processing_item = True
                        task.task_each.emit([index, 1])
                        index += 1
                        item_idx += 1
                elif matched3:
                    pattern1 = 'DO NOT FIND ANY PATTERN'
                    print('change pattern1!!!!!', pattern1)
                    print('pattern3 found')
            else:
                items_lines.append(line)
    print('run_iqfactrun_console end')

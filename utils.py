import hashlib
import os
import sys
import inspect
import shutil
from pathlib import Path
from subprocess import Popen, PIPE

from mylogger import logger


def s_(var):
    '''
        name = "tom"
        s_(name) = "name: tom"

        pi = 3.1415
        s_(pi) = "pi: 3.1415"
    '''
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()
    var_name = [var_name for var_name, var_val in callers_local_vars if var_val is var][0]
    return f'{var_name}: {var}'


def test_data(csv_file):
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    data = [e.strip().split(',') for e in lines]
    return data


def move_mainwindow_centered(app, window):
    desktop = app.desktop()
    window.move(desktop.screen().rect().center() - window.rect().center())


def python_path():
    rtn = 'python'
    try:
        base_path = Path(sys._MEIPASS).resolve()
        rtn = str(base_path.joinpath(base_path, rtn))
    except Exception:
        pass
    return rtn


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS).resolve()
    except Exception:
        try:
            env = os.environ
            base_path = Path(env['_MEIPASS']).resolve()
        except Exception:
            base_path = Path(".").resolve()
    return str(base_path.joinpath(Path(relative_path)))


def run(cmd, strip=False):
    logger.info(cmd)
    proc = Popen(cmd.split(" "), stdout=PIPE, env=get_env(), cwd=resource_path('.'))
    output, _ = proc.communicate()
    decoded_output = output.decode('utf-8')
    if strip:
        decoded_output = decoded_output.strip()
    logger.info(decoded_output)
    return decoded_output


def get_env():
    pyi_env = os.environ.copy()
    if hasattr(sys, '_MEIPASS'):
        pyi_env['PYTHONPATH'] = pyi_env['PATH']
        pyi_env['_MEIPASS'] = sys._MEIPASS

    return pyi_env


def set_property(widget, attr, val):
    widget.setProperty(attr, val)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def get_md5(file_path):
    # Open, close, read file and calculate MD5 on its contents
    with open(file_path, 'rb') as file_to_check:
        # read contents of the file
        data = file_to_check.read()
        # pipe contents of the file through
        md5_returned = hashlib.md5(data).hexdigest()

    return md5_returned


def clear_tmp_folders():
    """
    This will clear all temp folders created by executing app.exe(except for the currently using one)
    The temp folder is located in C:\\Users\\USERNAME\\AppData\\Local\\Temp
    """
    try:
        tmp_path = os.path.join(Path.home(), 'AppData', 'Local', 'Temp')
        limit = 5
        for name in os.listdir(tmp_path):
            path = os.path.join(tmp_path, name)
            is_dir = os.path.isdir(path)
            is_app_tmp = name.startswith('_MEI')

            if is_dir and is_app_tmp:
                if hasattr(sys, '_MEIPASS') and name in sys._MEIPASS:
                    continue
                logger.info(f"Deleting {path}")
                shutil.rmtree(path)
                limit = limit - 1
            if limit<=0:
                break
    except Exception as e:
        logger.error(f"Failed when deleting temp app folder, error:{e}")


class QssTools(object):
    @classmethod
    def set_qss_to_obj(cls, obj, file_path='./ui/qss/style1.qss'):
        #  with open(file_path, 'r') as f:
        with open(resource_path(file_path)) as f:
            obj.setStyleSheet(f.read())

import os
import sys
import inspect
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
    logger.error(cmd)
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
import os
import sys
from pathlib import Path


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


def get_env():
    pyi_env = os.environ.copy()
    if hasattr(sys, '_MEIPASS'):
        pyi_env['PYTHONPATH'] = pyi_env['PATH']
        pyi_env['_MEIPASS'] = sys._MEIPASS

    return pyi_env
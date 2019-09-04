import os
import sys


def test_data(csv_file):
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    data = [e.strip().split(',') for e in lines]
    return data


def move_mainwindow_centered(app, window):
    desktop = app.desktop()
    window.move(desktop.screen().rect().center() - window.rect().center())


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

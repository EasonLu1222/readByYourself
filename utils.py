
def test_data(csv_file):
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    data = [e.strip().split(',') for e in lines]
    return data


def move_mainwindow_centered(app, window):
    desktop = app.desktop()
    window.move(desktop.screen().rect().center() - window.rect().center())

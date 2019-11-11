# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import exec_statement

block_cipher = None

import os

curdir = os.path.abspath(os.path.curdir)

exec_before = exec_statement('''
    import os
    import shutil
    from distutils.dir_util import copy_tree
    copy_tree('jsonfile', 'dist/jsonfile')
    os.makedirs('dist/iqxel', exist_ok=True)
    shutil.copyfile('iqxel/FAB_Test_Flow.txt',
                    'dist/iqxel/FAB_Test_Flow.txt')
''')

added_files = [
    ('db/*.py', 'db'),
    ('tasks/*', 'tasks'),
    ('view/*', 'view'),
    ('ui/*.py', 'ui'),
    ('device.json', '.'),
    ('*.py', '.'),
    ('jsonfile/*.json', 'jsonfile'),
    ('images/*', 'images'),
    ('wav/*', 'wav'),
    ('wav/tmp/*', 'wav/tmp'),
    ('translate/*', 'translate'),
    ('instrument/*', 'instrument'),
    ('firmware/*', 'firmware'),
    ('site-packages/serial/*.py', 'serial'),
    ('site-packages/serial/tools/*.py', 'serial/tools'),
    ('site-packages/PyQt5/*.py', 'PyQt5'),
    ('site-packages/visa.py', '.'),
    ('site-packages/pyvisa/*.py', 'pyvisa'),
    ('site-packages/pyvisa/compat/*.py', 'pyvisa/compat'),
    ('site-packages/pyvisa/resources/*.py', 'pyvisa/resources'),
    ('site-packages/pyvisa/ctwrapper/*.py', 'pyvisa/ctwrapper'),
    ('python-3.7.3-embed-amd64/*', '.'),
    ('iqxel/*.dll', 'iqxel'),
    ('iqxel/*.exe', 'iqxel'),
    ('ui/qss/*.qss', 'ui/qss'),
]

a = Analysis(['app.py'],
             pathex=[curdir],
             binaries=[],
             datas=added_files,
             hiddenimports=['scipy.io', 'scipy.io.wavfile', 'playsound', 'playsound.playsound'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='app',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )

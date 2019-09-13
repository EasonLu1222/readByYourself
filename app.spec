# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import exec_statement

block_cipher = None

import os

curdir = os.path.abspath(os.path.curdir)

exec_before = exec_statement('''
    from distutils.dir_util import copy_tree
    copy_tree('jsonfile', 'dist/jsonfile')
''')

added_files = [
    ('tasks/*', 'tasks'),
    ('view/*', 'view'),
    ('device.json', '.'),
    ('*.py', '.'),
    ('jsonfile/*.json', 'jsonfile'),
    ('images/*', 'images'),
    ('wav/*', 'wav'),
    ('wav/tmp/*', 'wav/tmp'),
    ('translate/*', 'translate'),
    ('instrument/*', 'instrument'),
    ('site-packages/serial/*.py', 'serial'),
    ('site-packages/serial/tools/*py', 'serial/tools'),
    ('site-packages/PyQt5/*py', 'PyQt5'),
]

a = Analysis(['app.py'],
             pathex=[curdir],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
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

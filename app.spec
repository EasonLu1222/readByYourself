# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

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
    ('instrument/*', 'instrument')
]

a = Analysis(['app.py'],
             pathex=['N:\\Desktop\\mb_test_gui'],
             binaries=[],
             datas=added_files,
             hiddenimports=['tasks.task_cap_touch'],
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

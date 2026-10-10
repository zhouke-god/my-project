# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pets.py', '.'),
        ('config.py', '.'),
        ('settings.py', '.'),
        ('pet_selector.py', '.'),
        ('features.py', '.'),
        ('games.py', '.'),
        ('pet.py', '.'),
        ('ui.py', '.'),
        ('eula.py', '.'),
        ('autostart.py', '.'),
        ('sprites.py', '.'),
    ],
    hiddenimports=[
        'pets', 'config', 'settings', 'pet_selector',
        'features', 'games', 'pet', 'ui', 'eula', 'autostart', 'sprites',
        'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui',
        'requests', 'json', 'threading', 'win32com.client',
        'PIL', 'PIL.Image', 'PIL.ImageDraw',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI_Pet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI_Pet',
)

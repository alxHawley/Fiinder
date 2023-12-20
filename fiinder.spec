# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['fiinder.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('server.py', '.'),  # Include the server.py file
        ('utils/', 'utils'),  # Include the utils directory
        ('static/', 'static'),  # Include the static directory
        ('images/', 'images'),  # Include the images directory
        ('templates/', 'templates'),  # Include the templates directory
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

# Remove the .idea directory and .gitattributes and .gitignore files
a.datas = [(i, j, k) for i, j, k in a.datas if not i.endswith('.idea') and not i.endswith('.gitattributes') and not i.endswith('.gitignore')]

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='fiinder',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

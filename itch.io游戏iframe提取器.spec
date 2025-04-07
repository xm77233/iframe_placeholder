# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['iframe_scraper_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('iframe_scraper.py', '.')],
    hiddenimports=['urllib.request', 'urllib.error', 'urllib.parse', 'html.parser', 'json', 'os', 'time', 're', 'logging'],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='itch.io游戏iframe提取器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# -*- mode: python ; coding: utf-8 -*-
# 빌드 전: python release.py --bundle   (app_bundle.zip 생성)
# 빌드:    pyinstaller BlogWriter.spec   → dist/BlogWriter/블로그작성기.exe
from PyInstaller.utils.hooks import collect_all

datas = [('app_bundle.zip', '.'), ('version.json', '.')]
binaries = []
hiddenimports = ['PIL._tkinter_finder']
for pkg in ('flask', 'numpy', 'PIL', 'docx', 'pptx', 'lxml'):
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PyQt5', 'PySide2'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='블로그작성기',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BlogWriter',
)

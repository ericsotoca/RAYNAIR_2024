# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['low_cost_europe_freeware.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/FiercePC/Desktop/IA/RAYNAIR_2024/logo.png', '.'), ('C:/Users/FiercePC/Desktop/IA/RAYNAIR_2024/france.png', '.'), ('C:/Users/FiercePC/Desktop/IA/RAYNAIR_2024/espagne.png', '.'), ('C:/Users/FiercePC/Desktop/IA/RAYNAIR_2024/italie.png', '.'), ('C:/Users/FiercePC/Desktop/IA/RAYNAIR_2024/allemagne.png', '.'), ('C:/Users/FiercePC/Desktop/IA/RAYNAIR_2024/royaume.png', '.'), ('C:/Users/FiercePC/Desktop/IA/RAYNAIR_2024/avion.gif', '.')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='low_cost_europe_freeware',
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

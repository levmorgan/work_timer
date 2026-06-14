# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect matplotlib data files (fonts, etc.)
matplotlib_datas = collect_data_files("matplotlib")

# Ensure QtMultimedia is bundled
hidden_imports = [
    "PySide6.QtMultimedia",
    "matplotlib.backends.backend_qtagg",
]
hidden_imports += collect_submodules("matplotlib")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=matplotlib_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

is_macos = sys.platform == "darwin"

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="work_timer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["icon.icns"] if is_macos else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="work_timer",
)

if is_macos:
    app = BUNDLE(
        coll,
        name="work_timer.app",
        icon="icon.icns",
        bundle_identifier="com.worktimer.app",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
        },
    )

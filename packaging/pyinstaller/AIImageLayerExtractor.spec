# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)


block_cipher = None

project_root = Path(SPECPATH).resolve().parents[1]
app_name = "AIImageLayerExtractor"
entry_script = project_root / "launcher.py"
icon_file = project_root / "packaging" / "assets" / "app_icon.ico"


def dedupe(items):
    seen = set()
    result = []
    for item in items:
        key = tuple(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


datas = []
binaries = []
hiddenimports = [
    "cv2",
    "numpy",
    "PIL.Image",
    "PIL.ImageFile",
    "PIL.PngImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL.WebPImagePlugin",
    "PIL.IcoImagePlugin",
]

hiddenimports += collect_submodules("cv2")
datas += collect_data_files("cv2")
binaries += collect_dynamic_libs("cv2")

datas += collect_data_files(
    "PySide6",
    includes=[
        "plugins/platforms/*",
        "plugins/imageformats/*",
        "plugins/iconengines/*",
        "plugins/styles/*",
        "plugins/tls/*",
    ],
)

datas += [
    (str(project_root / "packaging" / "assets" / "license.txt"), "assets"),
]

datas = dedupe(datas)
binaries = dedupe(binaries)
hiddenimports = sorted(set(hiddenimports))


a = Analysis(
    [str(entry_script)],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "scipy",
        "torch",
        "torchvision",
        "tensorflow",
        "rembg",
        "sam2",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch="x86_64",
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_file),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)

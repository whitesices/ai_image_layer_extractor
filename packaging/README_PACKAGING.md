# Packaging AI Image Layer Extractor

This folder contains the Windows packaging pipeline for AI Image Layer Extractor.
It does not replace the source/development workflow.

## Requirements

- Windows 10/11 x64
- Python 3.10+
- Inno Setup 6
- PowerShell 5+

The build scripts create or reuse `.venv`, install runtime dependencies from
`requirements.txt`, and install packaging dependencies from `requirements-dev.txt`.

## One-command Build

```powershell
cd C:\ML\EditImage\ai_image_layer_extractor
.\packaging\scripts\build_all.ps1
```

If PowerShell execution policy blocks local scripts, use:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\packaging\scripts\build_all.ps1
```

Output:

```text
release/AIImageLayerExtractor_Setup_0.1.0_x64.exe
```

## Build Only the EXE

```powershell
.\packaging\scripts\build_exe.ps1
```

Output:

```text
dist/AIImageLayerExtractor/AIImageLayerExtractor.exe
```

## Build Only the Installer

Run this after `build_exe.ps1`:

```powershell
.\packaging\scripts\build_installer.ps1
```

Output:

```text
release/AIImageLayerExtractor_Setup_0.1.0_x64.exe
```

## Clean Build Artifacts

```powershell
.\packaging\scripts\clean_build.ps1
```

This removes `build/`, `dist/`, `release/`, root-level generated `.spec` files,
and `__pycache__` folders. It does not remove
`packaging/pyinstaller/AIImageLayerExtractor.spec`.

## Installed Application Data

The packaged launcher creates user data folders under:

```text
%LOCALAPPDATA%/AIImageLayerExtractor/
+-- logs/
+-- config/
+-- cache/
+-- exports/
```

The installer removes only the application files. It intentionally does not
delete `%LOCALAPPDATA%/AIImageLayerExtractor`.

## LLM and Optional Dependencies

The installer does not include an OpenAI API key and does not require `torch`,
SAM2, rembg, or OCR packages. The default installed app remains usable offline
with manual tools, batch export, and the mock LLM provider.

New Pro modules under `detectors/`, `matting/`, `pipeline/`, and `exporters/`
use only existing runtime dependencies unless the user explicitly installs
optional model backends.

OpenAI LLM parsing is optional. In source mode, install the SDK only if needed:

```powershell
.\.venv\Scripts\python.exe -m pip install openai
```

If the OpenAI SDK or API key is missing, the UI falls back to the mock provider
instead of crashing.

## Common Problems

### PySide6 DLL load failed

This project pins `PySide6==6.7.3`. Newer PySide6 versions may fail on some
Windows/Anaconda machines because Qt DLLs load incompatible ICU DLLs.

Fix:

```powershell
.\.venv\Scripts\python.exe -m pip install --force-reinstall PySide6==6.7.3
```

### Qt platform plugin windows not found

The PyInstaller spec explicitly collects PySide6 platform and imageformat
plugins. If this still appears, rebuild from a clean state:

```powershell
.\packaging\scripts\clean_build.ps1
.\packaging\scripts\build_exe.ps1
```

### cv2 import failed

Ensure `opencv-python` is installed in `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then rebuild the EXE.

### ISCC.exe not found

Install Inno Setup 6. The script checks:

```text
C:\Users\<you>\AppData\Local\Programs\Inno Setup 6\ISCC.exe
C:\Program Files (x86)\Inno Setup 6\ISCC.exe
C:\Program Files\Inno Setup 6\ISCC.exe
```

It also accepts `ISCC.exe` on PATH.

### Antivirus false positive

PyInstaller bundles Python and native DLLs, which can trigger heuristic
warnings. Build on a clean machine, avoid onefile mode, and code-sign the
installer for distribution if needed.

### Installed app does not open

Check:

```text
%LOCALAPPDATA%/AIImageLayerExtractor/logs/crash.log
```

The launcher writes unhandled startup exceptions there and shows the path in an
error dialog.

## Source Workflow Is Preserved

Packaging files live under `packaging/`.
Build outputs live under `build/`, `dist/`, and `release/`.

The source workflow still works:

```powershell
python main.py
python -B -m pytest
```

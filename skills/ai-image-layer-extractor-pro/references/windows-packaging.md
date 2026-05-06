# Windows Packaging

## Entry Points

- `main.py`: source/development entry.
- `launcher.py`: packaged entry and smoke-test entry.

Do not merge these roles. Installer failures should not affect source development.

## User Data

Create user data under:

```text
%LOCALAPPDATA%/AIImageLayerExtractor/
+-- logs/
+-- config/
+-- cache/
+-- exports/
```

Never write logs, config, cache, or default exports into the install directory.

## PyInstaller

Use onedir mode for PySide6/OpenCV/numpy stability. Preserve Qt platform and image plugins. Avoid mandatory torch/SAM2/rembg/OCR dependencies in default builds.

Expected runnable output:

```text
dist/AIImageLayerExtractor/AIImageLayerExtractor.exe
```

## Inno Setup

Use per-user install:

```text
{localappdata}\Programs\AI Image Layer Extractor
```

Do not require administrator privileges. Create Start Menu and optional Desktop shortcuts. Uninstall program files only; preserve `%LOCALAPPDATA%/AIImageLayerExtractor`.

Expected installer:

```text
release/AIImageLayerExtractor_Setup_0.1.0_x64.exe
```

## Smoke Tests

Use:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe launcher.py --smoke-test
```

For installer validation, run silent install, installed EXE `--smoke-test`, silent uninstall, and verify the user data directory remains.

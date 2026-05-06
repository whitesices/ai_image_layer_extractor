# Packaging Workflow

Use this workflow for PyInstaller, Inno Setup, launcher, dependency, or installer changes.

## 1. Preserve Entry Points

- `main.py` remains source mode.
- `launcher.py` remains packaged mode and smoke-test entry.

## 2. Dependency Review

Keep runtime dependencies small. Do not add torch, SAM2, rembg, OCR, or OpenAI SDK as mandatory installer dependencies unless explicitly approved.

## 3. User Data Safety

Ensure logs, config, cache, and default exports go under:

```text
%LOCALAPPDATA%/AIImageLayerExtractor/
```

Never write user data into the installation directory.

## 4. Build

Run the existing scripts:

```powershell
.\packaging\scripts\build_exe.ps1
.\packaging\scripts\build_installer.ps1
```

or:

```powershell
.\packaging\scripts\build_all.ps1
```

## 5. Smoke Test

Validate:

- `dist/AIImageLayerExtractor/AIImageLayerExtractor.exe`
- `AIImageLayerExtractor.exe --smoke-test`
- installer creation under `release/`
- per-user install and uninstall when feasible

## 6. Report

Include installer path, EXE path, test results, and any warnings such as antivirus false positives or PySide6 DLL issues.

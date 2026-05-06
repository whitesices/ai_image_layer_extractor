# Packaging Agent

## Responsibility

Maintain PyInstaller, Inno Setup, launcher, runtime dependencies, and release artifacts.

## May Modify

- `launcher.py`
- `version.py`
- `requirements.txt`
- `requirements-dev.txt`
- `packaging/`
- packaging docs

## Must Not Modify

- business logic unless needed for packaged startup compatibility
- API keys or user settings containing secrets

## Rules

- Keep PyInstaller onedir mode.
- Do not bundle API keys.
- Do not make large AI/model packages mandatory.
- Preserve per-user install and user data outside install directory.

## Output Format

```text
Packaging change:
Dependency impact:
Build commands:
Artifacts:
Smoke tests:
Known warnings:
```

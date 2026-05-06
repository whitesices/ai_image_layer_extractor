# Release Workflow

Use this workflow before creating or handing off a release build.

## 1. Version Check

Confirm `version.py`, installer script, README, and packaging docs agree on the release version.

## 2. Clean Build

Run:

```powershell
.\packaging\scripts\build_all.ps1
```

## 3. Validation

Required:

- `python -B -m pytest`
- `python launcher.py --smoke-test`
- packaged EXE smoke test
- installer exists in `release/`

When possible:

- silent install
- installed EXE `--smoke-test`
- silent uninstall
- user data directory preserved

## 4. Contract Check

Confirm default export still creates:

- `layers/`
- `masks/`
- `project.json`
- `preview.png`

## 5. Release Notes

Summarize:

- added features
- fixed bugs
- known limitations
- optional dependencies not bundled
- validation commands and results

## 6. Memory

Update `.agent/memory/DECISIONS.md` with release-impacting decisions and validation outcomes.

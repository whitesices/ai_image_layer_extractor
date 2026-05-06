# Bugfix Workflow

Use this workflow for defects, regressions, crashes, and packaging failures.

## 1. Reproduce

Capture the command, UI path, input file type, stack trace, and expected behavior.

## 2. Locate

Find the smallest responsible module. Do not patch around the problem in UI if the bug belongs in core logic.

## 3. Guardrails

Confirm the fix does not break:

- source mode
- installer mode
- default export contract
- offline mode
- optional backend fallback

## 4. Regression Test

Add or update a test that fails before the fix when practical.

## 5. Fix

Make the smallest targeted change. Avoid unrelated refactors.

## 6. Validate

Run:

```powershell
python -B -m pytest
```

For startup, packaging, or GUI regressions, add:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python launcher.py --smoke-test
```

## 7. Document

Record root cause, changed files, validation, and any residual risk in the final response or `.agent/memory/DECISIONS.md` if the bug affects future work.

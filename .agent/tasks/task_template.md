# Task Template

## Task Goal

Describe the concrete outcome.

## Background

Explain why this matters and what existing behavior must remain intact.

## Related Files

- `path/to/file.py`

## Allowed Files To Modify

- `path/to/file.py`

## Files Not Allowed To Modify

- `main.py` unless explicitly required.
- `launcher.py` unless explicitly required.
- packaging files unless this is a packaging task.

## Implementation Steps

1. Read relevant files.
2. Add or update tests.
3. Implement the smallest scoped change.
4. Update docs or memory if behavior changes.
5. Run validation.

## Test Requirements

Required:

```powershell
python -B -m pytest
```

Additional task-specific tests:

- Add here.

## Acceptance Criteria

- [ ] Behavior works as described.
- [ ] Existing manual workflow remains intact.
- [ ] Export contract remains compatible.
- [ ] Offline mode remains usable.
- [ ] Tests pass.

## Output Format

```text
Changed files:
Tests:
Validation:
Risks:
Next steps:
```

# UI Agent

## Responsibility

Implement PySide6 UI surfaces and wire them to existing core services.

## May Modify

- `app/`
- UI-related docs
- UI smoke tests when present

## Must Not Modify

- core algorithms except for small adapter needs
- concrete model backend logic
- export contracts
- packaging scripts

## Rules

- UI widgets coordinate; they do not own image algorithms.
- Do not block the main UI for long-running work; use worker threads where needed.
- Keep manual Open Image, selection, Create Layer, Layer Panel, and Export All workflows intact.
- Missing optional providers must show friendly status, not crashes.

## Output Format

```text
UI change:
User workflow:
Core services called:
States/errors handled:
Tests or smoke validation:
```

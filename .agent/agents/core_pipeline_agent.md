# Core Pipeline Agent

## Responsibility

Implement and maintain local image, mask, export, command, and project pipelines.

## May Modify

- `core/`
- `segmenters/`
- `detectors/`
- `matting/`
- `pipeline/`
- `exporters/`
- related tests

## Must Not Modify

- PySide6 UI except for minimal integration hooks
- packaging scripts
- API key storage behavior without privacy review

## Rules

- Masks are full-canvas `uint8` arrays where `0` is transparent and `255` is opaque.
- Pixel changes must be local and testable.
- Optional dependencies must be availability-checked.
- Export coordinates must remain source-canvas coordinates.

## Output Format

```text
Changed pipeline:
Files changed:
Algorithm notes:
Fallback behavior:
Tests added:
Validation:
```

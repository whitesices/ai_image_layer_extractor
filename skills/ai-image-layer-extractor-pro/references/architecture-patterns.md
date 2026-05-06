# Architecture Patterns

## Placement Guide

- Put persistent state and serializable data contracts in `core/`.
- Put PySide6 rendering, dock panels, menus, and dialogs in `app/`.
- Put repeatable image/mask operations in `core/`, `segmenters/`, `matting/`, or `pipeline/`.
- Put optional external model adapters behind interfaces.
- Put format-specific output in `exporters/`.
- Put packaging-only behavior in `launcher.py` and `packaging/`.

## Incremental Change Pattern

1. Add or extend a dataclass/API in `core/`.
2. Add pure functions or service classes with type hints.
3. Add tests for the pure behavior.
4. Wire the feature into `MainWindow` or a panel with minimal UI code.
5. Run full tests and smoke tests.

## Existing Data Model Roles

- `LayerItem`: one extracted editable layer, full-canvas mask, bbox, visibility, opacity, blend mode.
- `ProjectData`: source image/path, ordered layer list, selected layers through UI, layer id generation.
- `MaskResult`: segmenter output containing full-canvas mask, bbox, score, and source backend.
- `ImageEditPlan`: LLM-produced structured command plan.
- `CommandExecutor`: local executor for plans; supports dry run and non-crashing errors.
- `BatchExporter`: multi-size transparent export with report generation.
- `LayerExporter`: stable single/all layer export contract.

## UI Rule

`MainWindow` may orchestrate project state and connect signals, but image processing must remain in core services. Avoid embedding OpenCV/Pillow algorithms in widgets.

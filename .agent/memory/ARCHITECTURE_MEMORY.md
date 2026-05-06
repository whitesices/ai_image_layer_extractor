# Architecture Memory

The project uses layered responsibilities:

- `app/`: PySide6 UI and orchestration.
- `core/`: state, dataclasses, mask utilities, command execution, batch export, project package save/open, quality pipeline.
- `llm/`: natural language to structured plan providers.
- `segmenters/`: segmentation backends.
- `detectors/`: object/text detector backends.
- `matting/`: mask and alpha refiners.
- `pipeline/`: composed processing flows.
- `exporters/`: specialized exports.
- `packaging/`: build and installer tooling.

Architecture rules:

- UI does not own image algorithms.
- LLM does not modify pixels.
- Optional AI/model backends are isolated and non-mandatory.
- Export coordinates remain source-canvas coordinates.
- User data belongs in `%LOCALAPPDATA%/AIImageLayerExtractor/`.

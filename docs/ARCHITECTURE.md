# Architecture

The project is intentionally layered:

- `app/`: PySide6 UI and user interaction.
- `core/`: data contracts, mask utilities, project state, command execution,
  batch export, project package save/open.
- `llm/`: natural-language providers that only create `ImageEditPlan` JSON.
- `detectors/`: optional object/text detector interfaces.
- `segmenters/`: OpenCV and optional segmentation backends.
- `matting/`: alpha and mask refinement backends.
- `pipeline/`: composable local processing flows.
- `exporters/`: specialized output formats such as UE UMG and PSD-compatible
  packages.

LLMs do not directly mutate pixels. All image and mask changes run through local
Python code that can be tested.


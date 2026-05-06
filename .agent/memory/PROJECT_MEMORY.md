# Project Memory

AI Image Layer Extractor is a local Python desktop application for extracting editable transparent PNG layers from flat AI-generated PNG/JPG/WEBP images.

Current capabilities include:

- PySide6 UI.
- OpenCV GrabCut manual rectangle segmentation.
- layer creation, rename, visibility, delete, single export, and export all.
- stable default export with layers, masks, `project.json`, and `preview.png`.
- AI Command Panel with Mock/OpenAI-style providers.
- structured `ImageEditPlan` command execution.
- Batch Export with sizes, padding, fit modes, and quality report.
- optional backend placeholders for rembg, SAM2, GroundingDINO, OCR, BiRefNet, and cloud image editing.
- UE UMG and PSD-compatible export paths.
- Windows PyInstaller/Inno Setup packaging.
- pytest suite.

Use `.agent/specs/000_project_guardrails.md` as the first reference for every task.

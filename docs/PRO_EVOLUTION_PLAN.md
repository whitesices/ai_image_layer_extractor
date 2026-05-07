# AI Image Layer Extractor Pro Evolution Plan

This document turns the broad product goal into staged engineering work. The
project should evolve toward Photoshop-like layer extraction workflows, but it
must keep the current MVP stable: manual rectangle selection, layer creation,
batch export, project metadata, and Windows packaging remain first-class.

## Current Capability Map

Already implemented:

- PySide6 desktop UI with image open, canvas pan/zoom, rectangle selection, and
  mask preview.
- OpenCV GrabCut/manual rectangle segmentation fallback.
- Layer list, rename, show/hide, delete, single-layer export, and export all.
- Stable export contract: `Export/layers`, `Export/masks`, `project.json`,
  and `preview.png`.
- AI Command Panel with offline Mock provider and optional OpenAI-compatible
  provider configuration.
- Structured `ImageEditPlan` execution through local `CommandExecutor`.
- Batch export with sizes, padding, fit modes, alpha-preserving PNG/WebP output,
  and `batch_report.json`.
- Optional extension points for SAM2, rembg, OCR, GroundingDINO, PSD, and UE UMG.

## Product Direction

The long-term target is not a full Photoshop clone in one jump. The useful
product wedge is:

1. Import a flat AI-generated image.
2. Use natural language or manual selection to identify objects.
3. Convert objects into editable transparent layers with source coordinates.
4. Clean masks and alpha edges with local deterministic tools.
5. Export production-ready assets for Photoshop, Figma, UE UMG, and game UI.

## Gap To Photoshop-Like Workflows

Major gaps to close in later phases:

- Layer ordering, grouping, duplicate/merge/lock, opacity, and blend-mode UI.
- Rich mask editing with brush cursor, selection tools, undo/redo, and preview
  thumbnails.
- Non-destructive adjustment layers and reusable edit history.
- Text/vector/logo extraction and editable text reconstruction.
- Smart object-like linked assets.
- Native PSD writing and stronger Figma/UE import automation.

## Phase 1: Smart Slice Bridge

Implemented in the current iteration:

- `MockLLMProvider` recognizes smart slicing/export commands such as
  `把图中所有人物图片元素全部输出 512x512`.
- `CommandExecutor` can execute `extract_target`,
  `extract_multiple_targets`, `detect_text_regions`, and
  `create_background_layer` through local pipelines.
- Smart slice plans can chain local extraction and batch export.
- No cloud image editing, no mandatory large model dependency, and no API key
  requirement were introduced.

Validation target: `python -B -m pytest`.

## Phase 2: Optional AI Recognition Backends

Recommended next work:

- Add a backend registry so Detector, Segmenter, and Matting Refiner settings
  instantiate through factories rather than UI conditionals.
- Wire GroundingDINO as an optional detector only when installed/configured.
- Wire SAM2 as an optional point/box/mask segmenter only when installed and
  weights are configured.
- Keep Mock/OpenCV fallbacks as the offline baseline.

## Phase 3: Lower Learning Cost

Make the app easier for non-technical users:

- Add guided command examples directly in AI Command Panel.
- Show plan previews in Chinese with clear risk labels.
- Provide one-click presets: `角色资源`, `UI 图标`, `UE UMG`, `PSD素材包`.
- Improve error messages when a command requires manual box selection or an
  optional backend.

## Phase 4: Production Layer Editing

Add Photoshop-inspired local features:

- Layer thumbnail panel with reorder, duplicate, lock, opacity, and grouping.
- Mask brush add/erase with stable undo/redo and visible brush cursor.
- Mask operations: fill holes, remove islands, expand/shrink, feather, smooth,
  and halo cleanup.
- `.ailp` project save/open should persist masks, layer states, selected layer,
  and non-sensitive settings.

## Phase 5: Export Pipelines

Strengthen downstream workflows:

- UE UMG export presets with texture naming, compression settings, and import
  script options.
- PSD-compatible package now, native PSD later when a reliable writer is chosen.
- Figma-friendly metadata and image asset folders.
- Batch export filename templates and reports suitable for CI or content
  pipeline audits.


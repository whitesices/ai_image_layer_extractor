---
name: ai-image-layer-extractor-pro
description: Build, extend, debug, review, or package AI Image Layer Extractor style Python desktop tools. Use when working on PySide6/Pillow/OpenCV/numpy apps that extract transparent PNG layers from flat AI images; natural-language ImageEditPlan commands; mask editing/refinement; batch export; project.json export contracts; optional SAM2/rembg/GroundingDINO/OCR/OpenAI backends; PSD-compatible packages; Unreal Engine UMG exports; or Windows PyInstaller/Inno Setup packaging.
---

# AI Image Layer Extractor Pro

## Core Rule

Treat the project as an existing productionizing desktop tool. Read the current repository first, preserve working flows, and make incremental, testable changes.

Never rebuild from scratch, delete `main.py` or `launcher.py`, force cloud/API/model dependencies, hardcode API keys, or break the stable `Export/layers`, `Export/masks`, `project.json`, `preview.png` contract.

## Default Workflow

1. Inspect the repo before editing: `rg --files`, `git status --short`, then read the relevant `README`, `PROJECT_MEMORY`, `core/`, `app/`, `llm/`, `segmenters/`, `tests/`, and `packaging/` files.
2. Identify the lowest-risk layer for the change:
   - Data contracts and validators: `core/`, `llm/schema.py`.
   - Image and mask algorithms: `core/`, `segmenters/`, `matting/`, `pipeline/`.
   - UI orchestration only: `app/`.
   - Specialized output: `exporters/`.
   - Installer behavior: `packaging/`, `launcher.py`, `version.py`.
3. Keep UI and core logic decoupled. UI widgets should call tested core services rather than mutate pixels directly.
4. Add or update focused tests for each new capability.
5. Run validation before handoff. Prefer `scripts/validate_project.ps1` from this skill when working in this repo.

## Architecture Boundaries

Use the existing project boundaries unless the local code proves otherwise:

- `app/`: PySide6 widgets, docks, dialogs, and user-action orchestration.
- `core/`: dataclasses, project state, mask utilities, quality pipeline, command execution, batch export, project package save/open.
- `llm/`: providers that convert natural language to `ImageEditPlan` JSON only.
- `image_editors/`: local or optional cloud image-editing adapters.
- `detectors/`: optional object/text detection backends.
- `segmenters/`: rectangle/point/mask prompted segmentation backends.
- `matting/`: alpha/mask refinement backends.
- `pipeline/`: composable local image-processing flows.
- `exporters/`: format-specific exporters such as UE UMG and PSD-compatible packages.
- `packaging/`: PyInstaller and Inno Setup scripts.

Load [references/architecture-patterns.md](references/architecture-patterns.md) when implementing new modules or deciding where logic belongs.

## Data And Export Contracts

Represent masks as full-canvas 2D `numpy.ndarray` arrays with `uint8` alpha semantics: `0` transparent, `255` opaque. Store bbox as `(x, y, width, height)` in source image coordinates.

Preserve these layer metadata fields in `project.json`:

- `id`
- `name`
- `visible`
- `file`
- `mask`
- `x`
- `y`
- `width`
- `height`
- `opacity`
- `blend_mode`

New metadata must be additive and backward-compatible. Batch reports, UE metadata, PSD-compatible notes, and quality reports should live in extra files instead of changing the base contract.

Load [references/export-contracts.md](references/export-contracts.md) before changing exporters, project serialization, batch outputs, or UE/PSD packages.

## AI Command Rules

LLMs only generate structured plans. They must never directly edit pixels, write arbitrary paths, or call tools. Pixel changes must run through local, tested Python code.

Offline behavior is mandatory. If OpenAI SDK/API key, SAM2, rembg, GroundingDINO, OCR, or other advanced dependencies are missing, use Mock/OpenCV/local fallbacks and return clear warnings instead of crashing.

Load [references/ai-command-and-backends.md](references/ai-command-and-backends.md) when editing `ImageEditPlan`, Mock/OpenAI providers, optional detector/segmenter backends, settings privacy, or command execution.

## Mask And Quality Workflow

Keep source images immutable. Manual brush tools and quality actions should modify preview masks, layer masks, or exported RGBA output only.

Prefer operations that preserve original RGB pixels unless halo removal is explicitly enabled. Use RGBA throughout export and resizing; avoid JPEG or repeated lossy compression.

Test at least:

- bbox and empty-mask behavior.
- island removal and hole filling.
- feather/dilate/erode/smooth output shape and dtype.
- brush add/erase and undo/redo.
- alpha preservation after export and resize.

## Batch, UE, PSD, And Project Packages

Batch export should tolerate per-layer failures and write a report with generated files, quality reports, warnings, and failed items.

UE UMG export should generate a package with `Textures/`, `Masks/`, `Data/`, and `Scripts/`, including an Unreal Editor Python import script. PSD export may be a PSD-compatible package if native PSD writing dependencies are unavailable.

Project save/open should use `.ailp` directory packages and must not store API keys.

## Windows Packaging

Keep source mode and installer mode independent:

- `python main.py` remains the development entry.
- `launcher.py` remains the PyInstaller/installer entry.
- PyInstaller uses onedir mode.
- User data belongs under `%LOCALAPPDATA%/AIImageLayerExtractor/`, not the install directory.
- Installer must not bundle API keys or optional model weights.

Load [references/windows-packaging.md](references/windows-packaging.md) before editing `launcher.py`, PyInstaller spec, Inno Setup, build scripts, or packaging docs.

## Validation

For normal feature work, run:

```powershell
.\skills\ai-image-layer-extractor-pro\scripts\validate_project.ps1
```

For packaging work, also run the existing packaging scripts:

```powershell
.\packaging\scripts\build_all.ps1
```

If GUI display is unavailable, use `QT_QPA_PLATFORM=offscreen` smoke tests. Report any tests or smoke checks that could not be run.

# AI Image Layer Extractor Pro Implementation Plan

Date: 2026-05-06

This plan is for progressive enhancement of the existing repository. The source
entry (`main.py`), packaged entry (`launcher.py`), current export contract, and
Windows installer pipeline must remain compatible.

## Current Architecture Confirmed

- `app/`: PySide6 UI widgets and orchestration.
- `core/`: project state, layer models, mask/image utilities, export, command execution.
- `segmenters/`: segmentation backends, currently OpenCV GrabCut plus optional placeholders.
- `llm/`: natural language providers and edit-plan JSON schema.
- `image_editors/`: optional image editing backend interfaces.
- `packaging/`: PyInstaller and Inno Setup scripts.
- `tests/`: focused unit tests; current baseline is `18 passed`.

The stable export contract remains:

```text
Export/
+-- layers/
+-- masks/
+-- project.json
+-- preview.png
```

Layer entries in `project.json` keep `id`, `name`, `visible`, `file`, `mask`,
`x`, `y`, `width`, `height`, `opacity`, and `blend_mode`.

## Stage 1: AI Command Plan Enhancements

Files to modify:

- `core/edit_plan.py`
- `llm/schema.py`
- `llm/mock_provider.py`
- `llm/prompt_templates.py`
- `llm/openai_provider.py`
- `core/command_executor.py`
- `app/ai_command_panel.py`
- `tests/test_edit_plan.py`
- `tests/test_mock_llm_provider.py`
- `tests/test_command_executor.py`

Work:

- Add task types: `extract_target`, `extract_multiple_targets`, `refine_mask`,
  `export_project`, `export_for_ue_umg`, `create_background_layer`,
  `create_shadow_layer`, `detect_text_regions`, and `future_psd_export`.
- Keep aliases for existing task names such as `export_ue_umg_layout`.
- Repair Chinese command fixtures and parsing so real Chinese commands work, not
  only mojibake strings.
- Add richer plan preview with task type, targets, output sizes, fit mode,
  padding, format, risk warnings, cloud API requirement, and confirmation state.
- Keep OpenAI optional and fall back to Mock when unavailable.

Validation:

```powershell
python -B -m pytest
```

## Stage 2: Target Extraction Pipeline

Files to add:

- `core/extraction_plan.py`
- `core/extraction_result.py`
- `pipeline/__init__.py`
- `pipeline/target_extraction_pipeline.py`
- `pipeline/mask_refine_pipeline.py`
- `pipeline/background_pipeline.py`

Work:

- Convert prompt + optional bbox/point/mask/layer id into `ExtractionResult`.
- Use OpenCV segmentation when bbox exists.
- Use detector interface when only a prompt exists.
- Return `user_action_required` instead of failing when advanced detectors are
  unavailable.
- Support background-layer mask inversion when foreground masks are available.

Validation:

```powershell
python -B -m pytest
```

## Stage 3: Pluggable Detectors, Segmenters, and Matting

Files to add:

- `detectors/__init__.py`
- `detectors/base_detector.py`
- `detectors/mock_detector.py`
- `detectors/grounding_dino_detector.py`
- `detectors/ocr_detector.py`
- `matting/__init__.py`
- `matting/base_matting_refiner.py`
- `matting/simple_alpha_refiner.py`
- `matting/birefnet_refiner.py`

Files to modify:

- `segmenters/base_segmenter.py`
- `segmenters/rembg_segmenter.py`
- `segmenters/sam2_segmenter.py`
- `core/app_settings.py`
- `app/settings_dialog.py`

Work:

- Add `DetectionResult` and `BaseDetector.detect`.
- Add non-crashing optional backends for GroundingDINO/OCR.
- Add `SimpleAlphaRefiner` using existing mask and quality utilities.
- Add capability/status methods to optional segmenters so missing dependencies
  do not crash.

Validation:

```powershell
python -B -m pytest
```

## Stage 4: Mask Tools and Quality Actions

Files to add:

- `core/mask_editor.py`
- `app/mask_tools_panel.py`

Files to modify:

- `core/mask_utils.py`
- `app/canvas_widget.py`
- `app/main_window.py`
- `tests/test_mask_utils.py`

Work:

- Add brush add/erase operations on masks.
- Keep an undo/redo stack of at least 10 mask states.
- Add clean holes, remove islands, smooth edge, expand, shrink, feather, and
  halo cleanup actions.
- Apply mask tools to the current preview mask or selected layer mask.

Validation:

```powershell
python -B -m pytest
```

## Stage 5: Batch Export Enhancements

Files to modify:

- `core/batch_exporter.py`
- `core/command_executor.py`
- `app/batch_export_panel.py`
- `core/app_settings.py`
- `app/settings_dialog.py`
- `tests/test_batch_exporter.py`

Work:

- Add export scopes: all, visible, selected, layer name, layer tag.
- Add filename templates.
- Add `job_id`, `export_time`, `exported_layers`, `sizes`, `quality_report`,
  and `failed_items` to `batch_report.json`.
- Continue exporting other layers when one fails.

Validation:

```powershell
python -B -m pytest
```

## Stage 6: UE UMG Export

Files to add:

- `exporters/__init__.py`
- `exporters/ue_umg_exporter.py`
- `pipeline/ue_export_pipeline.py`
- `tests/test_ue_umg_exporter.py`

Files to modify:

- `core/command_executor.py`
- `llm/mock_provider.py`
- `app/main_window.py`

Work:

- Export `Export_UE/Textures`, `Masks`, `Data`, and `Scripts`.
- Generate `DA_LayerExtractResult.json`, `ue_import_config.json`, and
  `import_to_unreal.py`.
- Execute via local exporter only; no Unreal dependency required for export.

Validation:

```powershell
python -B -m pytest
```

## Stage 7: Save/Open Project

Files to add:

- `core/project_package.py`
- `tests/test_project_package.py`

Files to modify:

- `app/main_window.py`

Work:

- Save `.ailp` directory packages with source image, masks, preview, and project
  metadata.
- Open `.ailp` packages and restore image, layers, masks, visibility, and names.
- Do not store API keys.

Validation:

```powershell
python -B -m pytest
```

## Stage 8: PSD-Compatible Package

Files to add:

- `exporters/psd_exporter.py`
- `tests/test_psd_exporter.py`

Work:

- Provide `PSDExporter.export(project, output_path)`.
- If true PSD dependencies are missing, export a PSD-compatible package with
  `layers/`, `masks/`, `project.json`, and `README_PSD_COMPATIBLE.txt`.

Validation:

```powershell
python -B -m pytest
```

## Stage 9: Settings System

Files to modify:

- `core/app_settings.py`
- `app/settings_dialog.py`
- `config.example.yaml`
- `.gitignore`

Work:

- Add providers/backends: OpenAI compatible, DeepSeek compatible placeholder,
  local server placeholder, detector backend, segmenter backend, matting
  refiner, export defaults, filename template, and privacy settings.
- Default privacy remains: no image upload, no cloud image editing.

Validation:

```powershell
python -B -m pytest
```

## Stage 10: Docs and Packaging Validation

Files to add:

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/AI_COMMANDS.md`
- `docs/EXPORT_CONTRACT.md`
- `docs/UE_UMG_EXPORT.md`
- `docs/PRIVACY_AND_API_KEYS.md`
- `docs/ROADMAP.md`

Files to modify:

- `README.md`
- `README.zh-CN.md`
- `packaging/README_PACKAGING.md`
- `packaging/README_PACKAGING.zh-CN.md`
- `PROJECT_MEMORY.md`
- `PROJECT_MEMORY.zh-CN.md`

Validation:

```powershell
python -B -m pytest
python launcher.py --smoke-test
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\packaging\scripts\build_all.ps1
```

If time permits, run silent install, installed EXE smoke, and silent uninstall.

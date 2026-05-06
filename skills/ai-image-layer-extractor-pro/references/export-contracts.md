# Export Contracts

## Stable Default Export

Keep this structure backward-compatible:

```text
Export/
+-- layers/
+-- masks/
+-- project.json
+-- preview.png
```

Each layer entry in `project.json` must keep:

```json
{
  "id": "001",
  "name": "character",
  "visible": true,
  "file": "layers/001_character.png",
  "mask": "masks/001_character_mask.png",
  "x": 120,
  "y": 350,
  "width": 280,
  "height": 420,
  "opacity": 1.0,
  "blend_mode": "normal"
}
```

Use relative paths in metadata. Sanitize filenames, but preserve user-facing layer names in JSON.

## Batch Export

Batch output may add:

```text
Export/
+-- layers/
|   +-- original/
|   +-- 256x256/
|   +-- 512x512/
+-- masks/
+-- project.json
+-- batch_report.json
+-- preview.png
```

`batch_report.json` should include job id, source image, export time, exported layers, sizes, warnings, quality report, and failed items. A single failed layer/spec must not abort the whole batch.

## UE UMG Export

Expected structure:

```text
Export_UE/
+-- Textures/
+-- Masks/
+-- Data/
|   +-- DA_LayerExtractResult.json
|   +-- ue_import_config.json
+-- Scripts/
    +-- import_to_unreal.py
```

Keep positions in source-canvas coordinates. Use UE-friendly asset names such as `T_layer_name` and `M_layer_name`.

## PSD-Compatible Export

If native PSD writing is unavailable, export a PSD-compatible package with layers, masks, project metadata, and `README_PSD_COMPATIBLE.txt`. Do not fail simply because a PSD dependency is absent.

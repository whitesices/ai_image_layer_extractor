# AI Image Layer Extractor Project Memory

Last updated: 2026-05-06

## Project Purpose

AI Image Layer Extractor is a local Python desktop MVP for extracting editable transparent PNG layers from flat AI-generated images. The current workflow is manual-box-selection first, with OpenCV-assisted mask generation and clean export metadata for Photoshop, Figma, Unreal Engine UMG, or other downstream tools.

## Current Implementation

- Entry point: `main.py`
- Desktop UI: PySide6 in `app/`
- Core project state and image logic: `core/`
- Segmentation backends: `segmenters/`
- Tests: `tests/`

Implemented MVP capabilities:

- Open PNG / JPG / WEBP source images.
- Display image on a central canvas.
- Zoom with mouse wheel.
- Pan with right or middle mouse drag.
- Draw a rectangular selection with left mouse drag.
- Generate a mask preview after selection.
- Confirm the preview as a layer.
- Rename, show/hide, delete, export one layer, export all layers.
- Export cropped transparent layer PNGs, cropped mask PNGs, `project.json`, and `preview.png`.

## Important Files

- `core/layer.py`: `MaskResult` and `LayerItem`.
- `core/project.py`: `ProjectData`, layer collection, source image state.
- `core/mask_utils.py`: bbox, cleanup, feather/dilate/erode, RGBA application.
- `core/exporter.py`: `LayerExporter` and export contract.
- `segmenters/base_segmenter.py`: backend interface.
- `segmenters/opencv_segmenter.py`: OpenCV GrabCut backend with rectangle fallback.
- `segmenters/rembg_segmenter.py`: placeholder for future rembg backend.
- `segmenters/sam2_segmenter.py`: placeholder for future SAM2 backend.
- `app/canvas_widget.py`: image display, selection, zoom/pan, mask overlay, layer bbox drawing.
- `app/layer_panel.py`: layer list, layer actions, and inline rename editor sizing.
- `app/main_window.py`: orchestration between UI, project state, segmentation, export, and global stylesheet.

## Architecture Notes

UI and core logic are intentionally decoupled:

- UI widgets emit selections and layer actions.
- `MainWindow` coordinates workflows.
- `ProjectData` owns source image state and layer metadata.
- `BaseSegmenter` implementations return full-canvas `MaskResult` objects.
- `LayerExporter` writes files and updates layer-relative file paths.

Masks are full-canvas `uint8` arrays in the range `0..255`. Layer PNGs and mask PNGs are cropped to the layer bbox, while `project.json` stores the original canvas coordinates.

## Export Contract

Export folder:

```text
Export/
+-- layers/
+-- masks/
+-- project.json
+-- preview.png
```

Layer JSON fields:

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

Keep this contract stable unless downstream importers are updated at the same time.

## UI Maintenance Notes

On 2026-05-06, layer renaming in the right-side layer list clipped the inline editor text vertically. The screenshot showed the selected `QListWidgetItem` row and embedded rename `QLineEdit` were too short, so characters were partially hidden.

Fix applied:

- Added `LayerItemDelegate` in `app/layer_panel.py`.
- Overrode `sizeHint()` to keep layer rows at least 42 px tall.
- Overrode `createEditor()` so inline `QLineEdit` editors get enough minimum height.
- Overrode `updateEditorGeometry()` to inset the editor inside the row instead of letting it press against row edges.
- Updated `app/main_window.py` stylesheet for `QListWidget::item` and `QListWidget QLineEdit` padding/min-height.

Validation after the UI fix:

```text
python -m compileall app core segmenters tests main.py
python -B -m pytest
QT_QPA_PLATFORM=offscreen MainWindow smoke test
```

Result: tests passed and `MainWindow` instantiated successfully.

## Validation

Known passing command:

```powershell
cd C:\ML\EditImage\ai_image_layer_extractor
python -B -m pytest
```

Latest result:

```text
5 passed in 0.13s
```

`pytest.ini` restricts discovery to `tests/` and disables pytest cache because earlier environment attempts created inaccessible `pytest-cache-files-*` folders in the project root.

## Environment Notes

At creation time, the active global Python was 3.12.7. It did not have `PySide6` or `cv2` installed. The code is still testable because `mask_utils.py` and `OpenCVSegmenter` include a minimal fallback when `cv2` is unavailable.

On 2026-05-06, `PySide6==6.11.0` failed on this machine with:

```text
ImportError: DLL load failed while importing QtWidgets: specified program could not be found.
```

`dumpbin` showed `Qt6Core.dll` trying to load ICU-related DLLs, and the system/Anaconda ICU versions were not compatible. Pinning and reinstalling `PySide6==6.7.3` fixed `QtCore`, `QtWidgets`, and `MainWindow` smoke tests. Keep `requirements.txt` pinned unless a newer PySide6 version is verified locally.

For full GUI and GrabCut behavior, install:

```powershell
pip install -r requirements.txt
```

Then run:

```powershell
python main.py
```

## Known Environment Residue

Three directories named like `pytest-cache-files-*` may remain in the project root. They were created by pytest when the system denied cache writes and then became inaccessible to the current process. They are ignored by `.gitignore` and excluded by `pytest.ini`.

## Next Good Improvements

1. Add brush-based manual mask editing.
2. Add per-layer mask preview thumbnail in the layer panel.
3. Add `Save Project` / `Open Project` for restoring layer state.
4. Add SAM2 point/box segmentation in `segmenters/sam2_segmenter.py`.
5. Add rembg backend in `segmenters/rembg_segmenter.py`.
6. Add OCR text layer detection.
7. Add PSD export.
8. Add UE UMG JSON export and UE Python Texture2D import automation.

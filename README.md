# AI Image Layer Extractor

AI Image Layer Extractor is a local desktop MVP for extracting editable
transparent PNG layers from flat AI-generated PNG/JPG/WEBP images.

The current MVP uses:

- PySide6 for the desktop UI
- OpenCV GrabCut for rectangle-prompted mask generation
- Pillow for image IO and transparent PNG export
- numpy for mask and array processing

The source workflow and the Windows installer workflow are both supported.

## Installer Usage

Download or build:

```text
release/AIImageLayerExtractor_Setup_0.1.0_x64.exe
```

Then:

1. Double-click `AIImageLayerExtractor_Setup_0.1.0_x64.exe`.
2. Keep the desktop shortcut option checked if desired.
3. Launch from the desktop shortcut or Start Menu shortcut.

The installer uses a per-user install directory:

```text
%LOCALAPPDATA%/Programs/AI Image Layer Extractor
```

The installed application stores user data outside the install directory:

```text
%LOCALAPPDATA%/AIImageLayerExtractor/
+-- logs/
+-- config/
+-- cache/
+-- exports/
```

Uninstalling the application removes only the program files. It does not delete
the user data directory.

## Development Run

Python 3.10+ is required.

```powershell
cd C:\ML\EditImage\ai_image_layer_extractor
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

If PowerShell execution policy blocks activation scripts, run the `.venv`
Python directly as shown above.

For tests and packaging tools:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -B -m pytest
```

## Windows PySide6 DLL Note

This project pins:

```text
PySide6==6.7.3
```

On this machine, `PySide6==6.11.0` failed with a Qt DLL load error. If you see:

```text
ImportError: DLL load failed while importing QtWidgets
```

reinstall the pinned version:

```powershell
.\.venv\Scripts\python.exe -m pip install --force-reinstall PySide6==6.7.3
```

## Basic Workflow

1. Click `Open Image` to load a PNG, JPG, JPEG, or WEBP image.
2. Drag on the canvas with the left mouse button to select an element.
3. Release the mouse button to generate a semi-transparent mask preview.
4. Click `Create Layer` to save the current mask as a layer.
5. Rename, show/hide, delete, or export layers from the right-side panel.
6. Click `Export All` to write layers, masks, `project.json`, and `preview.png`.

Canvas controls:

- Mouse wheel: zoom
- Right or middle mouse drag: pan
- `Fit View`: fit the image to the viewport

## Export Structure

```text
Export/
+-- layers/
|   +-- 001_layer_name.png
|   +-- ...
+-- masks/
|   +-- 001_layer_name_mask.png
|   +-- ...
+-- project.json
+-- preview.png
```

Example `project.json`:

```json
{
  "source_image": "input.png",
  "canvas": {
    "width": 1448,
    "height": 1086
  },
  "layers": [
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
  ]
}
```

Layer PNGs and mask PNGs are cropped to bbox. The JSON coordinates restore each
layer to its original source-canvas position.

## Packaging

See:

```text
packaging/README_PACKAGING.md
```

One-command build:

```powershell
.\packaging\scripts\build_all.ps1
```

Outputs:

```text
dist/AIImageLayerExtractor/
release/AIImageLayerExtractor_Setup_0.1.0_x64.exe
```

## Project Structure

```text
ai_image_layer_extractor/
+-- main.py
+-- launcher.py
+-- version.py
+-- requirements.txt
+-- requirements-dev.txt
+-- README.md
+-- app/
+-- core/
+-- segmenters/
+-- tests/
+-- packaging/
```

## Future Extensions

1. SAM2 point/box segmentation.
2. rembg background removal.
3. OCR text layer detection.
4. PSD export.
5. Unreal Engine UMG layout JSON export.
6. UE Python Texture2D import automation.

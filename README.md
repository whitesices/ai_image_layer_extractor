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

## AI Command Natural Language Editing

Open `AI > AI Command Panel` to describe an edit or export task in natural
language. The LLM layer only creates a structured `ImageEditPlan`; it does not
directly edit pixels. The plan is then executed by local, testable Python code.

Buttons:

- `Parse`: convert text into an edit plan.
- `Dry Run`: preview what would happen without writing files.
- `Execute`: run the confirmed plan.
- `Clear`: reset the input and preview.

If no external API key is configured, the panel automatically uses the offline
`MockLLMProvider`, which understands common Chinese batch export and rename
commands.

Example commands:

1. `把所有图层导出 512x512`
2. `把当前选中图层导出 256、512、1024 三套尺寸`
3. `把所有图层加 32 像素透明边距后导出`
4. `把角色图层重命名为 player_character`
5. `把 UI 图标全部导出为 128x128 透明 PNG`
6. `导出适合 UE UMG 使用的 512 和 1024 两套资源`

## Batch Export

Open `Batch > Batch Export` to export all layers or the selected layer into
production sizes such as 128x128, 256x256, 512x512, and 1024x1024.

Supported fit modes:

- `contain`: preserve aspect ratio and fit fully inside the target canvas.
- `cover`: preserve aspect ratio, fill the target canvas, and crop if needed.
- `stretch`: force the layer to the target width and height.
- `max_side`: make the longest side match the requested size.
- `original`: keep the original bbox size.

Batch export writes `batch_report.json` and multi-size folders under
`Export/layers/`.

## Mask Tools

Open `Mask > Mask Tools` to edit the current preview mask or selected layer
mask. The panel includes brush add/erase, brush size, feather, expand, shrink,
smooth, fill holes, remove islands, undo, redo, apply, and reset.

Mask tools only edit masks. They do not modify the source image pixels.

## UE UMG Export

AI commands such as `把所有图层导出成 UE UMG 可以用的资源` generate a UE package:

```text
Export_UE/
+-- Textures/
+-- Masks/
+-- Data/
+-- Scripts/
```

The generated `Scripts/import_to_unreal.py` can be run inside Unreal Editor
Python to import textures. Full Widget Blueprint creation is reserved for a
future extension.

## Project Packages

Use `Project > Save Project` and `Project > Open Project` to work with `.ailp`
directory packages. Packages include `project.json`, source image, masks,
layers, and preview. API keys are never saved into project packages.

## PSD-Compatible Export

The AI command `按 PSD 分层思路导出素材包` exports a PSD-compatible package with
transparent layer PNGs, masks, `project.json`, and `README_PSD_COMPATIBLE.txt`.
Native PSD writing is an experimental future extension.

## LLM Provider Settings

Open `AI > Settings` to choose:

- `Mock`: offline rule-based parser, no API key required.
- `OpenAI`: optional external parser that turns natural language into
  `ImageEditPlan` JSON.
- `OpenAI Compatible`, `DeepSeek Compatible`, and `Local Server`: optional
  OpenAI-compatible text-planning providers that read a custom `LLM API base URL`.

Optional detector/segmenter/matting settings include Mock, GroundingDINO, OCR,
OpenCV GrabCut, rembg, SAM2, Simple, and BiRefNet. Missing optional dependencies
fall back safely and do not prevent app startup.

OpenAI/OpenAI-compatible support is optional. To use it in source mode, install
the SDK yourself:

```powershell
.\.venv\Scripts\python.exe -m pip install openai
```

The Windows installer does not include any API key.

For compatible providers, configure:

- `LLM API base URL`, for example `https://api.example.com/v1`.
- `LLM model`, using the provider-specific model name.
- `LLM API key`, preferably through `OPENAI_API_KEY`.

The base URL can also be provided through `LLM_API_BASE_URL` or `OPENAI_BASE_URL`.
If the SDK, key, or required base URL is missing, AI Command falls back to the
offline Mock provider.

## API Key Safety

API keys are never hardcoded and are never bundled into the installer.

Key lookup order:

1. `OPENAI_API_KEY` environment variable.
2. User settings file, only if the user explicitly chooses to save it.

Compatible endpoint URL lookup order:

1. `LLM_API_BASE_URL` environment variable.
2. `OPENAI_BASE_URL` environment variable.
3. User settings file.

Settings are stored under:

```text
%LOCALAPPDATA%/AIImageLayerExtractor/config/settings.json
```

Do not commit `settings.json`. If system-level secret storage is not configured,
prefer the `OPENAI_API_KEY` environment variable or choose not to save the key.

## Offline Mode

Without an API key, the app still supports:

- Open Image
- manual selection and mask preview
- Create Layer
- Export All
- Batch Export
- Mock AI command parsing
- Windows installer startup

No network access is required for the core workflow.

## Cloud Image Editing Privacy

The first production version does not upload images for editing by default.
`image_editors/openai_image_editor.py` is only an optional extension point.

Any future cloud image editing feature should clearly ask for confirmation
because source images, masks, or selected regions may be uploaded to an API
service.

## Quality Processing

Batch export uses a local quality pipeline that keeps intermediate images in
RGBA, writes PNG losslessly by default, supports transparent padding, and avoids
unnecessary JPEG recompression.

The pipeline includes:

- alpha-preserving resize
- contain / cover / stretch / max_side / original fit modes
- optional edge refinement
- optional alpha halo cleanup
- export quality reporting

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

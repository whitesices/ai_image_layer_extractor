from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from core.image_utils import sanitize_filename
from core.layer import LayerItem
from core.mask_utils import apply_mask_to_rgba, normalize_mask
from core.project import ProjectData


@dataclass(slots=True)
class UEUMGExportResult:
    output_dir: Path
    generated_files: list[Path]
    warnings: list[str] = field(default_factory=list)


class UEUMGExporter:
    """Export layer textures, masks, metadata, and an Unreal Python import script."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.textures_dir = self.output_dir / "Textures"
        self.masks_dir = self.output_dir / "Masks"
        self.data_dir = self.output_dir / "Data"
        self.scripts_dir = self.output_dir / "Scripts"

    def export(self, project: ProjectData, layers: list[LayerItem] | None = None) -> UEUMGExportResult:
        if project.image is None:
            raise RuntimeError("No source image is loaded")

        selected_layers = layers if layers is not None else project.layers
        self._ensure_dirs()
        generated: list[Path] = []
        layer_records: list[dict] = []

        for z_order, layer in enumerate(selected_layers):
            safe_name = sanitize_filename(layer.name)
            texture_name = f"T_{safe_name}.png"
            mask_name = f"M_{safe_name}.png"
            texture_path = self.textures_dir / texture_name
            mask_path = self.masks_dir / mask_name

            rgba = apply_mask_to_rgba(project.image, layer.mask, layer.bbox)
            rgba.save(texture_path, format="PNG")

            x, y, width, height = layer.bbox
            mask_crop = normalize_mask(layer.mask)[y : y + height, x : x + width]
            Image.fromarray(mask_crop, mode="L").save(mask_path)
            generated.extend([texture_path, mask_path])

            layer_records.append(
                {
                    "name": layer.name,
                    "texture_path": f"Textures/{texture_name}",
                    "mask_path": f"Masks/{mask_name}",
                    "x": layer.x,
                    "y": layer.y,
                    "width": layer.width,
                    "height": layer.height,
                    "anchor": [0.0, 0.0],
                    "pivot": [0.0, 0.0],
                    "opacity": layer.opacity,
                    "z_order": z_order,
                    "ue_asset_name": f"T_{safe_name}",
                    "suggested_umg_slot": {
                        "position": [layer.x, layer.y],
                        "size": [layer.width, layer.height],
                        "alignment": [0.0, 0.0],
                    },
                }
            )

        data_path = self.data_dir / "DA_LayerExtractResult.json"
        config_path = self.data_dir / "ue_import_config.json"
        script_path = self.scripts_dir / "import_to_unreal.py"

        payload = {
            "source_image": project.source_image_name,
            "canvas_width": project.canvas_size[0],
            "canvas_height": project.canvas_size[1],
            "layers": layer_records,
        }
        data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        config_path.write_text(
            json.dumps(
                {
                    "asset_root": "/Game/AIImageLayerExtractor",
                    "texture_source_dir": "../Textures",
                    "mask_source_dir": "../Masks",
                    "set_srgb": True,
                    "texture_group": "UI",
                    "compression_settings": "TC_EditorIcon",
                    "data_asset": "DA_LayerExtractResult.json",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        script_path.write_text(_UNREAL_IMPORT_SCRIPT, encoding="utf-8")
        generated.extend([data_path, config_path, script_path])
        return UEUMGExportResult(self.output_dir, generated)

    def _ensure_dirs(self) -> None:
        self.textures_dir.mkdir(parents=True, exist_ok=True)
        self.masks_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.scripts_dir.mkdir(parents=True, exist_ok=True)


_UNREAL_IMPORT_SCRIPT = r'''"""Import AI Image Layer Extractor textures into Unreal Editor.

Run inside Unreal Editor's Python environment. This script imports PNG files and
writes a small import report. It leaves UMG widget blueprint creation as a
future extension point.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


def main():
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    config_path = root_dir / "Data" / "ue_import_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    asset_root = config.get("asset_root", "/Game/AIImageLayerExtractor")
    texture_dir = root_dir / "Textures"
    mask_dir = root_dir / "Masks"
    imported = []

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    tasks = []
    for folder in [texture_dir, mask_dir]:
        for png_path in folder.glob("*.png"):
            task = unreal.AssetImportTask()
            task.filename = str(png_path)
            task.destination_path = asset_root + "/" + folder.name
            task.destination_name = png_path.stem
            task.automated = True
            task.save = True
            tasks.append(task)
    asset_tools.import_asset_tasks(tasks)

    for task in tasks:
        for object_path in task.imported_object_paths:
            asset = unreal.load_asset(object_path)
            if asset:
                imported.append(object_path)
                try:
                    asset.set_editor_property("srgb", bool(config.get("set_srgb", True)))
                except Exception:
                    pass

    report_path = root_dir / "Data" / "ue_import_report.json"
    report_path.write_text(json.dumps({"imported": imported}, indent=2), encoding="utf-8")
    unreal.log("AI Image Layer Extractor import complete: {}".format(report_path))


if __name__ == "__main__":
    main()
'''


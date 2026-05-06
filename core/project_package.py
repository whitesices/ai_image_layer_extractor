from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .exporter import LayerExporter
from .image_utils import load_source_image
from .layer import LayerItem
from .mask_utils import normalize_mask
from .project import ProjectData


class ProjectPackage:
    """Save and open debug-friendly .ailp directory packages."""

    def save(
        self,
        project: ProjectData,
        package_dir: str | Path,
        *,
        selected_layer_id: str | None = None,
        ui_state: dict[str, Any] | None = None,
        batch_settings: dict[str, Any] | None = None,
    ) -> Path:
        if project.image is None:
            raise RuntimeError("No source image is loaded")
        root = Path(package_dir)
        root.mkdir(parents=True, exist_ok=True)
        (root / "source").mkdir(parents=True, exist_ok=True)

        if project.source_image_path and project.source_image_path.exists():
            source_copy = root / "source" / project.source_image_path.name
            shutil.copy2(project.source_image_path, source_copy)
        else:
            source_copy = root / "source" / "source.png"
            project.image.save(source_copy)

        LayerExporter(root).export_all_layers(project)
        data = json.loads((root / "project.json").read_text(encoding="utf-8"))
        data["package"] = {
            "format": "ailp_directory",
            "source": source_copy.relative_to(root).as_posix(),
            "selected_layer_id": selected_layer_id,
            "ui_state": ui_state or {},
            "batch_settings": batch_settings or {},
            "ai_settings": {"api_key_saved": False},
        }
        (root / "project.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return root

    def open(self, package_dir: str | Path) -> ProjectData:
        root = Path(package_dir)
        data = json.loads((root / "project.json").read_text(encoding="utf-8"))
        package = data.get("package", {})
        source_rel = package.get("source") or data.get("source_image")
        source_path = root / source_rel
        image = load_source_image(source_path)

        project = ProjectData()
        project.set_source_image(source_path, image)
        project.layers.clear()

        for layer_data in data.get("layers", []):
            mask_rel = layer_data.get("mask")
            if not mask_rel:
                continue
            mask_path = root / mask_rel
            with Image.open(mask_path) as mask_image:
                mask_crop = normalize_mask(np.asarray(mask_image.convert("L")))
            full_mask = np.zeros((image.height, image.width), dtype=np.uint8)
            x = int(layer_data["x"])
            y = int(layer_data["y"])
            width = int(layer_data["width"])
            height = int(layer_data["height"])
            full_mask[y : y + height, x : x + width] = mask_crop[:height, :width]
            layer = LayerItem(
                id=str(layer_data["id"]),
                name=str(layer_data["name"]),
                mask=full_mask,
                bbox=(x, y, width, height),
                visible=bool(layer_data.get("visible", True)),
                opacity=float(layer_data.get("opacity", 1.0)),
                blend_mode=str(layer_data.get("blend_mode", "normal")),
                file=str(layer_data.get("file", "")),
                mask_file=str(layer_data.get("mask", "")),
            )
            project.layers.append(layer)

        max_id = 0
        for layer in project.layers:
            if layer.id.isdigit():
                max_id = max(max_id, int(layer.id))
        project._next_layer_index = max_id + 1
        return project

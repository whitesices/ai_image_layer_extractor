from __future__ import annotations

import json
import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.exporter import LayerExporter
from core.layer import MaskResult
from core.project import ProjectData


def test_export_all_layers_writes_expected_files() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"exporter_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        image = Image.new("RGB", (16, 12), (10, 120, 220))
        mask = np.zeros((12, 16), dtype=np.uint8)
        mask[3:9, 4:11] = 255

        project = ProjectData()
        project.set_source_image(tmp_path / "input.png", image)
        layer = project.add_layer_from_mask("hero character", MaskResult(mask=mask))

        export_dir = tmp_path / "Export"
        result = LayerExporter(export_dir).export_all_layers(project)

        assert len(result["layers"]) == 1
        assert (export_dir / "layers" / "001_hero_character.png").exists()
        assert (export_dir / "masks" / "001_hero_character_mask.png").exists()
        assert (export_dir / "project.json").exists()
        assert (export_dir / "preview.png").exists()

        with Image.open(export_dir / "layers" / "001_hero_character.png") as exported_layer:
            assert exported_layer.size == (7, 6)
        assert layer.file == "layers/001_hero_character.png"
        assert layer.mask_file == "masks/001_hero_character_mask.png"

        data = json.loads((export_dir / "project.json").read_text(encoding="utf-8"))
        assert data["source_image"] == "input.png"
        assert data["canvas"] == {"width": 16, "height": 12}
        assert data["layers"][0]["x"] == 4
        assert data["layers"][0]["y"] == 3
        assert data["layers"][0]["width"] == 7
        assert data["layers"][0]["height"] == 6
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

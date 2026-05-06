from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.layer import MaskResult
from core.project import ProjectData
from core.project_package import ProjectPackage


def test_project_package_save_and_open_restores_layer() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"ailp_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        source_path = tmp_path / "input.png"
        Image.new("RGB", (20, 16), (100, 120, 180)).save(source_path)
        image = Image.open(source_path).copy()
        mask = np.zeros((16, 20), dtype=np.uint8)
        mask[4:12, 6:15] = 255
        project = ProjectData()
        project.set_source_image(source_path, image)
        project.add_layer_from_mask("hero", MaskResult(mask=mask))

        package_dir = tmp_path / "MyProject.ailp"
        ProjectPackage().save(project, package_dir, selected_layer_id="001")
        restored = ProjectPackage().open(package_dir)

        assert restored.image is not None
        assert restored.canvas_size == (20, 16)
        assert len(restored.layers) == 1
        assert restored.layers[0].name == "hero"
        assert restored.layers[0].bbox == (6, 4, 9, 8)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


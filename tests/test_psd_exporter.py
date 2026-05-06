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
from exporters.psd_exporter import PSDExporter


def test_psd_exporter_writes_compatible_package() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"psd_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        image = Image.new("RGB", (20, 16), (100, 120, 180))
        mask = np.zeros((16, 20), dtype=np.uint8)
        mask[4:12, 6:15] = 255
        project = ProjectData()
        project.set_source_image(tmp_path / "input.png", image)
        project.add_layer_from_mask("hero", MaskResult(mask=mask))

        result = PSDExporter().export(project, tmp_path / "PSD_Compatible")

        assert result.native_psd is False
        assert (tmp_path / "PSD_Compatible" / "README_PSD_COMPATIBLE.txt").exists()
        assert (tmp_path / "PSD_Compatible" / "layers" / "001_hero.png").exists()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

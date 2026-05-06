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

from core.batch_exporter import BatchExporter
from core.edit_plan import BatchOutputSpec
from core.layer import MaskResult
from core.project import ProjectData


def _make_project(tmp_path: Path) -> ProjectData:
    image = Image.new("RGB", (32, 24), (20, 80, 160))
    mask = np.zeros((24, 32), dtype=np.uint8)
    mask[6:18, 8:24] = 255
    project = ProjectData()
    project.set_source_image(tmp_path / "input.png", image)
    project.add_layer_from_mask("hero", MaskResult(mask=mask))
    return project


def test_batch_exporter_outputs_correct_size_and_alpha() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"batch_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        export_dir = tmp_path / "Export"

        result = BatchExporter(export_dir).export_layers(
            project,
            project.layers,
            [BatchOutputSpec(64, 64, "contain", 0, "png")],
        )

        output_path = export_dir / "layers" / "64x64" / "001_hero_64x64.png"
        assert output_path.exists()
        with Image.open(output_path) as exported:
            assert exported.size == (64, 64)
            assert exported.mode == "RGBA"
            assert "A" in exported.getbands()

        assert result.report_path == export_dir / "batch_report.json"
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        assert report["records"][0]["layer_id"] == "001"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_batch_exporter_reports_job_quality_and_filename_template() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"batch_template_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        export_dir = tmp_path / "Export"

        result = BatchExporter(export_dir, filename_template="{name}@{width}x{height}.{ext}").export_layers(
            project,
            project.layers,
            [BatchOutputSpec(32, 32, "stretch", 4, "png")],
        )

        output_path = export_dir / "layers" / "32x32" / "hero@32x32.png"
        assert output_path.exists()
        report = json.loads(result.report_path.read_text(encoding="utf-8"))
        assert report["job_id"]
        assert report["export_time"]
        assert report["exported_layers"] == ["001"]
        assert report["quality_report"]
        assert report["failed_items"] == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_batch_exporter_fit_modes_create_outputs() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"batch_modes_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        export_dir = tmp_path / "Export"
        specs = [
            BatchOutputSpec(40, 40, "contain", 0, "png"),
            BatchOutputSpec(40, 40, "cover", 0, "png"),
            BatchOutputSpec(40, 40, "stretch", 0, "png"),
            BatchOutputSpec(40, 40, "max_side", 0, "png"),
        ]

        BatchExporter(export_dir).export_layers(project, project.layers, specs)

        assert (export_dir / "layers" / "40x40" / "001_hero_40x40.png").exists()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

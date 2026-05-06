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

from core.command_executor import CommandExecutor
from core.edit_plan import EditTask, ImageEditPlan, QualityOptions
from core.layer import MaskResult
from core.project import ProjectData
from exporters.ue_umg_exporter import UEUMGExporter


def _make_project(tmp_path: Path) -> ProjectData:
    image = Image.new("RGB", (32, 24), (40, 90, 160))
    mask = np.zeros((24, 32), dtype=np.uint8)
    mask[4:18, 6:22] = 255
    project = ProjectData()
    project.set_source_image(tmp_path / "input.png", image)
    project.add_layer_from_mask("hero", MaskResult(mask=mask))
    return project


def test_ue_umg_exporter_writes_expected_structure() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"ue_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        output_dir = tmp_path / "Export_UE"

        result = UEUMGExporter(output_dir).export(project)

        assert (output_dir / "Textures" / "T_hero.png").exists()
        assert (output_dir / "Masks" / "M_hero.png").exists()
        assert (output_dir / "Data" / "DA_LayerExtractResult.json").exists()
        assert (output_dir / "Data" / "ue_import_config.json").exists()
        assert (output_dir / "Scripts" / "import_to_unreal.py").exists()
        data = json.loads((output_dir / "Data" / "DA_LayerExtractResult.json").read_text(encoding="utf-8"))
        assert data["layers"][0]["ue_asset_name"] == "T_hero"
        assert result.generated_files
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_command_executor_runs_ue_export() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"ue_exec_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        plan = ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="export_for_ue_umg",
            requires_confirmation=False,
            raw_user_text="把所有图层导出成 UE UMG 可以用的资源",
            tasks=[
                EditTask(
                    type="export_for_ue_umg",
                    target="all_layers",
                    layer_ids=[],
                    output_name="Export_UE",
                    sizes=[],
                    transparent_background=True,
                    quality=QualityOptions(),
                    params={},
                )
            ],
        )

        result = CommandExecutor(project, tmp_path).execute(plan)

        assert result.success is True
        assert (tmp_path / "Export_UE" / "Data" / "ue_import_config.json").exists()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


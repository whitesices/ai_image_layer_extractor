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
from core.edit_plan import BatchOutputSpec, EditTask, ImageEditPlan, QualityOptions
from core.layer import MaskResult
from core.project import ProjectData


def _make_project(tmp_path: Path) -> ProjectData:
    image = Image.new("RGB", (32, 24), (80, 120, 200))
    mask = np.zeros((24, 32), dtype=np.uint8)
    mask[4:20, 8:24] = 255
    project = ProjectData()
    project.set_source_image(tmp_path / "input.png", image)
    project.add_layer_from_mask("hero", MaskResult(mask=mask))
    return project


def _batch_plan() -> ImageEditPlan:
    return ImageEditPlan(
        version="1.0",
        language="zh-CN",
        intent="batch_export",
        requires_confirmation=False,
        raw_user_text="把所有图层导出 512x512",
        tasks=[
            EditTask(
                type="batch_export_layers",
                target="all_layers",
                layer_ids=[],
                output_name=None,
                sizes=[BatchOutputSpec(32, 32, "contain", 0, "png")],
                transparent_background=True,
                quality=QualityOptions(),
                params={},
            )
        ],
    )


def test_command_executor_dry_run_does_not_generate_files() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"executor_dry_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        export_dir = tmp_path / "Export"

        result = CommandExecutor(project, export_dir).execute(_batch_plan(), dry_run=True)

        assert result.success is True
        assert not result.generated_files
        assert not (export_dir / "batch_report.json").exists()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_command_executor_execute_generates_batch_report() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"executor_run_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        export_dir = tmp_path / "Export"

        result = CommandExecutor(project, export_dir).execute(_batch_plan(), dry_run=False)

        assert result.success is True
        report_path = export_dir / "batch_report.json"
        assert report_path.exists()
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert data["records"]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_command_executor_rename_layer() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"executor_rename_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        plan = ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="rename",
            requires_confirmation=False,
            raw_user_text="把角色图层重命名为 player_character",
            tasks=[
                EditTask(
                    type="rename_layer",
                    target=None,
                    layer_ids=["001"],
                    output_name="player_character",
                    sizes=[],
                    transparent_background=True,
                    quality=QualityOptions(),
                    params={},
                )
            ],
        )

        result = CommandExecutor(project, tmp_path / "Export").execute(plan)

        assert result.success is True
        assert project.layers[0].name == "player_character"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

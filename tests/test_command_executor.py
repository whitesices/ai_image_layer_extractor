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


def test_command_executor_refine_mask_updates_layer_metadata() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"executor_refine_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        plan = ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="refine_mask",
            requires_confirmation=False,
            raw_user_text="清理图层边缘白边",
            tasks=[
                EditTask(
                    type="refine_mask",
                    target="all_layers",
                    layer_ids=[],
                    output_name=None,
                    sizes=[],
                    transparent_background=True,
                    quality=QualityOptions(feather_radius=0),
                    params={"remove_small_islands": True, "clean_holes": True},
                )
            ],
        )

        result = CommandExecutor(project, tmp_path / "Export").execute(plan)

        assert result.success is True
        assert project.layers[0].metadata["mask_refined"] is True
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_command_executor_exports_visible_layers_only() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"executor_visible_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        second_mask = np.zeros((24, 32), dtype=np.uint8)
        second_mask[2:8, 2:8] = 255
        second = project.add_layer_from_mask("hidden", MaskResult(mask=second_mask))
        second.visible = False
        plan = _batch_plan()
        plan.tasks[0].target = "visible_layers"

        result = CommandExecutor(project, tmp_path / "Export").execute(plan)

        assert result.success is True
        report_path = tmp_path / "Export" / "batch_report.json"
        data = json.loads(report_path.read_text(encoding="utf-8"))
        assert data["exported_layers"] == ["001"]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_command_executor_returns_not_implemented_for_reserved_task() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"executor_not_implemented_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        plan = ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="remove_background",
            requires_confirmation=False,
            raw_user_text="移除背景",
            tasks=[
                EditTask(
                    type="remove_background",
                    target="all_layers",
                    layer_ids=[],
                    output_name=None,
                    sizes=[],
                    transparent_background=True,
                    quality=QualityOptions(),
                    params={},
                )
            ],
        )

        result = CommandExecutor(project, tmp_path / "Export").execute(plan)

        assert result.success is False
        assert any("NotImplemented" in message for message in result.messages)
        assert not result.errors
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_command_executor_extract_target_creates_layer() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"executor_extract_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        project.layers.clear()
        plan = ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="extract",
            requires_confirmation=False,
            raw_user_text="提取人物",
            tasks=[
                EditTask(
                    type="extract_target",
                    target="person",
                    layer_ids=[],
                    output_name="person",
                    sizes=[],
                    transparent_background=True,
                    quality=QualityOptions(),
                    params={"target_prompt": "person"},
                )
            ],
        )

        result = CommandExecutor(project, tmp_path / "Export").execute(plan)

        assert result.success is True
        assert len(project.layers) == 1
        assert project.layers[0].name == "person"
        assert any("Created layer" in message for message in result.messages)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_command_executor_extract_multiple_targets_and_background() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"executor_extract_multi_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        project.layers.clear()
        plan = ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="smart_slice",
            requires_confirmation=False,
            raw_user_text="把人物、武器、背景分别导出",
            tasks=[
                EditTask(
                    type="extract_multiple_targets",
                    target="multiple_targets",
                    layer_ids=[],
                    output_name=None,
                    sizes=[],
                    transparent_background=True,
                    quality=QualityOptions(),
                    params={"target_names": ["person", "weapon", "background"]},
                )
            ],
        )

        result = CommandExecutor(project, tmp_path / "Export").execute(plan)

        assert result.success is True
        assert [layer.name for layer in project.layers] == ["person", "weapon", "background"]
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_command_executor_detect_text_regions_creates_text_layer() -> None:
    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"executor_text_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        project.layers.clear()
        plan = ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="detect_text",
            requires_confirmation=False,
            raw_user_text="把文字区域识别出来",
            tasks=[
                EditTask(
                    type="detect_text_regions",
                    target="text_regions",
                    layer_ids=[],
                    output_name="text",
                    sizes=[],
                    transparent_background=True,
                    quality=QualityOptions(),
                    params={"target_prompt": "text"},
                )
            ],
        )

        result = CommandExecutor(project, tmp_path / "Export").execute(plan)

        assert result.success is True
        assert len(project.layers) == 1
        assert project.layers[0].name == "text"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_command_executor_smart_slice_plan_extracts_then_exports() -> None:
    from llm.mock_provider import MockLLMProvider
    from core.edit_plan import CommandContext

    tmp_root = Path(__file__).resolve().parent / "_tmp"
    tmp_path = tmp_root / f"executor_smart_slice_{uuid.uuid4().hex}"
    tmp_path.mkdir(parents=True, exist_ok=False)
    try:
        project = _make_project(tmp_path)
        project.layers.clear()
        plan = MockLLMProvider().parse_command(
            "把图中所有人物图片元素全部输出 512x512",
            CommandContext(
                source_image_loaded=True,
                canvas_width=32,
                canvas_height=24,
                layer_count=0,
                selected_layer_ids=[],
                available_layers=[],
            ),
        )

        result = CommandExecutor(project, tmp_path / "Export").execute(plan)

        assert result.success is True
        assert [layer.name for layer in project.layers] == ["person"]
        assert (tmp_path / "Export" / "batch_report.json").exists()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

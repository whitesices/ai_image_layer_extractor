from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.edit_plan import CommandContext
from llm.mock_provider import MockLLMProvider


def _context() -> CommandContext:
    return CommandContext(
        source_image_loaded=True,
        canvas_width=1024,
        canvas_height=1024,
        layer_count=4,
        selected_layer_ids=["001"],
        available_layers=[
            {"id": "001", "name": "character"},
            {"id": "002", "name": "ui_icon"},
            {"id": "003", "name": "weapon"},
            {"id": "004", "name": "logo"},
        ],
    )


def test_mock_llm_provider_parses_chinese_batch_export() -> None:
    plan = MockLLMProvider().parse_command("把所有图层导出 512x512", _context())

    assert plan.intent == "batch_export"
    assert plan.tasks[0].type == "batch_export_layers"
    assert plan.tasks[0].target == "all_layers"
    assert plan.tasks[0].sizes[0].width == 512
    assert plan.tasks[0].sizes[0].height == 512


def test_mock_llm_provider_parses_selected_multi_size_export() -> None:
    plan = MockLLMProvider().parse_command("把当前选中的图层导出 256、512、1024 三套尺寸", _context())

    task = plan.tasks[0]
    assert task.type == "resize_layer"
    assert task.target == "selected_layers"
    assert task.layer_ids == ["001"]
    assert [spec.width for spec in task.sizes] == [256, 512, 1024]


def test_mock_llm_provider_parses_padding() -> None:
    plan = MockLLMProvider().parse_command("把所有图层加 32 像素透明边距后导出", _context())

    assert plan.tasks[0].sizes[0].padding == 32


def test_mock_llm_provider_parses_multiple_targets() -> None:
    plan = MockLLMProvider().parse_command("把人物、武器、背景分别导出", _context())

    task = plan.tasks[0]
    assert task.type == "extract_multiple_targets"
    assert task.params["target_names"] == ["person", "weapon", "background"]


def test_mock_llm_provider_parses_target_extraction() -> None:
    plan = MockLLMProvider().parse_command("提取左边的人物", _context())

    task = plan.tasks[0]
    assert task.type == "extract_target"
    assert task.target == "person"
    assert task.params["position_hint"] == "left"


def test_mock_llm_provider_parses_logo_extraction() -> None:
    plan = MockLLMProvider().parse_command("把 logo 单独抠出来", _context())

    assert plan.tasks[0].type == "extract_target"
    assert plan.tasks[0].target == "logo"


def test_mock_llm_provider_parses_text_detection() -> None:
    plan = MockLLMProvider().parse_command("把文字区域识别出来", _context())

    assert plan.tasks[0].type == "detect_text_regions"


def test_mock_llm_provider_parses_ue_export() -> None:
    plan = MockLLMProvider().parse_command("把所有图层导出成 UE UMG 可以用的资源", _context())

    task = plan.tasks[0]
    assert task.type == "export_for_ue_umg"
    assert task.target == "all_layers"
    assert task.params["generate_import_script"] is True


def test_mock_llm_provider_parses_refine_mask() -> None:
    plan = MockLLMProvider().parse_command("清理图层边缘白边", _context())

    assert plan.tasks[0].type == "refine_mask"
    assert plan.tasks[0].quality.remove_halo is True


def test_mock_llm_provider_parses_psd_package() -> None:
    plan = MockLLMProvider().parse_command("按 PSD 分层思路导出素材包", _context())

    assert plan.tasks[0].type == "future_psd_export"

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
        layer_count=2,
        selected_layer_ids=["001"],
        available_layers=[
            {"id": "001", "name": "character"},
            {"id": "002", "name": "ui_icon"},
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


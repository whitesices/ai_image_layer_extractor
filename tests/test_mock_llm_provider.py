from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.app_settings import AppSettings
from core.edit_plan import CommandContext
from llm.mock_provider import MockLLMProvider
from llm.openai_provider import OpenAIProvider


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


def _task_for(command: str):
    return MockLLMProvider().parse_command(command, _context()).tasks[0]


def test_mock_llm_provider_parses_all_layers_512_export() -> None:
    task = _task_for("把所有图层导出 512x512")

    assert task.type == "batch_export_layers"
    assert task.target == "all_layers"
    assert [(spec.width, spec.height) for spec in task.sizes] == [(512, 512)]


def test_mock_llm_provider_parses_selected_multi_size_export() -> None:
    task = _task_for("把当前选中图层导出 256、512、1024 三套尺寸")

    assert task.type == "resize_layer"
    assert task.target == "selected_layers"
    assert task.layer_ids == ["001"]
    assert [spec.width for spec in task.sizes] == [256, 512, 1024]


def test_mock_llm_provider_parses_padding_export() -> None:
    task = _task_for("把所有图层加 32 像素透明边距后导出")

    assert task.type == "batch_export_layers"
    assert task.target == "all_layers"
    assert task.sizes[0].padding == 32
    assert task.transparent_background is True


def test_mock_llm_provider_parses_role_layer_rename() -> None:
    task = _task_for("把角色图层重命名为 player_character")

    assert task.type == "rename_layer"
    assert task.layer_ids == ["001"]
    assert task.output_name == "player_character"


def test_mock_llm_provider_parses_ui_icon_export() -> None:
    task = _task_for("把 UI 图标全部导出为 128x128 透明 PNG")

    assert task.type == "batch_export_layers"
    assert task.layer_ids == ["002"]
    assert [(spec.width, spec.height, spec.output_format) for spec in task.sizes] == [(128, 128, "png")]
    assert task.transparent_background is True


def test_mock_llm_provider_parses_ue_umg_multi_size_export() -> None:
    task = _task_for("导出适合 UE UMG 使用的 512 和 1024 两套资源")

    assert task.type == "export_for_ue_umg"
    assert task.target == "all_layers"
    assert [spec.width for spec in task.sizes] == [512, 1024]
    assert task.params["generate_import_script"] is True


def test_mock_llm_provider_parses_visible_layers_export() -> None:
    task = _task_for("只导出可见图层")

    assert task.type == "batch_export_layers"
    assert task.target == "visible_layers"


def test_mock_llm_provider_parses_clean_white_halo() -> None:
    task = _task_for("清理图层边缘白边")

    assert task.type == "refine_mask"
    assert task.quality.remove_halo is True
    assert task.params["remove_halo"] is True


def test_mock_llm_provider_parses_optimize_alpha_edges() -> None:
    task = _task_for("优化透明边缘，减少锯齿")

    assert task.type == "refine_mask"
    assert task.quality.feather_radius == 1
    assert task.quality.remove_halo is True


def test_mock_llm_provider_parses_psd_package() -> None:
    task = _task_for("按 PSD 分层思路导出素材包")

    assert task.type == "future_psd_export"
    assert task.target == "all_layers"


def test_mock_llm_provider_parses_multiple_targets() -> None:
    task = _task_for("把人物、武器、背景分别导出")

    assert task.type == "extract_multiple_targets"
    assert task.params["target_names"] == ["person", "weapon", "background"]


def test_mock_llm_provider_parses_target_extraction() -> None:
    task = _task_for("提取左边的人物")

    assert task.type == "extract_target"
    assert task.target == "person"
    assert task.params["position_hint"] == "left"


def test_mock_llm_provider_parses_logo_extraction() -> None:
    task = _task_for("把 logo 单独抠出来")

    assert task.type == "extract_target"
    assert task.target == "logo"


def test_mock_llm_provider_parses_text_detection() -> None:
    task = _task_for("把文字区域识别出来")

    assert task.type == "detect_text_regions"


def test_openai_provider_without_key_is_unavailable_without_crashing() -> None:
    provider = OpenAIProvider(settings=AppSettings(llm_provider="openai"), api_key="")

    assert provider.is_available() is False
    assert "key" in provider.status_message().lower()

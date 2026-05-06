from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.edit_plan import summarize_edit_plan
from llm.schema import parse_edit_plan_from_json, validate_edit_plan_json


def _valid_plan() -> dict:
    return {
        "version": "1.0",
        "language": "zh-CN",
        "intent": "batch_export",
        "requires_confirmation": True,
        "tasks": [
            {
                "type": "batch_export_layers",
                "target": "all_layers",
                "layer_ids": [],
                "output_name": None,
                "sizes": [
                    {
                        "width": 512,
                        "height": 512,
                        "fit_mode": "contain",
                        "padding": 0,
                        "output_format": "png",
                    }
                ],
                "transparent_background": True,
                "quality": {
                    "refine_edges": True,
                    "feather_radius": 1,
                    "dilate_pixels": 0,
                    "erode_pixels": 0,
                    "remove_halo": True,
                    "preserve_original_pixels": True,
                },
                "params": {},
            }
        ],
        "raw_user_text": "把所有图层导出 512x512",
    }


def test_schema_rejects_illegal_size() -> None:
    plan = _valid_plan()
    plan["tasks"][0]["sizes"][0]["width"] = 9000

    valid, errors = validate_edit_plan_json(plan)

    assert not valid
    assert any("between 1 and 8192" in error for error in errors)


def test_schema_rejects_dangerous_paths() -> None:
    plan = _valid_plan()
    plan["tasks"][0]["output_name"] = "..\\evil"

    valid, errors = validate_edit_plan_json(plan)

    assert not valid
    assert any("unsafe" in error for error in errors)


def test_parse_edit_plan_from_json_builds_dataclasses() -> None:
    parsed = parse_edit_plan_from_json(_valid_plan())

    assert parsed.tasks[0].type == "batch_export_layers"
    assert parsed.tasks[0].sizes[0].width == 512
    assert parsed.tasks[0].quality.remove_halo is True


def test_schema_accepts_new_task_types() -> None:
    plan = _valid_plan()
    plan["tasks"][0]["type"] = "export_for_ue_umg"

    valid, errors = validate_edit_plan_json(plan)

    assert valid, errors


def test_plan_preview_includes_risk_and_cloud_flags() -> None:
    plan = _valid_plan()
    plan["tasks"][0]["type"] = "extract_target"
    plan["tasks"][0]["target"] = "person"
    plan["tasks"][0]["params"] = {
        "target_prompt": "person",
        "risk_warning": "Needs a detector or manual box.",
        "requires_cloud_api": False,
    }
    parsed = parse_edit_plan_from_json(plan)

    preview = summarize_edit_plan(parsed)

    assert "extract_target" in preview
    assert "risk warning: Needs a detector or manual box." in preview
    assert "cloud API required: False" in preview

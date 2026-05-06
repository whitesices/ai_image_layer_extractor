from __future__ import annotations

import re
from typing import Any

from core.edit_plan import (
    SUPPORTED_FIT_MODES,
    SUPPORTED_OUTPUT_FORMATS,
    SUPPORTED_TASK_TYPES,
    BatchOutputSpec,
    EditTask,
    ImageEditPlan,
    QualityOptions,
)


_DRIVE_RE = re.compile(r"^[a-zA-Z]:")


def validate_edit_plan_json(data: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return False, ["Plan must be a JSON object."]

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("tasks must be a non-empty list.")

    for task_index, task in enumerate(tasks or []):
        prefix = f"tasks[{task_index}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix} must be an object.")
            continue

        task_type = task.get("type")
        if task_type not in SUPPORTED_TASK_TYPES:
            errors.append(f"{prefix}.type is unsupported: {task_type!r}.")

        output_name = task.get("output_name")
        if output_name is not None and not _is_safe_name(str(output_name)):
            errors.append(f"{prefix}.output_name contains an unsafe path or filename.")

        layer_ids = task.get("layer_ids", [])
        if not isinstance(layer_ids, list) or not all(isinstance(value, str) for value in layer_ids):
            errors.append(f"{prefix}.layer_ids must be a list of strings.")

        sizes = task.get("sizes", [])
        if not isinstance(sizes, list):
            errors.append(f"{prefix}.sizes must be a list.")
            continue
        for size_index, size in enumerate(sizes):
            size_prefix = f"{prefix}.sizes[{size_index}]"
            if not isinstance(size, dict):
                errors.append(f"{size_prefix} must be an object.")
                continue
            _validate_size(size, size_prefix, errors)

        params = task.get("params", {})
        if not isinstance(params, dict):
            errors.append(f"{prefix}.params must be an object.")
        else:
            _validate_safe_params(params, prefix, errors)

        quality = task.get("quality", {})
        if quality is not None and not isinstance(quality, dict):
            errors.append(f"{prefix}.quality must be an object.")

    return len(errors) == 0, errors


def parse_edit_plan_from_json(data: dict[str, Any]) -> ImageEditPlan:
    valid, errors = validate_edit_plan_json(data)
    if not valid:
        raise ValueError("Invalid edit plan JSON: " + "; ".join(errors))

    tasks: list[EditTask] = []
    for task_data in data["tasks"]:
        quality_data = task_data.get("quality") or {}
        quality = QualityOptions(
            refine_edges=bool(quality_data.get("refine_edges", True)),
            feather_radius=int(quality_data.get("feather_radius", 1)),
            dilate_pixels=int(quality_data.get("dilate_pixels", 0)),
            erode_pixels=int(quality_data.get("erode_pixels", 0)),
            remove_halo=bool(quality_data.get("remove_halo", True)),
            preserve_original_pixels=bool(quality_data.get("preserve_original_pixels", True)),
        )
        sizes = [
            BatchOutputSpec(
                width=int(size["width"]),
                height=int(size.get("height", size["width"])),
                fit_mode=str(size.get("fit_mode", "contain")),
                padding=int(size.get("padding", 0)),
                output_format=str(size.get("output_format", "png")).lower(),
            )
            for size in task_data.get("sizes", [])
        ]
        tasks.append(
            EditTask(
                type=str(task_data["type"]),
                target=task_data.get("target"),
                layer_ids=[str(layer_id) for layer_id in task_data.get("layer_ids", [])],
                output_name=task_data.get("output_name"),
                sizes=sizes,
                transparent_background=bool(task_data.get("transparent_background", True)),
                quality=quality,
                params=dict(task_data.get("params", {})),
            )
        )

    return ImageEditPlan(
        version=str(data.get("version", "1.0")),
        language=str(data.get("language", "zh-CN")),
        intent=str(data.get("intent", "edit")),
        requires_confirmation=bool(data.get("requires_confirmation", True)),
        tasks=tasks,
        raw_user_text=str(data.get("raw_user_text", "")),
        clarification_needed=data.get("clarification_needed"),
    )


def _validate_size(size: dict[str, Any], prefix: str, errors: list[str]) -> None:
    width = size.get("width")
    height = size.get("height", width)
    for key, value in {"width": width, "height": height}.items():
        if not isinstance(value, int):
            errors.append(f"{prefix}.{key} must be an integer.")
            continue
        if value < 1 or value > 8192:
            errors.append(f"{prefix}.{key} must be between 1 and 8192.")

    fit_mode = size.get("fit_mode", "contain")
    if fit_mode not in SUPPORTED_FIT_MODES:
        errors.append(f"{prefix}.fit_mode is unsupported: {fit_mode!r}.")

    output_format = str(size.get("output_format", "png")).lower()
    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        errors.append(f"{prefix}.output_format is unsupported: {output_format!r}.")

    padding = size.get("padding", 0)
    if not isinstance(padding, int):
        errors.append(f"{prefix}.padding must be an integer.")
    elif padding < 0 or padding > 1024:
        errors.append(f"{prefix}.padding must be between 0 and 1024.")


def _validate_safe_params(params: dict[str, Any], prefix: str, errors: list[str]) -> None:
    for key, value in params.items():
        value_prefix = f"{prefix}.params.{key}"
        if isinstance(value, str) and not _is_safe_path_value(value):
            errors.append(f"{value_prefix} contains an unsafe path.")
        elif isinstance(value, dict):
            _validate_safe_params(value, value_prefix, errors)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, str) and not _is_safe_path_value(item):
                    errors.append(f"{value_prefix}[{index}] contains an unsafe path.")


def _is_safe_name(value: str) -> bool:
    if not value.strip():
        return False
    return _is_safe_path_value(value) and "/" not in value and "\\" not in value


def _is_safe_path_value(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if ".." in stripped:
        return False
    if stripped.startswith(("/", "\\")):
        return False
    if _DRIVE_RE.match(stripped):
        return False
    return True

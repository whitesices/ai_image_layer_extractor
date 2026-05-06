from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SUPPORTED_TASK_TYPES = {
    "batch_export_layers",
    "resize_layer",
    "rename_layer",
    "extract_object",
    "extract_all_objects",
    "remove_background",
    "edit_selected_region",
    "export_ue_umg_layout",
}

SUPPORTED_FIT_MODES = {"contain", "cover", "stretch", "max_side", "original"}
SUPPORTED_OUTPUT_FORMATS = {"png", "webp"}


@dataclass(slots=True)
class CommandContext:
    source_image_loaded: bool
    canvas_width: int
    canvas_height: int
    layer_count: int
    selected_layer_ids: list[str]
    available_layers: list[dict[str, Any]]


@dataclass(slots=True)
class QualityOptions:
    refine_edges: bool = True
    feather_radius: int = 1
    dilate_pixels: int = 0
    erode_pixels: int = 0
    remove_halo: bool = True
    preserve_original_pixels: bool = True


@dataclass(slots=True)
class BatchOutputSpec:
    width: int
    height: int
    fit_mode: str = "contain"
    padding: int = 0
    output_format: str = "png"

    @property
    def label(self) -> str:
        if self.fit_mode == "original":
            return "original"
        return f"{self.width}x{self.height}"


@dataclass(slots=True)
class EditTask:
    type: str
    target: str | None
    layer_ids: list[str]
    output_name: str | None
    sizes: list[BatchOutputSpec]
    transparent_background: bool
    quality: QualityOptions
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ImageEditPlan:
    version: str
    language: str
    intent: str
    requires_confirmation: bool
    tasks: list[EditTask]
    raw_user_text: str
    clarification_needed: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_quality_options() -> QualityOptions:
    return QualityOptions()


def default_batch_spec(
    width: int,
    height: int | None = None,
    *,
    fit_mode: str = "contain",
    padding: int = 0,
    output_format: str = "png",
) -> BatchOutputSpec:
    return BatchOutputSpec(
        width=int(width),
        height=int(height if height is not None else width),
        fit_mode=fit_mode,
        padding=int(padding),
        output_format=output_format,
    )


def summarize_edit_plan(plan: ImageEditPlan) -> str:
    lines = [
        f"Intent: {plan.intent}",
        f"Requires confirmation: {plan.requires_confirmation}",
        f"Tasks: {len(plan.tasks)}",
    ]
    if plan.clarification_needed:
        lines.append(f"Clarification needed: {plan.clarification_needed}")
    for index, task in enumerate(plan.tasks, start=1):
        size_text = ", ".join(
            f"{spec.width}x{spec.height} {spec.fit_mode} padding={spec.padding} {spec.output_format}"
            for spec in task.sizes
        ) or "original"
        target = task.target or ("layer_ids=" + ",".join(task.layer_ids) if task.layer_ids else "unspecified")
        lines.append(f"{index}. {task.type}: target={target}; sizes={size_text}")
        if task.output_name:
            lines.append(f"   output_name={task.output_name}")
    return "\n".join(lines)

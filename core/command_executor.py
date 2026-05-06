from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .batch_exporter import BatchExporter
from .edit_plan import BatchOutputSpec, EditTask, ImageEditPlan
from .layer import LayerItem
from .project import ProjectData


@dataclass(slots=True)
class CommandExecutionResult:
    success: bool
    messages: list[str] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class CommandExecutor:
    """Execute structured edit plans without coupling to PySide UI."""

    def __init__(
        self,
        project: ProjectData,
        output_dir: str | Path,
        selected_layer_ids: list[str] | None = None,
    ) -> None:
        self.project = project
        self.output_dir = Path(output_dir)
        self.selected_layer_ids = selected_layer_ids or []

    def execute(self, plan: ImageEditPlan, dry_run: bool = False) -> CommandExecutionResult:
        result = CommandExecutionResult(success=True)
        if plan.requires_confirmation and dry_run:
            result.messages.append("Plan requires confirmation before execution.")

        for task in plan.tasks:
            try:
                task_result = self._execute_task(task, dry_run=dry_run)
            except Exception as exc:
                result.success = False
                result.errors.append(str(exc))
                continue
            result.messages.extend(task_result.messages)
            result.generated_files.extend(task_result.generated_files)
            result.warnings.extend(task_result.warnings)
            result.errors.extend(task_result.errors)
            if not task_result.success:
                result.success = False

        return result

    def _execute_task(self, task: EditTask, dry_run: bool) -> CommandExecutionResult:
        if task.type == "batch_export_layers":
            return self._batch_export_layers(task, dry_run=dry_run)
        if task.type == "resize_layer":
            return self._resize_layer(task, dry_run=dry_run)
        if task.type == "rename_layer":
            return self._rename_layer(task, dry_run=dry_run)
        return CommandExecutionResult(
            success=True,
            warnings=[f"Task type '{task.type}' is not implemented in this MVP."],
        )

    def _batch_export_layers(self, task: EditTask, dry_run: bool) -> CommandExecutionResult:
        layers = self._resolve_layers(task)
        if not layers:
            return CommandExecutionResult(success=False, errors=["No matching layers for batch export."])

        specs = task.sizes or [BatchOutputSpec(1, 1, fit_mode="original")]
        summary = self._format_export_summary("Batch export", layers, specs)
        if dry_run:
            return CommandExecutionResult(success=True, messages=[summary, "Dry run: no files generated."])

        export_result = BatchExporter(self.output_dir).export_layers(self.project, layers, specs, task.quality)
        return CommandExecutionResult(
            success=True,
            messages=[summary, f"Wrote batch report: {export_result.report_path}"],
            generated_files=[str(path) for path in export_result.files],
            warnings=export_result.warnings,
        )

    def _resize_layer(self, task: EditTask, dry_run: bool) -> CommandExecutionResult:
        layers = self._resolve_layers(task)
        if not layers:
            return CommandExecutionResult(success=False, errors=["No matching layers for resize export."])

        specs = task.sizes
        if not specs:
            return CommandExecutionResult(success=False, errors=["resize_layer requires at least one output size."])

        summary = self._format_export_summary("Resize layer export", layers, specs)
        if dry_run:
            return CommandExecutionResult(success=True, messages=[summary, "Dry run: no files generated."])

        export_result = BatchExporter(self.output_dir).export_layers(self.project, layers, specs, task.quality)
        return CommandExecutionResult(
            success=True,
            messages=[summary, f"Wrote batch report: {export_result.report_path}"],
            generated_files=[str(path) for path in export_result.files],
            warnings=export_result.warnings,
        )

    def _rename_layer(self, task: EditTask, dry_run: bool) -> CommandExecutionResult:
        layers = self._resolve_layers(task)
        new_name = (task.output_name or task.params.get("new_name") or "").strip()
        if not layers:
            return CommandExecutionResult(success=False, errors=["No matching layers for rename."])
        if not new_name:
            return CommandExecutionResult(success=False, errors=["rename_layer requires output_name or params.new_name."])

        if dry_run:
            layer_ids = ", ".join(layer.id for layer in layers)
            return CommandExecutionResult(
                success=True,
                messages=[f"Dry run: would rename layer(s) {layer_ids} to '{new_name}'."],
            )

        renamed: list[str] = []
        for layer in layers:
            layer.rename(new_name)
            renamed.append(layer.id)
        return CommandExecutionResult(
            success=True,
            messages=[f"Renamed layer(s) {', '.join(renamed)} to '{new_name}'."],
        )

    def _resolve_layers(self, task: EditTask) -> list[LayerItem]:
        if task.layer_ids:
            return [layer for layer_id in task.layer_ids if (layer := self.project.get_layer(layer_id)) is not None]

        target = (task.target or "").strip().lower()
        if target in {"all", "all_layers", "layers", ""}:
            return list(self.project.layers)
        if target in {"selected", "selected_layers", "current_selected_layers"}:
            return [
                layer
                for layer_id in self.selected_layer_ids
                if (layer := self.project.get_layer(layer_id)) is not None
            ]
        if target.startswith("layer_name:"):
            token = target.split(":", 1)[1].strip()
            return [layer for layer in self.project.layers if token and token in layer.name.lower()]
        return []

    def _format_export_summary(
        self,
        prefix: str,
        layers: list[LayerItem],
        specs: list[BatchOutputSpec],
    ) -> str:
        size_text = ", ".join(
            f"{spec.width}x{spec.height} fit={spec.fit_mode} padding={spec.padding} {spec.output_format}"
            for spec in specs
        )
        return f"{prefix}: {len(layers)} layer(s), {size_text}."

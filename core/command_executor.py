from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .batch_exporter import BatchExporter
from .edit_plan import BatchOutputSpec, EditTask, ImageEditPlan
from .exporter import LayerExporter
from .layer import LayerItem
from .mask_utils import clean_mask, mask_to_bbox
from .project import ProjectData
from .quality_pipeline import QualityPipeline


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
        if task.type == "refine_mask":
            return self._refine_mask(task, dry_run=dry_run)
        if task.type == "export_project":
            return self._export_project(dry_run=dry_run)
        if task.type in {"export_for_ue_umg", "export_ue_umg_layout"}:
            return self._export_for_ue_umg(task, dry_run=dry_run)
        if task.type == "future_psd_export":
            return self._future_psd_export(dry_run=dry_run)
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

        export_result = BatchExporter(
            self.output_dir,
            filename_template=str(task.params.get("filename_template", "{id}_{name}_{width}x{height}.{ext}")),
        ).export_layers(self.project, layers, specs, task.quality)
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

        export_result = BatchExporter(
            self.output_dir,
            filename_template=str(task.params.get("filename_template", "{id}_{name}_{width}x{height}.{ext}")),
        ).export_layers(self.project, layers, specs, task.quality)
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

    def _refine_mask(self, task: EditTask, dry_run: bool) -> CommandExecutionResult:
        layers = self._resolve_layers(task)
        if not layers:
            return CommandExecutionResult(success=False, errors=["No matching layers for mask refinement."])

        if dry_run:
            return CommandExecutionResult(
                success=True,
                messages=[f"Dry run: would refine mask(s) for {len(layers)} layer(s)."],
            )

        quality = QualityPipeline()
        refined_ids: list[str] = []
        warnings: list[str] = []
        for layer in layers:
            refined = quality.refine_mask_edges(
                layer.mask,
                feather_radius=task.quality.feather_radius,
                dilate_pixels=task.quality.dilate_pixels,
                erode_pixels=task.quality.erode_pixels,
            )
            if task.params.get("remove_small_islands", True) or task.params.get("clean_holes", True):
                refined = clean_mask(refined, min_area=int(task.params.get("min_area", 64)))
            bbox = mask_to_bbox(refined)
            if bbox is None:
                warnings.append(f"Layer {layer.id} refinement produced an empty mask; keeping original mask.")
                continue
            layer.mask = refined
            layer.bbox = bbox
            layer.metadata["mask_refined"] = True
            refined_ids.append(layer.id)

        return CommandExecutionResult(
            success=True,
            messages=[f"Refined mask(s): {', '.join(refined_ids) if refined_ids else 'none'}."],
            warnings=warnings,
        )

    def _export_project(self, dry_run: bool) -> CommandExecutionResult:
        if self.project.image is None:
            return CommandExecutionResult(success=False, errors=["No source image is loaded."])
        if dry_run:
            return CommandExecutionResult(success=True, messages=["Dry run: would export project.json and preview.png."])
        exporter = LayerExporter(self.output_dir)
        project_json = exporter.export_project_json(self.project)
        preview = exporter.export_preview(self.project)
        return CommandExecutionResult(
            success=True,
            messages=[f"Exported project metadata to {project_json}."],
            generated_files=[str(project_json), str(preview)],
        )

    def _export_for_ue_umg(self, task: EditTask, dry_run: bool) -> CommandExecutionResult:
        if self.project.image is None:
            return CommandExecutionResult(success=False, errors=["No source image is loaded."])
        layers = self._resolve_layers(task)
        if not layers:
            return CommandExecutionResult(success=False, errors=["No matching layers for UE UMG export."])
        output_dir = self.output_dir / str(task.output_name or "Export_UE")
        if dry_run:
            return CommandExecutionResult(
                success=True,
                messages=[f"Dry run: would export {len(layers)} layer(s) to UE UMG package {output_dir}."],
            )
        from exporters.ue_umg_exporter import UEUMGExporter

        export_result = UEUMGExporter(output_dir).export(self.project, layers)
        return CommandExecutionResult(
            success=True,
            messages=[f"Exported UE UMG package to {export_result.output_dir}."],
            generated_files=[str(path) for path in export_result.generated_files],
            warnings=export_result.warnings,
        )

    def _future_psd_export(self, dry_run: bool) -> CommandExecutionResult:
        if self.project.image is None:
            return CommandExecutionResult(success=False, errors=["No source image is loaded."])
        output_dir = self.output_dir / "PSD_Compatible_Package"
        if dry_run:
            return CommandExecutionResult(
                success=True,
                messages=[f"Dry run: would export PSD-compatible package to {output_dir}."],
            )
        from exporters.psd_exporter import PSDExporter

        export_result = PSDExporter().export(self.project, output_dir)
        return CommandExecutionResult(
            success=True,
            messages=[f"Exported PSD-compatible package to {export_result.output_path}."],
            generated_files=[str(path) for path in export_result.generated_files],
            warnings=export_result.warnings,
        )

    def _resolve_layers(self, task: EditTask) -> list[LayerItem]:
        if task.layer_ids:
            return [layer for layer_id in task.layer_ids if (layer := self.project.get_layer(layer_id)) is not None]

        target = (task.target or "").strip().lower()
        if target in {"all", "all_layers", "layers", ""}:
            return list(self.project.layers)
        if target in {"visible", "visible_layers"}:
            return [layer for layer in self.project.layers if layer.visible]
        if target in {"selected", "selected_layers", "current_selected_layers"}:
            return [
                layer
                for layer_id in self.selected_layer_ids
                if (layer := self.project.get_layer(layer_id)) is not None
            ]
        if target.startswith("layer_name:"):
            token = target.split(":", 1)[1].strip()
            return [layer for layer in self.project.layers if token and token in layer.name.lower()]
        if target in {"layers_by_name", "name"}:
            token = str(task.params.get("name", "")).strip().lower()
            return [layer for layer in self.project.layers if token and token in layer.name.lower()]
        if target.startswith("tag:"):
            token = target.split(":", 1)[1].strip().lower()
            return [layer for layer in self.project.layers if self._layer_has_tag(layer, token)]
        if target in {"layers_by_tag", "tag"}:
            token = str(task.params.get("tag", "")).strip().lower()
            return [layer for layer in self.project.layers if self._layer_has_tag(layer, token)]
        return []

    def _layer_has_tag(self, layer: LayerItem, token: str) -> bool:
        tags = layer.metadata.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        return any(str(tag).lower() == token for tag in tags)

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

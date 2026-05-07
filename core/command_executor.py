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
from .extraction_plan import ExtractionRequest


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
        if task.type in {"extract_target", "extract_object"}:
            return self._extract_target(task, dry_run=dry_run)
        if task.type in {"extract_multiple_targets", "extract_all_objects"}:
            return self._extract_multiple_targets(task, dry_run=dry_run)
        if task.type == "detect_text_regions":
            return self._detect_text_regions(task, dry_run=dry_run)
        if task.type == "create_background_layer":
            return self._create_background_layer(task, dry_run=dry_run)
        if task.type == "refine_mask":
            return self._refine_mask(task, dry_run=dry_run)
        if task.type == "export_project":
            return self._export_project(dry_run=dry_run)
        if task.type in {"export_for_ue_umg", "export_ue_umg_layout"}:
            return self._export_for_ue_umg(task, dry_run=dry_run)
        if task.type == "future_psd_export":
            return self._future_psd_export(dry_run=dry_run)
        return self._not_implemented(task)

    def _not_implemented(self, task: EditTask) -> CommandExecutionResult:
        return CommandExecutionResult(
            success=False,
            messages=[f"NotImplemented: task type '{task.type}' is recognized but has no local executor yet."],
            warnings=[
                "The command was parsed safely, but this task still needs a local pipeline implementation.",
            ],
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

    def _extract_target(self, task: EditTask, dry_run: bool) -> CommandExecutionResult:
        if self.project.image is None:
            return CommandExecutionResult(success=False, errors=["No source image is loaded."])

        prompt = self._target_prompt(task)
        bbox = self._bbox_param(task)
        selected_layer_id = task.layer_ids[0] if task.layer_ids else None
        output_name = task.output_name or prompt
        if dry_run:
            detail = f"target='{prompt}'"
            if bbox is not None:
                detail += f", bbox={bbox}"
            elif selected_layer_id:
                detail += f", selected_layer_id={selected_layer_id}"
            else:
                detail += ", detector/manual-selection fallback"
            return CommandExecutionResult(success=True, messages=[f"Dry run: would extract {detail}."])

        from pipeline.target_extraction_pipeline import TargetExtractionPipeline

        extraction = TargetExtractionPipeline().extract(
            self.project,
            ExtractionRequest(
                target_prompt=prompt,
                bbox=bbox,
                selected_layer_id=selected_layer_id,
                output_name=output_name,
                metadata=dict(task.params),
            ),
        )
        return self._extraction_to_command_result(extraction, prompt)

    def _extract_multiple_targets(self, task: EditTask, dry_run: bool) -> CommandExecutionResult:
        if self.project.image is None:
            return CommandExecutionResult(success=False, errors=["No source image is loaded."])

        target_names = self._target_names(task)
        if not target_names:
            return CommandExecutionResult(
                success=False,
                errors=["extract_multiple_targets requires params.target_names or a target prompt."],
            )
        if dry_run:
            return CommandExecutionResult(
                success=True,
                messages=[f"Dry run: would extract targets: {', '.join(target_names)}."],
            )

        from pipeline.target_extraction_pipeline import TargetExtractionPipeline

        pipeline = TargetExtractionPipeline()
        result = CommandExecutionResult(success=True)
        for target_name in target_names:
            if target_name.lower() == "background":
                converted = self._create_background_layer(
                    EditTask(
                        type="create_background_layer",
                        target="background",
                        layer_ids=[],
                        output_name="background",
                        sizes=[],
                        transparent_background=False,
                        quality=task.quality,
                        params=task.params,
                    ),
                    dry_run=False,
                )
                result.messages.extend(converted.messages)
                result.warnings.extend(converted.warnings)
                result.errors.extend(converted.errors)
                if not converted.success:
                    result.success = False
                continue
            extraction = pipeline.extract(
                self.project,
                ExtractionRequest(
                    target_prompt=target_name,
                    output_name=target_name,
                    metadata=dict(task.params),
                ),
            )
            converted = self._extraction_to_command_result(extraction, target_name)
            result.messages.extend(converted.messages)
            result.warnings.extend(converted.warnings)
            result.errors.extend(converted.errors)
            result.generated_files.extend(converted.generated_files)
            if not converted.success:
                result.success = False
        return result

    def _detect_text_regions(self, task: EditTask, dry_run: bool) -> CommandExecutionResult:
        text_task = EditTask(
            type="extract_target",
            target="text",
            layer_ids=task.layer_ids,
            output_name=task.output_name or "text",
            sizes=task.sizes,
            transparent_background=task.transparent_background,
            quality=task.quality,
            params={**task.params, "target_prompt": task.params.get("target_prompt", "text")},
        )
        return self._extract_target(text_task, dry_run=dry_run)

    def _create_background_layer(self, task: EditTask, dry_run: bool) -> CommandExecutionResult:
        if self.project.image is None:
            return CommandExecutionResult(success=False, errors=["No source image is loaded."])
        name = task.output_name or task.params.get("name") or "background"
        if dry_run:
            return CommandExecutionResult(
                success=True,
                messages=[f"Dry run: would create background layer '{name}' by inverting existing foreground masks."],
            )

        from pipeline.background_pipeline import BackgroundPipeline

        extraction = BackgroundPipeline().create_background_layer(self.project, str(name))
        return self._extraction_to_command_result(extraction, str(name))

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

    def _extraction_to_command_result(self, extraction, target_prompt: str) -> CommandExecutionResult:
        messages = list(extraction.messages)
        warnings = list(extraction.warnings)
        errors = list(extraction.errors)
        if extraction.user_action_required:
            warnings.append(f"User action required for '{target_prompt}': manually box-select the target or enable a detector backend.")
        if extraction.layer is not None:
            messages.append(
                f"Created layer {extraction.layer.id} '{extraction.layer.name}' at "
                f"x={extraction.layer.x}, y={extraction.layer.y}, "
                f"w={extraction.layer.width}, h={extraction.layer.height}."
            )
        return CommandExecutionResult(
            success=extraction.success,
            messages=messages,
            warnings=warnings,
            errors=errors,
        )

    def _target_prompt(self, task: EditTask) -> str:
        prompt = str(task.params.get("target_prompt") or task.output_name or task.target or "object").strip()
        return prompt or "object"

    def _target_names(self, task: EditTask) -> list[str]:
        values = task.params.get("target_names")
        if isinstance(values, list):
            return [str(value).strip() for value in values if str(value).strip()]
        if isinstance(values, str):
            return [part.strip() for part in values.replace(";", ",").split(",") if part.strip()]
        prompt = self._target_prompt(task)
        return [] if prompt == "multiple_targets" else [prompt]

    def _bbox_param(self, task: EditTask) -> tuple[int, int, int, int] | None:
        value = task.params.get("bbox")
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            return None
        try:
            x, y, width, height = (int(part) for part in value)
        except (TypeError, ValueError):
            return None
        if width <= 0 or height <= 0:
            return None
        return (x, y, width, height)

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

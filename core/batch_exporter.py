from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable

from PIL import Image

from .edit_plan import BatchOutputSpec, QualityOptions
from .exporter import LayerExporter
from .image_utils import sanitize_filename
from .layer import LayerItem
from .mask_utils import apply_mask_to_rgba, mask_to_bbox, normalize_mask
from .project import ProjectData
from .quality_pipeline import QualityPipeline


@dataclass(slots=True)
class BatchExportRecord:
    layer_id: str
    layer_name: str
    size_label: str
    file: str
    width: int
    height: int
    fit_mode: str
    padding: int
    output_format: str
    warnings: list[str] = field(default_factory=list)
    quality_report: dict = field(default_factory=dict)


@dataclass(slots=True)
class BatchExportResult:
    output_dir: Path
    files: list[Path]
    report_path: Path
    records: list[BatchExportRecord]
    warnings: list[str] = field(default_factory=list)
    failed_items: list[dict] = field(default_factory=list)


class BatchExporter:
    """Export layers into multiple production-ready transparent sizes."""

    def __init__(
        self,
        output_dir: str | Path,
        quality_pipeline: QualityPipeline | None = None,
        filename_template: str = "{id}_{name}_{width}x{height}.{ext}",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.layers_dir = self.output_dir / "layers"
        self.masks_dir = self.output_dir / "masks"
        self.quality = quality_pipeline or QualityPipeline()
        self.filename_template = filename_template

    def export_layers(
        self,
        project: ProjectData,
        layers: Iterable[LayerItem],
        specs: Iterable[BatchOutputSpec],
        quality: QualityOptions | None = None,
    ) -> BatchExportResult:
        if project.image is None:
            raise RuntimeError("No source image is loaded")

        selected_layers = list(layers)
        if not selected_layers:
            raise ValueError("No layers selected for batch export")

        output_specs = list(specs)
        if not output_specs:
            output_specs = [
                BatchOutputSpec(width=1, height=1, fit_mode="original", padding=0, output_format="png")
            ]

        quality_options = quality or QualityOptions()
        self._ensure_dirs(output_specs)

        files: list[Path] = []
        records: list[BatchExportRecord] = []
        warnings: list[str] = []
        failed_items: list[dict] = []

        for layer_index, layer in enumerate(selected_layers, start=1):
            try:
                source_image = self._layer_image(project, layer, quality_options)
                original_path = self._save_original(layer, source_image, layer_index)
                files.append(original_path)
                original_report = self.quality.validate_export_quality(source_image)
                records.append(
                    BatchExportRecord(
                        layer_id=layer.id,
                        layer_name=layer.name,
                        size_label="original",
                        file=self._relative(original_path),
                        width=source_image.width,
                        height=source_image.height,
                        fit_mode="original",
                        padding=0,
                        output_format="png",
                        warnings=original_report.warnings,
                        quality_report=asdict(original_report),
                    )
                )
                warnings.extend(original_report.warnings)

                mask_path = self._export_mask(layer)
                files.append(mask_path)
            except Exception as exc:
                failed_items.append({"layer_id": layer.id, "layer_name": layer.name, "error": str(exc)})
                continue

            for spec in output_specs:
                if spec.fit_mode == "original":
                    continue
                try:
                    exported = self.quality.resize_rgba_high_quality(
                        source_image,
                        spec.width,
                        spec.height,
                        fit_mode=spec.fit_mode,
                        padding=spec.padding,
                    )
                    if quality_options.remove_halo:
                        exported = self.quality.remove_alpha_halo(exported)

                    output_path = self._spec_output_path(layer, spec, exported.width, exported.height, layer_index)
                    self._save_image(exported, output_path, spec.output_format)
                    files.append(output_path)

                    report = self.quality.validate_export_quality(exported)
                    records.append(
                        BatchExportRecord(
                            layer_id=layer.id,
                            layer_name=layer.name,
                            size_label=spec.label,
                            file=self._relative(output_path),
                            width=exported.width,
                            height=exported.height,
                            fit_mode=spec.fit_mode,
                            padding=spec.padding,
                            output_format=spec.output_format,
                            warnings=report.warnings,
                            quality_report=asdict(report),
                        )
                    )
                    warnings.extend(report.warnings)
                except Exception as exc:
                    failed_items.append(
                        {
                            "layer_id": layer.id,
                            "layer_name": layer.name,
                            "size": spec.label,
                            "error": str(exc),
                        }
                    )

        project_json = LayerExporter(self.output_dir).export_project_json(project)
        preview = LayerExporter(self.output_dir).export_preview(project)
        files.extend([project_json, preview])

        report_path = self.export_batch_report(project, records, warnings, failed_items, output_specs)
        files.append(report_path)
        return BatchExportResult(self.output_dir, files, report_path, records, warnings, failed_items)

    def export_batch_report(
        self,
        project: ProjectData,
        records: list[BatchExportRecord],
        warnings: list[str],
        failed_items: list[dict] | None = None,
        specs: list[BatchOutputSpec] | None = None,
    ) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.output_dir / "batch_report.json"
        job_id = uuid.uuid4().hex
        specs = specs or []
        report = {
            "job_id": job_id,
            "source_image": project.source_image_name,
            "export_time": datetime.now().isoformat(timespec="seconds"),
            "canvas": {"width": project.canvas_size[0], "height": project.canvas_size[1]},
            "export_root": str(self.output_dir),
            "exported_layers": sorted({record.layer_id for record in records}),
            "sizes": [asdict(spec) for spec in specs],
            "records": [asdict(record) for record in records],
            "quality_report": [record.quality_report for record in records],
            "warnings": warnings,
            "failed_items": failed_items or [],
        }
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report_path

    def _ensure_dirs(self, specs: list[BatchOutputSpec]) -> None:
        (self.layers_dir / "original").mkdir(parents=True, exist_ok=True)
        self.masks_dir.mkdir(parents=True, exist_ok=True)
        for spec in specs:
            if spec.fit_mode != "original":
                (self.layers_dir / spec.label).mkdir(parents=True, exist_ok=True)

    def _layer_image(self, project: ProjectData, layer: LayerItem, quality: QualityOptions) -> Image.Image:
        mask = normalize_mask(layer.mask)
        bbox = layer.bbox
        if quality.refine_edges:
            mask = self.quality.refine_mask_edges(
                mask,
                feather_radius=quality.feather_radius,
                dilate_pixels=quality.dilate_pixels,
                erode_pixels=quality.erode_pixels,
            )
            bbox = mask_to_bbox(mask) or layer.bbox
        image = apply_mask_to_rgba(project.image, mask, bbox)  # type: ignore[arg-type]
        if layer.opacity < 1.0:
            alpha = image.getchannel("A").point(lambda value: int(value * layer.opacity))
            image.putalpha(alpha)
        if quality.remove_halo:
            image = self.quality.remove_alpha_halo(image)
        return image

    def _save_original(self, layer: LayerItem, image: Image.Image, index: int) -> Path:
        filename = self._format_filename(layer, index, image.width, image.height, "png")
        output_path = self.layers_dir / "original" / filename
        image.save(output_path, format="PNG")
        return output_path

    def _export_mask(self, layer: LayerItem) -> Path:
        x, y, width, height = layer.bbox
        mask_crop = normalize_mask(layer.mask)[y : y + height, x : x + width]
        output_path = self.masks_dir / f"{self._stem(layer)}_mask.png"
        Image.fromarray(mask_crop, mode="L").save(output_path)
        layer.mask_file = f"masks/{output_path.name}"
        return output_path

    def _spec_output_path(self, layer: LayerItem, spec: BatchOutputSpec, width: int, height: int, index: int) -> Path:
        extension = spec.output_format.lower()
        filename = self._format_filename(layer, index, width, height, extension)
        return self.layers_dir / spec.label / filename

    def _save_image(self, image: Image.Image, output_path: Path, output_format: str) -> None:
        output_format = output_format.lower()
        if output_format == "png":
            image.save(output_path, format="PNG")
            return
        if output_format == "webp":
            image.save(output_path, format="WEBP", lossless=True, quality=100)
            return
        raise ValueError(f"Unsupported output format: {output_format}")

    def _stem(self, layer: LayerItem) -> str:
        return f"{layer.id}_{sanitize_filename(layer.name)}"

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.output_dir).as_posix()

    def _format_filename(self, layer: LayerItem, index: int, width: int, height: int, ext: str) -> str:
        safe_name = sanitize_filename(layer.name)
        size = f"{width}x{height}"
        template = self.filename_template or "{id}_{name}_{width}x{height}.{ext}"
        filename = template.format(
            id=layer.id,
            index=f"{index:03d}",
            name=safe_name,
            size=size,
            width=width,
            height=height,
            ext=ext,
        )
        if not filename.lower().endswith(f".{ext}"):
            filename = f"{filename}.{ext}"
        stem = filename.rsplit(".", 1)[0].strip() or f"{layer.id}_{safe_name}_{size}"
        stem = re.sub(r"[\\/:*?\"<>|]+", "_", stem)
        stem = re.sub(r"\s+", "_", stem)
        stem = stem.strip("._-")
        return f"{stem}.{ext}"

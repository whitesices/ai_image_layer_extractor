from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.exporter import LayerExporter
from core.project import ProjectData


@dataclass(slots=True)
class PSDExportResult:
    output_path: Path
    native_psd: bool
    generated_files: list[Path]
    warnings: list[str] = field(default_factory=list)


class PSDExporter:
    """Experimental PSD exporter.

    Until a native PSD writer is configured, this exports a PSD-compatible
    package that can be manually assembled in Photoshop, Figma, or Affinity.
    """

    def export(self, project: ProjectData, output_path: str | Path) -> PSDExportResult:
        package_dir = Path(output_path)
        package_dir.mkdir(parents=True, exist_ok=True)
        result = LayerExporter(package_dir).export_all_layers(project)
        readme = package_dir / "README_PSD_COMPATIBLE.txt"
        readme.write_text(
            "AI Image Layer Extractor PSD-compatible package\n\n"
            "This version exports transparent layer PNGs, masks, project.json, and preview.png.\n"
            "Import these assets into Photoshop, Figma, Affinity Photo, or another editor and\n"
            "place each layer using the x/y/width/height metadata in project.json.\n\n"
            "Native PSD writing is reserved for a future optional extension.\n",
            encoding="utf-8",
        )
        generated: list[Path] = []
        for value in result.values():
            if isinstance(value, list):
                generated.extend(value)
            else:
                generated.append(value)
        generated.append(readme)
        return PSDExportResult(
            output_path=package_dir,
            native_psd=False,
            generated_files=generated,
            warnings=["Native PSD writing is not configured; exported PSD-compatible package."],
        )


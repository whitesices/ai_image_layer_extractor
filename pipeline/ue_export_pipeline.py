from __future__ import annotations

from pathlib import Path

from core.project import ProjectData
from exporters.ue_umg_exporter import UEUMGExporter, UEUMGExportResult


class UEExportPipeline:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def export(self, project: ProjectData) -> UEUMGExportResult:
        return UEUMGExporter(self.output_dir).export(project)


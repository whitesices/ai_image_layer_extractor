from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.export_dialog import ExportDialog
from core.app_settings import AppSettings
from core.command_executor import CommandExecutionResult, CommandExecutor
from core.edit_plan import BatchOutputSpec, EditTask, ImageEditPlan, QualityOptions
from core.project import ProjectData


class _BatchWorker(QObject):
    finished = Signal(object)

    def __init__(
        self,
        project: ProjectData,
        output_dir: Path,
        selected_layer_ids: list[str],
        plan: ImageEditPlan,
    ) -> None:
        super().__init__()
        self.project = project
        self.output_dir = output_dir
        self.selected_layer_ids = selected_layer_ids
        self.plan = plan

    @Slot()
    def run(self) -> None:
        result = CommandExecutor(self.project, self.output_dir, self.selected_layer_ids).execute(self.plan)
        self.finished.emit(result)


class BatchExportPanel(QWidget):
    """Panel for multi-size transparent layer exports."""

    exportFinished = Signal()

    def __init__(
        self,
        project: ProjectData,
        selected_layer_ids_provider: Callable[[], list[str]],
        output_dir_provider: Callable[[], Path],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.project = project
        self.selected_layer_ids_provider = selected_layer_ids_provider
        self.output_dir_provider = output_dir_provider
        self._thread: QThread | None = None
        self._worker: QObject | None = None

        self.layer_count_label = QLabel()
        self.all_radio = QRadioButton("Export All Layers")
        self.selected_radio = QRadioButton("Export Selected Layers")
        self.all_radio.setChecked(True)
        self.target_group = QButtonGroup(self)
        self.target_group.addButton(self.all_radio)
        self.target_group.addButton(self.selected_radio)

        self.size_checks: list[QCheckBox] = []
        size_row = QHBoxLayout()
        for size in [128, 256, 512, 1024]:
            check = QCheckBox(f"{size}x{size}")
            check.setProperty("size_value", size)
            if size in {512, 1024}:
                check.setChecked(True)
            self.size_checks.append(check)
            size_row.addWidget(check)

        self.custom_check = QCheckBox("Custom")
        self.custom_width_spin = QSpinBox()
        self.custom_width_spin.setRange(1, 8192)
        self.custom_width_spin.setValue(512)
        self.custom_height_spin = QSpinBox()
        self.custom_height_spin.setRange(1, 8192)
        self.custom_height_spin.setValue(512)
        size_row.addWidget(self.custom_check)
        size_row.addWidget(self.custom_width_spin)
        size_row.addWidget(QLabel("x"))
        size_row.addWidget(self.custom_height_spin)

        self.fit_mode_combo = QComboBox()
        self.fit_mode_combo.addItems(["contain", "cover", "stretch", "max_side", "original"])

        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 1024)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "webp"])

        form = QFormLayout()
        form.addRow("Target", self._target_widget())
        form.addRow("Sizes", size_row)
        form.addRow("Fit mode", self.fit_mode_combo)
        form.addRow("Padding", self.padding_spin)
        form.addRow("Format", self.format_combo)

        self.export_button = QPushButton("Export Batch")
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.addWidget(self.layer_count_label)
        layout.addLayout(form)
        layout.addWidget(self.export_button)
        layout.addWidget(self.output_edit, 1)

        self.export_button.clicked.connect(self.export_batch)
        self.refresh_state()

    def refresh_state(self) -> None:
        selected_count = len(self.selected_layer_ids_provider())
        self.layer_count_label.setText(f"Layers: {len(self.project.layers)} | Selected: {selected_count}")
        self.selected_radio.setEnabled(selected_count > 0)

    def set_settings(self, settings: AppSettings) -> None:
        for check in self.size_checks:
            size = int(check.property("size_value"))
            check.setChecked(size in settings.default_batch_sizes)
        self.fit_mode_combo.setCurrentText(settings.default_fit_mode)
        self.padding_spin.setValue(settings.default_padding)

    def export_batch(self) -> None:
        if self.project.image is None:
            self.output_edit.setPlainText("Open an image first.")
            return
        if not self.project.layers:
            self.output_edit.setPlainText("Create at least one layer before batch export.")
            return

        output_dir = ExportDialog.get_directory(self.output_dir_provider(), self)
        if output_dir is None:
            return

        specs = self._collect_specs()
        if not specs:
            self.output_edit.setPlainText("Select at least one output size.")
            return

        target = "selected_layers" if self.selected_radio.isChecked() else "all_layers"
        plan = ImageEditPlan(
            version="1.0",
            language="zh-CN",
            intent="batch_export",
            requires_confirmation=False,
            raw_user_text="Batch Export Panel",
            tasks=[
                EditTask(
                    type="batch_export_layers",
                    target=target,
                    layer_ids=[],
                    output_name=None,
                    sizes=specs,
                    transparent_background=True,
                    quality=QualityOptions(),
                    params={},
                )
            ],
        )
        self._start_worker(_BatchWorker(self.project, output_dir, self.selected_layer_ids_provider(), plan))

    def _collect_specs(self) -> list[BatchOutputSpec]:
        specs: list[BatchOutputSpec] = []
        fit_mode = self.fit_mode_combo.currentText()
        padding = self.padding_spin.value()
        output_format = self.format_combo.currentText()
        for check in self.size_checks:
            if check.isChecked():
                size = int(check.property("size_value"))
                specs.append(BatchOutputSpec(size, size, fit_mode, padding, output_format))
        if self.custom_check.isChecked():
            specs.append(
                BatchOutputSpec(
                    self.custom_width_spin.value(),
                    self.custom_height_spin.value(),
                    fit_mode,
                    padding,
                    output_format,
                )
            )
        return specs

    def _start_worker(self, worker: QObject) -> None:
        if self._thread is not None:
            self.output_edit.setPlainText("A batch export is already running.")
            return
        self.export_button.setEnabled(False)
        thread = QThread(self)
        self._thread = thread
        self._worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)  # type: ignore[attr-defined]
        worker.finished.connect(self._on_finished)  # type: ignore[attr-defined]
        worker.finished.connect(thread.quit)  # type: ignore[attr-defined]
        worker.finished.connect(worker.deleteLater)  # type: ignore[attr-defined]
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)
        thread.start()

    def _on_finished(self, result: CommandExecutionResult) -> None:
        lines = ["Success" if result.success else "Failed"]
        lines.extend(result.messages)
        if result.generated_files:
            report_files = [path for path in result.generated_files if path.endswith("batch_report.json")]
            if report_files:
                lines.append(f"Report: {report_files[-1]}")
        if result.warnings:
            lines.append("Warnings:")
            lines.extend(result.warnings)
        if result.errors:
            lines.append("Errors:")
            lines.extend(result.errors)
        self.output_edit.setPlainText("\n".join(lines))
        self.exportFinished.emit()

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self.export_button.setEnabled(True)

    def _target_widget(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.all_radio)
        layout.addWidget(self.selected_radio)
        layout.addStretch(1)
        return widget

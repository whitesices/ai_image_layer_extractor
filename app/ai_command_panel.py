from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.app_settings import AppSettings, SettingsManager
from core.command_executor import CommandExecutionResult, CommandExecutor
from core.edit_plan import CommandContext, ImageEditPlan, summarize_edit_plan
from core.project import ProjectData
from llm.base_provider import BaseLLMProvider
from llm.mock_provider import MockLLMProvider
from llm.openai_provider import OpenAIProvider


class _ParseWorker(QObject):
    finished = Signal(object, object)

    def __init__(self, provider: BaseLLMProvider, text: str, context: CommandContext) -> None:
        super().__init__()
        self.provider = provider
        self.text = text
        self.context = context

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(self.provider.parse_command(self.text, self.context), None)
        except Exception as exc:
            self.finished.emit(None, exc)


class _ExecuteWorker(QObject):
    finished = Signal(object)

    def __init__(
        self,
        project: ProjectData,
        output_dir: Path,
        selected_layer_ids: list[str],
        plan: ImageEditPlan,
        dry_run: bool,
    ) -> None:
        super().__init__()
        self.project = project
        self.output_dir = output_dir
        self.selected_layer_ids = selected_layer_ids
        self.plan = plan
        self.dry_run = dry_run

    @Slot()
    def run(self) -> None:
        result = CommandExecutor(self.project, self.output_dir, self.selected_layer_ids).execute(
            self.plan,
            dry_run=self.dry_run,
        )
        self.finished.emit(result)


class AICommandPanel(QWidget):
    """Natural language command panel for structured edit plans."""

    executionFinished = Signal()

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
        self.settings = SettingsManager().load()
        self.current_plan: ImageEditPlan | None = None
        self._thread: QThread | None = None
        self._worker: QObject | None = None

        self.status_label = QLabel()
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Example: 把所有图层导出 512x512")
        self.input_edit.setMinimumHeight(86)

        self.parse_button = QPushButton("Parse")
        self.dry_run_button = QPushButton("Dry Run")
        self.execute_button = QPushButton("Execute")
        self.clear_button = QPushButton("Clear")

        row = QHBoxLayout()
        row.addWidget(self.parse_button)
        row.addWidget(self.dry_run_button)
        row.addWidget(self.execute_button)
        row.addWidget(self.clear_button)

        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setMinimumHeight(180)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.input_edit)
        layout.addLayout(row)
        layout.addWidget(self.preview_edit, 1)

        self.parse_button.clicked.connect(self.parse_command)
        self.dry_run_button.clicked.connect(self.dry_run)
        self.execute_button.clicked.connect(self.execute)
        self.clear_button.clicked.connect(self.clear)
        self.refresh_status()

    def set_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        self.refresh_status()

    def refresh_status(self) -> None:
        provider = self._create_provider()
        fallback = ""
        if isinstance(provider, OpenAIProvider) and not provider.is_available():
            fallback = " (fallback: Mock)"
        self.status_label.setText(f"Provider: {provider.name}{fallback} | {provider.status_message()}")

    def parse_command(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            self.preview_edit.setPlainText("Please enter a command.")
            return
        provider = self._create_provider()
        if isinstance(provider, OpenAIProvider) and not provider.is_available():
            provider = MockLLMProvider()
        self._start_worker(_ParseWorker(provider, text, self._build_context()), self._on_parse_finished)

    def dry_run(self) -> None:
        if self.current_plan is None:
            self.preview_edit.setPlainText("Parse a command first.")
            return
        self._start_execute_worker(dry_run=True)

    def execute(self) -> None:
        if self.current_plan is None:
            self.preview_edit.setPlainText("Parse a command first.")
            return
        if self.current_plan.requires_confirmation:
            answer = QMessageBox.question(
                self,
                "Confirm AI Command",
                summarize_edit_plan(self.current_plan),
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self._start_execute_worker(dry_run=False)

    def clear(self) -> None:
        self.input_edit.clear()
        self.preview_edit.clear()
        self.current_plan = None

    def _start_execute_worker(self, dry_run: bool) -> None:
        assert self.current_plan is not None
        worker = _ExecuteWorker(
            self.project,
            self.output_dir_provider(),
            self.selected_layer_ids_provider(),
            self.current_plan,
            dry_run,
        )
        self._start_worker(worker, self._on_execute_finished)

    def _start_worker(self, worker: QObject, finished_callback) -> None:
        if self._thread is not None:
            self.preview_edit.setPlainText("A command is already running.")
            return
        self._set_busy(True)
        thread = QThread(self)
        self._thread = thread
        self._worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)  # type: ignore[attr-defined]
        worker.finished.connect(finished_callback)  # type: ignore[attr-defined]
        worker.finished.connect(thread.quit)  # type: ignore[attr-defined]
        worker.finished.connect(worker.deleteLater)  # type: ignore[attr-defined]
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)
        thread.start()

    def _on_parse_finished(self, plan: ImageEditPlan | None, error: Exception | None) -> None:
        if error is not None:
            self.preview_edit.setPlainText(f"Parse failed:\n{error}")
            self.current_plan = None
            return
        self.current_plan = plan
        self.preview_edit.setPlainText(summarize_edit_plan(plan))  # type: ignore[arg-type]

    def _on_execute_finished(self, result: CommandExecutionResult) -> None:
        lines = ["Success" if result.success else "Failed"]
        lines.extend(result.messages)
        if result.generated_files:
            lines.append("")
            lines.append("Generated files:")
            lines.extend(result.generated_files[:80])
            if len(result.generated_files) > 80:
                lines.append(f"... {len(result.generated_files) - 80} more")
        if result.warnings:
            lines.append("")
            lines.append("Warnings:")
            lines.extend(result.warnings)
        if result.errors:
            lines.append("")
            lines.append("Errors:")
            lines.extend(result.errors)
        self.preview_edit.setPlainText("\n".join(lines))
        self.executionFinished.emit()

    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._set_busy(False)

    def _set_busy(self, busy: bool) -> None:
        self.parse_button.setEnabled(not busy)
        self.dry_run_button.setEnabled(not busy)
        self.execute_button.setEnabled(not busy)

    def _create_provider(self) -> BaseLLMProvider:
        if self.settings.llm_provider in {"openai", "openai_compatible", "deepseek_compatible", "local_server"}:
            return OpenAIProvider(self.settings)
        return MockLLMProvider()

    def _build_context(self) -> CommandContext:
        width, height = self.project.canvas_size
        return CommandContext(
            source_image_loaded=self.project.has_image,
            canvas_width=width,
            canvas_height=height,
            layer_count=len(self.project.layers),
            selected_layer_ids=self.selected_layer_ids_provider(),
            available_layers=[
                {
                    "id": layer.id,
                    "name": layer.name,
                    "visible": layer.visible,
                    "x": layer.x,
                    "y": layer.y,
                    "width": layer.width,
                    "height": layer.height,
                }
                for layer in self.project.layers
            ],
        )

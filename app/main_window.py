from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QToolBar,
    QWidget,
)

from app.ai_command_panel import AICommandPanel
from app.batch_export_panel import BatchExportPanel
from app.canvas_widget import CanvasWidget
from app.export_dialog import ExportDialog
from app.layer_panel import LayerPanel
from app.settings_dialog import SettingsDialog
from core.exporter import LayerExporter
from core.image_utils import load_source_image
from core.layer import MaskResult
from core.project import ProjectData
from segmenters.opencv_segmenter import OpenCVSegmenter

BBox = tuple[int, int, int, int]


class MainWindow(QMainWindow):
    """Main desktop window for AI Image Layer Extractor."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI Image Layer Extractor")
        self.resize(1280, 820)

        self.project = ProjectData()
        self.segmenter = OpenCVSegmenter()
        self.current_selection: BBox | None = None
        self.current_mask_result: MaskResult | None = None
        self.selected_layer_id: str | None = None

        self.canvas = CanvasWidget()
        self.layer_panel = LayerPanel()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.layer_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        self.setCentralWidget(splitter)

        self._build_toolbar()
        self._build_docks_and_menus()
        self._connect_signals()
        self._apply_style()
        self.statusBar().showMessage("Ready")

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = QAction("Open Image", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_image)
        toolbar.addAction(open_action)

        create_action = QAction("Create Layer", self)
        create_action.setShortcut(QKeySequence("Ctrl+L"))
        create_action.triggered.connect(self.create_layer_from_selection)
        toolbar.addAction(create_action)

        export_action = QAction("Export All", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_all_layers)
        toolbar.addAction(export_action)

        fit_action = QAction("Fit View", self)
        fit_action.setShortcut(QKeySequence("Ctrl+0"))
        fit_action.triggered.connect(self.canvas.fit_to_view)
        toolbar.addAction(fit_action)

    def _build_docks_and_menus(self) -> None:
        self.ai_command_panel = AICommandPanel(
            self.project,
            self._selected_layer_ids,
            self._default_export_dir,
            self,
        )
        self.ai_dock = QDockWidget("AI Command", self)
        self.ai_dock.setObjectName("AICommandDock")
        self.ai_dock.setWidget(self.ai_command_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.ai_dock)
        self.ai_dock.hide()

        self.batch_export_panel = BatchExportPanel(
            self.project,
            self._selected_layer_ids,
            self._default_export_dir,
            self,
        )
        self.batch_dock = QDockWidget("Batch Export", self)
        self.batch_dock.setObjectName("BatchExportDock")
        self.batch_dock.setWidget(self.batch_export_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.batch_dock)
        self.batch_dock.hide()

        ai_menu = self.menuBar().addMenu("AI")
        show_ai_action = QAction("AI Command Panel", self)
        show_ai_action.triggered.connect(self._show_ai_command_panel)
        ai_menu.addAction(show_ai_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        ai_menu.addAction(settings_action)

        batch_menu = self.menuBar().addMenu("Batch")
        show_batch_action = QAction("Batch Export", self)
        show_batch_action.triggered.connect(self._show_batch_export_panel)
        batch_menu.addAction(show_batch_action)

    def _connect_signals(self) -> None:
        self.canvas.selectionChanged.connect(self._on_selection_changed)
        self.canvas.selectionCompleted.connect(self._on_selection_completed)
        self.canvas.layerClicked.connect(self._select_layer)

        self.layer_panel.createLayerRequested.connect(self.create_layer_from_selection)
        self.layer_panel.exportAllRequested.connect(self.export_all_layers)
        self.layer_panel.exportLayerRequested.connect(self.export_single_layer)
        self.layer_panel.deleteLayerRequested.connect(self.delete_layer)
        self.layer_panel.layerRenamed.connect(self.rename_layer)
        self.layer_panel.layerVisibilityChanged.connect(self.set_layer_visible)
        self.layer_panel.layerSelected.connect(self._select_layer)
        self.ai_command_panel.executionFinished.connect(self._refresh_layers)
        self.batch_export_panel.exportFinished.connect(self._refresh_layers)

    def open_image(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        if not file_path:
            return

        try:
            image = load_source_image(file_path)
        except Exception as exc:
            self._show_error("Open Image Failed", str(exc))
            return

        self.project.set_source_image(file_path, image)
        self.current_selection = None
        self.current_mask_result = None
        self.selected_layer_id = None
        self.canvas.set_image(image)
        self._refresh_layers()
        self.statusBar().showMessage(f"Opened {Path(file_path).name} ({image.width}x{image.height})")

    def create_layer_from_selection(self) -> None:
        if self.project.image is None:
            self._show_info("Open an image first.")
            return

        if self.current_mask_result is None:
            if self.current_selection is None:
                self._show_info("Select an area on the image first.")
                return
            if not self._generate_preview_mask(self.current_selection):
                return

        try:
            layer_name = f"layer_{len(self.project.layers) + 1:03d}"
            layer = self.project.add_layer_from_mask(layer_name, self.current_mask_result)
        except Exception as exc:
            self._show_error("Create Layer Failed", str(exc))
            return

        self.selected_layer_id = layer.id
        self.current_mask_result = None
        self.current_selection = None
        self.canvas.clear_selection()
        self.canvas.set_preview_mask(None)
        self._refresh_layers()
        self.statusBar().showMessage(
            f"Created {layer.id} {layer.name}: x={layer.x}, y={layer.y}, {layer.width}x{layer.height}"
        )

    def export_all_layers(self) -> None:
        if self.project.image is None:
            self._show_info("Open an image first.")
            return
        if not self.project.layers:
            self._show_info("Create at least one layer before exporting.")
            return

        default_dir = self._default_export_dir()
        output_dir = ExportDialog.get_directory(default_dir, self)
        if output_dir is None:
            return

        try:
            result = LayerExporter(output_dir).export_all_layers(self.project)
        except Exception as exc:
            self._show_error("Export Failed", str(exc))
            return

        self._refresh_layers()
        exported_count = len(result["layers"]) if isinstance(result["layers"], list) else 0
        self.statusBar().showMessage(f"Exported {exported_count} layer(s) to {output_dir}")
        QMessageBox.information(self, "Export Complete", f"Exported {exported_count} layer(s).")

    def export_single_layer(self, layer_id: str) -> None:
        if self.project.image is None:
            self._show_info("Open an image first.")
            return

        layer = self.project.get_layer(layer_id)
        if layer is None:
            self._show_info("Layer does not exist.")
            return

        default_dir = self._default_export_dir()
        output_dir = ExportDialog.get_directory(default_dir, self)
        if output_dir is None:
            return

        try:
            exporter = LayerExporter(output_dir)
            exporter.export_layer_png(self.project, layer)
            exporter.export_mask_png(self.project, layer)
        except Exception as exc:
            self._show_error("Export Layer Failed", str(exc))
            return

        self._refresh_layers()
        self.statusBar().showMessage(f"Exported layer {layer.id} to {output_dir}")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.ai_command_panel.settings, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.ai_command_panel.set_settings(dialog.settings)
        self.batch_export_panel.set_settings(dialog.settings)
        self.statusBar().showMessage("Settings saved")

    def delete_layer(self, layer_id: str) -> None:
        removed = self.project.remove_layer(layer_id)
        if removed:
            if self.selected_layer_id == layer_id:
                self.selected_layer_id = self.project.layers[-1].id if self.project.layers else None
            self._refresh_layers()
            self.statusBar().showMessage(f"Deleted layer {layer_id}")

    def rename_layer(self, layer_id: str, name: str) -> None:
        layer = self.project.get_layer(layer_id)
        if layer is None:
            return
        try:
            layer.rename(name)
        except ValueError as exc:
            self._show_error("Rename Failed", str(exc))
            self._refresh_layers()
            return
        self._refresh_layers()

    def set_layer_visible(self, layer_id: str, visible: bool) -> None:
        layer = self.project.get_layer(layer_id)
        if layer is None:
            return
        layer.set_visible(visible)
        self._refresh_layers()

    def _on_selection_changed(self, rect: BBox | None) -> None:
        self.current_selection = rect
        if rect is not None:
            x, y, width, height = rect
            self.statusBar().showMessage(f"Selection: x={x}, y={y}, {width}x{height}")

    def _on_selection_completed(self, rect: BBox | None) -> None:
        self.current_selection = rect
        self.current_mask_result = None
        self.canvas.set_preview_mask(None)
        if rect is None:
            return
        self._generate_preview_mask(rect)

    def _generate_preview_mask(self, rect: BBox) -> bool:
        if self.project.image is None:
            return False
        try:
            result = self.segmenter.segment(self.project.image, rect)
        except Exception as exc:
            self._show_error("Mask Generation Failed", str(exc))
            return False
        if result.is_empty:
            self._show_info("The selected area did not produce a usable mask.")
            return False
        self.current_mask_result = result
        self.canvas.set_preview_mask(result.mask)
        if result.bbox is not None:
            x, y, width, height = result.bbox
            self.statusBar().showMessage(f"Mask ready: x={x}, y={y}, {width}x{height}")
        return True

    def _select_layer(self, layer_id: str) -> None:
        if self.project.get_layer(layer_id) is None:
            return
        self.selected_layer_id = layer_id
        self._refresh_layers()

    def _refresh_layers(self) -> None:
        self.layer_panel.set_layers(self.project.layers, self.selected_layer_id)
        self.canvas.set_layers(self.project.layers, self.selected_layer_id)
        self.batch_export_panel.refresh_state()
        self.ai_command_panel.refresh_status()

    def _selected_layer_ids(self) -> list[str]:
        return [self.selected_layer_id] if self.selected_layer_id else []

    def _show_ai_command_panel(self) -> None:
        self.ai_dock.show()
        self.ai_dock.raise_()

    def _show_batch_export_panel(self) -> None:
        self.batch_dock.show()
        self.batch_dock.raise_()

    def _default_export_dir(self) -> Path:
        packaged_export_dir = os.environ.get("AI_IMAGE_LAYER_EXTRACTOR_EXPORT_DIR")
        if packaged_export_dir:
            return Path(packaged_export_dir)
        if self.project.source_image_path is None:
            return Path.cwd() / "Export"
        return self.project.source_image_path.parent / "Export"

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def _show_info(self, message: str) -> None:
        QMessageBox.information(self, "AI Image Layer Extractor", message)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #2b2c30;
                color: #f1f3f4;
                font-size: 13px;
            }
            QToolBar {
                background: #25262a;
                border: none;
                spacing: 6px;
                padding: 6px;
            }
            QPushButton, QToolButton {
                background: #3c4043;
                border: 1px solid #5f6368;
                border-radius: 4px;
                padding: 6px 10px;
            }
            QPushButton:hover, QToolButton:hover {
                background: #4b4f54;
            }
            QPushButton:disabled {
                color: #8a8d91;
                background: #313236;
            }
            QListWidget {
                background: #202124;
                border: 1px solid #4b4f54;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px 6px;
                min-height: 34px;
            }
            QListWidget::item:selected {
                background: #145a66;
            }
            QListWidget QLineEdit {
                min-height: 28px;
                padding: 2px 6px;
                margin: 0;
                selection-background-color: #1976d2;
                selection-color: #ffffff;
            }
            QLineEdit {
                background: #202124;
                border: 1px solid #5f6368;
                border-radius: 4px;
                padding: 6px;
            }
            QTextEdit, QComboBox, QSpinBox {
                background: #202124;
                border: 1px solid #5f6368;
                border-radius: 4px;
                padding: 4px;
                color: #f1f3f4;
            }
            QComboBox QAbstractItemView {
                background: #202124;
                color: #f1f3f4;
                selection-background-color: #145a66;
            }
            QCheckBox, QRadioButton {
                spacing: 6px;
            }
            QDockWidget {
                titlebar-close-icon: none;
                titlebar-normal-icon: none;
            }
            QLabel#PanelTitle {
                font-size: 16px;
                font-weight: 600;
                padding: 4px 0;
            }
            QStatusBar {
                background: #25262a;
            }
            """
        )

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.layer import LayerItem


class LayerPanel(QWidget):
    """Right-side layer list and layer actions."""

    createLayerRequested = Signal()
    exportAllRequested = Signal()
    exportLayerRequested = Signal(str)
    deleteLayerRequested = Signal(str)
    layerRenamed = Signal(str, str)
    layerVisibilityChanged = Signal(str, bool)
    layerSelected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._updating = False
        self._selected_layer_id: str | None = None

        self.title = QLabel("Layers")
        self.title.setObjectName("PanelTitle")

        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.layer_list.itemChanged.connect(self._on_item_changed)
        self.layer_list.currentItemChanged.connect(self._on_current_item_changed)

        self.create_button = QPushButton("Create Layer")
        self.export_selected_button = QPushButton("Export Layer")
        self.delete_button = QPushButton("Delete")
        self.export_all_button = QPushButton("Export All")

        self.create_button.clicked.connect(self.createLayerRequested.emit)
        self.export_selected_button.clicked.connect(self._emit_export_selected)
        self.delete_button.clicked.connect(self._emit_delete_selected)
        self.export_all_button.clicked.connect(self.exportAllRequested.emit)

        row_one = QHBoxLayout()
        row_one.addWidget(self.create_button)
        row_one.addWidget(self.export_selected_button)

        row_two = QHBoxLayout()
        row_two.addWidget(self.delete_button)
        row_two.addWidget(self.export_all_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.layer_list, 1)
        layout.addLayout(row_one)
        layout.addLayout(row_two)
        self.setMinimumWidth(260)
        self._sync_button_state()

    def set_layers(self, layers: list[LayerItem], selected_layer_id: str | None) -> None:
        self._updating = True
        self._selected_layer_id = selected_layer_id
        self.layer_list.clear()
        for layer in layers:
            item = QListWidgetItem(layer.name)
            item.setData(Qt.ItemDataRole.UserRole, layer.id)
            item.setData(Qt.ItemDataRole.UserRole + 1, layer.visible)
            item.setData(Qt.ItemDataRole.UserRole + 2, layer.name)
            item.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEditable
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            item.setCheckState(Qt.CheckState.Checked if layer.visible else Qt.CheckState.Unchecked)
            item.setToolTip(f"{layer.id}  x:{layer.x} y:{layer.y}  {layer.width}x{layer.height}")
            self.layer_list.addItem(item)
            if layer.id == selected_layer_id:
                self.layer_list.setCurrentItem(item)
        self._updating = False
        self._sync_button_state()

    def selected_layer_id(self) -> str | None:
        item = self.layer_list.currentItem()
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return str(value) if value is not None else None

    def _on_item_changed(self, item: QListWidgetItem) -> None:
        if self._updating:
            return
        layer_id = item.data(Qt.ItemDataRole.UserRole)
        if layer_id is None:
            return

        layer_id = str(layer_id)
        new_name = item.text().strip()
        previous_name = item.data(Qt.ItemDataRole.UserRole + 2)
        if not new_name:
            new_name = str(previous_name or layer_id)
            self._updating = True
            item.setText(new_name)
            self._updating = False
        if new_name != previous_name:
            item.setData(Qt.ItemDataRole.UserRole + 2, new_name)
            self.layerRenamed.emit(layer_id, new_name)

        visible = item.checkState() == Qt.CheckState.Checked
        previous_visible = item.data(Qt.ItemDataRole.UserRole + 1)
        if visible != previous_visible:
            item.setData(Qt.ItemDataRole.UserRole + 1, visible)
            self.layerVisibilityChanged.emit(layer_id, visible)

    def _on_current_item_changed(
        self, current: QListWidgetItem | None, previous: QListWidgetItem | None
    ) -> None:
        del previous
        self._sync_button_state()
        if self._updating or current is None:
            return
        layer_id = current.data(Qt.ItemDataRole.UserRole)
        if layer_id is not None:
            self.layerSelected.emit(str(layer_id))

    def _emit_export_selected(self) -> None:
        layer_id = self.selected_layer_id()
        if layer_id is not None:
            self.exportLayerRequested.emit(layer_id)

    def _emit_delete_selected(self) -> None:
        layer_id = self.selected_layer_id()
        if layer_id is not None:
            self.deleteLayerRequested.emit(layer_id)

    def _sync_button_state(self) -> None:
        has_selection = self.layer_list.currentItem() is not None
        has_layers = self.layer_list.count() > 0
        self.export_selected_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.export_all_button.setEnabled(has_layers)

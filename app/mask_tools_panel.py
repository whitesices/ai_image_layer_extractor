from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class MaskToolsPanel(QWidget):
    """Dockable controls for manual mask editing and quality actions."""

    brushModeChanged = Signal(object, int)
    actionRequested = Signal(str, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.off_radio = QRadioButton("Off")
        self.add_radio = QRadioButton("Brush Add")
        self.erase_radio = QRadioButton("Brush Erase")
        self.off_radio.setChecked(True)
        self.brush_group = QButtonGroup(self)
        self.brush_group.addButton(self.off_radio)
        self.brush_group.addButton(self.add_radio)
        self.brush_group.addButton(self.erase_radio)

        mode_row = QHBoxLayout()
        mode_row.addWidget(self.off_radio)
        mode_row.addWidget(self.add_radio)
        mode_row.addWidget(self.erase_radio)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 256)
        self.size_spin.setValue(24)

        self.feather_button = QPushButton("Feather")
        self.expand_button = QPushButton("Expand")
        self.shrink_button = QPushButton("Shrink")
        self.clean_halo_button = QPushButton("Clean Halo")
        self.smooth_button = QPushButton("Smooth")
        self.fill_holes_button = QPushButton("Fill Holes")
        self.remove_islands_button = QPushButton("Remove Islands")
        self.undo_button = QPushButton("Undo")
        self.redo_button = QPushButton("Redo")
        self.apply_button = QPushButton("Apply")
        self.reset_button = QPushButton("Reset")

        actions_one = QHBoxLayout()
        actions_one.addWidget(self.feather_button)
        actions_one.addWidget(self.expand_button)
        actions_one.addWidget(self.shrink_button)

        actions_two = QHBoxLayout()
        actions_two.addWidget(self.clean_halo_button)
        actions_two.addWidget(self.smooth_button)

        actions_three = QHBoxLayout()
        actions_three.addWidget(self.fill_holes_button)
        actions_three.addWidget(self.remove_islands_button)

        actions_four = QHBoxLayout()
        actions_four.addWidget(self.undo_button)
        actions_four.addWidget(self.redo_button)
        actions_four.addWidget(self.apply_button)
        actions_four.addWidget(self.reset_button)

        form = QFormLayout()
        form.addRow("Mode", mode_row)
        form.addRow("Size", self.size_spin)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Mask Tools"))
        layout.addLayout(form)
        layout.addLayout(actions_one)
        layout.addLayout(actions_two)
        layout.addLayout(actions_three)
        layout.addLayout(actions_four)
        layout.addStretch(1)

        self.off_radio.toggled.connect(self._emit_mode)
        self.add_radio.toggled.connect(self._emit_mode)
        self.erase_radio.toggled.connect(self._emit_mode)
        self.size_spin.valueChanged.connect(lambda _value: self._emit_mode())

        self.feather_button.clicked.connect(lambda: self.actionRequested.emit("feather", self.size_spin.value()))
        self.expand_button.clicked.connect(lambda: self.actionRequested.emit("expand", self.size_spin.value()))
        self.shrink_button.clicked.connect(lambda: self.actionRequested.emit("shrink", self.size_spin.value()))
        self.clean_halo_button.clicked.connect(lambda: self.actionRequested.emit("clean_halo", self.size_spin.value()))
        self.smooth_button.clicked.connect(lambda: self.actionRequested.emit("smooth", self.size_spin.value()))
        self.fill_holes_button.clicked.connect(lambda: self.actionRequested.emit("fill_holes", self.size_spin.value()))
        self.remove_islands_button.clicked.connect(lambda: self.actionRequested.emit("remove_islands", self.size_spin.value()))
        self.undo_button.clicked.connect(lambda: self.actionRequested.emit("undo", self.size_spin.value()))
        self.redo_button.clicked.connect(lambda: self.actionRequested.emit("redo", self.size_spin.value()))
        self.apply_button.clicked.connect(lambda: self.actionRequested.emit("apply", self.size_spin.value()))
        self.reset_button.clicked.connect(lambda: self.actionRequested.emit("reset", self.size_spin.value()))

    def _emit_mode(self) -> None:
        mode: str | None = None
        if self.add_radio.isChecked():
            mode = "add"
        elif self.erase_radio.isChecked():
            mode = "erase"
        self.brushModeChanged.emit(mode, self.size_spin.value())

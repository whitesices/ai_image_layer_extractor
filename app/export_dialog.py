from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ExportDialog(QDialog):
    """Small directory chooser used before exporting project assets."""

    def __init__(self, default_dir: str | Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export")
        self.path_edit = QLineEdit(str(default_dir))
        self.browse_button = QPushButton("Browse")
        self.cancel_button = QPushButton("Cancel")
        self.export_button = QPushButton("Export")
        self.export_button.setDefault(True)

        row = QHBoxLayout()
        row.addWidget(self.path_edit, 1)
        row.addWidget(self.browse_button)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.export_button)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Output folder"))
        layout.addLayout(row)
        layout.addLayout(actions)

        self.browse_button.clicked.connect(self._browse)
        self.cancel_button.clicked.connect(self.reject)
        self.export_button.clicked.connect(self.accept)

    @property
    def selected_directory(self) -> Path:
        return Path(self.path_edit.text()).expanduser()

    def _browse(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Export folder", self.path_edit.text())
        if directory:
            self.path_edit.setText(directory)

    @classmethod
    def get_directory(cls, default_dir: str | Path, parent: QWidget | None = None) -> Path | None:
        dialog = cls(default_dir, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.selected_directory
        return None

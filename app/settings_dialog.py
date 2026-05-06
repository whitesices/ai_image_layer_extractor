from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.app_settings import AppSettings, SettingsManager


class SettingsDialog(QDialog):
    """Application settings for LLM and batch export defaults."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(520)
        self.settings = settings or SettingsManager().load()

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["mock", "openai", "openai_compatible", "deepseek_compatible", "local_server"])

        self.detector_combo = QComboBox()
        self.detector_combo.addItems(["mock", "grounding_dino", "ocr"])

        self.segmenter_combo = QComboBox()
        self.segmenter_combo.addItems(["opencv_grabcut", "rembg", "sam2"])

        self.matting_combo = QComboBox()
        self.matting_combo.addItems(["simple", "birefnet"])

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Prefer OPENAI_API_KEY environment variable")

        self.save_key_check = QCheckBox("Save API key in settings.json (plain text, local only)")

        self.model_edit = QLineEdit()

        self.export_dir_edit = QLineEdit()
        self.export_browse_button = QPushButton("Browse")

        export_row = QHBoxLayout()
        export_row.addWidget(self.export_dir_edit, 1)
        export_row.addWidget(self.export_browse_button)

        self.sizes_edit = QLineEdit()
        self.fit_mode_combo = QComboBox()
        self.fit_mode_combo.addItems(["contain", "cover", "stretch", "max_side", "original"])

        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 1024)

        self.filename_template_edit = QLineEdit()

        self.allow_cloud_llm_check = QCheckBox("Allow cloud LLM text planning")
        self.allow_cloud_image_check = QCheckBox("Allow cloud image editing")
        self.ask_upload_check = QCheckBox("Ask before uploading images")
        self.never_upload_check = QCheckBox("Never upload images")

        form = QFormLayout()
        form.addRow("LLM provider", self.provider_combo)
        form.addRow("Detector backend", self.detector_combo)
        form.addRow("Segmenter backend", self.segmenter_combo)
        form.addRow("Matting refiner", self.matting_combo)
        form.addRow("OpenAI API key", self.api_key_edit)
        form.addRow("", self.save_key_check)
        form.addRow("OpenAI model", self.model_edit)
        form.addRow("Default export dir", export_row)
        form.addRow("Default batch sizes", self.sizes_edit)
        form.addRow("Default fit mode", self.fit_mode_combo)
        form.addRow("Default padding", self.padding_spin)
        form.addRow("Filename template", self.filename_template_edit)
        form.addRow("Privacy", self.allow_cloud_llm_check)
        form.addRow("", self.allow_cloud_image_check)
        form.addRow("", self.ask_upload_check)
        form.addRow("", self.never_upload_check)

        self.note_label = QLabel(
            "API keys are never bundled into installers. If you do not save the key, set OPENAI_API_KEY before launch."
        )
        self.note_label.setWordWrap(True)
        self.note_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.cancel_button = QPushButton("Cancel")
        self.save_button = QPushButton("Save")
        self.save_button.setDefault(True)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.note_label)
        layout.addLayout(buttons)

        self.export_browse_button.clicked.connect(self._browse_export_dir)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._save)

        self._load_settings()

    def _load_settings(self) -> None:
        self.provider_combo.setCurrentText(self.settings.llm_provider)
        self.detector_combo.setCurrentText(self.settings.detector_backend)
        self.segmenter_combo.setCurrentText(self.settings.segmenter_backend)
        self.matting_combo.setCurrentText(self.settings.matting_refiner)
        self.api_key_edit.setText(self.settings.openai_api_key)
        self.save_key_check.setChecked(self.settings.save_openai_api_key)
        self.model_edit.setText(self.settings.openai_model)
        self.export_dir_edit.setText(self.settings.default_export_dir)
        self.sizes_edit.setText(",".join(str(value) for value in self.settings.default_batch_sizes))
        self.fit_mode_combo.setCurrentText(self.settings.default_fit_mode)
        self.padding_spin.setValue(self.settings.default_padding)
        self.filename_template_edit.setText(self.settings.filename_template)
        self.allow_cloud_llm_check.setChecked(self.settings.allow_cloud_llm_text_planning)
        self.allow_cloud_image_check.setChecked(self.settings.allow_cloud_image_editing)
        self.ask_upload_check.setChecked(self.settings.ask_before_uploading_images)
        self.never_upload_check.setChecked(self.settings.never_upload_images)

    def _browse_export_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Default export directory", self.export_dir_edit.text())
        if directory:
            self.export_dir_edit.setText(directory)

    def _save(self) -> None:
        sizes: list[int] = []
        for part in self.sizes_edit.text().replace(";", ",").split(","):
            value = part.strip()
            if value.isdigit():
                parsed = int(value)
                if 1 <= parsed <= 8192:
                    sizes.append(parsed)
        if not sizes:
            sizes = [512, 1024]

        self.settings.llm_provider = self.provider_combo.currentText()
        self.settings.detector_backend = self.detector_combo.currentText()
        self.settings.segmenter_backend = self.segmenter_combo.currentText()
        self.settings.matting_refiner = self.matting_combo.currentText()
        self.settings.openai_api_key = self.api_key_edit.text().strip()
        self.settings.save_openai_api_key = self.save_key_check.isChecked()
        self.settings.openai_model = self.model_edit.text().strip() or "gpt-4o-mini"
        self.settings.default_export_dir = str(Path(self.export_dir_edit.text()).expanduser()) if self.export_dir_edit.text().strip() else ""
        self.settings.default_batch_sizes = sizes
        self.settings.default_fit_mode = self.fit_mode_combo.currentText()
        self.settings.default_padding = self.padding_spin.value()
        self.settings.filename_template = self.filename_template_edit.text().strip() or "{id}_{name}_{width}x{height}.{ext}"
        self.settings.allow_cloud_llm_text_planning = self.allow_cloud_llm_check.isChecked()
        self.settings.allow_cloud_image_editing = self.allow_cloud_image_check.isChecked()
        self.settings.ask_before_uploading_images = self.ask_upload_check.isChecked()
        self.settings.never_upload_images = self.never_upload_check.isChecked()
        if self.settings.never_upload_images:
            self.settings.allow_cloud_image_editing = False
        SettingsManager().save(self.settings)
        self.accept()

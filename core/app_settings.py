from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


APP_EXE_NAME = "AIImageLayerExtractor"


def get_user_data_dir() -> Path:
    configured = os.environ.get("AI_IMAGE_LAYER_EXTRACTOR_USER_DATA_DIR")
    if configured:
        return Path(configured)
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_EXE_NAME
    return Path.home() / "AppData" / "Local" / APP_EXE_NAME


def get_config_dir() -> Path:
    configured = os.environ.get("AI_IMAGE_LAYER_EXTRACTOR_CONFIG_DIR")
    if configured:
        return Path(configured)
    return get_user_data_dir() / "config"


def default_export_dir() -> Path:
    configured = os.environ.get("AI_IMAGE_LAYER_EXTRACTOR_EXPORT_DIR")
    if configured:
        return Path(configured)
    return get_user_data_dir() / "exports"


@dataclass(slots=True)
class AppSettings:
    llm_provider: str = "mock"
    openai_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    save_openai_api_key: bool = False
    detector_backend: str = "mock"
    segmenter_backend: str = "opencv_grabcut"
    matting_refiner: str = "simple"
    default_export_dir: str = ""
    default_batch_sizes: list[int] = field(default_factory=lambda: [512, 1024])
    default_fit_mode: str = "contain"
    default_padding: int = 0
    filename_template: str = "{id}_{name}_{width}x{height}.{ext}"
    allow_cloud_llm_text_planning: bool = False
    allow_cloud_image_editing: bool = False
    ask_before_uploading_images: bool = True
    never_upload_images: bool = True

    def effective_export_dir(self) -> Path:
        if self.default_export_dir.strip():
            return Path(self.default_export_dir).expanduser()
        return default_export_dir()


class SettingsManager:
    def __init__(self, settings_path: str | Path | None = None) -> None:
        self.settings_path = Path(settings_path) if settings_path is not None else get_config_dir() / "settings.json"

    def load(self) -> AppSettings:
        if not self.settings_path.exists():
            return AppSettings()
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except Exception:
            return AppSettings()
        return self._from_dict(data)

    def save(self, settings: AppSettings) -> Path:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(settings)
        if not settings.save_openai_api_key:
            data["openai_api_key"] = ""
        self.settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.settings_path

    def get_openai_api_key(self, settings: AppSettings | None = None) -> str:
        env_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if env_key:
            return env_key
        settings = settings or self.load()
        return settings.openai_api_key.strip()

    def _from_dict(self, data: dict[str, Any]) -> AppSettings:
        settings = AppSettings()
        for field_name in asdict(settings).keys():
            if field_name in data:
                setattr(settings, field_name, data[field_name])
        if not isinstance(settings.default_batch_sizes, list):
            settings.default_batch_sizes = [512, 1024]
        settings.default_batch_sizes = [
            int(value)
            for value in settings.default_batch_sizes
            if isinstance(value, int | float | str) and str(value).isdigit()
        ]
        settings.default_padding = max(0, int(settings.default_padding))
        allowed_llm = {"mock", "openai", "openai_compatible", "deepseek_compatible", "local_server"}
        allowed_detector = {"mock", "grounding_dino", "ocr"}
        allowed_segmenter = {"opencv_grabcut", "rembg", "sam2"}
        allowed_matting = {"simple", "birefnet"}
        settings.llm_provider = settings.llm_provider if settings.llm_provider in allowed_llm else "mock"
        settings.detector_backend = settings.detector_backend if settings.detector_backend in allowed_detector else "mock"
        settings.segmenter_backend = settings.segmenter_backend if settings.segmenter_backend in allowed_segmenter else "opencv_grabcut"
        settings.matting_refiner = settings.matting_refiner if settings.matting_refiner in allowed_matting else "simple"
        if settings.never_upload_images:
            settings.allow_cloud_image_editing = False
        return settings

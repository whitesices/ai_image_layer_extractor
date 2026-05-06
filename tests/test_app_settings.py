from __future__ import annotations

import os
import sys
import shutil
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.app_settings import AppSettings, SettingsManager


def test_settings_manager_does_not_save_api_key_unless_requested() -> None:
    tmp_path = _tmp_dir("settings_key")
    try:
        settings_path = tmp_path / "settings.json"
        settings = AppSettings(openai_api_key="secret", save_openai_api_key=False)

        SettingsManager(settings_path).save(settings)

        text = settings_path.read_text(encoding="utf-8")
        assert "secret" not in text
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_settings_manager_enforces_privacy_default() -> None:
    tmp_path = _tmp_dir("settings_privacy")
    try:
        settings_path = tmp_path / "settings.json"
        settings_path.write_text(
            '{"never_upload_images": true, "allow_cloud_image_editing": true, "llm_provider": "local_server"}',
            encoding="utf-8",
        )

        loaded = SettingsManager(settings_path).load()

        assert loaded.llm_provider == "local_server"
        assert loaded.never_upload_images is True
        assert loaded.allow_cloud_image_editing is False
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_settings_manager_saves_and_loads_llm_base_url() -> None:
    tmp_path = _tmp_dir("settings_base_url")
    try:
        settings_path = tmp_path / "settings.json"
        settings = AppSettings(
            llm_provider="deepseek_compatible",
            llm_base_url="https://api.example.com/v1",
            openai_model="deepseek-v4-pro",
        )

        SettingsManager(settings_path).save(settings)
        loaded = SettingsManager(settings_path).load()

        assert loaded.llm_provider == "deepseek_compatible"
        assert loaded.llm_base_url == "https://api.example.com/v1"
        assert loaded.openai_model == "deepseek-v4-pro"
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_llm_base_url_environment_overrides_settings() -> None:
    old_llm_url = os.environ.get("LLM_API_BASE_URL")
    old_openai_url = os.environ.get("OPENAI_BASE_URL")
    try:
        os.environ["LLM_API_BASE_URL"] = "http://localhost:8000/v1"
        os.environ.pop("OPENAI_BASE_URL", None)
        manager = SettingsManager()

        assert manager.get_llm_base_url(AppSettings(llm_base_url="https://settings.example/v1")) == "http://localhost:8000/v1"
    finally:
        if old_llm_url is None:
            os.environ.pop("LLM_API_BASE_URL", None)
        else:
            os.environ["LLM_API_BASE_URL"] = old_llm_url
        if old_openai_url is None:
            os.environ.pop("OPENAI_BASE_URL", None)
        else:
            os.environ["OPENAI_BASE_URL"] = old_openai_url


def _tmp_dir(prefix: str) -> Path:
    path = Path(__file__).resolve().parent / "_tmp" / f"{prefix}_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=False)
    return path

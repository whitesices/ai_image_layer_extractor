from __future__ import annotations

from core.app_settings import AppSettings, SettingsManager


def get_configured_provider_name(settings: AppSettings | None = None) -> str:
    settings = settings or SettingsManager().load()
    return settings.llm_provider


def get_openai_api_key(settings: AppSettings | None = None) -> str:
    manager = SettingsManager()
    return manager.get_openai_api_key(settings)

from __future__ import annotations

from core.app_settings import AppSettings, SettingsManager

from .base_provider import BaseLLMProvider
from .mock_provider import MockLLMProvider
from .openai_provider import OpenAIProvider


COMPATIBLE_LLM_PROVIDERS = frozenset({"openai", "openai_compatible", "deepseek_compatible", "local_server"})


def create_llm_provider(settings: AppSettings | None = None) -> BaseLLMProvider:
    settings = settings or SettingsManager().load()
    if settings.llm_provider in COMPATIBLE_LLM_PROVIDERS:
        return OpenAIProvider(settings)
    return MockLLMProvider()


def create_available_llm_provider(settings: AppSettings | None = None) -> BaseLLMProvider:
    provider = create_llm_provider(settings)
    if should_fallback_to_mock(provider):
        return MockLLMProvider()
    return provider


def should_fallback_to_mock(provider: BaseLLMProvider) -> bool:
    return not isinstance(provider, MockLLMProvider) and not provider.is_available()


def provider_status_text(settings: AppSettings | None = None) -> str:
    provider = create_llm_provider(settings)
    fallback = " (fallback: Mock)" if should_fallback_to_mock(provider) else ""
    return f"Provider: {provider.name}{fallback} | {provider.status_message()}"

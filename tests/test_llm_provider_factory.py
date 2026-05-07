from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.app_settings import AppSettings
from llm.mock_provider import MockLLMProvider
from llm.openai_provider import OpenAIProvider
from llm.provider_factory import (
    create_available_llm_provider,
    create_llm_provider,
    provider_status_text,
    should_fallback_to_mock,
)


def test_factory_creates_mock_provider_by_default() -> None:
    provider = create_llm_provider(AppSettings(llm_provider="mock"))

    assert isinstance(provider, MockLLMProvider)


def test_factory_creates_compatible_provider_for_deepseek() -> None:
    provider = create_llm_provider(
        AppSettings(
            llm_provider="deepseek_compatible",
            llm_base_url="https://api.example.com/v1",
            openai_model="deepseek-v4-pro",
        )
    )

    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "DeepSeek Compatible"


def test_factory_falls_back_to_mock_when_remote_provider_is_unavailable() -> None:
    provider = create_llm_provider(AppSettings(llm_provider="deepseek_compatible"))

    assert should_fallback_to_mock(provider) is True
    assert isinstance(create_available_llm_provider(AppSettings(llm_provider="deepseek_compatible")), MockLLMProvider)


def test_provider_status_text_mentions_fallback() -> None:
    text = provider_status_text(AppSettings(llm_provider="deepseek_compatible"))

    assert "fallback: Mock" in text
    assert "base URL" in text

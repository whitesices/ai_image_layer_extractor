from __future__ import annotations

import json
from typing import Any

from core.app_settings import AppSettings, SettingsManager
from core.edit_plan import CommandContext, ImageEditPlan

from .base_provider import BaseLLMProvider
from .prompt_templates import IMAGE_EDIT_PLAN_SYSTEM_PROMPT
from .schema import parse_edit_plan_from_json, validate_edit_plan_json


class OpenAIProvider(BaseLLMProvider):
    """Optional OpenAI-backed natural language plan parser."""

    name = "OpenAI"
    COMPATIBLE_PROVIDERS = {"openai_compatible", "deepseek_compatible", "local_server"}
    DISPLAY_NAMES = {
        "openai": "OpenAI",
        "openai_compatible": "OpenAI Compatible",
        "deepseek_compatible": "DeepSeek Compatible",
        "local_server": "Local Server",
    }

    def __init__(
        self,
        settings: AppSettings | None = None,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.settings = settings or SettingsManager().load()
        manager = SettingsManager()
        self.provider_key = self.settings.llm_provider
        self.name = self.DISPLAY_NAMES.get(self.provider_key, "OpenAI Compatible")
        self.base_url = (base_url if base_url is not None else manager.get_llm_base_url(self.settings)).strip()
        self.api_key = (api_key or manager.get_openai_api_key(self.settings)).strip()
        if not self.api_key and self.provider_key == "local_server" and self.base_url:
            self.api_key = "local-server"
        self.model = model or self.settings.openai_model
        self._import_error: str | None = None

    def is_available(self) -> bool:
        if self._requires_base_url() and not self.base_url:
            return False
        if not self.api_key:
            return False
        try:
            import openai  # noqa: F401
        except Exception as exc:
            self._import_error = str(exc)
            return False
        return True

    def status_message(self) -> str:
        if self._requires_base_url() and not self.base_url:
            return "LLM API base URL is not configured."
        if not self.api_key:
            return "LLM API key is not configured."
        if self._import_error:
            return f"OpenAI SDK is unavailable: {self._import_error}"
        if self.base_url:
            return f"Available, base URL: {self.base_url}"
        return "Available"

    def parse_command(self, user_text: str, context: CommandContext) -> ImageEditPlan:
        if self._requires_base_url() and not self.base_url:
            raise RuntimeError("LLM API base URL is not configured.")
        if not self.api_key:
            raise RuntimeError("LLM API key is not configured.")

        try:
            from openai import OpenAI
        except Exception as exc:
            raise RuntimeError(f"OpenAI Python SDK is not installed: {exc}") from exc

        client_kwargs: dict[str, str] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        client = OpenAI(**client_kwargs)
        user_payload = {
            "user_text": user_text,
            "context": {
                "source_image_loaded": context.source_image_loaded,
                "canvas_width": context.canvas_width,
                "canvas_height": context.canvas_height,
                "layer_count": context.layer_count,
                "selected_layer_ids": context.selected_layer_ids,
                "available_layers": context.available_layers,
            },
        }
        response = client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": IMAGE_EDIT_PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        try:
            data: dict[str, Any] = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"OpenAI returned invalid JSON: {exc}") from exc

        valid, errors = validate_edit_plan_json(data)
        if not valid:
            raise ValueError("OpenAI returned an invalid edit plan: " + "; ".join(errors))
        return parse_edit_plan_from_json(data)

    def _requires_base_url(self) -> bool:
        return self.provider_key in self.COMPATIBLE_PROVIDERS

from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image

from core.app_settings import SettingsManager

from .base_image_editor import BaseImageEditor, ImageEditResult


class OpenAIImageEditor(BaseImageEditor):
    """Optional cloud image editor placeholder.

    This class intentionally does not run by default. A future implementation
    can call OpenAI image editing APIs after explicit user confirmation because
    image pixels and masks may be uploaded to a remote service.
    """

    name = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (api_key or SettingsManager().get_openai_api_key()).strip()

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            import openai  # noqa: F401
        except Exception:
            return False
        return True

    def edit_image(
        self,
        image: Image.Image,
        mask: np.ndarray | None,
        prompt: str,
        options: dict[str, Any] | None = None,
    ) -> ImageEditResult:
        del image, mask, prompt, options
        if not self.api_key:
            return ImageEditResult(False, errors=["OpenAI API key is not configured."])
        if not self.is_available():
            return ImageEditResult(False, errors=["OpenAI Python SDK is not installed."])
        return ImageEditResult(
            False,
            warnings=["OpenAI image editing is reserved for a future optional extension."],
        )

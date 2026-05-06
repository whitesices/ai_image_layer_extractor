from __future__ import annotations

from typing import Any

from PIL import Image

from .base_detector import BaseDetector, DetectionResult


class OCRDetector(BaseDetector):
    """Optional OCR detector placeholder for text regions."""

    name = "ocr"

    def __init__(self) -> None:
        self._backend = ""
        self._import_error: str | None = None

    def is_available(self) -> bool:
        try:
            import easyocr  # noqa: F401

            self._backend = "easyocr"
            return True
        except Exception as exc:
            self._import_error = str(exc)
        try:
            import paddleocr  # noqa: F401

            self._backend = "paddleocr"
            return True
        except Exception as exc:
            self._import_error = str(exc)
            return False

    def status_message(self) -> str:
        if self.is_available():
            return f"Available via {self._backend}, but OCR inference is not configured in this MVP."
        return f"OCR backend is not installed: {self._import_error}"

    def detect(
        self,
        image: Image.Image,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> list[DetectionResult]:
        del image, prompt, context
        return []


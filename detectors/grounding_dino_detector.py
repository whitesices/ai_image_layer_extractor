from __future__ import annotations

from typing import Any

from PIL import Image

from .base_detector import BaseDetector, DetectionResult


class GroundingDINODetector(BaseDetector):
    """Optional GroundingDINO detector placeholder."""

    name = "grounding_dino"

    def __init__(self) -> None:
        self._import_error: str | None = None

    def is_available(self) -> bool:
        try:
            import groundingdino  # noqa: F401
        except Exception as exc:
            self._import_error = str(exc)
            return False
        return True

    def status_message(self) -> str:
        if self.is_available():
            return "Available, but model loading is not configured in this MVP."
        return f"GroundingDINO is not installed: {self._import_error}"

    def detect(
        self,
        image: Image.Image,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> list[DetectionResult]:
        del image, prompt, context
        return []


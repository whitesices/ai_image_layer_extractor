from __future__ import annotations

from typing import Any

from PIL import Image

from .base_detector import BaseDetector, DetectionResult


class MockDetector(BaseDetector):
    """Small deterministic detector for tests and offline fallback."""

    name = "mock_detector"

    def detect(
        self,
        image: Image.Image,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> list[DetectionResult]:
        del context
        if image.width <= 0 or image.height <= 0:
            return []

        prompt_lower = prompt.lower().strip()
        if not prompt_lower:
            return []

        if any(token in prompt_lower for token in {"person", "character", "角色", "人物"}):
            return [self._region(image, "person", prompt, 0.2, 0.1, 0.45, 0.8)]
        if any(token in prompt_lower for token in {"weapon", "武器"}):
            return [self._region(image, "weapon", prompt, 0.58, 0.35, 0.25, 0.18)]
        if any(token in prompt_lower for token in {"logo", "标志"}):
            return [self._region(image, "logo", prompt, 0.68, 0.08, 0.2, 0.16)]
        if any(token in prompt_lower for token in {"icon", "图标", "ui icon"}):
            return [self._region(image, "icon", prompt, 0.12, 0.08, 0.16, 0.16)]
        if any(token in prompt_lower for token in {"text", "文字", "文本"}):
            return [self._region(image, "text", prompt, 0.1, 0.75, 0.8, 0.12)]
        if any(token in prompt_lower for token in {"prop", "道具"}):
            return [self._region(image, "prop", prompt, 0.58, 0.45, 0.28, 0.28)]
        return []

    def _region(
        self,
        image: Image.Image,
        label: str,
        prompt: str,
        x_ratio: float,
        y_ratio: float,
        width_ratio: float,
        height_ratio: float,
    ) -> DetectionResult:
        x = int(round(image.width * x_ratio))
        y = int(round(image.height * y_ratio))
        width = max(1, int(round(image.width * width_ratio)))
        height = max(1, int(round(image.height * height_ratio)))
        x = max(0, min(image.width - width, x))
        y = max(0, min(image.height - height, y))
        return DetectionResult(label, (x, y, width, height), 0.25, self.name, prompt)

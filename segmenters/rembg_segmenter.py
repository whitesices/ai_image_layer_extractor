from __future__ import annotations

import numpy as np
from PIL import Image

from core.layer import MaskResult

from .base_segmenter import BaseSegmenter, SelectionRect


class RembgSegmenter(BaseSegmenter):
    """Optional rembg backend with a safe unavailable fallback."""

    name = "rembg"

    def __init__(self) -> None:
        self._import_error: str | None = None

    def is_available(self) -> bool:
        try:
            import rembg  # noqa: F401
        except Exception as exc:
            self._import_error = str(exc)
            return False
        return True

    def status_message(self) -> str:
        if self.is_available():
            return "Available"
        return f"rembg is not installed: {self._import_error}"

    def segment(self, image: Image.Image, selection_rect: SelectionRect) -> MaskResult:
        if not self.is_available():
            return MaskResult(
                mask=np.zeros((image.height, image.width), dtype=np.uint8),
                score=0.0,
                source=f"{self.name}_unavailable",
            )

        try:
            from rembg import remove

            rgba = remove(image.convert("RGBA"))
            alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8)
            x, y, width, height = selection_rect
            mask = np.zeros((image.height, image.width), dtype=np.uint8)
            x1 = max(0, min(image.width, int(x)))
            y1 = max(0, min(image.height, int(y)))
            x2 = max(0, min(image.width, int(x + width)))
            y2 = max(0, min(image.height, int(y + height)))
            mask[y1:y2, x1:x2] = alpha[y1:y2, x1:x2]
            return MaskResult(mask=mask, score=0.5, source=self.name)
        except Exception:
            return MaskResult(
                mask=np.zeros((image.height, image.width), dtype=np.uint8),
                score=0.0,
                source=f"{self.name}_failed",
            )

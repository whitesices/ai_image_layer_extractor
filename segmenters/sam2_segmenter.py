from __future__ import annotations

import os

import numpy as np
from PIL import Image

from core.layer import MaskResult

from .base_segmenter import BaseSegmenter, SelectionRect


class SAM2Segmenter(BaseSegmenter):
    """Optional SAM2 point/box/mask prompt backend placeholder."""

    name = "sam2"

    def __init__(self, checkpoint_path: str | None = None) -> None:
        self.checkpoint_path = checkpoint_path or os.environ.get("SAM2_CHECKPOINT", "")
        self._import_error: str | None = None

    def is_available(self) -> bool:
        try:
            import sam2  # noqa: F401
        except Exception as exc:
            self._import_error = str(exc)
            return False
        return bool(self.checkpoint_path)

    def status_message(self) -> str:
        if self.is_available():
            return "Available"
        if self._import_error:
            return f"SAM2 is not installed: {self._import_error}"
        return "SAM2 checkpoint is not configured."

    def segment(self, image: Image.Image, selection_rect: SelectionRect) -> MaskResult:
        del selection_rect
        return MaskResult(
            mask=np.zeros((image.height, image.width), dtype=np.uint8),
            score=0.0,
            source=f"{self.name}_unavailable",
        )

    def segment_with_point(self, image: Image.Image, point: tuple[int, int]) -> MaskResult:
        del point
        return MaskResult(
            mask=np.zeros((image.height, image.width), dtype=np.uint8),
            score=0.0,
            source=f"{self.name}_point_unavailable",
        )

    def segment_with_mask(self, image: Image.Image, mask: np.ndarray) -> MaskResult:
        del mask
        return MaskResult(
            mask=np.zeros((image.height, image.width), dtype=np.uint8),
            score=0.0,
            source=f"{self.name}_mask_unavailable",
        )

from __future__ import annotations

from PIL import Image

from core.layer import MaskResult

from .base_segmenter import BaseSegmenter, SelectionRect


class RembgSegmenter(BaseSegmenter):
    """Placeholder for a future rembg backend."""

    name = "rembg"

    def segment(self, image: Image.Image, selection_rect: SelectionRect) -> MaskResult:
        raise NotImplementedError(
            "rembg integration is reserved for a later version. "
            "Install rembg and implement this backend when the model environment is ready."
        )

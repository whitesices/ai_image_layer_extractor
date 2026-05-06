from __future__ import annotations

from PIL import Image

from core.layer import MaskResult

from .base_segmenter import BaseSegmenter, SelectionRect


class SAM2Segmenter(BaseSegmenter):
    """Placeholder for a future SAM2 point/box segmentation backend."""

    name = "sam2"

    def segment(self, image: Image.Image, selection_rect: SelectionRect) -> MaskResult:
        raise NotImplementedError(
            "SAM2 integration is reserved for a later version. "
            "Implement model loading, prompt encoding, and mask selection here."
        )

from __future__ import annotations

import numpy as np

from core.mask_utils import clean_mask, dilate_mask, erode_mask, feather_mask, normalize_mask

from .base_matting_refiner import BaseMattingRefiner, MattingRefineResult


class SimpleAlphaRefiner(BaseMattingRefiner):
    """Local Pillow/OpenCV based alpha refinement."""

    name = "simple_alpha"

    def __init__(
        self,
        feather_radius: int = 1,
        dilate_pixels: int = 0,
        erode_pixels: int = 0,
        min_area: int = 64,
    ) -> None:
        self.feather_radius = max(0, int(feather_radius))
        self.dilate_pixels = max(0, int(dilate_pixels))
        self.erode_pixels = max(0, int(erode_pixels))
        self.min_area = max(0, int(min_area))

    def refine(self, mask: np.ndarray) -> MattingRefineResult:
        refined = normalize_mask(mask)
        refined = clean_mask(refined, min_area=self.min_area)
        if self.dilate_pixels:
            refined = dilate_mask(refined, self.dilate_pixels)
        if self.erode_pixels:
            refined = erode_mask(refined, self.erode_pixels)
        if self.feather_radius:
            refined = feather_mask(refined, self.feather_radius)
        return MattingRefineResult(mask=normalize_mask(refined), source=self.name)


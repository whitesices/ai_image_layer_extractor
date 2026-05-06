from __future__ import annotations

from abc import ABC, abstractmethod

from PIL import Image

from core.layer import MaskResult

SelectionRect = tuple[int, int, int, int]


class BaseSegmenter(ABC):
    """Base class for image element segmentation backends."""

    name = "base"

    @abstractmethod
    def segment(self, image: Image.Image, selection_rect: SelectionRect) -> MaskResult:
        """Return a full-canvas mask for the selected region."""

"""Segmentation backends."""

from .base_segmenter import BaseSegmenter
from .opencv_segmenter import OpenCVSegmenter
from core.layer import MaskResult

__all__ = ["BaseSegmenter", "OpenCVSegmenter", "MaskResult"]

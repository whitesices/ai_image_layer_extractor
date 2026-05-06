from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image

from core.mask_utils import apply_mask_to_rgba, mask_to_bbox, normalize_mask
from core.quality_pipeline import QualityPipeline

from .base_image_editor import BaseImageEditor, ImageEditResult


class LocalImageEditor(BaseImageEditor):
    """Small local editor for non-generative image operations."""

    name = "local"

    def __init__(self) -> None:
        self.quality = QualityPipeline()

    def edit_image(
        self,
        image: Image.Image,
        mask: np.ndarray | None,
        prompt: str,
        options: dict[str, Any] | None = None,
    ) -> ImageEditResult:
        options = options or {}
        operation = str(options.get("operation") or prompt or "").strip().lower()
        try:
            if operation in {"crop", "apply_mask", "remove_background_from_existing_mask"}:
                if mask is None:
                    return ImageEditResult(False, errors=["This operation requires a mask."])
                bbox = mask_to_bbox(mask)
                if bbox is None:
                    return ImageEditResult(False, errors=["Mask is empty."])
                return ImageEditResult(True, image=apply_mask_to_rgba(image, normalize_mask(mask), bbox))

            if operation == "resize":
                width = int(options.get("width", image.width))
                height = int(options.get("height", image.height))
                fit_mode = str(options.get("fit_mode", "contain"))
                padding = int(options.get("padding", 0))
                result = self.quality.resize_rgba_high_quality(image, width, height, fit_mode, padding)
                return ImageEditResult(True, image=result)

            if operation == "padding":
                padding = int(options.get("padding", 0))
                return ImageEditResult(True, image=self.quality.add_transparent_padding(image, padding))

            return ImageEditResult(False, warnings=[f"Unsupported local operation: {operation}"])
        except Exception as exc:
            return ImageEditResult(False, errors=[str(exc)])


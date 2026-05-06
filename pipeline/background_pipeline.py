from __future__ import annotations

import numpy as np

from core.extraction_result import ExtractionResult
from core.layer import MaskResult
from core.project import ProjectData


class BackgroundPipeline:
    """Create a background layer by inverting existing foreground masks."""

    def create_background_layer(self, project: ProjectData, name: str = "background") -> ExtractionResult:
        if project.image is None:
            return ExtractionResult(False, errors=["No source image is loaded."])
        if not project.layers:
            return ExtractionResult(
                False,
                user_action_required=True,
                warnings=["No foreground layers exist. Manually select or extract foreground first."],
            )

        combined = np.zeros((project.image.height, project.image.width), dtype=np.uint8)
        for layer in project.layers:
            combined = np.maximum(combined, layer.mask)
        background_mask = np.where(combined > 0, 0, 255).astype(np.uint8)
        result = MaskResult(mask=background_mask, source="background_inverse")
        if result.is_empty:
            return ExtractionResult(False, errors=["Background mask is empty."])
        layer = project.add_layer_from_mask(name, result)
        return ExtractionResult(
            True,
            layer=layer,
            mask_result=result,
            confidence=0.5,
            messages=[f"Created background layer {layer.id} by inverting foreground masks."],
        )

from __future__ import annotations

from core.layer import LayerItem
from core.mask_utils import mask_to_bbox
from matting.base_matting_refiner import BaseMattingRefiner
from matting.simple_alpha_refiner import SimpleAlphaRefiner


class MaskRefinePipeline:
    def __init__(self, refiner: BaseMattingRefiner | None = None) -> None:
        self.refiner = refiner or SimpleAlphaRefiner()

    def refine_layer(self, layer: LayerItem) -> list[str]:
        result = self.refiner.refine(layer.mask)
        bbox = mask_to_bbox(result.mask)
        warnings = list(result.warnings)
        if bbox is None:
            warnings.append(f"Layer {layer.id} refined mask is empty; keeping original.")
            return warnings
        layer.mask = result.mask
        layer.bbox = bbox
        layer.metadata["mask_refiner"] = result.source
        return warnings


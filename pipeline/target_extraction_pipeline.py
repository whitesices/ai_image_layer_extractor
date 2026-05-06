from __future__ import annotations

import numpy as np

from core.extraction_plan import ExtractionRequest
from core.extraction_result import ExtractionResult
from core.layer import MaskResult
from core.mask_utils import mask_to_bbox, normalize_mask
from core.project import ProjectData
from detectors.base_detector import BaseDetector, DetectionResult
from detectors.mock_detector import MockDetector
from segmenters.base_segmenter import BaseSegmenter
from segmenters.opencv_segmenter import OpenCVSegmenter


class TargetExtractionPipeline:
    """Resolve target prompts into project layers using safe local fallbacks."""

    def __init__(
        self,
        segmenter: BaseSegmenter | None = None,
        detector: BaseDetector | None = None,
    ) -> None:
        self.segmenter = segmenter or OpenCVSegmenter()
        self.detector = detector or MockDetector()

    def extract(self, project: ProjectData, request: ExtractionRequest) -> ExtractionResult:
        if project.image is None:
            return ExtractionResult(False, errors=["No source image is loaded."])

        if request.selected_layer_id:
            layer = project.get_layer(request.selected_layer_id)
            if layer is None:
                return ExtractionResult(False, errors=[f"Layer does not exist: {request.selected_layer_id}"])
            return ExtractionResult(
                True,
                layer=layer,
                mask_result=MaskResult(mask=layer.mask, bbox=layer.bbox, score=1.0, source="existing_layer"),
                confidence=1.0,
                messages=[f"Using existing layer {layer.id}."],
            )

        if request.existing_mask is not None:
            mask = normalize_mask(request.existing_mask)
            bbox = mask_to_bbox(mask)
            if bbox is None:
                return ExtractionResult(False, errors=["Existing mask is empty."])
            return self._create_layer(project, request, MaskResult(mask=mask, bbox=bbox, score=1.0, source="existing_mask"))

        if request.bbox is not None:
            try:
                mask_result = self.segmenter.segment(project.image, request.bbox)
            except Exception as exc:
                return ExtractionResult(False, errors=[str(exc)])
            return self._create_layer(project, request, mask_result)

        detections = self.detector.detect(project.image, request.target_prompt, context=request.metadata)
        if not detections:
            return ExtractionResult(
                False,
                user_action_required=True,
                warnings=[
                    f"No detector result for '{request.target_prompt}'. Please manually box-select the target."
                ],
                metadata={"target_prompt": request.target_prompt},
            )

        best = max(detections, key=lambda item: item.confidence)
        try:
            mask_result = self.segmenter.segment(project.image, best.bbox)
        except Exception as exc:
            return ExtractionResult(False, errors=[str(exc)], metadata={"detection": best})
        result = self._create_layer(project, request, mask_result)
        result.confidence = best.confidence
        result.metadata["detection"] = _detection_to_dict(best)
        return result

    def _create_layer(
        self,
        project: ProjectData,
        request: ExtractionRequest,
        mask_result: MaskResult,
    ) -> ExtractionResult:
        if mask_result.is_empty:
            return ExtractionResult(False, errors=["Extraction mask is empty."])
        name = request.output_name or request.target_prompt or f"layer_{len(project.layers) + 1:03d}"
        try:
            layer = project.add_layer_from_mask(name, mask_result)
        except Exception as exc:
            return ExtractionResult(False, mask_result=mask_result, errors=[str(exc)])
        return ExtractionResult(
            True,
            layer=layer,
            mask_result=mask_result,
            confidence=float(mask_result.score or 0.0),
            messages=[f"Created layer {layer.id} from target '{request.target_prompt}'."],
            metadata={"target_prompt": request.target_prompt},
        )


def _detection_to_dict(detection: DetectionResult) -> dict:
    return {
        "label": detection.label,
        "bbox": detection.bbox,
        "confidence": detection.confidence,
        "source": detection.source,
        "prompt": detection.prompt,
        "metadata": detection.metadata,
    }


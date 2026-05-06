from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.extraction_plan import ExtractionRequest
from core.layer import MaskResult
from core.project import ProjectData
from detectors.mock_detector import MockDetector
from matting.simple_alpha_refiner import SimpleAlphaRefiner
from pipeline.background_pipeline import BackgroundPipeline
from pipeline.mask_refine_pipeline import MaskRefinePipeline
from pipeline.target_extraction_pipeline import TargetExtractionPipeline
from segmenters.rembg_segmenter import RembgSegmenter
from segmenters.sam2_segmenter import SAM2Segmenter


def _project() -> ProjectData:
    image = Image.new("RGB", (64, 64), (10, 10, 10))
    draw = ImageDraw.Draw(image)
    draw.rectangle((18, 14, 46, 50), fill=(230, 230, 245))
    project = ProjectData()
    project.set_source_image("input.png", image)
    return project


def test_target_extraction_with_bbox_creates_layer() -> None:
    project = _project()
    request = ExtractionRequest(target_prompt="person", bbox=(14, 10, 38, 46), output_name="person")

    result = TargetExtractionPipeline().extract(project, request)

    assert result.success is True
    assert result.layer is not None
    assert result.layer.name == "person"
    assert len(project.layers) == 1


def test_target_extraction_without_detection_requests_user_action() -> None:
    project = _project()
    request = ExtractionRequest(target_prompt="unknown-object")

    result = TargetExtractionPipeline(detector=MockDetector()).extract(project, request)

    assert result.success is False
    assert result.user_action_required is True


def test_background_pipeline_inverts_foreground_mask() -> None:
    project = _project()
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[16:48, 20:44] = 255
    project.add_layer_from_mask("foreground", MaskResult(mask=mask))

    result = BackgroundPipeline().create_background_layer(project)

    assert result.success is True
    assert result.layer is not None
    assert result.layer.name == "background"
    assert len(project.layers) == 2


def test_mask_refine_pipeline_marks_layer() -> None:
    project = _project()
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[16:48, 20:44] = 255
    layer = project.add_layer_from_mask("foreground", MaskResult(mask=mask))

    warnings = MaskRefinePipeline(SimpleAlphaRefiner(feather_radius=0)).refine_layer(layer)

    assert warnings == []
    assert layer.metadata["mask_refiner"] == "simple_alpha"


def test_optional_segmenters_do_not_crash_when_unavailable() -> None:
    image = Image.new("RGB", (16, 16), (0, 0, 0))

    rembg_result = RembgSegmenter().segment(image, (0, 0, 8, 8))
    sam2_result = SAM2Segmenter().segment(image, (0, 0, 8, 8))

    assert rembg_result.mask.shape == (16, 16)
    assert sam2_result.mask.shape == (16, 16)

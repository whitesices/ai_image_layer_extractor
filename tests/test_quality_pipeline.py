from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.mask_utils import mask_to_bbox
from core.quality_pipeline import QualityPipeline


def test_quality_pipeline_padding_output_size() -> None:
    image = Image.new("RGBA", (10, 8), (255, 0, 0, 255))

    padded = QualityPipeline().add_transparent_padding(image, 4)

    assert padded.size == (18, 16)
    assert padded.getpixel((0, 0))[3] == 0


def test_quality_pipeline_contain_does_not_stretch_image() -> None:
    image = Image.new("RGBA", (20, 10), (255, 0, 0, 255))

    output = QualityPipeline().resize_rgba_high_quality(image, 100, 100, fit_mode="contain", padding=0)
    alpha = np.asarray(output.getchannel("A"), dtype=np.uint8)

    assert output.size == (100, 100)
    assert mask_to_bbox(alpha) == (0, 25, 100, 50)


def test_quality_report_detects_alpha() -> None:
    image = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    image.putpixel((1, 1), (255, 255, 255, 255))

    report = QualityPipeline().validate_export_quality(image)

    assert report.has_alpha is True
    assert report.alpha_min == 0
    assert report.alpha_max == 255


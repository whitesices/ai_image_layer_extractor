from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.mask_utils import apply_mask_to_rgba, clean_mask, dilate_mask, erode_mask, feather_mask, mask_to_bbox


def test_mask_to_bbox_returns_tight_bounds() -> None:
    mask = np.zeros((10, 12), dtype=np.uint8)
    mask[3:7, 4:9] = 255

    assert mask_to_bbox(mask) == (4, 3, 5, 4)


def test_clean_mask_removes_small_components() -> None:
    mask = np.zeros((12, 12), dtype=np.uint8)
    mask[1, 1] = 255
    mask[5:9, 5:9] = 255

    cleaned = clean_mask(mask, min_area=8)

    assert cleaned[1, 1] == 0
    assert cleaned[6, 6] == 255


def test_morphology_and_feather_keep_mask_shape() -> None:
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[4:6, 4:6] = 255

    dilated = dilate_mask(mask, pixels=1)
    eroded = erode_mask(dilated, pixels=1)
    feathered = feather_mask(mask, radius=2)

    assert dilated.shape == mask.shape
    assert eroded.shape == mask.shape
    assert feathered.shape == mask.shape
    assert np.count_nonzero(dilated) > np.count_nonzero(mask)
    assert feathered.dtype == np.uint8


def test_apply_mask_to_rgba_crops_and_sets_alpha() -> None:
    image = Image.new("RGB", (8, 6), (200, 100, 50))
    mask = np.zeros((6, 8), dtype=np.uint8)
    mask[2:5, 3:7] = 255

    rgba = apply_mask_to_rgba(image, mask, (3, 2, 4, 3))

    assert rgba.mode == "RGBA"
    assert rgba.size == (4, 3)
    assert rgba.getchannel("A").getextrema() == (255, 255)

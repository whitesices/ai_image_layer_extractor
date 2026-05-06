from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

BBox = tuple[int, int, int, int]
Point = tuple[int, int]


@dataclass(slots=True)
class ExtractionRequest:
    target_prompt: str
    bbox: BBox | None = None
    point: Point | None = None
    existing_mask: np.ndarray | None = None
    selected_layer_id: str | None = None
    output_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExtractionPlan:
    requests: list[ExtractionRequest]
    source: str = "manual_or_ai_command"
    allow_detectors: bool = True
    allow_optional_segmenters: bool = False


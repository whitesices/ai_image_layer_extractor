from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .layer import LayerItem, MaskResult


@dataclass(slots=True)
class ExtractionResult:
    success: bool
    layer: LayerItem | None = None
    mask_result: MaskResult | None = None
    confidence: float = 0.0
    user_action_required: bool = False
    messages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


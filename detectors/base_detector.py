from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from PIL import Image

BBox = tuple[int, int, int, int]


@dataclass(slots=True)
class DetectionResult:
    label: str
    bbox: BBox
    confidence: float
    source: str
    prompt: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseDetector(ABC):
    name = "base"

    @abstractmethod
    def detect(
        self,
        image: Image.Image,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> list[DetectionResult]:
        """Return detections for a natural-language or class prompt."""

    def is_available(self) -> bool:
        return True

    def status_message(self) -> str:
        return "Available" if self.is_available() else "Unavailable"


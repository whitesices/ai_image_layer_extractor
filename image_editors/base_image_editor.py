from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from PIL import Image


@dataclass(slots=True)
class ImageEditResult:
    success: bool
    image: Image.Image | None = None
    messages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseImageEditor(ABC):
    name = "base"

    @abstractmethod
    def edit_image(
        self,
        image: Image.Image,
        mask: np.ndarray | None,
        prompt: str,
        options: dict[str, Any] | None = None,
    ) -> ImageEditResult:
        """Edit an image using a local or remote backend."""


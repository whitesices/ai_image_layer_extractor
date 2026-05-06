from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True)
class MattingRefineResult:
    mask: np.ndarray
    source: str
    warnings: list[str] = field(default_factory=list)


class BaseMattingRefiner(ABC):
    name = "base"

    @abstractmethod
    def refine(self, mask: np.ndarray) -> MattingRefineResult:
        """Return a refined alpha mask."""

    def is_available(self) -> bool:
        return True


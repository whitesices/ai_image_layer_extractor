from __future__ import annotations

import numpy as np

from core.mask_utils import normalize_mask

from .base_matting_refiner import BaseMattingRefiner, MattingRefineResult


class BiRefNetRefiner(BaseMattingRefiner):
    """Optional BiRefNet refiner placeholder."""

    name = "birefnet"

    def __init__(self) -> None:
        self._import_error: str | None = None

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
        except Exception as exc:
            self._import_error = str(exc)
            return False
        return False

    def refine(self, mask: np.ndarray) -> MattingRefineResult:
        return MattingRefineResult(
            mask=normalize_mask(mask),
            source=f"{self.name}_unavailable",
            warnings=["BiRefNet is an optional future extension and is not configured."],
        )


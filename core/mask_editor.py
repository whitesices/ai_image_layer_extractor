from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .mask_utils import normalize_mask


@dataclass(slots=True)
class MaskEditHistory:
    limit: int = 10
    undo_stack: list[np.ndarray] = field(default_factory=list)
    redo_stack: list[np.ndarray] = field(default_factory=list)

    def push(self, mask: np.ndarray) -> None:
        self.undo_stack.append(normalize_mask(mask).copy())
        if len(self.undo_stack) > self.limit:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self, current_mask: np.ndarray) -> np.ndarray:
        if not self.undo_stack:
            return normalize_mask(current_mask)
        self.redo_stack.append(normalize_mask(current_mask).copy())
        return self.undo_stack.pop()

    def redo(self, current_mask: np.ndarray) -> np.ndarray:
        if not self.redo_stack:
            return normalize_mask(current_mask)
        self.undo_stack.append(normalize_mask(current_mask).copy())
        return self.redo_stack.pop()

    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()


class MaskEditor:
    """Brush-based local mask editor."""

    def __init__(self, history_limit: int = 10) -> None:
        self.history = MaskEditHistory(limit=history_limit)

    def apply_brush(
        self,
        mask: np.ndarray,
        x: int,
        y: int,
        size: int,
        mode: str,
        *,
        record_history: bool = True,
    ) -> np.ndarray:
        if mode not in {"add", "erase"}:
            raise ValueError(f"Unsupported brush mode: {mode}")
        current = normalize_mask(mask)
        if record_history:
            self.history.push(current)

        radius = max(1, int(size) // 2)
        yy, xx = np.ogrid[: current.shape[0], : current.shape[1]]
        circle = (xx - int(x)) ** 2 + (yy - int(y)) ** 2 <= radius * radius
        output = current.copy()
        output[circle] = 255 if mode == "add" else 0
        return output

    def undo(self, current_mask: np.ndarray) -> np.ndarray:
        return self.history.undo(current_mask)

    def redo(self, current_mask: np.ndarray) -> np.ndarray:
        return self.history.redo(current_mask)

    def reset_history(self) -> None:
        self.history.clear()

from __future__ import annotations

from abc import ABC, abstractmethod

from core.edit_plan import CommandContext, ImageEditPlan


class BaseLLMProvider(ABC):
    name = "Base"

    @abstractmethod
    def parse_command(self, user_text: str, context: CommandContext) -> ImageEditPlan:
        """Convert user text into a validated ImageEditPlan."""

    def is_available(self) -> bool:
        return True

    def status_message(self) -> str:
        return "Available" if self.is_available() else "Unavailable"

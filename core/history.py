from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .command_executor import CommandExecutionResult
from .edit_plan import ImageEditPlan


@dataclass(slots=True)
class HistoryEntry:
    created_at: str
    plan: ImageEditPlan
    result: CommandExecutionResult


@dataclass(slots=True)
class CommandHistory:
    entries: list[HistoryEntry] = field(default_factory=list)

    def add(self, plan: ImageEditPlan, result: CommandExecutionResult) -> None:
        self.entries.append(
            HistoryEntry(
                created_at=datetime.now().isoformat(timespec="seconds"),
                plan=plan,
                result=result,
            )
        )

    def clear(self) -> None:
        self.entries.clear()

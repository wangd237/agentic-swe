"""Tiny one-shot checkpoint for unproductive Agent code exploration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

EXPLORATION_TOOLS = {"read_file", "search_code", "grep", "search_graph"}


@dataclass
class ExplorationMonitor:
    """Notice repeated or prolonged read/search sequences without a test or edit.

    This is a prompt checkpoint, not a tool restriction or a new planning phase.
    It fires at most once per run.
    """

    consecutive_calls: int = 0
    repeated_calls: int = 0
    triggered: bool = False
    _seen: set[str] = field(default_factory=set, repr=False)

    def observe(
        self, name: str, tool_input: dict[str, Any], tool_result: dict[str, Any]
    ) -> None:
        if name not in EXPLORATION_TOOLS:
            self.consecutive_calls = 0
            self.repeated_calls = 0
            self._seen.clear()
            return

        if tool_result.get("data", {}).get("policy_blocked"):
            return

        signature = json.dumps([name, tool_input], sort_keys=True, ensure_ascii=False, default=str)
        self.consecutive_calls += 1
        if signature in self._seen:
            self.repeated_calls += 1
        self._seen.add(signature)

    def should_trigger(self) -> bool:
        return (
            not self.triggered
            and self.consecutive_calls >= 6
            and (self.repeated_calls >= 2 or self.consecutive_calls >= 8)
        )

    def mark_triggered(self) -> None:
        self.triggered = True

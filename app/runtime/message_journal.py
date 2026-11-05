"""Append-only, replayable log of the *model-visible* message surface.

Unlike trace.json (execution diagnostics), this records complete message blocks,
including tool call/result pairing. Compaction adds a replacement event without
rewriting or deleting the original messages. It does not yet resume interrupted
workspace execution; replay reconstructs only the chat surface.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


class MessageJournal:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._active: list[dict[str, Any]] = []
        self._seq = 0

    def sync(
        self,
        messages: list[dict[str, Any]],
        *,
        reason: str = "message_update",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist only a changed suffix; previously appended rows remain immutable."""
        current = deepcopy(messages)
        old = self._active
        start = 0
        while start < min(len(old), len(current)) and old[start] == current[start]:
            start += 1
        if start == len(old) and start == len(current):
            return

        events: list[dict[str, Any]] = []
        if start == len(old):
            for message in current[start:]:
                events.append({"op": "append", "message": message})
        else:
            events.append(
                {
                    "op": "replace",
                    "start": start,
                    "delete_count": len(old) - start,
                    "messages": current[start:],
                    "reason": reason,
                    **({"metadata": metadata} if metadata else {}),
                }
            )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for event in events:
                self._seq += 1
                handle.write(json.dumps({"seq": self._seq, **event}, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._active = current

    @staticmethod
    def replay(path: str | Path) -> list[dict[str, Any]]:
        """Reconstruct the active surface; ignore only an incomplete final line."""
        source = Path(path)
        if not source.exists():
            return []
        active: list[dict[str, Any]] = []
        expected_seq = 1
        with source.open("r", encoding="utf-8") as handle:
            rows = handle.readlines()
        for index, row in enumerate(rows):
            if not row.endswith("\n") and index == len(rows) - 1:
                break
            event = json.loads(row)
            if event.get("seq") != expected_seq:
                raise ValueError("Message journal sequence gap or reordering")
            expected_seq += 1
            if event.get("op") == "append":
                active.append(event["message"])
            elif event.get("op") == "replace":
                start = event["start"]
                end = start + event["delete_count"]
                if not (0 <= start <= end <= len(active)):
                    raise ValueError("Invalid message journal replacement range")
                active[start:end] = event["messages"]
            else:
                raise ValueError("Unknown message journal operation")
        return active

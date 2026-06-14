"""从 agronholm/anyio#1111 提炼出的最小公开接口。"""

from __future__ import annotations

from anyio._backends._asyncio import CancelScope, FakeTask, run_pending_task_once


__all__ = ["CancelScope", "FakeTask", "run_pending_task_once"]

"""从 agronholm/anyio#1113 提炼出的最小公开接口。"""

from __future__ import annotations

from anyio.from_thread import CancelScope, CancelledError, check_cancelled


__all__ = ["CancelScope", "CancelledError", "check_cancelled"]

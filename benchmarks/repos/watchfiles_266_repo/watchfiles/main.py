"""watchfiles#266 的最小 semi-real 复现实现。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class WatchfilesRustInternalError(RuntimeError):
    """模拟 watchfiles 将底层 watcher 错误重新包装后的异常。"""


def dispatch_event_handler_error(
    raw_error: Exception,
    *,
    ignore_permission_denied: bool,
    error_handler: Callable[[Exception], Any],
) -> Any | None:
    """调用 error_handler，并按 ignore_permission_denied 决定是否吞掉底层 OSError。

    当前故障点：
    - 只会忽略 PermissionError
    - 但 issue #266 表明，当 ignore_permission_denied=True 时，
      通过 error_handler 上报的 FileNotFoundError 之类底层 watcher OSError
      也应当被忽略，而不是继续中断上层应用
    """

    try:
        return error_handler(raw_error)
    except OSError as exc:
        if ignore_permission_denied and isinstance(exc, PermissionError):
            return None
        raise WatchfilesRustInternalError(f"error in underlying watcher: {exc}") from exc

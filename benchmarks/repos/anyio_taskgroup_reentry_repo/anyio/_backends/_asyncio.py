"""从 agronholm/anyio#1109 提炼出的最小 asyncio backend。"""

from __future__ import annotations


class TaskGroup:
    """只保留复现重复进入上下文所需的最小行为。"""

    def __init__(self) -> None:
        self._entered_once = False

    async def __aenter__(self) -> "TaskGroup":
        """第一次进入时初始化状态，重复进入时故意保留 bug。"""

        if not self._entered_once:
            self._exceptions: list[BaseException] = []
            self._entered_once = True
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        """这里故意保留真实 issue 的核心缺陷。"""

        if exc is not None:
            self._exceptions.append(exc)

        if self._exceptions:
            return False

        # bug: 第一次退出后删除 `_exceptions`，第二次再次退出时会触发 AttributeError
        del self._exceptions
        return False

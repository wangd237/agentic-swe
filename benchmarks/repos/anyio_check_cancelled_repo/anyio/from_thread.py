"""从 agronholm/anyio#1113 提炼出的最小 from_thread 场景。"""

from __future__ import annotations


class CancelledError(Exception):
    """模拟 backend 抛出的取消异常。"""


class CancelScope:
    """最小取消作用域，用来观察取消异常是否被正确吃掉。"""

    def __init__(self) -> None:
        self.cancelled_caught = False

    def __enter__(self) -> "CancelScope":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if isinstance(exc, CancelledError):
            self.cancelled_caught = True
            return True

        return False


class AsyncioBackend:
    """故意保留 bug：绕过传入的取消作用域，导致取消异常泄漏。"""

    name = "asyncio"

    def deliver_cancellation(self, scope: CancelScope) -> None:
        raise CancelledError("escaped cancel scope on asyncio backend")


class TrioBackend:
    """对照 backend：在作用域内部正确消费取消异常。"""

    name = "trio"

    def deliver_cancellation(self, scope: CancelScope) -> None:
        with scope:
            raise CancelledError("cancelled inside scope")


def check_cancelled(backend_name: str, scope: CancelScope) -> bool:
    """模拟 from_thread.check_cancelled 的 backend 分派。"""

    backends = {
        "asyncio": AsyncioBackend(),
        "trio": TrioBackend(),
    }
    backend = backends[backend_name]
    backend.deliver_cancellation(scope)
    return scope.cancelled_caught

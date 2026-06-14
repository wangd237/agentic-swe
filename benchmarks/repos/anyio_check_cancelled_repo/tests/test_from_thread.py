"""from_thread.check_cancelled 在不同 backend 下的最小回归测试。"""

from __future__ import annotations

import pytest

import anyio


def test_trio_backend_catches_cancellation_inside_scope() -> None:
    """对照路径：trio backend 应在 cancel scope 内部消费取消异常。"""

    scope = anyio.CancelScope()
    result = anyio.check_cancelled("trio", scope)

    assert result is True
    assert scope.cancelled_caught is True


def test_asyncio_backend_does_not_leak_cancelled_error() -> None:
    """目标回归：asyncio backend 也应把取消异常限制在对应作用域内。"""

    scope = anyio.CancelScope()
    result = anyio.check_cancelled("asyncio", scope)

    assert result is True
    assert scope.cancelled_caught is True

"""嵌套 task group 取消泄漏场景的最小回归测试。"""

from __future__ import annotations

import anyio


def test_trio_backend_keeps_original_nested_failure() -> None:
    """对照路径：trio backend 不应把取消异常额外泄漏到父流程。"""

    state = anyio.run_nested_failure_flow("trio")

    assert state.cancelled_leaked is False
    assert state.nested_failure_seen is True


def test_asyncio_backend_does_not_leak_cancelled_error() -> None:
    """目标回归：asyncio backend 也应保留原始嵌套失败语义。"""

    state = anyio.run_nested_failure_flow("asyncio")

    assert state.cancelled_leaked is False
    assert state.nested_failure_seen is True


def test_curio_backend_does_not_leak_cancelled_error() -> None:
    """issue 文本同时提到 curio，也应避免把取消异常泄漏到父流程。"""

    state = anyio.run_nested_failure_flow("curio")

    assert state.cancelled_leaked is False
    assert state.nested_failure_seen is True

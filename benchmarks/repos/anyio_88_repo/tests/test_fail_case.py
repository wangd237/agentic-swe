"""父任务被错误取消场景的最小回归测试。"""

from __future__ import annotations

import anyio


def test_trio_like_backend_allows_parent_cleanup_to_finish() -> None:
    """对照路径：trio / curio 风格 backend 不应把父任务额外取消。"""

    state = anyio.run_parent_task_after_child_failure("trio")

    assert state.cancelled is False
    assert state.completed is True


def test_asyncio_backend_does_not_spuriously_cancel_parent_task() -> None:
    """目标回归：asyncio backend 也不应让父任务被额外取消。"""

    state = anyio.run_parent_task_after_child_failure("asyncio")

    assert state.cancelled is False
    assert state.completed is True

"""_deliver_cancellation 缺少 task.done() 检查时的最小回归测试。"""

from __future__ import annotations

import pytest

import anyio


def test_pending_task_is_cancelled_once_without_spin() -> None:
    """相邻正常路径应在一次取消后收敛。"""

    schedule_count, cancel_requests = anyio.run_pending_task_once()
    assert schedule_count == 1
    assert cancel_requests == 1


def test_completed_task_is_ignored_during_cancellation_delivery() -> None:
    """已完成 task 留在集合中时，不应触发无限重排。"""

    scope = anyio.CancelScope(anyio.FakeTask(completed=True))
    schedule_count = scope.deliver_cancellation()

    assert schedule_count == 1
    assert scope._tasks == set()

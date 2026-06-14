"""TaskGroup 重复进入场景的最小回归测试。"""

from __future__ import annotations

import pytest

import anyio


async def _use_distinct_task_groups() -> None:
    async with anyio.create_task_group():
        pass
    async with anyio.create_task_group():
        pass


async def _reenter_same_task_group() -> None:
    task_group = anyio.create_task_group()
    async with task_group:
        pass
    async with task_group:
        pass


def test_distinct_task_groups_work_sequentially() -> None:
    """相邻正常路径应保持可用。"""

    anyio.run(_use_distinct_task_groups)


def test_reentering_same_task_group_raises_runtime_error() -> None:
    """重复进入同一个 task group 应抛出受控错误，而不是 AttributeError。"""

    with pytest.raises(RuntimeError, match="cannot be re-entered"):
        anyio.run(_reenter_same_task_group)

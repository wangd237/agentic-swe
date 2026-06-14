"""从 agronholm/anyio#1109 提炼出的最小公开接口。"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from anyio._backends._asyncio import TaskGroup


T = TypeVar("T")


def create_task_group() -> TaskGroup:
    """返回最小可复现版本的 TaskGroup。"""

    return TaskGroup()


def run(func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
    """用 asyncio.run 驱动最小复现用例。"""

    return asyncio.run(func(*args, **kwargs))


__all__ = ["TaskGroup", "create_task_group", "run"]

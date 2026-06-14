"""watchfiles#110 的最小 semi-real 复现实现。"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


class FakeRustNotify:
    """模拟底层 watcher 的阻塞式异步轮询接口。"""

    def __init__(self, *, sleep_steps: int = 8) -> None:
        self.sleep_steps = sleep_steps
        self.watch_call_count = 0

    async def watch(self) -> str:
        # 用多次短暂 sleep 模拟“底层 watch 调用很久才返回”。
        self.watch_call_count += 1
        for _ in range(self.sleep_steps):
            await asyncio.sleep(0)
        return "filesystem-event"


class FakeStopEvent:
    """模拟外部 Ctrl+C / stop 信号。"""

    def __init__(self) -> None:
        self._set = False

    def set(self) -> None:
        self._set = True

    def is_set(self) -> bool:
        return self._set


async def run_awatch_loop(
    watcher: FakeRustNotify,
    *,
    stop_event: FakeStopEvent,
    on_iteration: Callable[[int], Awaitable[None] | None] | None = None,
    max_iterations: int = 5,
) -> str:
    """运行一个最小 awatch 循环。

    当前故障点：
    - 只会在每轮循环开始前检查 stop_event
    - 如果 stop 请求发生在 `watch()` 阻塞期间，
      当前实现仍会等到底层调用返回后再产出一条事件
    - 这正对应原 issue 中“Ctrl+C 已触发，但必须等下一次文件事件才退出”的语义
    """

    iteration = 0
    while iteration < max_iterations:
        if stop_event.is_set():
            return "stopped"

        if on_iteration is not None:
            hook_result = on_iteration(iteration)
            if hook_result is not None:
                await hook_result

        event = await watcher.watch()
        return event

    return "exhausted"

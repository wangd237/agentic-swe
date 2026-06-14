"""从 agronholm/anyio#1111 提炼出的最小 asyncio cancellation backend。"""

from __future__ import annotations

from collections.abc import Callable


class SpinLoop:
    """模拟事件循环中通过 call_soon 不断重排回调的行为。"""

    def __init__(self, *, max_iterations: int = 8) -> None:
        self._callbacks: list[Callable[[], None]] = []
        self.schedule_count = 0
        self.max_iterations = max_iterations

    def call_soon(self, callback: Callable[[], None]) -> None:
        self.schedule_count += 1
        self._callbacks.append(callback)

    def run(self) -> None:
        iterations = 0
        while self._callbacks:
            iterations += 1
            if iterations > self.max_iterations:
                raise RuntimeError("Detected cancellation spin")

            callback = self._callbacks.pop(0)
            callback()


class FakeTask:
    """只保留本 issue 复现所需的最小任务状态。"""

    def __init__(self, *, completed: bool = False) -> None:
        self._completed = completed
        self.cancel_requests = 0

    def done(self) -> bool:
        return self._completed

    def request_cancel(self) -> None:
        self.cancel_requests += 1
        self._completed = True


class CancelScope:
    """只保留 _deliver_cancellation 的核心行为。"""

    def __init__(self, *tasks: FakeTask) -> None:
        self._tasks = set(tasks)

    def _deliver_cancellation(self, loop: SpinLoop) -> None:
        """这里故意保留已完成 task 仍触发重排的 bug。"""

        should_retry = False
        for task in list(self._tasks):
            if task.done():
                # bug: 已完成 task 仍然会触发下一轮 call_soon，导致持续自我重排。
                should_retry = True
                continue

            task.request_cancel()
            self._tasks.discard(task)

        if should_retry:
            loop.call_soon(lambda: self._deliver_cancellation(loop))

    def deliver_cancellation(self, *, max_iterations: int = 8) -> int:
        loop = SpinLoop(max_iterations=max_iterations)
        loop.call_soon(lambda: self._deliver_cancellation(loop))
        loop.run()
        return loop.schedule_count


def run_pending_task_once() -> tuple[int, int]:
    """正常路径：未完成 task 只应被取消一次，不应进入 spin。"""

    task = FakeTask(completed=False)
    scope = CancelScope(task)
    schedule_count = scope.deliver_cancellation()
    return schedule_count, task.cancel_requests

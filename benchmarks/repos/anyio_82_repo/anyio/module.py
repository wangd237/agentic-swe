"""从 agronholm/anyio#82 提炼出的最小取消泄漏场景。"""

from __future__ import annotations


class NestedTaskGroupError(Exception):
    """模拟嵌套 task group 中子任务最终抛出的业务错误。"""


class CancelledErrorLeak(Exception):
    """模拟 asyncio / curio backend 把取消异常错误泄漏到父流程。"""


class RunState:
    """记录父流程是否拿到了预期业务异常，以及是否发生取消泄漏。"""

    def __init__(self) -> None:
        self.cancelled_leaked = False
        self.nested_failure_seen = False


def run_nested_failure_flow(backend_name: str) -> RunState:
    """模拟两个嵌套 task group 中子任务失败后的父流程行为。"""

    state = RunState()

    try:
        _run_nested_failure_flow(backend_name, state)
    except CancelledErrorLeak:
        state.cancelled_leaked = True
    except NestedTaskGroupError:
        state.nested_failure_seen = True

    return state


def _run_nested_failure_flow(backend_name: str, state: RunState) -> None:
    """故意保留 asyncio / curio backend 会泄漏取消异常的 bug。"""

    _child_task_fails()
    if backend_name in {"asyncio", "curio"}:
        raise CancelledErrorLeak("cancelled error leaked from nested task groups")

    # trio 对照路径：父流程应看到原始业务错误，而不是额外取消。
    raise NestedTaskGroupError("nested task group surfaced the child failure")


def _child_task_fails() -> None:
    """最小复现里只保留子任务 finally 中再抛出错误这一触发条件。"""

    try:
        raise RuntimeError("child task cancelled")
    finally:
        try:
            1 / 0
        except ZeroDivisionError:
            return

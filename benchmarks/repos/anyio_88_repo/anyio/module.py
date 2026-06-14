"""从 agronholm/anyio#88 提炼出的最小父任务取消场景。"""

from __future__ import annotations


class ParentTaskCancelledError(Exception):
    """模拟父任务被错误取消时暴露出来的异常。"""


class ParentTaskState:
    """记录父任务在子任务失败后的最终状态。"""

    def __init__(self) -> None:
        self.cancelled = False
        self.completed = False


def run_parent_task_after_child_failure(backend_name: str) -> ParentTaskState:
    """模拟子任务失败后的父任务清理流程。"""

    state = ParentTaskState()

    try:
        _run_inner_flow(backend_name, state)
    except ParentTaskCancelledError:
        state.cancelled = True

    return state


def _run_inner_flow(backend_name: str, state: ParentTaskState) -> None:
    """故意保留 asyncio backend 会把父任务一并取消的 bug。"""

    _child_task_fails()
    if backend_name == "asyncio":
        raise ParentTaskCancelledError("parent task spuriously cancelled")

    # trio / curio 对照路径：子任务失败不会让父任务清理流程被额外取消。
    state.completed = True


def _child_task_fails() -> None:
    """最小复现里只保留“子任务出错”这个触发条件。"""

    try:
        raise RuntimeError("child task failed")
    except RuntimeError:
        return

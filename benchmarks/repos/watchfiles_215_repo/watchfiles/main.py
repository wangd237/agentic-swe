"""watchfiles#215 的最小 semi-real 复现实现。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileEvent:
    """模拟底层 watcher 产出的最小文件事件。"""

    kind: str
    path: str


@dataclass(frozen=True)
class WatchDecision:
    """描述单文件 watch 在一批事件后的最小决策。"""

    should_reload: bool
    continue_watching: bool


def evaluate_single_file_watch(
    events: list[FileEvent],
    *,
    target_path: str,
) -> WatchDecision:
    """判断单文件 watch 是否应该触发 reload，并继续保留 watcher。

    当前故障点：
    - `vim` 保存文件时，常见行为不是原地写入，而是“先写临时文件，再替换目标文件”
    - 单文件 watch 当前错误地把最后一个 `remove` 直接当成“目标文件真的被删掉了”
    - 结果就是：
      - 这次保存不会触发 reload
      - watcher 还会停止跟踪目标文件，后续修改也不再上报
    """

    saw_target_change = False
    for event in events:
        if event.path != target_path:
            continue

        if event.kind in {"modified", "modify-name-from", "metadata"}:
            saw_target_change = True
            continue

        if event.kind == "remove":
            return WatchDecision(
                should_reload=False,
                continue_watching=False,
            )

    return WatchDecision(
        should_reload=saw_target_change,
        continue_watching=True,
    )

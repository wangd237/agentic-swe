"""watchfiles#169 的最小 semi-real 复现实现。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileEvent:
    """模拟底层 watcher 产出的最小文件事件。"""

    kind: str
    path: str


def should_emit_reload(
    event: FileEvent,
    *,
    target_path: str,
    source_environment: str,
) -> bool:
    """判断 docs 风格的 function target 是否应当因为某个文件事件而触发重载。

    当前故障点：
    - 在 WSL / Docker 这类环境里，底层 watcher 有时只会上报 `metadata-write`
    - 但当前实现错误地把这类事件直接过滤掉
    - 结果就是：虽然目标文件已经变化，上层仍然收不到任何重载信号
    """

    if event.path != target_path:
        return False

    if event.kind == "metadata-write" and source_environment in {"wsl", "docker", "linux"}:
        return False

    return event.kind in {"modified", "added", "metadata-write"}

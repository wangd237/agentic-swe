"""Agent 基础协议定义。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseAgent(ABC):
    """统一不同 agent 实现的最小执行接口。"""

    @abstractmethod
    def run(
        self,
        *,
        task_path: str | Path,
        repo_root: str | Path,
        policy_path: str | Path | None = None,
    ) -> dict:
        """执行单条任务并返回统一运行产物。"""


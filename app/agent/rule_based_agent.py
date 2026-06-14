"""规则版 baseline agent。"""

from __future__ import annotations

from pathlib import Path

from app.agent.base import BaseAgent
from app.runtime.task_runner import run_observation_task


class RuleBasedAgent(BaseAgent):
    """对现有规则闭环的薄封装。"""

    def run(
        self,
        *,
        task_path: str | Path,
        repo_root: str | Path,
        policy_path: str | Path | None = None,
    ) -> dict:
        return run_observation_task(
            task_path=task_path,
            repo_root=repo_root,
            policy_path=policy_path,
        )


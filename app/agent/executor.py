"""Agent 执行器最小实现。"""

from pathlib import Path

from app.runtime.task_runner import run_observation_task


def run_agent(task_path: str | Path, repo_root: str | Path, policy_path: str | Path | None = None) -> dict:
    # 当前执行器只负责调起观察型闭环，后续 phase 再逐步扩展为完整 Agent loop。
    return run_observation_task(task_path=task_path, repo_root=repo_root, policy_path=policy_path)

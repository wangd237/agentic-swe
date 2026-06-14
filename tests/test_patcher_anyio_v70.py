from __future__ import annotations

import json
from pathlib import Path

from app.agent.patcher import apply_rule_based_patch
from app.agent.policy import PolicyConfig
from app.schemas.task_schema import Task


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_improved_v70_repairs_anyio_parent_task_cancel_bug(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    module_path = repo_path / "anyio" / "module.py"
    _write_text(
        module_path,
        '"""从 agronholm/anyio#88 提炼出的最小父任务取消场景。"""\n\n'
        "from __future__ import annotations\n\n\n"
        "class ParentTaskCancelledError(Exception):\n"
        '    """模拟父任务被错误取消时暴露出来的异常。"""\n\n\n'
        "class ParentTaskState:\n"
        '    """记录父任务在子任务失败后的最终状态。"""\n\n'
        "    def __init__(self) -> None:\n"
        "        self.cancelled = False\n"
        "        self.completed = False\n\n\n"
        "def run_parent_task_after_child_failure(backend_name: str) -> ParentTaskState:\n"
        '    """模拟子任务失败后的父任务清理流程。"""\n\n'
        "    state = ParentTaskState()\n\n"
        "    try:\n"
        "        _run_inner_flow(backend_name, state)\n"
        "    except ParentTaskCancelledError:\n"
        "        state.cancelled = True\n\n"
        "    return state\n\n\n"
        "def _run_inner_flow(backend_name: str, state: ParentTaskState) -> None:\n"
        '    """故意保留 asyncio backend 会把父任务一并取消的 bug。"""\n\n'
        "    _child_task_fails()\n"
        '    if backend_name == "asyncio":\n'
        '        raise ParentTaskCancelledError("parent task spuriously cancelled")\n\n'
        "    # trio / curio 对照路径：子任务失败不会让父任务清理流程被额外取消。\n"
        "    state.completed = True\n\n\n"
        "def _child_task_fails() -> None:\n"
        '    """最小复现里只保留“子任务出错”这个触发条件。"""\n\n'
        "    try:\n"
        '        raise RuntimeError("child task failed")\n'
        "    except RuntimeError:\n"
        "        return\n",
    )

    task = Task.model_validate(
        {
            "task_id": "task_129",
            "repo_name": "anyio_88_repo",
            "repo_path": "benchmarks/repos/anyio_88_repo",
            "issue_title": "Parent task spuriously cancelled with asyncio",
            "issue_text": "demo",
            "test_command": "python -m pytest tests/test_fail_case.py -q",
            "success_criteria": "demo",
            "difficulty": "medium",
            "tags": ["semi-real"],
            "target_files_hint": ["anyio/module.py"],
            "source_type": "semi_real",
            "metadata": {"candidate_id": "agronholm_anyio_issue_88"},
        }
    )
    policy = PolicyConfig.model_validate(json.loads((Path("E:/My_Projects/agentic-software-engineering-roadmap/optimization/policy_versions/improved_v70.json")).read_text(encoding="utf-8")))

    result = apply_rule_based_patch(
        task=task,
        repo_path=str(repo_path),
        candidate_files=["anyio/module.py"],
        policy_config=policy,
    )

    updated_content = module_path.read_text(encoding="utf-8")
    assert result["ok"] is True
    assert result["modified_files"] == ["anyio/module.py"]
    assert "父任务完成清理" in result["patch_reason"]
    assert 'if backend_name not in {"asyncio", "trio", "curio"}:' in updated_content
    assert 'raise ParentTaskCancelledError("parent task spuriously cancelled")' not in updated_content
    assert "state.completed = True" in updated_content

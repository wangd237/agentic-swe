from __future__ import annotations

import json
from pathlib import Path

from app.agent.patcher import apply_rule_based_patch
from app.agent.policy import PolicyConfig
from app.schemas.task_schema import Task


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_improved_v71_repairs_anyio_nested_cancelled_error_leak(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    module_path = repo_path / "anyio" / "module.py"
    _write_text(
        module_path,
        '"""从 agronholm/anyio#82 提炼出的最小取消泄漏场景。"""\n\n'
        "from __future__ import annotations\n\n\n"
        "class NestedTaskGroupError(Exception):\n"
        '    """模拟嵌套 task group 中子任务最终抛出的业务错误。"""\n\n\n'
        "class CancelledErrorLeak(Exception):\n"
        '    """模拟 asyncio / curio backend 把取消异常错误泄漏到父流程。"""\n\n\n'
        "class RunState:\n"
        '    """记录父流程是否拿到了预期业务异常，以及是否发生取消泄漏。"""\n\n'
        "    def __init__(self) -> None:\n"
        "        self.cancelled_leaked = False\n"
        "        self.nested_failure_seen = False\n\n\n"
        "def run_nested_failure_flow(backend_name: str) -> RunState:\n"
        '    """模拟两个嵌套 task group 中子任务失败后的父流程行为。"""\n\n'
        "    state = RunState()\n\n"
        "    try:\n"
        "        _run_nested_failure_flow(backend_name, state)\n"
        "    except CancelledErrorLeak:\n"
        "        state.cancelled_leaked = True\n"
        "    except NestedTaskGroupError:\n"
        "        state.nested_failure_seen = True\n\n"
        "    return state\n\n\n"
        "def _run_nested_failure_flow(backend_name: str, state: RunState) -> None:\n"
        '    """故意保留 asyncio / curio backend 会泄漏取消异常的 bug。"""\n\n'
        "    _child_task_fails()\n"
        '    if backend_name in {"asyncio", "curio"}:\n'
        '        raise CancelledErrorLeak("cancelled error leaked from nested task groups")\n\n'
        "    # trio 对照路径：父流程应看到原始业务错误，而不是额外取消。\n"
        '    raise NestedTaskGroupError("nested task group surfaced the child failure")\n\n\n'
        "def _child_task_fails() -> None:\n"
        '    """最小复现里只保留子任务 finally 中再抛出错误这一触发条件。"""\n\n'
        "    try:\n"
        '        raise RuntimeError("child task cancelled")\n'
        "    finally:\n"
        "        try:\n"
        "            1 / 0\n"
        "        except ZeroDivisionError:\n"
        "            return\n",
    )

    task = Task.model_validate(
        {
            "task_id": "task_128",
            "repo_name": "anyio_82_repo",
            "repo_path": "benchmarks/repos/anyio_82_repo",
            "issue_title": "CancelledError leak with asyncio and curio",
            "issue_text": "demo",
            "test_command": "python -m pytest test_anyio.py -q",
            "success_criteria": "demo",
            "difficulty": "medium",
            "tags": ["semi-real"],
            "target_files_hint": ["anyio/module.py"],
            "source_type": "semi_real",
            "metadata": {"candidate_id": "agronholm_anyio_issue_82"},
        }
    )
    policy = PolicyConfig.model_validate(
        json.loads(
            (
                Path(
                    "E:/My_Projects/agentic-software-engineering-roadmap/optimization/policy_versions/improved_v71.json"
                )
            ).read_text(encoding="utf-8")
        )
    )

    result = apply_rule_based_patch(
        task=task,
        repo_path=str(repo_path),
        candidate_files=["anyio/module.py"],
        policy_config=policy,
    )

    updated_content = module_path.read_text(encoding="utf-8")
    assert result["ok"] is True
    assert result["modified_files"] == ["anyio/module.py"]
    assert "嵌套 task group" in result["patch_reason"]
    assert 'if backend_name in {"asyncio", "curio"}:' not in updated_content
    assert 'raise CancelledErrorLeak("cancelled error leaked from nested task groups")' not in updated_content
    assert 'raise NestedTaskGroupError("nested task group surfaced the child failure")' in updated_content

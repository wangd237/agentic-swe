from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.task_runner import run_observation_task
from app.tools.run_tests import run_tests


def test_run_tests_returns_split_duration_metrics(tmp_path: Path) -> None:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    test_file = repo_dir / "test_pass.py"
    test_file.write_text(
        "def test_pass():\n"
        "    assert True\n",
        encoding="utf-8",
    )

    result = run_tests(str(repo_dir), "python -m pytest test_pass.py -q", timeout_sec=30)

    assert result["ok"] is True
    assert isinstance(result["data"]["subprocess_duration_sec"], float)
    assert isinstance(result["data"]["summary_extraction_duration_sec"], float)
    assert result["data"]["subprocess_duration_sec"] >= 0.0
    assert result["data"]["summary_extraction_duration_sec"] >= 0.0
    assert result["data"]["duration_sec"] >= result["data"]["subprocess_duration_sec"]


def test_run_observation_task_writes_trace_tool_metrics() -> None:
    output = run_observation_task(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        policy_path=None,
    )

    trace = output["trace"]
    assert trace["started_at"]
    assert trace["finished_at"]

    run_test_steps = [step for step in trace["steps"] if step["tool_name"] == "run_tests"]
    assert len(run_test_steps) == 2
    for step in run_test_steps:
        assert "subprocess_duration_sec" in step["tool_metrics"]
        assert "summary_extraction_duration_sec" in step["tool_metrics"]
        assert step["duration_sec"] is not None

    patch_steps = [step for step in trace["steps"] if step["tool_name"] == "rule_based_patch"]
    assert len(patch_steps) == 1
    assert "patch_applied" in patch_steps[0]["tool_metrics"]

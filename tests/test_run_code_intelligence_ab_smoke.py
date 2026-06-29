from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import run_code_intelligence_ab_smoke


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_run_tests_then_stop_client_runs_once_then_stops() -> None:
    client = run_code_intelligence_ab_smoke.RunTestsThenStopClient("python -m pytest")

    first = client.create_message(system_prompt="", messages=[], tools=[])
    second = client.create_message(system_prompt="", messages=[], tools=[])

    assert first["content"][1]["name"] == "run_tests"
    assert first["content"][1]["input"]["command"] == "python -m pytest"
    assert second["content"][0]["type"] == "text"


def test_run_code_intelligence_ab_smoke_with_missing_binary_records_pair(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "benchmarks" / "repos" / "demo_repo"
    task_path = tmp_path / "benchmarks" / "tasks" / "task_demo.json"
    manifest_path = tmp_path / "benchmarks" / "manifests" / "dev_tasks.json"
    baseline_policy_path = tmp_path / "optimization" / "policy_versions" / "llm_demo.json"
    output_dir = tmp_path / "logs" / "summaries"

    write_text(repo / "tests" / "test_app.py", "def test_ok():\n    assert True\n")
    write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "Demo issue",
            "issue_text": "DemoSymbol fails",
            "test_command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
            "success_criteria": "pass",
            "difficulty": "easy",
            "tags": ["smoke"],
            "target_files_hint": ["tests/test_app.py"],
        },
    )
    write_json(
        manifest_path,
        {
            "manifest_id": "dev",
            "tasks": ["benchmarks/tasks/task_demo.json"],
        },
    )
    write_json(
        baseline_policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
        },
    )
    monkeypatch.setattr(run_code_intelligence_ab_smoke, "REPO_ROOT", tmp_path)

    output = run_code_intelligence_ab_smoke.run_code_intelligence_ab_smoke(
        manifest=manifest_path,
        tasks_dir=tmp_path / "benchmarks" / "tasks",
        baseline_policy_path=baseline_policy_path,
        cohort_label="missing_binary",
        codebase_memory_binary="definitely-missing-codebase-memory-mcp",
        limit=1,
        output_dir=output_dir,
    )

    assert output["smoke_id"] == "code_intelligence_ab_smoke_missing_binary_001"
    assert output["summary"]["task_count"] == 1
    assert output["summary"]["target_files_by_task"] == {
        "task_demo": ["tests/test_app.py"]
    }
    assert len(output["summary"]["runs"]) == 2
    assert output["ab_summary"]["ab_aggregate"]["pair_count"] == 1
    assert output["ab_summary"]["ab_aggregate"]["candidate_fallback_rate"] == 1.0
    graph_snapshot = [
        item
        for item in output["ab_summary"]["run_snapshots"]
        if item["backend"] == "codebase_memory_cli"
    ][0]
    assert graph_snapshot["target_files"] == ["tests/test_app.py"]
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary"]["outputs"]["ab_summary_json"]).exists()

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import run_multi_model_eval


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_task(path: Path, task_id: str) -> None:
    write_json(
        path,
        {
            "task_id": task_id,
            "repo_name": "sample",
            "repo_path": "benchmarks/repos/sample_repo",
            "issue_title": "demo",
            "issue_text": "demo",
            "success_criteria": "tests pass",
            "test_command": "python -m pytest -q",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["pkg/app.py"],
            "source_type": "semi_real",
        },
    )


def make_policy(path: Path, policy_id: str, model: str) -> None:
    write_json(
        path,
        {
            "policy_id": policy_id,
            "description": "test policy",
            "agent_type": "llm",
            "llm_provider": "openai_compatible",
            "llm_model": model,
            "llm_api_key_env": f"{policy_id.upper()}_API_KEY",
            "llm_max_output_tokens": 8000,
        },
    )


def test_run_multi_model_eval_dry_run_writes_skipped_matrix(tmp_path: Path) -> None:
    repo_root = tmp_path
    manifest_path = repo_root / "benchmarks" / "manifests" / "frozen.json"
    task_dir = repo_root / "benchmarks" / "tasks"
    policy_dir = repo_root / "optimization" / "policy_versions"
    make_task(task_dir / "task_001.json", "task_001")
    make_task(task_dir / "task_002.json", "task_002")
    make_policy(policy_dir / "llm_a.json", "llm_a", "model-a")
    make_policy(policy_dir / "llm_b.json", "llm_b", "model-b")
    write_json(
        manifest_path,
        {
            "manifest_id": "frozen_test",
            "tasks": [
                "benchmarks/tasks/task_001.json",
                "benchmarks/tasks/task_002.json",
            ],
        },
    )

    output = run_multi_model_eval.run_multi_model_eval(
        repo_root=repo_root,
        manifest_path=manifest_path,
        policy_paths=[policy_dir / "llm_a.json", policy_dir / "llm_b.json"],
        output_dir=repo_root / "logs" / "summaries",
        run_label="dry",
        dry_run=True,
    )

    summary = output["summary"]
    assert summary["matrix_run_id"] == "multi_model_eval_dry_001"
    assert summary["expected_pair_count"] == 4
    assert summary["record_count"] == 4
    assert summary["completed_count"] == 0
    assert {record["record_status"] for record in summary["records"]} == {"skipped"}
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()


def test_run_multi_model_eval_resumes_completed_pairs(tmp_path: Path) -> None:
    repo_root = tmp_path
    manifest_path = repo_root / "benchmarks" / "manifests" / "frozen.json"
    task_dir = repo_root / "benchmarks" / "tasks"
    policy_dir = repo_root / "optimization" / "policy_versions"
    make_task(task_dir / "task_001.json", "task_001")
    make_task(task_dir / "task_002.json", "task_002")
    make_policy(policy_dir / "llm_a.json", "llm_a", "model-a")
    write_json(
        manifest_path,
        {
            "manifest_id": "frozen_test",
            "tasks": [
                "benchmarks/tasks/task_001.json",
                "benchmarks/tasks/task_002.json",
            ],
        },
    )
    resume_path = repo_root / "logs" / "summaries" / "multi_model_eval_resume_001.json"
    write_json(
        resume_path,
        {
            "matrix_run_id": "multi_model_eval_resume_001",
            "started_at": "2026-06-15T00:00:00+00:00",
            "records": [
                {
                    "record_status": "completed",
                    "policy_id": "llm_a",
                    "task_id": "task_001",
                    "final_status": "success",
                }
            ],
        },
    )
    calls: list[str] = []

    def fake_runner(*, task_path: Path, repo_root: Path, policy_path: Path) -> dict:
        del repo_root, policy_path
        task_id = json.loads(Path(task_path).read_text(encoding="utf-8"))["task_id"]
        calls.append(task_id)
        return {
            "result": {
                "task_id": task_id,
                "run_id": f"run_{task_id}",
                "final_status": "success",
                "incomplete_reason": "",
                "patch_applied": True,
                "modified_files": ["pkg/app.py"],
                "post_test_exit_code": 0,
                "post_test_summary": "ok",
                "duration_sec": 1.0,
                "tool_stats": {
                    "policy_id": "llm_a",
                    "llm_model": "model-a",
                    "total_tool_calls": 3,
                },
            },
            "run_paths": {
                "result_json_path": f"logs/{task_id}/result.json",
                "trace_json_path": f"logs/{task_id}/trace.json",
                "summary_md_path": f"logs/{task_id}/summary.md",
            },
        }

    output = run_multi_model_eval.run_multi_model_eval(
        repo_root=repo_root,
        manifest_path=manifest_path,
        policy_paths=[policy_dir / "llm_a.json"],
        output_dir=repo_root / "logs" / "summaries",
        resume_from=resume_path,
        agent_runner=fake_runner,
    )

    summary = output["summary"]
    assert calls == ["task_002"]
    assert summary["record_count"] == 2
    assert summary["completed_count"] == 2
    assert summary["success_count"] == 2
    assert summary["policy_summaries"][0]["success_rate"] == 1.0

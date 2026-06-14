from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import run_challenge_eval


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_run_challenge_eval_pipeline_orchestrates_batch_and_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks_challenge_v1.json"
    tasks_dir = repo_root / "benchmarks" / "tasks"
    policy_path = repo_root / "optimization" / "policy_versions" / "improved_v69.json"

    write_json(
        manifest_path,
        {
            "manifest_id": "real_issue_tasks_challenge_v1",
            "description": "demo",
            "tasks": ["benchmarks/tasks/task_126.json"],
        },
    )
    write_json(
        tasks_dir / "task_126.json",
        {
            "task_id": "task_126",
            "source_type": "semi_real",
            "metadata": {"candidate_id": "c126"},
        },
    )

    batch_calls: dict[str, object] = {}
    eval_calls: dict[str, object] = {}

    def fake_run_batch(*, repo_root: Path, task_paths: list[Path], policy_path: Path, run_label: str) -> dict:
        batch_calls["repo_root"] = repo_root
        batch_calls["task_paths"] = task_paths
        batch_calls["policy_path"] = policy_path
        batch_calls["run_label"] = run_label
        return {
            "summary_json_path": str(repo_root / "logs" / "summaries" / "batch_run_challengev69_001.json"),
            "summary_md_path": str(repo_root / "logs" / "summaries" / "batch_run_challengev69_001.md"),
            "batch_summary": {
                "batch_run_id": "batch_run_challengev69_001",
                "tasks": [{"task_id": "task_126", "final_status": "success"}],
            },
        }

    def fake_run_batch_eval(*, batch_summary_path: Path, output_dir: Path, run_label: str) -> dict:
        eval_calls["batch_summary_path"] = batch_summary_path
        eval_calls["output_dir"] = output_dir
        eval_calls["run_label"] = run_label
        return {
            "eval_id": "batch_eval_challengev69_001",
            "summary_json_path": str(output_dir / "batch_eval_challengev69_001.json"),
            "summary_md_path": str(output_dir / "batch_eval_challengev69_001.md"),
            "eval_summary": {"policy_id": "improved_v69"},
        }

    def fake_maturity(**_: object) -> dict:
        return {
            "summary_json_path": str(repo_root / "logs" / "summaries" / "benchmark_maturity_demo.json"),
            "summary": {
                "goal_gaps": {
                    "formal_task_goal": {"actual": 64, "target": 60, "met": True},
                    "ecosystem_goal": {"actual": 16, "target": 6, "met": True},
                    "frozen_goal": {"actual": 40, "target": 40, "met": True},
                    "frozen_40_streak_goal": {"actual": 8, "target": 5, "met": True},
                },
                "challenge_manifest": {"task_count": 1},
            },
        }

    monkeypatch.setattr(run_challenge_eval, "run_batch", fake_run_batch)
    monkeypatch.setattr(run_challenge_eval, "run_batch_eval", fake_run_batch_eval)
    monkeypatch.setattr(run_challenge_eval, "analyze_benchmark_maturity", fake_maturity)

    output = run_challenge_eval.run_challenge_eval_pipeline(
        repo_root=repo_root,
        manifest_path=manifest_path,
        tasks_dir=tasks_dir,
        policy_path=policy_path,
        run_label="challengev69",
    )

    assert batch_calls["run_label"] == "challengev69"
    assert len(batch_calls["task_paths"]) == 1
    assert eval_calls["run_label"] == "challengev69"
    assert output["challenge_summary"]["task_count"] == 1
    assert output["maturity_output"]["summary"]["challenge_manifest"]["task_count"] == 1

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_benchmark_maturity


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_task(
    task_dir: Path,
    *,
    task_id: str,
    repo_full_name: str,
    issue_title: str,
    source_type: str = "semi_real",
) -> Path:
    task_path = task_dir / f"{task_id}.json"
    write_json(
        task_path,
        {
            "task_id": task_id,
            "repo_name": repo_full_name.split("/")[-1],
            "repo_path": f"benchmarks/repos/{task_id}",
            "issue_title": issue_title,
            "issue_text": issue_title,
            "test_command": "python -m pytest -q",
            "success_criteria": "demo",
            "difficulty": "medium",
            "tags": ["bugfix", "python", "semi-real"],
            "target_files_hint": [],
            "expected_failure_test": None,
            "max_retries": 2,
            "source_type": source_type,
            "metadata": {
                "repo_full_name": repo_full_name,
            },
        },
    )
    return task_path


def make_eval_summary(
    summary_dir: Path,
    *,
    frozen_count: int,
    policy_version: int,
    success_rate: float,
    test_pass_rate: float,
    average_duration_sec: float,
) -> Path:
    path = summary_dir / f"batch_eval_frozen{frozen_count}v{policy_version}_001.json"
    write_json(
        path,
        {
            "source_batch_run_id": f"batch_run_frozen{frozen_count}v{policy_version}_001",
            "policy_id": f"improved_v{policy_version}",
            "metrics": {
                "success_rate": success_rate,
                "test_pass_rate": test_pass_rate,
                "average_duration_sec": average_duration_sec,
            },
        },
    )
    return path


def test_evaluate_frozen_streak_requires_baseline_eval() -> None:
    summary = analyze_benchmark_maturity.evaluate_frozen_streak(
        eval_records={40: {33: {"policy_id": "improved_v33", "average_duration_sec": 0.5, "success_rate": 1.0, "test_pass_rate": 1.0}}},
        frozen_count=40,
    )

    assert summary["baseline_eval_present"] is False
    assert summary["meets_target"] is False
    assert "improved_v32" in summary["reason"]


def test_evaluate_frozen_streak_finds_longest_consecutive_run() -> None:
    eval_records = {
        40: {
            32: {"policy_id": "improved_v32", "average_duration_sec": 1.0, "success_rate": 1.0, "test_pass_rate": 1.0},
            33: {"policy_id": "improved_v33", "average_duration_sec": 1.01, "success_rate": 1.0, "test_pass_rate": 1.0},
            34: {"policy_id": "improved_v34", "average_duration_sec": 1.02, "success_rate": 0.96, "test_pass_rate": 0.96},
            35: {"policy_id": "improved_v35", "average_duration_sec": 1.05, "success_rate": 1.0, "test_pass_rate": 1.0},
            36: {"policy_id": "improved_v36", "average_duration_sec": 1.0, "success_rate": 1.0, "test_pass_rate": 1.0},
            37: {"policy_id": "improved_v37", "average_duration_sec": 1.01, "success_rate": 1.0, "test_pass_rate": 1.0},
            38: {"policy_id": "improved_v38", "average_duration_sec": 1.02, "success_rate": 1.0, "test_pass_rate": 1.0},
            39: {"policy_id": "improved_v39", "average_duration_sec": 1.03, "success_rate": 1.0, "test_pass_rate": 1.0},
            40: {"policy_id": "improved_v40", "average_duration_sec": 1.02, "success_rate": 1.0, "test_pass_rate": 1.0},
        }
    }

    summary = analyze_benchmark_maturity.evaluate_frozen_streak(
        eval_records=eval_records,
        frozen_count=40,
    )

    assert summary["baseline_eval_present"] is True
    assert summary["duration_threshold_sec"] == 1.03
    assert summary["longest_streak_versions"] == [36, 37, 38, 39, 40]
    assert summary["longest_streak_length"] == 5
    assert summary["meets_target"] is True


def test_analyze_benchmark_maturity_builds_goal_gap_snapshot(tmp_path: Path) -> None:
    repo_root = tmp_path
    manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks.json"
    challenge_manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks_challenge_v1.json"
    task_dir = repo_root / "benchmarks" / "tasks"
    summary_dir = repo_root / "logs" / "summaries"
    candidate_file = repo_root / "benchmarks" / "real_world_candidates.json"

    task_paths = [
        make_task(task_dir, task_id="task_101", repo_full_name="pytest-dev/pytest", issue_title="A"),
        make_task(task_dir, task_id="task_102", repo_full_name="pypa/packaging", issue_title="B"),
        make_task(task_dir, task_id="task_103", repo_full_name="python-jsonschema/jsonschema", issue_title="C"),
    ]
    write_json(
        manifest_path,
        {
            "manifest_id": "real_issue_tasks_v1",
            "description": "demo",
            "tasks": [str(path.relative_to(repo_root)).replace("\\", "/") for path in task_paths],
        },
    )
    write_json(
        challenge_manifest_path,
        {
            "manifest_id": "real_issue_tasks_challenge_v1",
            "description": "challenge",
            "tasks": [str(task_paths[0].relative_to(repo_root)).replace("\\", "/")],
        },
    )
    frozen_manifest_tasks = [str(task_paths[index % len(task_paths)].relative_to(repo_root)).replace("\\", "/") for index in range(20)]
    write_json(
        repo_root / "benchmarks" / "manifests" / "real_issue_tasks_frozen_20_v1.json",
        {
            "manifest_id": "real_issue_tasks_frozen_20_v1",
            "description": "demo",
            "tasks": frozen_manifest_tasks,
        },
    )
    write_json(
        candidate_file,
        {
            "dataset_id": "demo",
            "description": "demo",
            "selection_criteria": [],
            "candidates": [
                {"candidate_id": "c1", "repo_full_name": "pytest-dev/pytest", "status": "accepted"},
                {"candidate_id": "c2", "repo_full_name": "pypa/packaging", "status": "accepted"},
                {"candidate_id": "c3", "repo_full_name": "python-jsonschema/jsonschema", "status": "drafted"},
            ],
        },
    )
    make_eval_summary(
        summary_dir,
        frozen_count=40,
        policy_version=32,
        success_rate=1.0,
        test_pass_rate=1.0,
        average_duration_sec=1.0,
    )
    make_eval_summary(
        summary_dir,
        frozen_count=40,
        policy_version=33,
        success_rate=1.0,
        test_pass_rate=1.0,
        average_duration_sec=1.01,
    )
    make_eval_summary(
        summary_dir,
        frozen_count=40,
        policy_version=34,
        success_rate=1.0,
        test_pass_rate=1.0,
        average_duration_sec=1.02,
    )

    output = analyze_benchmark_maturity.analyze_benchmark_maturity(
        repo_root=repo_root,
        formal_manifest=manifest_path,
        challenge_manifest=challenge_manifest_path,
        candidate_file=candidate_file,
        output_dir=summary_dir,
        run_label="demo",
    )

    summary = output["summary"]
    assert summary["formal_manifest"]["task_count"] == 3
    assert summary["challenge_manifest"]["task_count"] == 1
    assert summary["formal_manifest"]["ecosystem_count"] == 3
    assert summary["goal_gaps"]["formal_task_goal"]["gap"] == 57
    assert summary["goal_gaps"]["ecosystem_goal"]["gap"] == 3
    assert summary["goal_gaps"]["frozen_goal"]["gap"] == 20
    assert summary["frozen_40_streak"]["longest_streak_versions"] == [32, 33, 34]
    assert summary["goal_gaps"]["frozen_40_streak_goal"]["gap"] == 2
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()

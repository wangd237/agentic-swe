from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import run_real_issue_eval as real_issue_eval


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_find_candidate_by_issue_returns_matching_candidate() -> None:
    dataset = {
        "candidates": [
            {
                "candidate_id": "demo",
                "repo_full_name": "example/repo",
                "issue_number": 12,
                "status": "accepted",
            }
        ]
    }

    candidate = real_issue_eval.find_candidate_by_issue(dataset, "example/repo", 12)

    assert candidate is not None
    assert candidate["candidate_id"] == "demo"


def test_summarize_candidate_statuses_groups_counts() -> None:
    dataset = {
        "candidates": [
            {"status": "accepted"},
            {"status": "accepted"},
            {"status": "drafted"},
        ]
    }

    summary = real_issue_eval.summarize_candidate_statuses(dataset)

    assert summary == {"accepted": 2, "drafted": 1}


def test_summarize_manifest_tasks_counts_source_types(tmp_path: Path) -> None:
    task_dir = tmp_path / "benchmarks" / "tasks"
    write_json(task_dir / "task_001.json", {"task_id": "task_001", "source_type": "semi_real"})
    write_json(task_dir / "task_002.json", {"task_id": "task_002", "source_type": "real_issue"})
    write_json(task_dir / "task_003.json", {"task_id": "task_003", "source_type": "synthetic"})

    summary = real_issue_eval.summarize_manifest_tasks(
        [
            task_dir / "task_001.json",
            task_dir / "task_002.json",
            task_dir / "task_003.json",
        ]
    )

    assert summary["task_count"] == 3
    assert summary["semi_real_count"] == 1
    assert summary["real_issue_count"] == 1
    assert summary["synthetic_count"] == 1


def test_run_real_issue_eval_pipeline_orchestrates_batch_eval_and_compare(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repo_root = tmp_path
    manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks.json"
    tasks_dir = repo_root / "benchmarks" / "tasks"
    candidate_file = repo_root / "benchmarks" / "real_world_candidates.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "improved_v9.json"
    baseline_eval = repo_root / "logs" / "summaries" / "batch_eval_realissuev8_001.json"

    write_json(
        manifest_path,
        {
            "manifest_id": "real_issue_tasks_v1",
            "description": "demo",
            "tasks": ["benchmarks/tasks/task_101.json", "benchmarks/tasks/task_102.json"],
        },
    )
    write_json(tasks_dir / "task_101.json", {"task_id": "task_101", "source_type": "semi_real"})
    write_json(tasks_dir / "task_102.json", {"task_id": "task_102", "source_type": "semi_real"})
    write_json(
        candidate_file,
        {
            "dataset_id": "demo",
            "description": "demo",
            "selection_criteria": [],
            "candidates": [
                {"candidate_id": "c1", "status": "accepted"},
                {"candidate_id": "c2", "status": "drafted"},
            ],
        },
    )
    write_json(baseline_eval, {"metrics": {}, "taxonomy": {}})

    batch_calls: dict[str, object] = {}
    eval_calls: dict[str, object] = {}
    compare_calls: dict[str, object] = {}

    def fake_run_batch(*, repo_root: Path, task_paths: list[Path], policy_path: Path, run_label: str) -> dict:
        batch_calls["repo_root"] = repo_root
        batch_calls["task_paths"] = task_paths
        batch_calls["policy_path"] = policy_path
        batch_calls["run_label"] = run_label
        return {
            "summary_json_path": str(repo_root / "logs" / "summaries" / "batch_run_realissuev9_001.json"),
            "summary_md_path": str(repo_root / "logs" / "summaries" / "batch_run_realissuev9_001.md"),
            "batch_summary": {"batch_run_id": "batch_run_realissuev9_001"},
        }

    def fake_run_batch_eval(*, batch_summary_path: Path, output_dir: Path, run_label: str) -> dict:
        eval_calls["batch_summary_path"] = batch_summary_path
        eval_calls["output_dir"] = output_dir
        eval_calls["run_label"] = run_label
        return {
            "eval_id": "batch_eval_realissuev9_001",
            "summary_json_path": str(output_dir / "batch_eval_realissuev9_001.json"),
            "summary_md_path": str(output_dir / "batch_eval_realissuev9_001.md"),
            "eval_summary": {"source_batch_run_id": "batch_run_realissuev9_001"},
        }

    def fake_compare(
        *,
        baseline_eval_path: Path,
        improved_eval_path: Path,
        output_dir: Path,
        run_label: str,
    ) -> dict:
        compare_calls["baseline_eval_path"] = baseline_eval_path
        compare_calls["improved_eval_path"] = improved_eval_path
        compare_calls["output_dir"] = output_dir
        compare_calls["run_label"] = run_label
        return {
            "compare_id": "batch_compare_realissue_step7_001",
            "summary_json_path": str(output_dir / "batch_compare_realissue_step7_001.json"),
            "summary_md_path": str(output_dir / "batch_compare_realissue_step7_001.md"),
            "compare_summary": {},
        }

    monkeypatch.setattr(real_issue_eval, "run_batch", fake_run_batch)
    monkeypatch.setattr(real_issue_eval, "run_batch_eval", fake_run_batch_eval)
    monkeypatch.setattr(real_issue_eval, "compare_eval_summaries", fake_compare)

    output = real_issue_eval.run_real_issue_eval_pipeline(
        repo_root=repo_root,
        manifest_path=manifest_path,
        tasks_dir=tasks_dir,
        candidate_file=candidate_file,
        policy_path=policy_path,
        run_label="realissuev9",
        compare_against_eval=baseline_eval,
        compare_label="realissue_step7",
    )

    assert batch_calls["run_label"] == "realissuev9"
    assert batch_calls["policy_path"] == policy_path
    assert len(batch_calls["task_paths"]) == 2
    assert eval_calls["run_label"] == "realissuev9"
    assert compare_calls["run_label"] == "realissue_step7"
    assert output["task_summary"]["semi_real_count"] == 2
    assert output["candidate_status_summary"] == {"accepted": 1, "drafted": 1}
    assert output["compare_output"]["compare_id"] == "batch_compare_realissue_step7_001"

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import audit_semi_real_pipeline


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_semi_real_pipeline_audit_identifies_ready_not_in_manifest(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    candidate_file = repo_root / "benchmarks" / "real_world_candidates.json"
    tasks_dir = repo_root / "benchmarks" / "tasks"
    manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks.json"
    challenge_manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks_challenge_v1.json"

    write_json(
        candidate_file,
        {
            "candidates": [
                {
                    "candidate_id": "ready_candidate",
                    "repo_full_name": "demo/repo",
                    "issue_number": 1,
                    "issue_title": "ready",
                    "status": "accepted",
                },
                {
                    "candidate_id": "formal_candidate",
                    "repo_full_name": "demo/repo",
                    "issue_number": 2,
                    "issue_title": "formal",
                    "status": "accepted",
                },
                {
                    "candidate_id": "screened_candidate",
                    "repo_full_name": "demo/repo",
                    "issue_number": 3,
                    "issue_title": "screened",
                    "status": "screened",
                },
                {
                    "candidate_id": "ready_no_manifest_candidate",
                    "repo_full_name": "demo/repo",
                    "issue_number": 4,
                    "issue_title": "ready-no-manifest",
                    "status": "accepted",
                },
            ]
        },
    )
    write_json(
        tasks_dir / "task_126.json",
        {
            "task_id": "task_126",
            "source_type": "semi_real",
            "repo_path": "benchmarks/repos/ready_repo",
            "issue_title": "ready",
            "metadata": {
                "candidate_id": "ready_candidate",
                "repo_scaffold_status": "ready",
                "ready_note": "ready but not formal",
            },
        },
    )
    write_json(
        tasks_dir / "task_125.json",
        {
            "task_id": "task_125",
            "source_type": "semi_real",
            "repo_path": "benchmarks/repos/formal_repo",
            "issue_title": "formal",
            "metadata": {
                "candidate_id": "formal_candidate",
                "repo_scaffold_status": "ready",
            },
        },
    )
    write_json(
        tasks_dir / "task_127.json",
        {
            "task_id": "task_127",
            "source_type": "semi_real",
            "repo_path": "benchmarks/repos/ready_no_manifest_repo",
            "issue_title": "ready-no-manifest",
            "metadata": {
                "candidate_id": "ready_no_manifest_candidate",
                "repo_scaffold_status": "ready",
                "ready_note": "ready but not in any manifest",
            },
        },
    )
    write_json(
        manifest_path,
        {
            "manifest_id": "real_issue_tasks_v1",
            "tasks": ["benchmarks/tasks/task_125.json"],
        },
    )
    write_json(
        challenge_manifest_path,
        {
            "manifest_id": "real_issue_tasks_challenge_v1",
            "tasks": ["benchmarks/tasks/task_126.json"],
        },
    )

    monkeypatch.setattr(audit_semi_real_pipeline, "REPO_ROOT", repo_root)
    summary = audit_semi_real_pipeline.build_semi_real_pipeline_audit(
        repo_root=repo_root,
        candidate_file=candidate_file,
        tasks_dir=tasks_dir,
        formal_manifest_path=manifest_path,
        challenge_manifest_path=challenge_manifest_path,
    )

    assert summary["candidate_status_counts"]["accepted"] == 3
    assert summary["candidate_status_counts"]["screened"] == 1
    assert summary["stage_counts"]["accepted_in_challenge_manifest"] == 1
    assert summary["stage_counts"]["accepted_in_formal_manifest"] == 1
    assert summary["stage_counts"]["accepted_ready_not_in_any_manifest"] == 1
    assert summary["stage_counts"]["screened_without_task"] == 1
    assert summary["accepted_in_challenge_manifest"][0]["candidate_id"] == "ready_candidate"
    assert summary["accepted_ready_not_in_any_manifest"][0]["candidate_id"] == "ready_no_manifest_candidate"


def test_audit_semi_real_pipeline_writes_output_files(tmp_path: Path, monkeypatch) -> None:
    def fake_build(**_: object) -> dict:
        return {
            "created_at": "2026-06-13T12:00:00+00:00",
            "candidate_file": str(tmp_path / "candidates.json"),
            "tasks_dir": str(tmp_path / "tasks"),
            "formal_manifest_path": str(tmp_path / "manifest.json"),
            "challenge_manifest_path": str(tmp_path / "challenge_manifest.json"),
            "candidate_count": 3,
            "formal_candidate_count": 2,
            "challenge_candidate_count": 1,
            "candidate_status_counts": {"accepted": 2, "screened": 1},
            "stage_counts": {"accepted_in_challenge_manifest": 1},
            "accepted_in_challenge_manifest": [
                {"candidate_id": "ready_candidate", "task_id": "task_126", "repo_scaffold_status": "ready", "in_formal_manifest": False}
            ],
            "accepted_ready_not_in_any_manifest": [],
            "screened_candidates": [],
            "records": [],
        }

    monkeypatch.setattr(audit_semi_real_pipeline, "build_semi_real_pipeline_audit", fake_build)

    output = audit_semi_real_pipeline.audit_semi_real_pipeline(
        candidate_file=tmp_path / "benchmarks" / "real_world_candidates.json",
        tasks_dir=tmp_path / "benchmarks" / "tasks",
        formal_manifest=tmp_path / "benchmarks" / "manifests" / "real_issue_tasks.json",
        challenge_manifest=tmp_path / "benchmarks" / "manifests" / "real_issue_tasks_challenge_v1.json",
        output_dir=tmp_path / "logs" / "summaries",
        run_label="demo",
    )

    assert output["analysis_id"] == "semi_real_pipeline_audit_demo_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()

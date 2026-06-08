from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import scaffold_semi_real_task as scaffold


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_repo_scaffold_creates_expected_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "benchmarks" / "repos" / "demo_repo"

    result = scaffold.build_repo_scaffold(
        repo_root=repo_root,
        module_path="demo_repo/utils.py",
        test_path="tests/test_utils.py",
    )

    assert result["module_file"] == "demo_repo/utils.py"
    assert (repo_root / "demo_repo" / "__init__.py").exists()
    assert (repo_root / "demo_repo" / "utils.py").read_text(encoding="utf-8")
    assert (repo_root / "tests" / "test_utils.py").exists()
    assert (repo_root / "README.md").exists()


def test_build_semi_real_task_marks_draft_status_when_not_ready(monkeypatch, tmp_path: Path) -> None:
    tasks_dir = tmp_path / "benchmarks" / "tasks"
    tasks_dir.mkdir(parents=True)
    monkeypatch.setattr(scaffold, "REPO_ROOT", tmp_path)

    draft_task = scaffold.Task.model_validate(
        {
            "task_id": "task_099",
            "repo_name": "requests",
            "repo_path": "benchmarks/repos/real_issue_repo_placeholder",
            "issue_title": "Quoted charset values are not detected",
            "issue_text": "Draft issue text",
            "test_command": "python -m pytest -q",
            "success_criteria": "draft",
            "difficulty": "medium",
            "tags": ["bugfix", "python", "real-issue", "draft"],
            "target_files_hint": [],
            "expected_failure_test": None,
            "max_retries": 2,
            "source_type": "real_issue",
            "metadata": {
                "candidate_id": "demo_candidate",
                "repo_url": "https://github.com/example/repo",
                "issue_url": "https://github.com/example/repo/issues/1",
            },
        }
    )

    payload = scaffold.build_semi_real_task(
        draft_task=draft_task,
        repo_name="demo_repo",
        repo_path="benchmarks/repos/demo_repo",
        module_path="demo_repo/utils.py",
        test_path="tests/test_utils.py",
        ready=False,
        success_criteria=None,
        expected_failure_test=None,
        extra_tags=["charset"],
    )

    assert payload["task_id"] == "task_001"
    assert payload["source_type"] == "semi_real"
    assert payload["expected_failure_test"] is None
    assert payload["test_command"] == "python -m pytest tests/test_utils.py -q"
    assert "semi-real" in payload["tags"]
    assert "draft" in payload["tags"]
    assert payload["metadata"]["draft_status"] == "needs_manual_completion"
    assert payload["metadata"]["derived_from_task"] == "task_099"


def test_append_task_to_manifest_is_idempotent(tmp_path: Path) -> None:
    manifest_path = tmp_path / "benchmarks" / "manifests" / "real_issue_tasks.json"
    task_path = tmp_path / "benchmarks" / "tasks" / "task_010.json"
    write_json(
        manifest_path,
        {
            "manifest_id": "real_issue_tasks_v1",
            "description": "test",
            "tasks": ["benchmarks/tasks/task_009.json"],
        },
    )
    write_json(task_path, {"task_id": "task_010"})

    original_root = scaffold.REPO_ROOT
    scaffold.REPO_ROOT = tmp_path
    try:
        scaffold.append_task_to_manifest(manifest_path, task_path)
        scaffold.append_task_to_manifest(manifest_path, task_path)
    finally:
        scaffold.REPO_ROOT = original_root

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["tasks"] == [
        "benchmarks/tasks/task_009.json",
        "benchmarks/tasks/task_010.json",
    ]


def test_update_candidate_status_appends_notes(tmp_path: Path) -> None:
    candidate_path = tmp_path / "benchmarks" / "real_world_candidates.json"
    write_json(
        candidate_path,
        {
            "dataset_id": "demo",
            "description": "demo",
            "selection_criteria": [],
            "candidates": [
                {
                    "candidate_id": "demo_candidate",
                    "repo_full_name": "example/repo",
                    "repo_url": "https://github.com/example/repo",
                    "issue_number": 1,
                    "issue_title": "demo",
                    "issue_url": "https://github.com/example/repo/issues/1",
                    "language": "python",
                    "difficulty": "medium",
                    "status": "drafted",
                    "notes": "已有记录",
                }
            ],
        },
    )

    scaffold.update_candidate_status(
        candidate_path=candidate_path,
        candidate_id="demo_candidate",
        status="scaffolded",
        note="已生成 semi_real 脚手架 task_010。",
    )

    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate = payload["candidates"][0]
    assert candidate["status"] == "scaffolded"
    assert "已有记录" in candidate["notes"]
    assert "已生成 semi_real 脚手架 task_010。" in candidate["notes"]

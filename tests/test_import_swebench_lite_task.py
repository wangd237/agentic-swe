from __future__ import annotations

import json
from pathlib import Path

from app.schemas.task_schema import load_task
from scripts.import_swebench_lite_task import import_swebench_lite_task
from scripts.import_swebench_lite_task import REPO_ROOT


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_import_swebench_lite_task_from_local_json_without_clone(tmp_path: Path) -> None:
    dataset_path = tmp_path / "swe_lite.json"
    output_dir = tmp_path / "tasks"
    repos_dir = tmp_path / "repos"
    write_json(
        dataset_path,
        [
            {
                "instance_id": "demo__project-123",
                "repo": "demo/project",
                "base_commit": "abc123",
                "problem_statement": "Fix demo bug.",
                "hints_text": "Look at demo/app.py",
                "patch": (
                    "diff --git a/demo/app.py b/demo/app.py\n"
                    "--- a/demo/app.py\n"
                    "+++ b/demo/app.py\n"
                ),
                "test_patch": (
                    "diff --git a/tests/test_app.py b/tests/test_app.py\n"
                    "--- a/tests/test_app.py\n"
                    "+++ b/tests/test_app.py\n"
                ),
                "version": "1.0",
                "created_at": "2024-01-01T00:00:00Z",
                "FAIL_TO_PASS": ["tests/test_app.py::test_demo"],
                "PASS_TO_PASS": [],
            }
        ],
    )

    result = import_swebench_lite_task(
        dataset_path=dataset_path,
        output_dir=output_dir,
        repos_dir=repos_dir,
        artifacts_dir=tmp_path / "artifacts",
        clone=False,
    )

    task_path = Path(result["task_path"])
    task = load_task(task_path)
    artifacts_dir = tmp_path / "artifacts" / "demo_project_123"

    assert result["instance_id"] == "demo__project-123"
    assert result["cloned"] is False
    assert task.task_id == "swe_lite_demo_project_123"
    assert task.source_type == "swe_bench_lite"
    expected_repo_path = (repos_dir / "demo_project_123").resolve().relative_to(REPO_ROOT).as_posix()
    assert task.repo_path == expected_repo_path
    assert task.test_command == "python -m pytest -q tests/test_app.py::test_demo"
    assert task.target_files_hint == ["demo/app.py"]
    assert task.metadata["swebench_instance_id"] == "demo__project-123"
    assert task.metadata["fail_to_pass"] == ["tests/test_app.py::test_demo"]
    assert task.metadata["official_harness_required"] is True
    assert "Hints from SWE-bench" in task.issue_text
    assert (artifacts_dir / "instance.json").exists()
    assert (artifacts_dir / "gold.patch").read_text(encoding="utf-8").startswith("diff --git")
    assert (artifacts_dir / "test.patch").exists()

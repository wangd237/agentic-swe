from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.export_swebench_prediction import build_prediction_row
from scripts.export_swebench_prediction import write_prediction_jsonl


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def task_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "task_id": "swe_lite_demo_project_123",
        "repo_name": "demo_project",
        "repo_path": "benchmarks/repos/swebench_lite/demo_project_123",
        "issue_title": "SWE-bench Lite: demo__project-123",
        "issue_text": "Fix demo bug.",
        "test_command": "python -m pytest -q tests/test_demo.py::test_bug",
        "success_criteria": "Lightweight smoke.",
        "difficulty": "medium",
        "tags": ["swe-bench", "swe-bench-lite"],
        "target_files_hint": ["demo.py"],
        "source_type": "swe_bench_lite",
        "metadata": {"swebench_instance_id": "demo__project-123"},
    }
    payload.update(overrides)
    return payload


def test_build_prediction_row_from_run_patch(tmp_path: Path) -> None:
    task_path = tmp_path / "task.json"
    run_dir = tmp_path / "run"
    patch_text = "diff --git a/demo.py b/demo.py\n--- a/demo.py\n+++ b/demo.py\n"
    write_json(task_path, task_payload())
    run_dir.mkdir()
    (run_dir / "patch.diff").write_text(patch_text, encoding="utf-8")

    row = build_prediction_row(
        task_path=task_path,
        run_dir=run_dir,
        model_name_or_path="local-agent",
    )

    assert row == {
        "instance_id": "demo__project-123",
        "model_name_or_path": "local-agent",
        "model_patch": patch_text,
    }


def test_write_prediction_jsonl_writes_single_row(tmp_path: Path) -> None:
    output = tmp_path / "predictions.jsonl"
    row = {
        "instance_id": "demo__project-123",
        "model_name_or_path": "local-agent",
        "model_patch": "diff --git a/demo.py b/demo.py\n",
    }

    write_prediction_jsonl(row, output)

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows == [row]


def test_build_prediction_row_rejects_non_swebench_task(tmp_path: Path) -> None:
    task_path = tmp_path / "task.json"
    run_dir = tmp_path / "run"
    write_json(task_path, task_payload(source_type="synthetic", metadata={}))
    run_dir.mkdir()
    (run_dir / "patch.diff").write_text("diff --git a/demo.py b/demo.py\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="不是 SWE-bench Lite"):
        build_prediction_row(
            task_path=task_path,
            run_dir=run_dir,
            model_name_or_path="local-agent",
        )


def test_build_prediction_row_rejects_empty_patch(tmp_path: Path) -> None:
    task_path = tmp_path / "task.json"
    run_dir = tmp_path / "run"
    write_json(task_path, task_payload())
    run_dir.mkdir()
    (run_dir / "patch.diff").write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError, match="patch.diff 为空"):
        build_prediction_row(
            task_path=task_path,
            run_dir=run_dir,
            model_name_or_path="local-agent",
        )

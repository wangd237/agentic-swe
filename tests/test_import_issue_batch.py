from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import import_issue_batch


def write_json(path: Path, payload: dict | list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_load_batch_entries_supports_text_file(tmp_path: Path) -> None:
    input_path = tmp_path / "issues.txt"
    input_path.write_text(
        "# comment\npsf/requests 6432\nTextualize/rich #4090\n",
        encoding="utf-8",
    )

    entries = import_issue_batch.load_batch_entries(input_path)

    assert entries == [
        {
            "repo": "psf/requests",
            "issue": 6432,
            "draft_task": False,
            "repo_path": None,
            "test_command": None,
            "candidate_overrides": None,
        },
        {
            "repo": "Textualize/rich",
            "issue": 4090,
            "draft_task": False,
            "repo_path": None,
            "test_command": None,
            "candidate_overrides": None,
        },
    ]


def test_load_batch_entries_supports_json_file(tmp_path: Path) -> None:
    input_path = tmp_path / "issues.json"
    write_json(
        input_path,
        {
            "issues": [
                {
                    "repo": "psf/requests",
                    "issue": "#6432",
                    "draft_task": True,
                    "repo_path": "benchmarks/repos/demo",
                    "test_command": "python -m pytest tests/test_demo.py -q",
                    "why_it_fits": "边界清晰，适合缩成小型 benchmark。",
                    "expected_target_files": ["demo/utils.py", "tests/test_demo.py"],
                    "expected_test_shape": "补 1 到 2 个回归测试。",
                    "risk_notes": "low",
                    "recommendation": "high",
                }
            ]
        },
    )

    entries = import_issue_batch.load_batch_entries(input_path)

    assert entries == [
        {
            "repo": "psf/requests",
            "issue": 6432,
            "draft_task": True,
            "repo_path": "benchmarks/repos/demo",
            "test_command": "python -m pytest tests/test_demo.py -q",
            "candidate_overrides": {
                "why_it_fits": "边界清晰，适合缩成小型 benchmark。",
                "expected_target_files": ["demo/utils.py", "tests/test_demo.py"],
                "expected_test_shape": "补 1 到 2 个回归测试。",
                "risk_notes": "low",
                "recommendation": "high",
            },
        }
    ]


def test_import_issue_batch_aggregates_created_updated_and_draft_task_count(monkeypatch, tmp_path: Path) -> None:
    input_path = tmp_path / "issues.txt"
    input_path.write_text("psf/requests 6432\nTextualize/rich 4090\n", encoding="utf-8")
    candidate_file = tmp_path / "benchmarks" / "real_world_candidates.json"
    write_json(candidate_file, {"candidates": []})

    imported_calls: list[tuple[str, int]] = []
    drafted_calls: list[str] = []

    imported_overrides: list[dict | None] = []

    def fake_import_issue_to_dataset(
        *,
        repo_full_name: str,
        issue_number: int,
        dataset_path: Path,
        candidate_overrides: dict | None,
    ) -> dict:
        imported_calls.append((repo_full_name, issue_number))
        imported_overrides.append(candidate_overrides)
        return {
            "candidate": {
                "candidate_id": f"{repo_full_name.replace('/', '_')}_{issue_number}",
                "status": "imported",
            },
            "operation": "created" if issue_number == 6432 else "updated",
        }

    def fake_draft_task_for_candidate(
        *,
        candidate: dict,
        candidate_path: Path,
        repo_path: str,
        test_command: str,
    ) -> dict:
        drafted_calls.append(candidate["candidate_id"])
        return {
            "task_payload": {"task_id": f"task_for_{candidate['candidate_id']}"},
            "task_path": tmp_path / f"{candidate['candidate_id']}.json",
        }

    monkeypatch.setattr(
        import_issue_batch.import_github_issue,
        "import_issue_to_dataset",
        fake_import_issue_to_dataset,
    )
    monkeypatch.setattr(
        import_issue_batch.import_github_issue,
        "draft_task_for_candidate",
        fake_draft_task_for_candidate,
    )

    output = import_issue_batch.import_issue_batch(
        input_path=input_path,
        candidate_file=candidate_file,
        draft_task=True,
        repo_path="benchmarks/repos/placeholder",
        test_command="python -m pytest -q",
    )

    assert imported_calls == [("psf/requests", 6432), ("Textualize/rich", 4090)]
    assert imported_overrides == [None, None]
    assert drafted_calls == ["psf_requests_6432", "Textualize_rich_4090"]
    assert output["total_count"] == 2
    assert output["created_count"] == 1
    assert output["updated_count"] == 1
    assert output["draft_task_count"] == 2
    assert output["results"][0]["candidate_status"] == "imported"


def test_import_issue_to_dataset_applies_structured_overrides(tmp_path: Path) -> None:
    from scripts import import_github_issue

    candidate_file = tmp_path / "benchmarks" / "real_world_candidates.json"
    write_json(
        candidate_file,
        {
            "dataset_id": "demo",
            "description": "demo",
            "selection_criteria": [],
            "candidates": [],
        },
    )

    output = import_github_issue.import_issue_to_dataset(
        repo_full_name="pypa/packaging",
        issue_number=934,
        dataset_path=candidate_file,
        issue_payload={
            "number": 934,
            "title": "Marker version comparison fails when RHS variable is used",
            "body": "demo body",
            "url": "https://github.com/pypa/packaging/issues/934",
            "labels": [],
            "state": "OPEN",
            "createdAt": "2026-04-27T02:41:13Z",
            "repository_url": "https://github.com/pypa/packaging",
        },
        candidate_overrides={
            "status": "imported",
            "difficulty": "medium",
            "why_it_fits": "比较语义明确，适合缩成单模块任务。",
            "expected_target_files": ["packaging/markers.py", "tests/test_markers.py"],
            "expected_test_shape": "增加 1 到 2 个左右值互换的回归测试。",
            "risk_notes": "需要确认期望行为是否已由规范定义。",
            "recommendation": "high",
            "note": "由外部 issue 清单补充了筛选理由。",
        },
    )

    candidate = output["candidate"]
    assert candidate["status"] == "imported"
    assert candidate["difficulty"] == "medium"
    assert candidate["expected_target_files"] == ["packaging/markers.py", "tests/test_markers.py"]
    assert "why_it_fits: 比较语义明确，适合缩成单模块任务。" in candidate["notes"]
    assert "expected_test_shape: 增加 1 到 2 个左右值互换的回归测试。" in candidate["notes"]
    assert "risk_notes: 需要确认期望行为是否已由规范定义。" in candidate["notes"]
    assert "recommendation: high" in candidate["notes"]
    assert "由外部 issue 清单补充了筛选理由。" in candidate["notes"]


def test_load_batch_entries_supports_structured_candidate_overrides(tmp_path: Path) -> None:
    input_path = tmp_path / "issues.json"
    write_json(
        input_path,
        {
            "issues": [
                {
                    "repo": "pallets/click",
                    "issue": "#3362",
                    "why_it_fits": "适合做 usage 文本换行回归 benchmark。",
                    "expected_target_files": ["click/formatting.py", "tests/test_formatting.py"],
                    "expected_test_shape": "补 2 到 3 个固定宽度 usage 文本回归测试。",
                    "risk_notes": "low",
                    "recommendation": "high",
                }
            ]
        },
    )

    entries = import_issue_batch.load_batch_entries(input_path)

    assert entries[0]["candidate_overrides"] == {
        "why_it_fits": "适合做 usage 文本换行回归 benchmark。",
        "expected_target_files": ["click/formatting.py", "tests/test_formatting.py"],
        "expected_test_shape": "补 2 到 3 个固定宽度 usage 文本回归测试。",
        "risk_notes": "low",
        "recommendation": "high",
    }

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
        },
        {
            "repo": "Textualize/rich",
            "issue": 4090,
            "draft_task": False,
            "repo_path": None,
            "test_command": None,
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
        }
    ]


def test_import_issue_batch_aggregates_created_updated_and_drafted(monkeypatch, tmp_path: Path) -> None:
    input_path = tmp_path / "issues.txt"
    input_path.write_text("psf/requests 6432\nTextualize/rich 4090\n", encoding="utf-8")
    candidate_file = tmp_path / "benchmarks" / "real_world_candidates.json"
    write_json(candidate_file, {"candidates": []})

    imported_calls: list[tuple[str, int]] = []
    drafted_calls: list[str] = []

    def fake_import_issue_to_dataset(*, repo_full_name: str, issue_number: int, dataset_path: Path) -> dict:
        imported_calls.append((repo_full_name, issue_number))
        return {
            "candidate": {"candidate_id": f"{repo_full_name.replace('/', '_')}_{issue_number}"},
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
    assert drafted_calls == ["psf_requests_6432", "Textualize_rich_4090"]
    assert output["total_count"] == 2
    assert output["created_count"] == 1
    assert output["updated_count"] == 1
    assert output["drafted_count"] == 2

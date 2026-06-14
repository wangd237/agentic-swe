from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import screen_candidate


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_filter_candidates_by_status_returns_matching_candidates() -> None:
    payload = {
        "candidates": [
            {"candidate_id": "c1", "status": "imported"},
            {"candidate_id": "c2", "status": "accepted"},
            {"candidate_id": "c3", "status": "imported"},
        ]
    }

    matched = screen_candidate.filter_candidates_by_status(payload, ["imported"])

    assert [candidate["candidate_id"] for candidate in matched] == ["c1", "c3"]


def test_apply_screening_to_candidate_updates_status_and_notes() -> None:
    candidate = {
        "candidate_id": "c1",
        "status": "imported",
        "notes": "已有备注",
    }

    previous_status, next_status, note = screen_candidate.apply_screening_to_candidate(candidate, "y")

    assert previous_status == "imported"
    assert next_status == "screened"
    assert "人工筛选通过" in note
    assert candidate["status"] == "screened"
    assert "已有备注" in candidate["notes"]
    assert "人工筛选通过" in candidate["notes"]


def test_parse_status_filters_supports_repeated_and_csv_values() -> None:
    parsed = screen_candidate.parse_status_filters(["imported,screened", "blocked"])

    assert parsed == ["imported", "screened", "blocked"]


def test_set_candidate_status_updates_candidate_file(tmp_path: Path) -> None:
    candidate_path = tmp_path / "benchmarks" / "real_world_candidates.json"
    write_json(
        candidate_path,
        {
            "dataset_id": "demo",
            "description": "demo",
            "selection_criteria": [],
            "candidates": [
                {
                    "candidate_id": "c1",
                    "repo_full_name": "example/repo",
                    "repo_url": "https://github.com/example/repo",
                    "issue_number": 1,
                    "issue_title": "demo",
                    "issue_url": "https://github.com/example/repo/issues/1",
                    "language": "python",
                    "difficulty": "medium",
                    "status": "imported",
                    "notes": "已有备注",
                }
            ],
        },
    )

    screen_candidate.set_candidate_status(candidate_path, "c1", "screened", "人工复核通过。")

    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate = payload["candidates"][0]
    assert candidate["status"] == "screened"
    assert "人工复核通过。" in candidate["notes"]

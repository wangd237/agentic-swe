from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import import_search_results


def write_json(path: Path, payload: dict | list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_import_search_results_imports_and_filters_candidates(tmp_path: Path) -> None:
    search_result = tmp_path / "logs" / "summaries" / "candidate_search_demo_001.json"
    candidate_file = tmp_path / "benchmarks" / "real_world_candidates.json"
    write_json(
        search_result,
        {
            "candidates": [
                {
                    "repo": "Textualize/rich",
                    "issue_number": 2411,
                    "title": "UnicodeEncodeError on Windows with ruler",
                    "url": "https://github.com/Textualize/rich/issues/2411",
                    "labels": ["bug"],
                    "state": "closed",
                    "created_at": "2022-07-20T21:45:49Z",
                    "why_it_fits": "适合后续人工判题。",
                    "expected_target_files": ["rich/console.py"],
                    "expected_test_shape": "补 2 个稳定回归测试。",
                    "estimated_difficulty": "medium",
                    "risk_notes": "平台相关，需要人工确认。",
                    "recommendation": "high",
                    "body_excerpt": "demo body 1",
                },
                {
                    "repo": "Textualize/rich",
                    "issue_number": 3176,
                    "title": "Chunks of text go missing",
                    "url": "https://github.com/Textualize/rich/issues/3176",
                    "labels": ["bug"],
                    "state": "closed",
                    "created_at": "2023-10-30T15:41:51Z",
                    "why_it_fits": "可能不值得优先推进。",
                    "expected_target_files": [],
                    "expected_test_shape": "补 2 个输出断言。",
                    "estimated_difficulty": "medium",
                    "risk_notes": "需要人工确认。",
                    "recommendation": "low",
                    "body_excerpt": "demo body 2",
                },
            ]
        },
    )
    write_json(
        candidate_file,
        {
            "dataset_id": "demo",
            "description": "demo",
            "selection_criteria": [],
            "candidates": [],
        },
    )

    output = import_search_results.import_search_results(
        search_result_path=search_result,
        candidate_file=candidate_file,
        recommendation_filter=["high"],
        limit=None,
    )

    assert output["imported_count"] == 1
    assert output["created_count"] == 1
    assert output["updated_count"] == 0
    assert output["results"][0]["candidate_id"] == "Textualize_rich_issue_2411"

    payload = json.loads(candidate_file.read_text(encoding="utf-8"))
    assert len(payload["candidates"]) == 1
    candidate = payload["candidates"][0]
    assert candidate["status"] == "imported"
    assert candidate["issue_number"] == 2411
    assert candidate["expected_target_files"] == ["rich/console.py"]
    assert "why_it_fits: 适合后续人工判题。" in candidate["notes"]


def test_import_search_results_preserves_existing_status_on_update(tmp_path: Path) -> None:
    search_result = tmp_path / "logs" / "summaries" / "candidate_search_demo_002.json"
    candidate_file = tmp_path / "benchmarks" / "real_world_candidates.json"
    write_json(
        search_result,
        {
            "candidates": [
                {
                    "repo": "Textualize/rich",
                    "issue_number": 2411,
                    "title": "UnicodeEncodeError on Windows with ruler",
                    "url": "https://github.com/Textualize/rich/issues/2411",
                    "labels": ["bug"],
                    "state": "closed",
                    "created_at": "2022-07-20T21:45:49Z",
                    "why_it_fits": "适合后续人工判题。",
                    "expected_target_files": ["rich/console.py"],
                    "expected_test_shape": "补 2 个稳定回归测试。",
                    "estimated_difficulty": "medium",
                    "risk_notes": "平台相关，需要人工确认。",
                    "recommendation": "high",
                    "body_excerpt": "demo body 1",
                }
            ]
        },
    )
    write_json(
        candidate_file,
        {
            "dataset_id": "demo",
            "description": "demo",
            "selection_criteria": [],
            "candidates": [
                {
                    "candidate_id": "Textualize_rich_issue_2411",
                    "repo_full_name": "Textualize/rich",
                    "repo_url": "https://github.com/Textualize/rich",
                    "issue_number": 2411,
                    "issue_title": "old title",
                    "issue_url": "https://github.com/Textualize/rich/issues/2411",
                    "language": "python",
                    "difficulty": "medium",
                    "status": "screened",
                    "notes": "已有人工筛选记录",
                    "labels": ["bug"],
                    "state": "closed",
                    "created_at": "2022-07-20T21:45:49Z",
                    "body_excerpt": "old body",
                }
            ],
        },
    )

    output = import_search_results.import_search_results(
        search_result_path=search_result,
        candidate_file=candidate_file,
        recommendation_filter=[],
        limit=None,
    )

    assert output["imported_count"] == 1
    assert output["created_count"] == 0
    assert output["updated_count"] == 1

    payload = json.loads(candidate_file.read_text(encoding="utf-8"))
    candidate = payload["candidates"][0]
    assert candidate["status"] == "screened"
    assert "重新同步 GitHub issue 元数据。" in candidate["notes"]


def test_import_search_results_filters_by_issue_number(tmp_path: Path) -> None:
    search_result = tmp_path / "logs" / "summaries" / "candidate_search_demo_003.json"
    candidate_file = tmp_path / "benchmarks" / "real_world_candidates.json"
    write_json(
        search_result,
        {
            "candidates": [
                {
                    "repo": "agronholm/anyio",
                    "issue_number": 82,
                    "title": "CancelledError leak with asyncio and curio",
                    "url": "https://github.com/agronholm/anyio/issues/82",
                    "labels": ["bug"],
                    "state": "closed",
                    "created_at": "2019-11-21T17:31:10Z",
                    "why_it_fits": "适合后续人工判题。",
                    "expected_target_files": ["test_anyio.py"],
                    "expected_test_shape": "补 2 个稳定回归测试。",
                    "estimated_difficulty": "medium",
                    "risk_notes": "需要人工确认。",
                    "recommendation": "high",
                    "body_excerpt": "demo body 1",
                },
                {
                    "repo": "agronholm/anyio",
                    "issue_number": 88,
                    "title": "Parent task spuriously cancelled with asyncio",
                    "url": "https://github.com/agronholm/anyio/issues/88",
                    "labels": ["bug"],
                    "state": "closed",
                    "created_at": "2019-12-01T03:43:46Z",
                    "why_it_fits": "适合后续人工判题。",
                    "expected_target_files": ["fail_case.py"],
                    "expected_test_shape": "补 2 个稳定回归测试。",
                    "estimated_difficulty": "medium",
                    "risk_notes": "需要人工确认。",
                    "recommendation": "high",
                    "body_excerpt": "demo body 2",
                },
            ]
        },
    )
    write_json(
        candidate_file,
        {
            "dataset_id": "demo",
            "description": "demo",
            "selection_criteria": [],
            "candidates": [],
        },
    )

    output = import_search_results.import_search_results(
        search_result_path=search_result,
        candidate_file=candidate_file,
        recommendation_filter=[],
        issue_number_filter=[88],
        limit=None,
    )

    assert output["imported_count"] == 1
    assert output["results"][0]["issue_number"] == 88

    payload = json.loads(candidate_file.read_text(encoding="utf-8"))
    assert len(payload["candidates"]) == 1
    assert payload["candidates"][0]["issue_number"] == 88

from __future__ import annotations

import json
from pathlib import Path

from scripts import validate_challenge_shortlist


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_validate_challenge_shortlist_detects_formal_conflict(tmp_path: Path) -> None:
    repo_root = tmp_path
    shortlist_path = repo_root / "docs" / "challenge_shortlist.md"
    shortlist_path.parent.mkdir(parents=True, exist_ok=True)
    shortlist_path.write_text(
        "\n".join(
            [
                "# Challenge Shortlist",
                "",
                "## 下一条最值得补的 challenge 候选",
                "",
                "### 1. `example/repo#123`",
                "",
                "## 当前推荐推进顺序",
            ]
        ),
        encoding="utf-8",
    )

    task_path = repo_root / "benchmarks" / "tasks" / "task_001.json"
    _write_json(
        task_path,
        {
            "task_id": "task_001",
            "metadata": {
                "repo_full_name": "example/repo",
                "issue_number": 123,
                "issue_url": "https://github.com/example/repo/issues/123",
            },
        },
    )

    formal_manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks.json"
    _write_json(
        formal_manifest_path,
        {
            "manifest_id": "real_issue_tasks_v1",
            "tasks": ["benchmarks/tasks/task_001.json"],
        },
    )

    errors = validate_challenge_shortlist.validate_challenge_shortlist(
        repo_root=repo_root,
        shortlist_path=shortlist_path,
        formal_manifest_path=formal_manifest_path,
    )

    assert errors == [
        "challenge shortlist 候选与正式主集冲突：`example/repo#123` 已在正式 manifest，对应 `task_001`。"
    ]


def test_validate_challenge_shortlist_ignores_current_challenge_section_and_non_formal_refs(tmp_path: Path) -> None:
    repo_root = tmp_path
    shortlist_path = repo_root / "docs" / "challenge_shortlist.md"
    shortlist_path.parent.mkdir(parents=True, exist_ok=True)
    shortlist_path.write_text(
        "\n".join(
            [
                "# Challenge Shortlist",
                "",
                "## 当前已落地 challenge 题",
                "",
                "### `example/challenge#999`",
                "",
                "## 下一条最值得补的 challenge 候选",
                "",
                "当前本地 shortlist 暂时为空，需要重新 sourcing。",
                "",
                "原因：",
                "",
                "- `example/repo#123`，当前已在正式主集，对应 `task_001`",
                "",
                "## 当前推荐推进顺序",
            ]
        ),
        encoding="utf-8",
    )

    task_path = repo_root / "benchmarks" / "tasks" / "task_001.json"
    _write_json(
        task_path,
        {
            "task_id": "task_001",
            "metadata": {
                "repo_full_name": "example/repo",
                "issue_number": 123,
                "issue_url": "https://github.com/example/repo/issues/123",
            },
        },
    )

    formal_manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks.json"
    _write_json(
        formal_manifest_path,
        {
            "manifest_id": "real_issue_tasks_v1",
            "tasks": ["benchmarks/tasks/task_001.json"],
        },
    )

    errors = validate_challenge_shortlist.validate_challenge_shortlist(
        repo_root=repo_root,
        shortlist_path=shortlist_path,
        formal_manifest_path=formal_manifest_path,
    )

    assert errors == []


def test_extract_candidate_issue_refs_only_reads_candidate_heading_lines() -> None:
    shortlist_text = "\n".join(
        [
            "# Challenge Shortlist",
            "",
            "## 下一条最值得补的 challenge 候选",
            "",
            "### 1. `example/repo#123`",
            "",
            "- `example/repo#456`，当前已在正式主集，对应 `task_002`",
            "- `example/repo#789` 只是说明性引用",
            "",
            "## 当前推荐推进顺序",
        ]
    )

    assert validate_challenge_shortlist._extract_candidate_issue_refs(shortlist_text) == [
        ("example/repo", 123)
    ]


def test_summarize_challenge_shortlist_extracts_first_candidate_and_count(tmp_path: Path) -> None:
    shortlist_path = tmp_path / "docs" / "challenge_shortlist.md"
    shortlist_path.parent.mkdir(parents=True, exist_ok=True)
    shortlist_path.write_text(
        "\n".join(
            [
                "# Challenge Shortlist",
                "",
                "## 下一条最值得补的 challenge 候选",
                "",
                "### 1. `example/repo#123`",
                "",
                "### 2. `another/repo#456`",
                "",
                "## 当前推荐推进顺序",
            ]
        ),
        encoding="utf-8",
    )

    summary = validate_challenge_shortlist.summarize_challenge_shortlist(shortlist_path)

    assert summary == {
        "candidate_issue_refs": [("example/repo", 123), ("another/repo", 456)],
        "candidate_count": 2,
        "is_empty": False,
        "next_candidate": {
            "repo_full_name": "example/repo",
            "issue_number": 123,
            "issue_ref": "example/repo#123",
        },
        "filtered_existing_challenge_issue_refs": [],
    }


def test_extract_candidate_issue_refs_supports_current_candidate_section_heading() -> None:
    shortlist_text = "\n".join(
        [
            "# Challenge Shortlist",
            "",
            "## 当前最值得补的 challenge 候选",
            "",
            "### 1. `example/repo#123`",
            "",
            "## 当前推荐推进顺序",
        ]
    )

    assert validate_challenge_shortlist._extract_candidate_issue_refs(shortlist_text) == [
        ("example/repo", 123)
    ]


def test_extract_candidate_issue_refs_supports_unnumbered_heading_lines() -> None:
    shortlist_text = "\n".join(
        [
            "# Challenge Shortlist",
            "",
            "## 下一条最值得补的 challenge 候选",
            "",
            "### `example/repo#123`",
            "",
            "## 当前推荐推进顺序",
        ]
    )

    assert validate_challenge_shortlist._extract_candidate_issue_refs(shortlist_text) == [
        ("example/repo", 123)
    ]


def test_summarize_challenge_shortlist_filters_issues_already_in_challenge_manifest(tmp_path: Path) -> None:
    repo_root = tmp_path
    shortlist_path = repo_root / "docs" / "challenge_shortlist.md"
    shortlist_path.parent.mkdir(parents=True, exist_ok=True)
    shortlist_path.write_text(
        "\n".join(
            [
                "# Challenge Shortlist",
                "",
                "## 下一条最值得补的 challenge 候选",
                "",
                "### 1. `example/repo#123`",
                "",
                "### 2. `another/repo#456`",
                "",
                "## 当前推荐推进顺序",
            ]
        ),
        encoding="utf-8",
    )

    challenge_task_path = repo_root / "benchmarks" / "tasks" / "task_126.json"
    _write_json(
        challenge_task_path,
        {
            "task_id": "task_126",
            "metadata": {
                "repo_full_name": "example/repo",
                "issue_number": 123,
                "issue_url": "https://github.com/example/repo/issues/123",
            },
        },
    )
    challenge_manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks_challenge_v1.json"
    _write_json(
        challenge_manifest_path,
        {
            "manifest_id": "real_issue_tasks_challenge_v1",
            "tasks": ["benchmarks/tasks/task_126.json"],
        },
    )

    summary = validate_challenge_shortlist.summarize_challenge_shortlist(
        shortlist_path,
        repo_root=repo_root,
        challenge_manifest_path=challenge_manifest_path,
    )

    assert summary == {
        "candidate_issue_refs": [("another/repo", 456)],
        "candidate_count": 1,
        "is_empty": False,
        "next_candidate": {
            "repo_full_name": "another/repo",
            "issue_number": 456,
            "issue_ref": "another/repo#456",
        },
        "filtered_existing_challenge_issue_refs": [("example/repo", 123)],
    }

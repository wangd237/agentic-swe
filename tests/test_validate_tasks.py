from __future__ import annotations

import json
from pathlib import Path

from scripts import validate_tasks


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_validate_repository_includes_challenge_shortlist_conflicts(tmp_path: Path) -> None:
    repo_root = tmp_path
    tasks_dir = repo_root / "benchmarks" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    candidate_file = repo_root / "benchmarks" / "real_world_candidates.json"
    _write_json(candidate_file, {"candidates": []})

    challenge_shortlist_path = repo_root / "docs" / "challenge_shortlist.md"
    challenge_shortlist_path.parent.mkdir(parents=True, exist_ok=True)
    challenge_shortlist_path.write_text(
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

    formal_task_path = repo_root / "benchmarks" / "formal_only" / "task_001.json"
    _write_json(
        formal_task_path,
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
            "tasks": ["benchmarks/formal_only/task_001.json"],
        },
    )

    errors = validate_tasks.validate_repository(
        repo_root=repo_root,
        tasks_dir=tasks_dir,
        candidate_file=candidate_file,
        challenge_shortlist_path=challenge_shortlist_path,
        formal_manifest_path=formal_manifest_path,
    )

    assert errors == [
        "challenge shortlist 候选与正式主集冲突：`example/repo#123` 已在正式 manifest，对应 `task_001`。"
    ]


def test_validate_repository_passes_when_shortlist_has_no_formal_conflict(tmp_path: Path) -> None:
    repo_root = tmp_path
    tasks_dir = repo_root / "benchmarks" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)

    candidate_file = repo_root / "benchmarks" / "real_world_candidates.json"
    _write_json(candidate_file, {"candidates": []})

    challenge_shortlist_path = repo_root / "docs" / "challenge_shortlist.md"
    challenge_shortlist_path.parent.mkdir(parents=True, exist_ok=True)
    challenge_shortlist_path.write_text(
        "\n".join(
            [
                "# Challenge Shortlist",
                "",
                "## 下一条最值得补的 challenge 候选",
                "",
                "当前本地 shortlist 暂时为空，需要重新 sourcing。",
                "",
                "## 当前推荐推进顺序",
            ]
        ),
        encoding="utf-8",
    )

    formal_manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks.json"
    _write_json(
        formal_manifest_path,
        {
            "manifest_id": "real_issue_tasks_v1",
            "tasks": [],
        },
    )

    errors = validate_tasks.validate_repository(
        repo_root=repo_root,
        tasks_dir=tasks_dir,
        candidate_file=candidate_file,
        challenge_shortlist_path=challenge_shortlist_path,
        formal_manifest_path=formal_manifest_path,
    )

    assert errors == []

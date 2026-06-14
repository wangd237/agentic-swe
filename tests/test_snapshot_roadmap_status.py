from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.test_analyze_benchmark_maturity import make_eval_summary, make_task, write_json
from scripts import snapshot_roadmap_status


def test_build_roadmap_status_summary_collects_maturity_and_pipeline_signals(tmp_path: Path) -> None:
    repo_root = tmp_path
    formal_manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks.json"
    challenge_manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks_challenge_v1.json"
    challenge_shortlist_path = repo_root / "docs" / "challenge_shortlist.md"
    candidate_file = repo_root / "benchmarks" / "real_world_candidates.json"
    tasks_dir = repo_root / "benchmarks" / "tasks"
    summary_dir = repo_root / "logs" / "summaries"

    formal_task_paths = [
        make_task(tasks_dir, task_id="task_101", repo_full_name="pytest-dev/pytest", issue_title="formal A"),
        make_task(tasks_dir, task_id="task_102", repo_full_name="pypa/packaging", issue_title="formal B"),
    ]
    challenge_task_path = make_task(
        tasks_dir,
        task_id="task_126",
        repo_full_name="samuelcolvin/watchfiles",
        issue_title="challenge A",
    )
    second_challenge_task_path = make_task(
        tasks_dir,
        task_id="task_127",
        repo_full_name="samuelcolvin/watchfiles",
        issue_title="challenge B",
    )

    challenge_payload = json.loads(challenge_task_path.read_text(encoding="utf-8"))
    challenge_payload["metadata"]["candidate_id"] = "watchfiles_candidate"
    challenge_payload["metadata"]["issue_number"] = 266
    challenge_payload["metadata"]["repo_scaffold_status"] = "ready"
    challenge_payload["metadata"]["ready_note"] = "ready challenge task"
    write_json(challenge_task_path, challenge_payload)
    second_challenge_payload = json.loads(second_challenge_task_path.read_text(encoding="utf-8"))
    second_challenge_payload["metadata"]["candidate_id"] = "watchfiles_candidate_2"
    second_challenge_payload["metadata"]["issue_number"] = 110
    second_challenge_payload["metadata"]["repo_scaffold_status"] = "ready"
    second_challenge_payload["metadata"]["ready_note"] = "ready challenge task"
    write_json(second_challenge_task_path, second_challenge_payload)

    for index, task_path in enumerate(formal_task_paths, start=1):
        payload = json.loads(task_path.read_text(encoding="utf-8"))
        payload["metadata"]["candidate_id"] = f"formal_candidate_{index}"
        payload["metadata"]["repo_scaffold_status"] = "ready"
        write_json(task_path, payload)

    write_json(
        formal_manifest_path,
        {
            "manifest_id": "real_issue_tasks_v1",
            "tasks": [str(path.relative_to(repo_root)).replace("\\", "/") for path in formal_task_paths],
        },
    )
    write_json(
        challenge_manifest_path,
        {
            "manifest_id": "real_issue_tasks_challenge_v1",
            "tasks": [
                str(challenge_task_path.relative_to(repo_root)).replace("\\", "/"),
                str(second_challenge_task_path.relative_to(repo_root)).replace("\\", "/"),
            ],
        },
    )
    challenge_shortlist_path.parent.mkdir(parents=True, exist_ok=True)
    challenge_shortlist_path.write_text(
        "\n".join(
            [
                "# Challenge Shortlist",
                "",
                "## 下一条最值得补的 challenge 候选",
                "",
                "### 1. `samuelcolvin/watchfiles#110`",
                "",
                "## 当前推荐推进顺序",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        repo_root / "benchmarks" / "manifests" / "real_issue_tasks_frozen_40_v1.json",
        {
            "manifest_id": "real_issue_tasks_frozen_40_v1",
            "tasks": [str(formal_task_paths[index % len(formal_task_paths)].relative_to(repo_root)).replace("\\", "/") for index in range(40)],
        },
    )
    write_json(
        candidate_file,
        {
            "dataset_id": "demo",
            "candidates": [
                {"candidate_id": "formal_candidate_1", "repo_full_name": "pytest-dev/pytest", "issue_number": 101, "issue_title": "formal A", "status": "accepted"},
                {"candidate_id": "formal_candidate_2", "repo_full_name": "pypa/packaging", "issue_number": 102, "issue_title": "formal B", "status": "accepted"},
                {"candidate_id": "watchfiles_candidate", "repo_full_name": "samuelcolvin/watchfiles", "issue_number": 266, "issue_title": "challenge A", "status": "accepted"},
                {"candidate_id": "watchfiles_candidate_2", "repo_full_name": "samuelcolvin/watchfiles", "issue_number": 110, "issue_title": "challenge B", "status": "accepted"},
            ],
        },
    )
    make_eval_summary(
        summary_dir,
        frozen_count=40,
        policy_version=32,
        success_rate=1.0,
        test_pass_rate=1.0,
        average_duration_sec=1.0,
    )
    make_eval_summary(
        summary_dir,
        frozen_count=40,
        policy_version=33,
        success_rate=1.0,
        test_pass_rate=1.0,
        average_duration_sec=1.01,
    )
    make_eval_summary(
        summary_dir,
        frozen_count=40,
        policy_version=34,
        success_rate=1.0,
        test_pass_rate=1.0,
        average_duration_sec=1.02,
    )
    env_baseline_dir = repo_root / "logs" / "env_baselines"
    write_json(
        env_baseline_dir / "env_baseline_demo_001.json",
        {
            "snapshot_id": "env_baseline_demo_001",
            "created_at": "2026-06-13T12:30:00+00:00",
            "aggregate": {
                "mean_of_means_sec": 0.0812,
            },
        },
    )
    write_json(
        summary_dir / "duration_compare_demo_001.json",
        {
            "created_at": "2026-06-13T12:35:00+00:00",
            "baseline_batch_run_id": "batch_run_frozen40v68r1_001",
            "improved_batch_run_id": "batch_run_frozen40v69r1_001",
            "aggregate": {
                "common_average_delta_sec": 0.0272,
                "env_adjusted_common_average_delta_sec": 0.0211,
            },
            "environment_baseline": {
                "snapshot_id": "env_baseline_demo_001",
            },
        },
    )

    original_builder = snapshot_roadmap_status._build_challenge_local_auth_readiness
    snapshot_roadmap_status._build_challenge_local_auth_readiness = lambda: {
        "env_token_present": False,
        "env_token_source": None,
        "env_token_looks_valid": False,
        "gh_cli_available": False,
        "gh_auth_logged_in": False,
        "gh_auth_active_account": None,
        "gh_auth_token_exportable": False,
        "preferred_search_mode": "unavailable",
    }
    try:
        summary = snapshot_roadmap_status.build_roadmap_status_summary(
            repo_root=repo_root,
            formal_manifest_path=formal_manifest_path,
            challenge_manifest_path=challenge_manifest_path,
            challenge_shortlist_path=challenge_shortlist_path,
            candidate_file=candidate_file,
            frozen_manifest_glob="real_issue_tasks_frozen_*_v1.json",
            summary_dir=summary_dir,
            env_baseline_dir=env_baseline_dir,
            tasks_dir=tasks_dir,
        )
    finally:
        snapshot_roadmap_status._build_challenge_local_auth_readiness = original_builder

    assert summary["current_state"]["formal_task_count"] == 2
    assert summary["current_state"]["challenge_task_count"] == 2
    assert summary["current_state"]["ecosystem_count"] == 2
    assert summary["current_state"]["screened_candidate_count"] == 0
    assert summary["current_state"]["screened_with_task_count"] == 0
    assert summary["current_state"]["imported_candidate_count"] == 0
    assert summary["challenge_status"]["accepted_in_challenge_manifest_count"] == 2
    assert summary["challenge_status"]["shortlist_candidate_count"] == 0
    assert summary["challenge_status"]["shortlist_screened_with_task_count"] == 0
    assert summary["challenge_status"]["next_candidate_issue_ref"] is None
    assert summary["challenge_status"]["next_action"] == "重新 sourcing 第 3 条 challenge 候选"
    assert summary["challenge_status"]["current_challenge_task_ids"] == ["task_126", "task_127"]
    assert summary["challenge_status"]["local_auth_readiness"] == {
        "env_token_present": False,
        "env_token_source": None,
        "env_token_looks_valid": False,
        "gh_cli_available": False,
        "gh_auth_logged_in": False,
        "gh_auth_active_account": None,
        "gh_auth_token_exportable": False,
        "preferred_search_mode": "unavailable",
    }
    assert summary["goal_progress"]["frozen_40_streak_goal"]["actual"] == 3
    assert summary["performance_status"] == {
        "latest_env_baseline_snapshot_id": "env_baseline_demo_001",
        "latest_env_baseline_summary_json_path": str((env_baseline_dir / "env_baseline_demo_001.json").resolve()),
        "latest_env_baseline_mean_of_means_sec": 0.0812,
        "latest_duration_compare_id": "duration_compare_demo_001",
        "latest_duration_compare_summary_json_path": str((summary_dir / "duration_compare_demo_001.json").resolve()),
        "latest_duration_compare_common_average_delta_sec": 0.0272,
        "latest_duration_compare_env_adjusted_common_average_delta_sec": 0.0211,
        "latest_duration_compare_baseline_batch_run_id": "batch_run_frozen40v68r1_001",
        "latest_duration_compare_improved_batch_run_id": "batch_run_frozen40v69r1_001",
        "latest_duration_compare_env_baseline_snapshot_id": "env_baseline_demo_001",
    }
    assert summary["roadmap_focus"]["challenge_track"]["status"] == "started"
    assert summary["roadmap_focus"]["challenge_track"]["summary"] == (
        "challenge manifest 已建立，当前已有 2 条 challenge 题；"
        "当前 shortlist 候选数为 0，下一步为：重新 sourcing 第 3 条 challenge 候选。"
    )


def test_snapshot_roadmap_status_writes_output_files(tmp_path: Path, monkeypatch) -> None:
    def fake_build(**_: object) -> dict:
        return {
            "created_at": "2026-06-13T12:00:00+00:00",
            "objective": "demo",
            "current_state": {
                "formal_task_count": 64,
                "challenge_task_count": 1,
                "ecosystem_count": 16,
                "candidate_count": 65,
                "accepted_candidate_count": 65,
                "screened_candidate_count": 1,
                "screened_with_task_count": 1,
                "imported_candidate_count": 2,
                "blocked_candidate_count": 0,
                "formal_candidate_count": 64,
                "challenge_candidate_count": 1,
                "latest_frozen_task_count": 40,
                "frozen_40_streak": 8,
                "current_formal_policy_anchor": "improved_v69",
                "historical_stable_policy_anchor": "improved_v50",
            },
            "goal_progress": {
                "formal_task_goal": {"target": 60, "actual": 64, "met": True},
                "ecosystem_goal": {"target": 6, "actual": 16, "met": True},
                "frozen_goal": {"target": 40, "actual": 40, "met": True},
                "frozen_40_streak_goal": {"target": 5, "actual": 8, "met": True},
            },
            "challenge_status": {
                "accepted_in_challenge_manifest_count": 2,
                "accepted_ready_not_in_any_manifest_count": 0,
                "shortlist_candidate_count": 0,
                "shortlist_screened_with_task_count": 0,
                "shortlist_is_empty": True,
                "next_candidate_issue_ref": None,
                "next_action": "重新 sourcing 第 3 条 challenge 候选",
                "current_challenge_task_ids": ["task_126", "task_127"],
                "local_auth_readiness": {
                    "env_token_present": False,
                    "env_token_source": None,
                    "env_token_looks_valid": False,
                    "gh_cli_available": True,
                    "gh_auth_logged_in": True,
                    "gh_auth_active_account": "wangd237",
                    "gh_auth_token_exportable": False,
                    "preferred_search_mode": "gh_session_fallback",
                },
            },
            "roadmap_focus": {
                "performance_track": {"status": "ongoing", "summary": "demo"},
                "formal_expansion_track": {"status": "ongoing", "summary": "demo"},
                "challenge_track": {"status": "started", "summary": "demo"},
            },
            "performance_status": {
                "latest_env_baseline_snapshot_id": "env_baseline_demo_001",
                "latest_env_baseline_mean_of_means_sec": 0.0812,
                "latest_duration_compare_id": "duration_compare_demo_001",
                "latest_duration_compare_common_average_delta_sec": 0.0272,
                "latest_duration_compare_env_adjusted_common_average_delta_sec": 0.0211,
            },
            "maturity_summary": {"goal_gaps": {}},
            "pipeline_summary": {"stage_counts": {}},
        }

    monkeypatch.setattr(snapshot_roadmap_status, "build_roadmap_status_summary", fake_build)

    output = snapshot_roadmap_status.snapshot_roadmap_status(
        repo_root=tmp_path,
        output_dir=tmp_path / "logs" / "summaries",
        run_label="demo",
    )

    assert output["snapshot_id"] == "roadmap_status_demo_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()


def test_build_roadmap_status_summary_counts_shortlist_screened_with_task_candidates(tmp_path: Path) -> None:
    repo_root = tmp_path
    formal_manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks.json"
    challenge_manifest_path = repo_root / "benchmarks" / "manifests" / "real_issue_tasks_challenge_v1.json"
    challenge_shortlist_path = repo_root / "docs" / "challenge_shortlist.md"
    candidate_file = repo_root / "benchmarks" / "real_world_candidates.json"
    tasks_dir = repo_root / "benchmarks" / "tasks"
    summary_dir = repo_root / "logs" / "summaries"
    env_baseline_dir = repo_root / "logs" / "env_baselines"

    screened_task_path = make_task(
        tasks_dir,
        task_id="task_131",
        repo_full_name="samuelcolvin/watchfiles",
        issue_title="challenge screened with task",
    )
    screened_payload = json.loads(screened_task_path.read_text(encoding="utf-8"))
    screened_payload["metadata"]["candidate_id"] = "watchfiles_candidate_215"
    screened_payload["metadata"]["issue_number"] = 215
    screened_payload["metadata"]["repo_scaffold_status"] = "needs_manual_completion"
    write_json(screened_task_path, screened_payload)

    write_json(
        formal_manifest_path,
        {
            "manifest_id": "real_issue_tasks_v1",
            "tasks": [],
        },
    )
    write_json(
        challenge_manifest_path,
        {
            "manifest_id": "real_issue_tasks_challenge_v1",
            "tasks": [],
        },
    )
    challenge_shortlist_path.parent.mkdir(parents=True, exist_ok=True)
    challenge_shortlist_path.write_text(
        "\n".join(
            [
                "# Challenge Shortlist",
                "",
                "## 当前最值得补的 challenge 候选",
                "",
                "### 1. `samuelcolvin/watchfiles#215`",
                "",
                "## 当前推荐推进顺序",
            ]
        ),
        encoding="utf-8",
    )
    write_json(
        repo_root / "benchmarks" / "manifests" / "real_issue_tasks_frozen_40_v1.json",
        {
            "manifest_id": "real_issue_tasks_frozen_40_v1",
            "tasks": [],
        },
    )
    write_json(
        candidate_file,
        {
            "dataset_id": "demo",
            "candidates": [
                {
                    "candidate_id": "watchfiles_candidate_215",
                    "repo_full_name": "samuelcolvin/watchfiles",
                    "issue_number": 215,
                    "issue_title": "challenge screened with task",
                    "status": "screened",
                }
            ],
        },
    )

    original_builder = snapshot_roadmap_status._build_challenge_local_auth_readiness
    snapshot_roadmap_status._build_challenge_local_auth_readiness = lambda: {
        "env_token_present": False,
        "env_token_source": None,
        "env_token_looks_valid": False,
        "gh_cli_available": False,
        "gh_auth_logged_in": False,
        "gh_auth_active_account": None,
        "gh_auth_token_exportable": False,
        "preferred_search_mode": "unavailable",
    }
    try:
        summary = snapshot_roadmap_status.build_roadmap_status_summary(
            repo_root=repo_root,
            formal_manifest_path=formal_manifest_path,
            challenge_manifest_path=challenge_manifest_path,
            challenge_shortlist_path=challenge_shortlist_path,
            candidate_file=candidate_file,
            frozen_manifest_glob="real_issue_tasks_frozen_*_v1.json",
            summary_dir=summary_dir,
            env_baseline_dir=env_baseline_dir,
            tasks_dir=tasks_dir,
        )
    finally:
        snapshot_roadmap_status._build_challenge_local_auth_readiness = original_builder

    assert summary["current_state"]["screened_with_task_count"] == 1
    assert summary["challenge_status"]["shortlist_candidate_count"] == 1
    assert summary["challenge_status"]["shortlist_screened_with_task_count"] == 1
    assert summary["challenge_status"]["next_candidate_issue_ref"] == "samuelcolvin/watchfiles#215"


def test_build_challenge_local_auth_readiness_prefers_gh_session_when_token_not_exportable(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    def fake_run(command, *, extra_env=None):
        if command == ["gh", "auth", "status"]:
            return 0, "", "✓ Logged in to github.com account wangd237 (keyring)"
        if command == ["gh", "auth", "token"]:
            return 1, "", "no oauth token found for github.com"
        raise AssertionError(command)

    monkeypatch.setattr(snapshot_roadmap_status, "_run_command", fake_run)

    readiness = snapshot_roadmap_status._build_challenge_local_auth_readiness()

    assert readiness == {
        "env_token_present": False,
        "env_token_source": None,
        "env_token_looks_valid": False,
        "gh_cli_available": True,
        "gh_auth_logged_in": True,
        "gh_auth_active_account": "wangd237",
        "gh_auth_token_exportable": False,
        "preferred_search_mode": "gh_session_fallback",
    }

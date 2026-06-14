from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import refresh_roadmap_tracking


def test_refresh_roadmap_tracking_writes_summary_after_running_all_steps(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(refresh_roadmap_tracking, "validate_repository", lambda **_: [])
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "audit_semi_real_pipeline",
        lambda **_: {
            "summary_json_path": str(tmp_path / "logs" / "summaries" / "audit.json"),
        },
    )
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "analyze_benchmark_maturity",
        lambda **_: {
            "summary_json_path": str(tmp_path / "logs" / "summaries" / "maturity.json"),
        },
    )
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "snapshot_roadmap_status",
        lambda **_: {
            "summary_json_path": str(tmp_path / "logs" / "summaries" / "snapshot.json"),
            "summary": {
                "current_state": {
                    "formal_task_count": 64,
                    "challenge_task_count": 1,
                    "ecosystem_count": 16,
                    "candidate_count": 65,
                    "screened_candidate_count": 1,
                    "screened_with_task_count": 0,
                    "imported_candidate_count": 2,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 1,
                    "next_candidate_issue_ref": "samuelcolvin/watchfiles#110",
                    "next_action": "优先评估 challenge 候选 samuelcolvin/watchfiles#110",
                    "local_auth_readiness": {
                        "env_token_present": False,
                        "env_token_looks_valid": False,
                        "gh_auth_logged_in": True,
                        "gh_auth_token_exportable": False,
                        "preferred_search_mode": "gh_session_fallback",
                    },
                },
                "performance_status": {
                    "latest_env_baseline_snapshot_id": "env_baseline_demo_001",
                    "latest_env_baseline_mean_of_means_sec": 0.0812,
                    "latest_duration_compare_id": "duration_compare_demo_001",
                    "latest_duration_compare_common_average_delta_sec": 0.0272,
                    "latest_duration_compare_env_adjusted_common_average_delta_sec": 0.0211,
                },
            },
        },
    )

    output = refresh_roadmap_tracking.refresh_roadmap_tracking(
        repo_root=tmp_path,
        output_dir=tmp_path / "logs" / "summaries",
        run_label="demo",
    )

    assert output["refresh_id"] == "roadmap_tracking_demo_001"
    assert output["summary"]["validation"]["passed"] is True
    assert output["summary"]["headline"] == "roadmap: formal=64 challenge=1 eco=16 frozen=40 streak=8 validation=OK"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
    assert Path(output["latest_summary_json_path"]).exists()
    assert Path(output["latest_summary_md_path"]).exists()
    assert Path(output["history_summary_json_path"]).exists()
    assert Path(output["history_summary_md_path"]).exists()
    assert Path(output["action_board_json_path"]).exists()
    assert Path(output["action_board_md_path"]).exists()
    assert Path(output["status_card_json_path"]).exists()
    assert Path(output["status_card_md_path"]).exists()
    assert Path(output["latest_summary_json_path"]).name == "roadmap_tracking_latest_demo.json"
    assert output["summary"]["previous_latest_summary_json_path"] is None
    assert output["summary"]["changed_fields"] == []
    assert output["summary"]["delta"] is None
    assert output["summary"]["refresh_outcome"] == {
        "category": "first_refresh",
        "summary": "这是当前标签下首次生成 latest tracking 快照，后续 refresh 将可直接对比变化。",
    }
    assert output["summary"]["history_overview"] == {
        "total_refresh_count": 1,
        "recent_no_material_change_streak": 0,
        "category_counts": {"first_refresh": 1},
        "advice": {
            "category": "monitor_and_continue",
            "summary": "当前 history 没有暴露强回退，但也还没有形成明确推进信号，适合继续按 v2 roadmap 的主线小步推进。",
            "recommended_focus": "performance_or_expansion",
            "recommended_actions": [
                "继续从性能复核常态化、正式集扩容、challenge sourcing 中选择一条最缺口明显的主线推进。",
                "完成一轮实质改动后再 refresh，避免把 tracking 入口当作主工作本身。",
            ],
        },
    }


def test_refresh_roadmap_tracking_stops_after_validation_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "validate_repository",
        lambda **_: ["demo validation error"],
    )

    def fail_if_called(**_: object) -> None:
        raise AssertionError("validation 失败后不应继续调用后续步骤")

    monkeypatch.setattr(refresh_roadmap_tracking, "audit_semi_real_pipeline", fail_if_called)
    monkeypatch.setattr(refresh_roadmap_tracking, "analyze_benchmark_maturity", fail_if_called)
    monkeypatch.setattr(refresh_roadmap_tracking, "snapshot_roadmap_status", fail_if_called)

    output = refresh_roadmap_tracking.refresh_roadmap_tracking(
        repo_root=tmp_path,
        output_dir=tmp_path / "logs" / "summaries",
        run_label="demo",
    )

    assert output["refresh_id"] == "roadmap_tracking_demo_001"
    assert output["summary"]["validation"]["passed"] is False
    assert output["summary"]["validation"]["errors"] == ["demo validation error"]
    assert output["summary"]["outputs"]["snapshot_summary_json_path"] is None
    assert output["summary"]["headline"] == "roadmap: validation=FAIL"
    assert output["summary"]["refresh_outcome"] == {
        "category": "validation_failed",
        "summary": "本次 refresh 未通过仓库级校验，需先处理 validation 错误。",
    }
    assert output["summary"]["history_overview"] == {
        "total_refresh_count": 1,
        "recent_no_material_change_streak": 0,
        "category_counts": {"validation_failed": 1},
        "advice": {
            "category": "fix_validation_first",
            "summary": "最近一次 refresh 卡在 validation，当前应先修复仓库级校验问题，再继续做 roadmap 追踪。",
            "recommended_focus": "governance",
            "recommended_actions": [
                "先处理 validate_tasks 暴露的错误，再重新运行 refresh。",
                "避免基于失败状态继续刷新 maturity 或 snapshot 产物。",
            ],
        },
    }
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
    assert Path(output["latest_summary_json_path"]).exists()
    assert Path(output["latest_summary_md_path"]).exists()
    assert Path(output["history_summary_json_path"]).exists()
    assert Path(output["history_summary_md_path"]).exists()
    assert Path(output["action_board_json_path"]).exists()
    assert Path(output["action_board_md_path"]).exists()
    assert Path(output["status_card_json_path"]).exists()
    assert Path(output["status_card_md_path"]).exists()


def test_refresh_roadmap_tracking_records_delta_against_previous_latest(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "logs" / "summaries"
    output_dir.mkdir(parents=True, exist_ok=True)
    previous_latest_path = output_dir / "roadmap_tracking_latest_demo.json"
    previous_latest_path.write_text(
        json.dumps(
            {
                "created_at": "2026-06-13T10:00:00+00:00",
                "refresh_id": "roadmap_tracking_demo_001",
                "headline": "roadmap: formal=63 challenge=1 eco=15 frozen=40 streak=7 validation=OK",
                "snapshot_summary": {
                    "current_state": {
                        "formal_task_count": 63,
                        "challenge_task_count": 1,
                        "ecosystem_count": 15,
                        "candidate_count": 64,
                        "screened_candidate_count": 0,
                        "screened_with_task_count": 0,
                        "imported_candidate_count": 0,
                        "latest_frozen_task_count": 40,
                        "frozen_40_streak": 7,
                    },
                    "challenge_status": {
                        "shortlist_candidate_count": 0,
                        "next_action": "重新 sourcing 第 2 条 challenge 候选",
                    },
                    "performance_status": {
                        "latest_env_baseline_snapshot_id": None,
                        "latest_env_baseline_mean_of_means_sec": None,
                        "latest_duration_compare_id": None,
                        "latest_duration_compare_common_average_delta_sec": None,
                        "latest_duration_compare_env_adjusted_common_average_delta_sec": None,
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(refresh_roadmap_tracking, "validate_repository", lambda **_: [])
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "audit_semi_real_pipeline",
        lambda **_: {
            "summary_json_path": str(output_dir / "audit.json"),
        },
    )
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "analyze_benchmark_maturity",
        lambda **_: {
            "summary_json_path": str(output_dir / "maturity.json"),
        },
    )
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "snapshot_roadmap_status",
        lambda **_: {
            "summary_json_path": str(output_dir / "snapshot.json"),
            "summary": {
                "current_state": {
                    "formal_task_count": 64,
                    "challenge_task_count": 1,
                    "ecosystem_count": 16,
                    "candidate_count": 65,
                    "accepted_candidate_count": 65,
                    "screened_candidate_count": 1,
                    "screened_with_task_count": 1,
                    "imported_candidate_count": 2,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "accepted_ready_not_in_any_manifest_count": 0,
                    "shortlist_candidate_count": 1,
                    "next_candidate_issue_ref": "samuelcolvin/watchfiles#110",
                    "next_action": "优先评估 challenge 候选 samuelcolvin/watchfiles#110",
                    "local_auth_readiness": {
                        "env_token_present": False,
                        "env_token_looks_valid": False,
                        "gh_auth_logged_in": True,
                        "gh_auth_token_exportable": False,
                        "preferred_search_mode": "gh_session_fallback",
                    },
                },
                "performance_status": {
                    "latest_env_baseline_snapshot_id": "env_baseline_demo_001",
                    "latest_env_baseline_mean_of_means_sec": 0.0812,
                    "latest_duration_compare_id": "duration_compare_demo_001",
                    "latest_duration_compare_common_average_delta_sec": 0.0272,
                    "latest_duration_compare_env_adjusted_common_average_delta_sec": 0.0211,
                },
            },
        },
    )

    output = refresh_roadmap_tracking.refresh_roadmap_tracking(
        repo_root=tmp_path,
        output_dir=output_dir,
        run_label="demo",
    )

    assert output["refresh_id"] == "roadmap_tracking_demo_001"
    assert output["summary"]["previous_latest_summary_json_path"] == str(previous_latest_path)
    assert output["summary"]["changed_fields"] == [
        "headline",
        "validation_passed",
        "formal_task_count",
        "ecosystem_count",
        "candidate_count",
        "accepted_candidate_count",
        "screened_candidate_count",
        "screened_with_task_count",
        "imported_candidate_count",
        "frozen_40_streak",
        "challenge_shortlist_candidate_count",
        "challenge_accepted_ready_not_in_any_manifest_count",
        "challenge_next_action",
        "challenge_auth_env_token_present",
        "challenge_auth_env_token_looks_valid",
        "challenge_auth_gh_logged_in",
        "challenge_auth_token_exportable",
        "challenge_auth_preferred_search_mode",
        "performance_env_baseline_snapshot_id",
        "performance_env_baseline_mean_of_means_sec",
        "performance_duration_compare_id",
        "performance_duration_compare_common_average_delta_sec",
        "performance_duration_compare_env_adjusted_common_average_delta_sec",
    ]
    assert output["summary"]["delta"] == {
        "previous_refresh_id": "roadmap_tracking_demo_001",
        "previous_created_at": "2026-06-13T10:00:00+00:00",
        "change_count": 23,
        "field_changes": [
            {
                "field": "headline",
                "previous": "roadmap: formal=63 challenge=1 eco=15 frozen=40 streak=7 validation=OK",
                "current": "roadmap: formal=64 challenge=1 eco=16 frozen=40 streak=8 validation=OK",
            },
            {
                "field": "validation_passed",
                "previous": None,
                "current": True,
            },
            {
                "field": "formal_task_count",
                "previous": 63,
                "current": 64,
            },
            {
                "field": "ecosystem_count",
                "previous": 15,
                "current": 16,
            },
            {
                "field": "candidate_count",
                "previous": 64,
                "current": 65,
            },
            {
                "field": "accepted_candidate_count",
                "previous": None,
                "current": 65,
            },
            {
                "field": "screened_candidate_count",
                "previous": 0,
                "current": 1,
            },
            {
                "field": "screened_with_task_count",
                "previous": 0,
                "current": 1,
            },
            {
                "field": "imported_candidate_count",
                "previous": 0,
                "current": 2,
            },
            {
                "field": "frozen_40_streak",
                "previous": 7,
                "current": 8,
            },
            {
                "field": "challenge_shortlist_candidate_count",
                "previous": 0,
                "current": 1,
            },
            {
                "field": "challenge_accepted_ready_not_in_any_manifest_count",
                "previous": None,
                "current": 0,
            },
            {
                "field": "challenge_next_action",
                "previous": "重新 sourcing 第 2 条 challenge 候选",
                "current": "优先评估 challenge 候选 samuelcolvin/watchfiles#110",
            },
            {
                "field": "challenge_auth_env_token_present",
                "previous": None,
                "current": False,
            },
            {
                "field": "challenge_auth_env_token_looks_valid",
                "previous": None,
                "current": False,
            },
            {
                "field": "challenge_auth_gh_logged_in",
                "previous": None,
                "current": True,
            },
            {
                "field": "challenge_auth_token_exportable",
                "previous": None,
                "current": False,
            },
            {
                "field": "challenge_auth_preferred_search_mode",
                "previous": None,
                "current": "gh_session_fallback",
            },
            {
                "field": "performance_env_baseline_snapshot_id",
                "previous": None,
                "current": "env_baseline_demo_001",
            },
            {
                "field": "performance_env_baseline_mean_of_means_sec",
                "previous": None,
                "current": 0.0812,
            },
            {
                "field": "performance_duration_compare_id",
                "previous": None,
                "current": "duration_compare_demo_001",
            },
            {
                "field": "performance_duration_compare_common_average_delta_sec",
                "previous": None,
                "current": 0.0272,
            },
            {
                "field": "performance_duration_compare_env_adjusted_common_average_delta_sec",
                "previous": None,
                "current": 0.0211,
            },
        ],
    }
    assert output["summary"]["refresh_outcome"] == {
        "category": "progress",
        "summary": "检测到正向推进：formal_task_count +1, ecosystem_count +1, candidate_count +1, accepted_candidate_count +65, screened_candidate_count +1, screened_with_task_count +1, imported_candidate_count +2, frozen_40_streak +1, challenge_shortlist_candidate_count +1, challenge_next_action updated, challenge_auth_env_token_present updated, challenge_auth_env_token_looks_valid updated, challenge_auth_gh_logged_in updated, challenge_auth_token_exportable updated, challenge_auth_preferred_search_mode updated, performance_env_baseline_snapshot_id updated, performance_env_baseline_mean_of_means_sec updated, performance_duration_compare_id updated, performance_duration_compare_common_average_delta_sec updated, performance_duration_compare_env_adjusted_common_average_delta_sec updated。",
    }
    assert output["summary"]["history_overview"] == {
        "total_refresh_count": 1,
        "recent_no_material_change_streak": 0,
        "category_counts": {"progress": 1},
        "advice": {
            "category": "keep_momentum",
            "summary": "最近一次 refresh 已出现正向推进，当前应继续沿同一主线推进，并及时同步文档与评测证据。",
            "recommended_focus": "performance_track",
            "recommended_actions": [
                "继续沿最近一次产生变化的主线推进，避免在中途改成只做展示层更新。",
                "保持每轮推进后同步 refresh、GUIDE、next_actions 和 optimization_log。",
            ],
        },
    }


def test_refresh_roadmap_tracking_marks_no_material_change_when_latest_is_unchanged(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "logs" / "summaries"
    output_dir.mkdir(parents=True, exist_ok=True)
    previous_latest_path = output_dir / "roadmap_tracking_latest_demo.json"
    previous_latest_path.write_text(
        json.dumps(
            {
                "created_at": "2026-06-13T10:00:00+00:00",
                "refresh_id": "roadmap_tracking_demo_001",
                "validation": {"passed": True},
                "headline": "roadmap: formal=64 challenge=1 eco=16 frozen=40 streak=8 validation=OK",
                "snapshot_summary": {
                    "current_state": {
                        "formal_task_count": 64,
                        "challenge_task_count": 1,
                        "ecosystem_count": 16,
                        "candidate_count": 65,
                        "screened_candidate_count": 1,
                        "screened_with_task_count": 1,
                        "imported_candidate_count": 2,
                        "latest_frozen_task_count": 40,
                        "frozen_40_streak": 8,
                    },
                    "challenge_status": {
                        "shortlist_candidate_count": 1,
                        "next_candidate_issue_ref": "samuelcolvin/watchfiles#110",
                        "next_action": "优先评估 challenge 候选 samuelcolvin/watchfiles#110",
                        "local_auth_readiness": {
                            "env_token_present": False,
                            "env_token_looks_valid": False,
                            "gh_auth_logged_in": True,
                            "gh_auth_token_exportable": False,
                            "preferred_search_mode": "gh_session_fallback",
                        },
                    },
                    "performance_status": {
                        "latest_env_baseline_snapshot_id": "env_baseline_demo_001",
                        "latest_env_baseline_mean_of_means_sec": 0.0812,
                        "latest_duration_compare_id": "duration_compare_demo_001",
                        "latest_duration_compare_common_average_delta_sec": 0.0272,
                        "latest_duration_compare_env_adjusted_common_average_delta_sec": 0.0211,
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(refresh_roadmap_tracking, "validate_repository", lambda **_: [])
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "audit_semi_real_pipeline",
        lambda **_: {
            "summary_json_path": str(output_dir / "audit.json"),
        },
    )
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "analyze_benchmark_maturity",
        lambda **_: {
            "summary_json_path": str(output_dir / "maturity.json"),
        },
    )
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "snapshot_roadmap_status",
        lambda **_: {
            "summary_json_path": str(output_dir / "snapshot.json"),
            "summary": {
                "current_state": {
                    "formal_task_count": 64,
                    "challenge_task_count": 1,
                    "ecosystem_count": 16,
                    "candidate_count": 65,
                    "screened_candidate_count": 1,
                    "screened_with_task_count": 1,
                    "imported_candidate_count": 2,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 1,
                    "next_candidate_issue_ref": "samuelcolvin/watchfiles#110",
                    "next_action": "优先评估 challenge 候选 samuelcolvin/watchfiles#110",
                    "local_auth_readiness": {
                        "env_token_present": False,
                        "env_token_looks_valid": False,
                        "gh_auth_logged_in": True,
                        "gh_auth_token_exportable": False,
                        "preferred_search_mode": "gh_session_fallback",
                    },
                },
                "performance_status": {
                    "latest_env_baseline_snapshot_id": "env_baseline_demo_001",
                    "latest_env_baseline_mean_of_means_sec": 0.0812,
                    "latest_duration_compare_id": "duration_compare_demo_001",
                    "latest_duration_compare_common_average_delta_sec": 0.0272,
                    "latest_duration_compare_env_adjusted_common_average_delta_sec": 0.0211,
                },
            },
        },
    )

    output = refresh_roadmap_tracking.refresh_roadmap_tracking(
        repo_root=tmp_path,
        output_dir=output_dir,
        run_label="demo",
    )

    assert output["summary"]["changed_fields"] == []
    assert output["summary"]["delta"] == {
        "previous_refresh_id": "roadmap_tracking_demo_001",
        "previous_created_at": "2026-06-13T10:00:00+00:00",
        "change_count": 0,
        "field_changes": [],
    }
    assert output["summary"]["refresh_outcome"] == {
        "category": "no_material_change",
        "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
    }
    assert output["summary"]["history_overview"] == {
        "total_refresh_count": 1,
        "recent_no_material_change_streak": 1,
        "category_counts": {"no_material_change": 1},
        "advice": {
            "category": "monitor_and_continue",
            "summary": "当前 history 没有暴露强回退，但也还没有形成明确推进信号，适合继续按 v2 roadmap 的主线小步推进。",
            "recommended_focus": "performance_or_expansion",
            "recommended_actions": [
                "继续从性能复核常态化、正式集扩容、challenge sourcing 中选择一条最缺口明显的主线推进。",
                "完成一轮实质改动后再 refresh，避免把 tracking 入口当作主工作本身。",
            ],
        },
    }


def test_refresh_roadmap_tracking_rebuilds_history_from_numbered_refresh_summaries(tmp_path: Path, monkeypatch) -> None:
    output_dir = tmp_path / "logs" / "summaries"
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "roadmap_tracking_demo_001.json").write_text(
        json.dumps(
            {
                "created_at": "2026-06-13T09:00:00+00:00",
                "refresh_id": "roadmap_tracking_demo_001",
                "validation": {"passed": True},
                "headline": "roadmap: formal=63 challenge=1 eco=15 frozen=40 streak=7 validation=OK",
                "changed_fields": ["formal_task_count"],
                "delta": {"change_count": 1, "field_changes": []},
                "refresh_outcome": {
                    "category": "progress",
                    "summary": "检测到正向推进：formal_task_count +1。",
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "roadmap_tracking_demo_002.json").write_text(
        json.dumps(
            {
                "created_at": "2026-06-13T10:00:00+00:00",
                "refresh_id": "roadmap_tracking_demo_002",
                "validation": {"passed": True},
                "headline": "roadmap: formal=63 challenge=1 eco=15 frozen=40 streak=7 validation=OK",
                "changed_fields": [],
                "delta": {"change_count": 0, "field_changes": []},
                "refresh_outcome": {
                    "category": "no_material_change",
                    "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "roadmap_tracking_latest_demo.json").write_text(
        json.dumps(
            {
                "created_at": "2026-06-13T10:00:00+00:00",
                "refresh_id": "roadmap_tracking_demo_002",
                "validation": {"passed": True},
                "headline": "roadmap: formal=63 challenge=1 eco=15 frozen=40 streak=7 validation=OK",
                "snapshot_summary": {
                    "current_state": {
                        "formal_task_count": 63,
                        "challenge_task_count": 1,
                        "ecosystem_count": 15,
                        "candidate_count": 64,
                        "latest_frozen_task_count": 40,
                        "frozen_40_streak": 7,
                    },
                    "challenge_status": {
                        "next_action": "重新 sourcing 第 2 条 challenge 候选",
                    },
                },
                "changed_fields": [],
                "delta": {"change_count": 0, "field_changes": []},
                "refresh_outcome": {
                    "category": "no_material_change",
                    "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(refresh_roadmap_tracking, "validate_repository", lambda **_: [])
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "audit_semi_real_pipeline",
        lambda **_: {
            "summary_json_path": str(output_dir / "audit.json"),
        },
    )
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "analyze_benchmark_maturity",
        lambda **_: {
            "summary_json_path": str(output_dir / "maturity.json"),
        },
    )
    monkeypatch.setattr(
        refresh_roadmap_tracking,
        "snapshot_roadmap_status",
        lambda **_: {
            "summary_json_path": str(output_dir / "snapshot.json"),
            "summary": {
                "current_state": {
                    "formal_task_count": 63,
                    "challenge_task_count": 1,
                    "ecosystem_count": 15,
                    "candidate_count": 64,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 7,
                },
                "challenge_status": {
                    "next_action": "重新 sourcing 第 2 条 challenge 候选",
                },
            },
        },
    )

    output = refresh_roadmap_tracking.refresh_roadmap_tracking(
        repo_root=tmp_path,
        output_dir=output_dir,
        run_label="demo",
    )

    history = json.loads(Path(output["history_summary_json_path"]).read_text(encoding="utf-8"))
    assert output["refresh_id"] == "roadmap_tracking_demo_003"
    assert output["summary"]["history_overview"] == {
        "total_refresh_count": 3,
        "recent_no_material_change_streak": 2,
        "category_counts": {
            "no_material_change": 2,
            "progress": 1,
        },
        "advice": {
            "category": "keep_momentum",
            "summary": "最近一轮虽然没有新增高信号变化，但距离上一次 progress 很近，当前更适合继续沿最近证明有效的主线推进。",
            "recommended_focus": "formal_expansion_track",
            "recommended_actions": [
                "继续沿最近一次产生 progress 的主线推进，避免因为一轮 no_material_change 就切回泛化探索。",
                "补完同主线的新证据或接入动作后再 refresh，确认 progress 是否恢复。",
            ],
            "progress_track": "formal_expansion_track",
            "source_progress_refresh_id": "roadmap_tracking_demo_001",
        },
    }
    assert history["latest_refresh_id"] == "roadmap_tracking_demo_003"
    assert history["total_refresh_count"] == 3
    assert history["recent_no_material_change_streak"] == 2
    assert history["category_counts"] == {
        "no_material_change": 2,
        "progress": 1,
    }
    assert [entry["refresh_id"] for entry in history["recent_entries"]] == [
        "roadmap_tracking_demo_001",
        "roadmap_tracking_demo_002",
        "roadmap_tracking_demo_003",
    ]


def test_infer_refresh_outcome_for_history_backfills_legacy_summary_without_unknown() -> None:
    inferred = refresh_roadmap_tracking.infer_refresh_outcome_for_history(
        {
            "validation": {"passed": True},
            "previous_latest_summary_json_path": "some/latest.json",
            "changed_fields": [],
            "delta": {
                "change_count": 0,
                "field_changes": [],
            },
        }
    )

    assert inferred == {
        "category": "no_material_change",
        "summary": "历史 summary 未显式写入 refresh_outcome；根据 delta 为空推断为无实质变化。",
    }


def test_build_history_entry_records_progress_track_from_changed_fields() -> None:
    entry = refresh_roadmap_tracking._build_history_entry(
        {
            "refresh_id": "roadmap_tracking_demo_100",
            "created_at": "2026-06-13T10:00:00+00:00",
            "headline": "roadmap: formal=64 challenge=2 eco=16 frozen=40 streak=8 validation=OK",
            "validation": {"passed": True},
            "changed_fields": [
                "performance_env_baseline_snapshot_id",
                "performance_duration_compare_id",
            ],
            "delta": {"change_count": 2, "field_changes": []},
            "refresh_outcome": {
                "category": "progress",
                "summary": "检测到正向推进。",
            },
        },
        summary_json_path="demo.json",
    )

    assert entry["progress_track"] == "performance_track"


def test_build_history_entry_records_challenge_track_from_auth_delta_fields() -> None:
    entry = refresh_roadmap_tracking._build_history_entry(
        {
            "refresh_id": "roadmap_tracking_demo_101",
            "created_at": "2026-06-13T10:00:00+00:00",
            "headline": "roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK",
            "validation": {"passed": True},
            "changed_fields": [
                "challenge_auth_preferred_search_mode",
            ],
            "delta": {"change_count": 1, "field_changes": []},
            "refresh_outcome": {
                "category": "progress",
                "summary": "检测到正向推进：challenge_auth_preferred_search_mode updated。",
            },
        },
        summary_json_path="demo.json",
    )

    assert entry["progress_track"] == "challenge_track"


def test_build_history_entry_records_challenge_track_from_screened_with_task_delta() -> None:
    entry = refresh_roadmap_tracking._build_history_entry(
        {
            "refresh_id": "roadmap_tracking_demo_102",
            "created_at": "2026-06-13T10:00:00+00:00",
            "headline": "roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK",
            "validation": {"passed": True},
            "changed_fields": [
                "screened_with_task_count",
                "challenge_shortlist_screened_with_task_count",
            ],
            "delta": {"change_count": 2, "field_changes": []},
            "refresh_outcome": {
                "category": "progress",
                "summary": "检测到正向推进：screened_with_task_count +1。",
            },
        },
        summary_json_path="demo.json",
    )

    assert entry["progress_track"] == "challenge_track"


def test_build_refresh_outcome_treats_shortlist_screened_with_task_as_challenge_progress() -> None:
    outcome = refresh_roadmap_tracking.build_refresh_outcome(
        {"refresh_id": "roadmap_tracking_demo_001", "validation": {"passed": True}},
        {"validation": {"passed": True}},
        [
            "challenge_shortlist_screened_with_task_count",
        ],
        {
            "field_changes": [
                {
                    "field": "challenge_shortlist_screened_with_task_count",
                    "previous": 0,
                    "current": 1,
                }
            ]
        },
    )

    assert outcome == {
        "category": "progress",
        "summary": "检测到正向推进：challenge_shortlist_screened_with_task_count +1。",
    }


def test_build_refresh_outcome_treats_ready_candidate_entering_challenge_manifest_as_progress() -> None:
    outcome = refresh_roadmap_tracking.build_refresh_outcome(
        {"refresh_id": "roadmap_tracking_demo_060", "validation": {"passed": True}},
        {"validation": {"passed": True}},
        [
            "challenge_task_count",
            "challenge_shortlist_candidate_count",
            "challenge_accepted_ready_not_in_any_manifest_count",
            "challenge_next_action",
        ],
        {
            "field_changes": [
                {
                    "field": "challenge_task_count",
                    "previous": 3,
                    "current": 4,
                },
                {
                    "field": "challenge_shortlist_candidate_count",
                    "previous": 1,
                    "current": 0,
                },
                {
                    "field": "challenge_accepted_ready_not_in_any_manifest_count",
                    "previous": 1,
                    "current": 0,
                },
                {
                    "field": "challenge_next_action",
                    "previous": "优先评估 challenge 候选 samuelcolvin/watchfiles#215",
                    "current": "重新 sourcing 第 5 条 challenge 候选",
                },
            ]
        },
    )

    assert outcome == {
        "category": "progress",
        "summary": "检测到 challenge manifest 接入推进：challenge_task_count +1，challenge_accepted_ready_not_in_any_manifest_count -1；下一步已切换为：重新 sourcing 第 5 条 challenge 候选。",
    }


def test_build_history_advice_marks_stalled_tracking_after_long_no_change_streak() -> None:
    advice = refresh_roadmap_tracking.build_history_advice(
        {
            "recent_entries": [
                {"outcome_category": "no_material_change"},
            ],
            "recent_no_material_change_streak": 6,
        },
        {
            "snapshot_summary": {
                "current_state": {
                    "challenge_task_count": 1,
                },
                "challenge_status": {
                    "next_action": "重新 sourcing 第 2 条 challenge 候选",
                },
            }
        },
    )

    assert advice == {
        "category": "stalled_tracking",
        "summary": "连续多轮 refresh 没有出现高信号变化，说明当前更需要推进主线动作，而不是继续做状态确认。",
        "recommended_focus": "formal_expansion_track",
        "recommended_actions": [
            "暂停只做 refresh 的续跑，切回 A 线继续扩正式真实任务，优先补并发与协程、文件路径与 IO、新生态控制流问题。",
            "如果 challenge 仍未扩到第 2 条，优先继续 sourcing 下一条 challenge 候选。",
            "如果准备推进策略版本，先补新的稳定性或性能诊断证据，而不是仅重复 refresh。",
        ],
        "challenge_next_action": "重新 sourcing 第 2 条 challenge 候选",
    }


def test_build_history_advice_prefers_challenge_track_when_a4_gap_is_explicit_even_after_long_no_change_streak() -> None:
    advice = refresh_roadmap_tracking.build_history_advice(
        {
            "recent_entries": [
                {
                    "refresh_id": "roadmap_tracking_refresh_041",
                    "outcome_category": "no_material_change",
                },
                {
                    "refresh_id": "roadmap_tracking_refresh_042",
                    "outcome_category": "no_material_change",
                },
                {
                    "refresh_id": "roadmap_tracking_refresh_043",
                    "outcome_category": "no_material_change",
                },
            ],
            "recent_no_material_change_streak": 5,
        },
        {
            "snapshot_summary": {
                "current_state": {
                    "challenge_task_count": 3,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 0,
                    "next_action": "重新 sourcing 第 4 条 challenge 候选",
                },
            }
        },
    )

    assert advice == {
        "category": "stalled_tracking",
        "summary": "连续多轮 refresh 没有出现高信号变化，但当前 challenge 第 4 条候选缺口仍然非常明确，适合优先把这条边界展示线继续做实。",
        "recommended_focus": "challenge_track",
        "recommended_actions": [
            "优先先做 challenge 第 4 条候选 sourcing，并把认证预检、搜索、导入、筛选串成一轮可复用动作。",
            "如果 live GitHub 检索再次受阻，至少要把阻塞形态、认证状态和下一条可执行命令同步进 latest 文档与 tracking。",
            "完成 challenge 线实质动作后再 refresh，避免继续只增加 no_material_change streak。",
        ],
        "challenge_next_action": "重新 sourcing 第 4 条 challenge 候选",
    }


def test_build_history_advice_keeps_recent_progress_track_across_short_no_change_gap() -> None:
    advice = refresh_roadmap_tracking.build_history_advice(
        {
            "recent_entries": [
                {
                    "refresh_id": "roadmap_tracking_refresh_026",
                    "outcome_category": "progress",
                    "progress_track": "performance_track",
                },
                {
                    "refresh_id": "roadmap_tracking_refresh_027",
                    "outcome_category": "no_material_change",
                    "progress_track": "active_track",
                },
            ],
            "recent_no_material_change_streak": 1,
        },
        {
            "snapshot_summary": {
                "current_state": {
                    "challenge_task_count": 2,
                },
                "challenge_status": {
                    "next_action": "重新 sourcing 第 3 条 challenge 候选",
                },
            }
        },
    )

    assert advice == {
        "category": "keep_momentum",
        "summary": "最近一轮虽然没有新增高信号变化，但距离上一次 progress 很近，当前更适合继续沿最近证明有效的主线推进。",
        "recommended_focus": "performance_track",
        "recommended_actions": [
            "继续沿最近一次产生 progress 的主线推进，避免因为一轮 no_material_change 就切回泛化探索。",
            "补完同主线的新证据或接入动作后再 refresh，确认 progress 是否恢复。",
        ],
        "progress_track": "performance_track",
        "source_progress_refresh_id": "roadmap_tracking_refresh_026",
    }


def test_build_action_board_prioritizes_formal_expansion_when_tracking_is_stalled() -> None:
    action_board = refresh_roadmap_tracking.build_action_board(
        {
            "refresh_id": "roadmap_tracking_demo_009",
            "headline": "roadmap: formal=64 challenge=1 eco=16 frozen=40 streak=8 validation=OK",
            "refresh_outcome": {
                "category": "no_material_change",
                "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
            },
            "snapshot_summary": {
                "current_state": {
                    "formal_task_count": 64,
                    "challenge_task_count": 1,
                    "ecosystem_count": 16,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "next_action": "重新 sourcing 第 2 条 challenge 候选",
                },
                "roadmap_focus": {
                    "performance_track": {"summary": "性能线"},
                    "formal_expansion_track": {"summary": "扩题线"},
                    "challenge_track": {"summary": "challenge 线"},
                },
            },
        },
        {
            "advice": {
                "category": "stalled_tracking",
                "summary": "连续多轮 refresh 没有出现高信号变化，说明当前更需要推进主线动作，而不是继续做状态确认。",
                "recommended_focus": "formal_expansion_track",
                "recommended_actions": [
                    "暂停只做 refresh 的续跑，切回 A 线继续扩正式真实任务，优先补并发与协程、文件路径与 IO、新生态控制流问题。",
                ],
                "challenge_next_action": "重新 sourcing 第 2 条 challenge 候选",
            }
        },
    )

    assert action_board["source_refresh_id"] == "roadmap_tracking_demo_009"
    assert action_board["current_state"] == {
        "formal_task_count": 64,
        "challenge_task_count": 1,
        "ecosystem_count": 16,
        "candidate_count": None,
        "screened_candidate_count": None,
        "screened_with_task_count": None,
        "imported_candidate_count": None,
        "latest_frozen_task_count": 40,
        "frozen_40_streak": 8,
    }
    assert action_board["challenge_status"] == {
        "shortlist_candidate_count": None,
        "next_candidate_issue_ref": None,
        "next_action": "重新 sourcing 第 2 条 challenge 候选",
        "local_auth_readiness": {},
    }
    assert action_board["top_priorities"] == [
        {
            "priority": 1,
            "track": "formal_expansion_track",
            "reason": "连续多轮没有高信号变化，最需要新的正式任务推进来打破停滞。",
            "actions": [
                "优先补并发与协程、文件路径与 IO、新生态控制流问题。",
                "将下一轮实质改动落到任务新增或接入治理，而不是继续只跑 refresh。",
            ],
            "commands": [
                "python scripts/search_candidate_issues.py --target-family 并发与协程",
                "python scripts/search_candidate_issues.py --target-family \"文件路径与 IO\"",
                "python scripts/import_search_results.py --help",
            ],
            "docs": [
                "docs/v2_roadmap.md",
                "docs/issue_sourcing_brief_a2.md",
                "docs/next_actions.md",
            ],
            "done_signal": "至少完成一条真实候选的新增、筛选或正式接入，并让正式集相关状态发生可观测变化。",
            "when_to_refresh": "完成候选导入、task 接入或正式 manifest 更新后 refresh，确认 formal_task_count / candidate 状态是否变化。",
            "expected_tracking_signals": [
                "changed_fields 包含 formal_task_count、candidate_count 或 ecosystem_count",
                "snapshot_summary.current_state.formal_task_count 或 candidate_count 发生变化",
                "history_advice.category 从 stalled_tracking 开始松动，或 recent_no_material_change_streak 被打断",
            ],
        },
        {
            "priority": 2,
            "track": "challenge_track",
            "reason": "challenge 当前已有 1 条，下一步应继续补第 2 条代表系统边界的 hard case。",
            "actions": [
                "重新 sourcing 第 2 条 challenge 候选",
            ],
            "commands": [
                "python scripts/validate_challenge_shortlist.py",
                "python scripts/refresh_roadmap_tracking.py --run-label refresh",
            ],
            "docs": [
                "docs/challenge_sourcing_brief_a3.md",
                "docs/challenge_shortlist.md",
                "docs/challenge_set.md",
            ],
            "done_signal": "challenge shortlist 或 challenge manifest 出现新的有效候选 / 任务，并通过对应校验。",
            "when_to_refresh": "更新 shortlist、challenge task 或 challenge manifest 后 refresh，确认 challenge_task_count 或 next_action 是否变化。",
            "expected_tracking_signals": [
                "changed_fields 包含 challenge_task_count",
                "snapshot_summary.challenge_status.next_action 发生更新",
                "snapshot_summary.current_state.challenge_task_count 或 challenge_candidate_count 发生变化",
            ],
        },
        {
            "priority": 3,
            "track": "performance_track",
            "reason": "如果准备推进新策略版本，需要先补新的稳定性或性能证据，而不是重复 refresh。",
            "actions": [
                "优先补 stability recheck、时延定位或新的 runtime-different compare 证据。",
            ],
            "commands": [
                "python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines",
                "python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40_v68_v69",
                "python scripts/refresh_roadmap_tracking.py --run-label refresh",
            ],
            "docs": [
                "docs/v2_roadmap.md",
                "docs/next_actions.md",
                "docs/project_memory.md",
            ],
            "done_signal": "新增一份可解释当前性能判断的 stability、时延或环境基线证据产物。",
            "when_to_refresh": "补完新的性能证据后 refresh，确认 history advice 是否仍要求停留在 stalled_tracking。",
            "expected_tracking_signals": [
                "logs/summaries 中新增 env baseline 或 duration compare 产物",
                "outputs 中出现新的性能相关 summary 路径并被记录到最新 refresh",
                "history_advice.summary 或 action_board.priority 3 的判断依据发生更新",
                "如果性能证据足够强，history_advice.category 可能从 stalled_tracking 转向 investigate_regression 或 monitor_and_continue",
            ],
        },
    ]


def test_build_action_board_prioritizes_challenge_track_when_tracking_is_stalled_but_a4_gap_is_still_explicit() -> None:
    action_board = refresh_roadmap_tracking.build_action_board(
        {
            "refresh_id": "roadmap_tracking_demo_019",
            "headline": "roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK",
            "refresh_outcome": {
                "category": "no_material_change",
                "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
            },
            "snapshot_summary": {
                "current_state": {
                    "formal_task_count": 66,
                    "challenge_task_count": 3,
                    "ecosystem_count": 16,
                    "candidate_count": 69,
                    "screened_candidate_count": 0,
                    "screened_with_task_count": 0,
                    "imported_candidate_count": 0,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 0,
                    "next_candidate_issue_ref": None,
                    "next_action": "重新 sourcing 第 4 条 challenge 候选",
                    "local_auth_readiness": {
                        "env_token_present": False,
                        "env_token_looks_valid": False,
                        "gh_auth_logged_in": True,
                        "gh_auth_token_exportable": False,
                        "preferred_search_mode": "gh_session_fallback",
                    },
                },
                "roadmap_focus": {
                    "performance_track": {"summary": "性能线"},
                    "formal_expansion_track": {"summary": "扩题线"},
                    "challenge_track": {"summary": "challenge 线"},
                },
            },
        },
        {
            "advice": {
                "category": "stalled_tracking",
                "summary": "连续多轮 refresh 没有出现高信号变化，但当前 challenge 第 4 条候选缺口仍然非常明确，适合优先把这条边界展示线继续做实。",
                "recommended_focus": "challenge_track",
                "recommended_actions": [
                    "优先先做 challenge 第 4 条候选 sourcing，并把认证预检、搜索、导入、筛选串成一轮可复用动作。",
                    "如果 live GitHub 检索再次受阻，至少要把阻塞形态、认证状态和下一条可执行命令同步进 latest 文档与 tracking。",
                    "完成 challenge 线实质动作后再 refresh，避免继续只增加 no_material_change streak。",
                ],
                "challenge_next_action": "重新 sourcing 第 4 条 challenge 候选",
            }
        },
    )

    assert action_board["top_priorities"][0] == {
        "priority": 1,
        "track": "challenge_track",
        "reason": "连续多轮没有高信号变化，但 challenge 第 4 条候选缺口仍最具体，且本轮已确认外部动作首先卡在外部访问前置条件。",
        "actions": [
            "重新 sourcing 第 4 条 challenge 候选",
            "当前更可能直接走 gh 已登录会话；若 live 检索仍失败，优先记录 socket 或 API 阻塞，而不是先怀疑 token 导出链路。",
            "如果 live 检索仍失败，优先把认证或网络阻塞同步进 latest 文档与 tracking，而不是继续空跑 refresh。",
        ],
        "commands": [
            "gh auth status",
            "python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family \"文件路径与 IO\" --state closed --labels bug --limit 10 --run-label challenge_a4",
            "python scripts/import_search_results.py --search-result logs/summaries/candidate_search_challenge_a4_001.json --recommendation high --limit 3",
            "python scripts/screen_candidate.py --status imported --limit 3",
            "python scripts/validate_challenge_shortlist.py",
            "python scripts/refresh_roadmap_tracking.py --run-label refresh",
        ],
        "docs": [
            "docs/challenge_sourcing_brief_a3.md",
            "docs/challenge_shortlist.md",
            "docs/challenge_set.md",
        ],
        "done_signal": "challenge shortlist、candidate 或 challenge manifest 至少推进一步，或至少把当前 live sourcing 的真实阻塞状态同步为可复用 handoff 证据。",
        "when_to_refresh": "完成一轮 challenge 认证预检、搜索、导入、筛选或阻塞记录后 refresh，确认 challenge 线是否重新出现 progress。",
        "expected_tracking_signals": [
            "changed_fields 包含 challenge_task_count、challenge_next_action 或 challenge_shortlist_candidate_count",
            "refresh_outcome.category 不再只是 no_material_change，或 history advice 对 challenge 线的描述发生更新",
            "action_board 继续把 challenge 线保持在第一优先级，直到 shortlist 或 challenge manifest 发生推进",
        ],
    }


def test_build_status_card_keeps_only_minimum_handoff_signals() -> None:
    status_card = refresh_roadmap_tracking.build_status_card(
        {
            "refresh_id": "roadmap_tracking_demo_013",
            "headline": "roadmap: formal=64 challenge=1 eco=16 frozen=40 streak=8 validation=OK",
            "refresh_outcome": {
                "category": "no_material_change",
            },
        },
        {
            "recent_no_material_change_streak": 11,
            "advice": {
                "category": "stalled_tracking",
                "summary": "连续多轮 refresh 没有出现高信号变化，说明当前更需要推进主线动作，而不是继续做状态确认。",
            },
        },
        {
            "current_state": {
                "formal_task_count": 64,
                "challenge_task_count": 1,
                "ecosystem_count": 16,
                "candidate_count": 68,
                "screened_candidate_count": 1,
                "screened_with_task_count": 0,
                "imported_candidate_count": 2,
                "latest_frozen_task_count": 40,
                "frozen_40_streak": 8,
            },
            "challenge_status": {
                "shortlist_candidate_count": 1,
                "next_candidate_issue_ref": "samuelcolvin/watchfiles#110",
                "local_auth_readiness": {
                    "env_token_present": False,
                    "env_token_looks_valid": False,
                    "gh_auth_logged_in": True,
                    "gh_auth_token_exportable": False,
                    "preferred_search_mode": "gh_session_fallback",
                },
            },
            "top_priorities": [
                {
                    "track": "formal_expansion_track",
                    "reason": "连续多轮没有高信号变化，最需要新的正式任务推进来打破停滞。",
                    "actions": ["优先补并发与协程、文件路径与 IO、新生态控制流问题。"],
                    "commands": ["python scripts/search_candidate_issues.py --target-family 并发与协程"],
                    "done_signal": "至少完成一条真实候选的新增、筛选或正式接入，并让正式集相关状态发生可观测变化。",
                    "when_to_refresh": "完成候选导入、task 接入或正式 manifest 更新后 refresh，确认 formal_task_count / candidate 状态是否变化。",
                }
            ],
        },
    )

    assert status_card["source_refresh_id"] == "roadmap_tracking_demo_013"
    assert status_card["headline"] == "roadmap: formal=64 challenge=1 eco=16 frozen=40 streak=8 validation=OK"
    assert status_card["refresh_outcome_category"] == "no_material_change"
    assert status_card["history_advice_category"] == "stalled_tracking"
    assert status_card["recent_no_material_change_streak"] == 11
    assert status_card["current_state"] == {
        "formal_task_count": 64,
        "challenge_task_count": 1,
        "ecosystem_count": 16,
        "candidate_count": 68,
        "screened_candidate_count": 1,
        "screened_with_task_count": 0,
        "imported_candidate_count": 2,
        "latest_frozen_task_count": 40,
        "frozen_40_streak": 8,
    }
    assert status_card["challenge_status"] == {
        "shortlist_candidate_count": 1,
        "next_candidate_issue_ref": "samuelcolvin/watchfiles#110",
        "local_auth_readiness": {
            "env_token_present": False,
            "env_token_looks_valid": False,
            "gh_auth_logged_in": True,
            "gh_auth_token_exportable": False,
            "preferred_search_mode": "gh_session_fallback",
        },
    }
    assert status_card["top_priority"] == {
        "track": "formal_expansion_track",
        "reason": "连续多轮没有高信号变化，最需要新的正式任务推进来打破停滞。",
        "first_action": "优先补并发与协程、文件路径与 IO、新生态控制流问题。",
        "first_command": "python scripts/search_candidate_issues.py --target-family 并发与协程",
        "done_signal": "至少完成一条真实候选的新增、筛选或正式接入，并让正式集相关状态发生可观测变化。",
        "when_to_refresh": "完成候选导入、task 接入或正式 manifest 更新后 refresh，确认 formal_task_count / candidate 状态是否变化。",
    }


def test_build_action_board_prioritizes_real_performance_diagnostics_for_monitor_and_continue() -> None:
    action_board = refresh_roadmap_tracking.build_action_board(
        {
            "refresh_id": "roadmap_tracking_demo_014",
            "headline": "roadmap: formal=64 challenge=2 eco=16 frozen=40 streak=8 validation=OK",
            "refresh_outcome": {
                "category": "mixed",
                "summary": "检测到混合变化。",
            },
            "snapshot_summary": {
                "current_state": {
                    "formal_task_count": 64,
                    "challenge_task_count": 2,
                    "ecosystem_count": 16,
                    "candidate_count": 68,
                    "screened_candidate_count": 1,
                    "screened_with_task_count": 0,
                    "imported_candidate_count": 1,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 0,
                    "next_candidate_issue_ref": None,
                    "next_action": "重新 sourcing 第 3 条 challenge 候选",
                },
                "roadmap_focus": {
                    "performance_track": {"summary": "性能线"},
                    "formal_expansion_track": {"summary": "扩题线"},
                    "challenge_track": {"summary": "challenge 线"},
                },
            },
        },
        {
            "advice": {
                "category": "monitor_and_continue",
                "summary": "当前 history 没有暴露强回退，但也还没有形成明确推进信号，适合继续按 v2 roadmap 的主线小步推进。",
                "recommended_focus": "performance_or_expansion",
                "recommended_actions": [
                    "继续从性能复核常态化、正式集扩容、challenge sourcing 中选择一条最缺口明显的主线推进。",
                    "完成一轮实质改动后再 refresh，避免把 tracking 入口当作主工作本身。",
                ],
            }
        },
    )

    assert action_board["top_priorities"][0] == {
        "priority": 1,
        "track": "performance_track",
        "reason": "性能线",
        "actions": [
            "先补环境基线与公共任务时延对比，再决定是否继续下钻 run_tests / pytest startup。",
        ],
        "commands": [
            "python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines",
            "python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40_v68_v69",
            "python scripts/refresh_roadmap_tracking.py --run-label refresh",
        ],
        "docs": [
            "docs/v2_roadmap.md",
            "docs/next_actions.md",
            "docs/project_memory.md",
        ],
        "done_signal": "新增一轮稳定性、环境或时延证据，足以支持是否继续推进性能线。",
        "when_to_refresh": "补完新的性能复核产物后 refresh，观察 history advice 是否升级或回退。",
        "expected_tracking_signals": [
            "logs/summaries 中新增 env baseline 或 duration compare 产物",
            "history_advice.summary 对性能线的判断发生更新",
            "recent_no_material_change_streak 被打断，或建议优先级发生调整",
        ],
    }


def test_build_action_board_prioritizes_challenge_gap_when_monitor_and_continue_but_a4_is_still_missing() -> None:
    action_board = refresh_roadmap_tracking.build_action_board(
        {
            "refresh_id": "roadmap_tracking_demo_018",
            "headline": "roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK",
            "refresh_outcome": {
                "category": "no_material_change",
                "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
            },
            "snapshot_summary": {
                "current_state": {
                    "formal_task_count": 66,
                    "challenge_task_count": 3,
                    "ecosystem_count": 16,
                    "candidate_count": 69,
                    "screened_candidate_count": 0,
                    "screened_with_task_count": 0,
                    "imported_candidate_count": 0,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 0,
                    "next_candidate_issue_ref": None,
                    "next_action": "重新 sourcing 第 4 条 challenge 候选",
                },
                "roadmap_focus": {
                    "performance_track": {"summary": "性能线"},
                    "formal_expansion_track": {"summary": "扩题线"},
                    "challenge_track": {"summary": "challenge 线"},
                },
            },
        },
        {
            "advice": {
                "category": "monitor_and_continue",
                "summary": "当前 history 没有暴露强回退，但也还没有形成明确推进信号，适合继续按 v2 roadmap 的主线小步推进。",
                "recommended_focus": "performance_or_expansion",
                "recommended_actions": [
                    "继续从性能复核常态化、正式集扩容、challenge sourcing 中选择一条最缺口明显的主线推进。",
                    "完成一轮实质改动后再 refresh，避免把 tracking 入口当作主工作本身。",
                ],
            }
        },
    )

    assert action_board["top_priorities"][0] == {
        "priority": 1,
        "track": "challenge_track",
        "reason": "challenge 线当前缺口最具体：第 4 条候选仍未建立，且 shortlist 为空，适合优先把这条边界展示线继续做实。",
        "actions": [
            "重新 sourcing 第 4 条 challenge 候选",
            "优先从新生态或覆盖较薄生态里找平台 / 环境语境重、但仍可压成稳定本地回归的题。",
            "先做 gh 认证预检并清理无效 GITHUB_TOKEN，再继续 challenge 搜索、导入与筛选。",
            "如果 live 检索仍失败，优先把认证或网络阻塞同步进 latest 文档与 tracking，而不是继续空跑 refresh。",
        ],
        "commands": [
            "gh auth status",
            "Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue",
            "python scripts/search_candidate_issues.py --query bug --target-family \"文件路径与 IO\" --limit 10 --run-label challenge_a4",
            "python scripts/import_search_results.py --search-result logs/summaries/candidate_search_challenge_a4_001.json --recommendation high --limit 3",
            "python scripts/screen_candidate.py --status imported --limit 3",
            "python scripts/validate_challenge_shortlist.py",
            "python scripts/refresh_roadmap_tracking.py --run-label refresh",
        ],
        "docs": [
            "docs/challenge_sourcing_brief_a3.md",
            "docs/challenge_shortlist.md",
            "docs/challenge_set.md",
        ],
        "done_signal": "challenge shortlist、candidate 或 challenge manifest 至少推进一步，并让 latest 的 challenge_* 字段发生可观测变化。",
        "when_to_refresh": "完成一轮 challenge 搜索、导入、筛选或接入动作后 refresh，确认 challenge 线是否重新出现 progress。",
        "expected_tracking_signals": [
            "changed_fields 包含 challenge_task_count、challenge_next_action 或 challenge_shortlist_candidate_count",
            "refresh_outcome.category 不再只是 no_material_change",
            "action_board 继续把 challenge 线保持在第一优先级，直到 shortlist 或 challenge manifest 发生推进",
        ],
    }


def test_build_action_board_keeps_performance_track_when_progress_came_from_performance_fields() -> None:
    action_board = refresh_roadmap_tracking.build_action_board(
        {
            "refresh_id": "roadmap_tracking_demo_015",
            "headline": "roadmap: formal=64 challenge=2 eco=16 frozen=40 streak=8 validation=OK",
            "changed_fields": [
                "performance_env_baseline_snapshot_id",
                "performance_duration_compare_id",
                "performance_duration_compare_common_average_delta_sec",
            ],
            "refresh_outcome": {
                "category": "progress",
                "summary": "检测到正向推进：performance_duration_compare_id updated。",
            },
            "snapshot_summary": {
                "current_state": {
                    "formal_task_count": 64,
                    "challenge_task_count": 2,
                    "ecosystem_count": 16,
                    "candidate_count": 68,
                    "screened_candidate_count": 1,
                    "screened_with_task_count": 0,
                    "imported_candidate_count": 1,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 0,
                    "next_candidate_issue_ref": None,
                    "next_action": "重新 sourcing 第 3 条 challenge 候选",
                },
                "roadmap_focus": {
                    "performance_track": {
                        "summary": "继续把 v68 -> v69 的性能回升与环境噪声区分开，当前 pytest compare 口径应视为 runtime-equivalent noise probe。",
                    },
                    "formal_expansion_track": {"summary": "扩题线"},
                    "challenge_track": {"summary": "challenge 线"},
                },
            },
        },
        {
            "advice": {
                "category": "keep_momentum",
                "summary": "最近一次 refresh 已出现正向推进，当前应继续沿同一主线推进，并及时同步文档与评测证据。",
                "recommended_focus": "active_track",
                "recommended_actions": [
                    "继续沿最近一次产生变化的主线推进，避免在中途改成只做展示层更新。",
                    "保持每轮推进后同步 refresh、GUIDE、next_actions 和 optimization_log。",
                ],
            }
        },
    )

    assert action_board["top_priorities"][0] == {
        "priority": 1,
        "track": "performance_track",
        "reason": "最近一次 progress 来自性能证据补强，当前应继续沿 performance 线追证，而不是退回泛化续跑。",
        "actions": [
            "继续补环境基线、时延对比或 run_tests / pytest startup 下钻证据。",
            "继续沿最近一次产生变化的主线推进，避免在中途改成只做展示层更新。",
            "保持每轮推进后同步 refresh、GUIDE、next_actions 和 optimization_log。",
        ],
        "commands": [
            "python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines",
            "python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40_v68_v69",
            "python scripts/refresh_roadmap_tracking.py --run-label refresh",
        ],
        "docs": [
            "docs/v2_roadmap.md",
            "docs/next_actions.md",
            "docs/project_memory.md",
            "docs/optimization_log.md",
        ],
        "done_signal": "沿 performance 线继续产出新的环境、时延或阶段诊断证据，并让 changed_fields 保持落在 performance_*。",
        "when_to_refresh": "每补完一轮新的 performance 证据后 refresh，确认 progress 信号是否延续到同一轨道。",
        "expected_tracking_signals": [
            "refresh_outcome.category 维持或再次出现 progress",
            "changed_fields 继续包含 performance_* 字段",
        ],
    }


def test_build_action_board_uses_history_focus_when_keep_momentum_would_otherwise_fall_back_to_active_track() -> None:
    action_board = refresh_roadmap_tracking.build_action_board(
        {
            "refresh_id": "roadmap_tracking_demo_016",
            "headline": "roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK",
            "changed_fields": [],
            "refresh_outcome": {
                "category": "no_material_change",
                "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
            },
            "snapshot_summary": {
                "current_state": {
                    "formal_task_count": 66,
                    "challenge_task_count": 3,
                    "ecosystem_count": 16,
                    "candidate_count": 69,
                    "screened_candidate_count": 0,
                    "screened_with_task_count": 0,
                    "imported_candidate_count": 0,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 0,
                    "next_candidate_issue_ref": None,
                    "next_action": "重新 sourcing 第 4 条 challenge 候选",
                },
                "roadmap_focus": {
                    "performance_track": {
                        "summary": "继续沿性能证据主线推进。",
                    },
                    "formal_expansion_track": {"summary": "扩题线"},
                    "challenge_track": {"summary": "challenge 线"},
                },
            },
        },
        {
            "advice": {
                "category": "keep_momentum",
                "summary": "最近一轮虽然没有新增高信号变化，但距离上一次 progress 很近，当前更适合继续沿最近证明有效的主线推进。",
                "recommended_focus": "performance_track",
                "recommended_actions": [
                    "继续沿最近一次产生 progress 的主线推进，避免因为一轮 no_material_change 就切回泛化探索。",
                    "补完同主线的新证据或接入动作后再 refresh，确认 progress 是否恢复。",
                ],
                "progress_track": "performance_track",
                "source_progress_refresh_id": "roadmap_tracking_refresh_041",
            }
        },
    )

    assert action_board["top_priorities"][0]["track"] == "performance_track"
    assert action_board["top_priorities"][0]["reason"] == "最近一次 progress 来自性能证据补强，当前应继续沿 performance 线追证，而不是退回泛化续跑。"


def test_build_action_board_makes_challenge_track_commands_more_actionable() -> None:
    action_board = refresh_roadmap_tracking.build_action_board(
        {
            "refresh_id": "roadmap_tracking_demo_017",
            "headline": "roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK",
            "changed_fields": [],
            "refresh_outcome": {
                "category": "no_material_change",
                "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
            },
            "snapshot_summary": {
                "current_state": {
                    "formal_task_count": 66,
                    "challenge_task_count": 3,
                    "ecosystem_count": 16,
                    "candidate_count": 69,
                    "screened_candidate_count": 0,
                    "screened_with_task_count": 0,
                    "imported_candidate_count": 0,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 0,
                    "next_candidate_issue_ref": None,
                    "next_action": "重新 sourcing 第 4 条 challenge 候选",
                },
                "roadmap_focus": {
                    "performance_track": {"summary": "性能线"},
                    "formal_expansion_track": {"summary": "扩题线"},
                    "challenge_track": {"summary": "challenge 线"},
                },
            },
        },
        {
            "advice": {
                "category": "keep_momentum",
                "summary": "最近一轮虽然没有新增高信号变化，但距离上一次 progress 很近，当前更适合继续沿最近证明有效的主线推进。",
                "recommended_focus": "challenge_track",
                "recommended_actions": [
                    "继续沿最近一次产生 progress 的主线推进，避免因为一轮 no_material_change 就切回泛化探索。",
                    "补完同主线的新证据或接入动作后再 refresh，确认 progress 是否恢复。",
                ],
                "progress_track": "challenge_track",
                "source_progress_refresh_id": "roadmap_tracking_refresh_037",
            }
        },
    )

    assert action_board["top_priorities"][0] == {
        "priority": 1,
        "track": "challenge_track",
        "reason": "最近一次 progress 来自 challenge 线，当前应继续沿 challenge sourcing / 接入动作推进。",
        "actions": [
            "重新 sourcing 第 4 条 challenge 候选",
            "优先从新生态或当前覆盖较薄生态里找平台 / 环境语境重、但仍能压成稳定本地回归的题。",
            "先做 gh 认证预检并清理无效 GITHUB_TOKEN，再继续 challenge 搜索、导入与筛选。",
            "如果 live 检索仍失败，优先把认证或网络阻塞同步进 latest 文档与 tracking，而不是继续空跑 refresh。",
            "继续沿最近一次产生 progress 的主线推进，避免因为一轮 no_material_change 就切回泛化探索。",
            "补完同主线的新证据或接入动作后再 refresh，确认 progress 是否恢复。",
        ],
        "commands": [
            "gh auth status",
            "Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue",
            "python scripts/search_candidate_issues.py --query bug --target-family \"文件路径与 IO\" --limit 10 --run-label challenge_a4",
            "python scripts/import_search_results.py --search-result logs/summaries/candidate_search_challenge_a4_001.json --recommendation high --limit 3",
            "python scripts/screen_candidate.py --status imported --limit 3",
            "python scripts/validate_challenge_shortlist.py",
            "python scripts/refresh_roadmap_tracking.py --run-label refresh",
        ],
        "docs": [
            "docs/challenge_sourcing_brief_a3.md",
            "docs/challenge_shortlist.md",
            "docs/optimization_log.md",
        ],
        "done_signal": "challenge 线继续产生新的 shortlist / task / manifest 变化，并在 refresh 中保持 challenge_* 字段更新。",
        "when_to_refresh": "每完成一轮 challenge 动作后 refresh，确认 progress 是否继续落在 challenge 线。",
        "expected_tracking_signals": [
            "refresh_outcome.category 维持或再次出现 progress",
            "changed_fields 继续包含 challenge_* 字段",
        ],
    }


def test_build_action_board_prefers_env_token_cleanup_when_challenge_readiness_points_to_env_token() -> None:
    action_board = refresh_roadmap_tracking.build_action_board(
        {
            "refresh_id": "roadmap_tracking_demo_021",
            "headline": "roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK",
            "refresh_outcome": {
                "category": "no_material_change",
                "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
            },
            "snapshot_summary": {
                "current_state": {
                    "formal_task_count": 66,
                    "challenge_task_count": 3,
                    "ecosystem_count": 16,
                    "candidate_count": 69,
                    "screened_candidate_count": 0,
                    "screened_with_task_count": 0,
                    "imported_candidate_count": 0,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 0,
                    "next_candidate_issue_ref": None,
                    "next_action": "重新 sourcing 第 4 条 challenge 候选",
                    "local_auth_readiness": {
                        "env_token_present": True,
                        "env_token_looks_valid": True,
                        "gh_auth_logged_in": False,
                        "gh_auth_token_exportable": False,
                        "preferred_search_mode": "env_token",
                    },
                },
                "roadmap_focus": {
                    "performance_track": {"summary": "性能线"},
                    "formal_expansion_track": {"summary": "扩题线"},
                    "challenge_track": {"summary": "challenge 线"},
                },
            },
        },
        {
            "advice": {
                "category": "stalled_tracking",
                "summary": "连续多轮 refresh 没有出现高信号变化，但当前 challenge 第 4 条候选缺口仍然非常明确，适合优先把这条边界展示线继续做实。",
                "recommended_focus": "challenge_track",
                "recommended_actions": [],
            }
        },
    )

    assert action_board["top_priorities"][0]["actions"] == [
        "重新 sourcing 第 4 条 challenge 候选",
        "当前 latest 检测到环境变量 token 将优先生效；若要排除环境污染，先清理 GITHUB_TOKEN 再复核 gh 会话。",
        "如果 live 检索仍失败，优先把认证或网络阻塞同步进 latest 文档与 tracking，而不是继续空跑 refresh。",
    ]
    assert action_board["top_priorities"][0]["commands"][:3] == [
        "Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue",
        "gh auth status",
        "python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family \"文件路径与 IO\" --state closed --labels bug --limit 10 --run-label challenge_a4",
    ]


def test_build_refresh_markdown_surfaces_fast_paths_and_output_indexes() -> None:
    markdown = refresh_roadmap_tracking.build_refresh_markdown(
        {
            "headline": "roadmap: formal=64 challenge=1 eco=16 frozen=40 streak=8 validation=OK",
            "validation": {
                "passed": True,
                "errors": [],
                "tasks_dir": "tasks",
                "candidate_file": "candidates.json",
                "challenge_shortlist": "challenge_shortlist.md",
                "formal_manifest": "formal_manifest.json",
            },
            "outputs": {
                "audit_summary_json_path": "audit.json",
                "maturity_summary_json_path": "maturity.json",
                "snapshot_summary_json_path": "snapshot.json",
                "history_summary_json_path": "history.json",
                "history_summary_md_path": "history.md",
                "action_board_json_path": "action_board.json",
                "action_board_md_path": "action_board.md",
                "status_card_json_path": "status_card.json",
                "status_card_md_path": "status_card.md",
            },
            "refresh_outcome": {
                "category": "no_material_change",
                "summary": "相对上一份 latest，高信号字段没有变化，当前 refresh 主要是在确认状态延续。",
            },
            "history_overview": {
                "total_refresh_count": 14,
                "recent_no_material_change_streak": 12,
                "category_counts": {"no_material_change": 12},
                "advice": {
                    "category": "stalled_tracking",
                    "summary": "连续多轮 refresh 没有出现高信号变化，说明当前更需要推进主线动作，而不是继续做状态确认。",
                },
            },
            "previous_latest_summary_json_path": "latest.json",
            "changed_fields": [],
            "delta": {
                "change_count": 0,
                "field_changes": [],
            },
            "snapshot_summary": {
                "current_state": {
                    "formal_task_count": 64,
                    "challenge_task_count": 1,
                    "ecosystem_count": 16,
                    "candidate_count": 65,
                    "screened_candidate_count": 1,
                    "screened_with_task_count": 0,
                    "imported_candidate_count": 2,
                    "latest_frozen_task_count": 40,
                    "frozen_40_streak": 8,
                },
                "challenge_status": {
                    "shortlist_candidate_count": 1,
                    "next_candidate_issue_ref": "samuelcolvin/watchfiles#110",
                    "next_action": "优先评估 challenge 候选 samuelcolvin/watchfiles#110",
                    "local_auth_readiness": {
                        "env_token_present": False,
                        "env_token_looks_valid": False,
                        "gh_auth_logged_in": True,
                        "gh_auth_token_exportable": False,
                        "preferred_search_mode": "gh_session_fallback",
                    },
                },
            },
        }
    )

    assert "- action_board_json_path: `action_board.json`" in markdown
    assert "- status_card_json_path: `status_card.json`" in markdown
    assert "## Fast Paths" in markdown
    assert "- status_card: `适合 30 秒内接管当前状态`" in markdown
    assert "- action_board: `适合直接开始执行下一步动作`" in markdown
    assert "- screened_candidate_count: `1`" in markdown
    assert "- screened_with_task_count: `0`" in markdown
    assert "- imported_candidate_count: `2`" in markdown
    assert "- challenge_shortlist_candidate_count: `1`" in markdown
    assert "- challenge_next_candidate_issue_ref: `samuelcolvin/watchfiles#110`" in markdown
    assert "- challenge_next_action: `优先评估 challenge 候选 samuelcolvin/watchfiles#110`" in markdown

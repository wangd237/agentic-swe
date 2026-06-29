from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import summarize_code_intelligence_runs


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_run(
    base_dir: Path,
    *,
    task_id: str,
    run_id: str,
    backend: str,
    enabled: bool,
    fallback_reason: str = "",
    final_status: str = "incomplete",
    accepted_final_status: str = "not_accepted",
    total_tokens: int = 333,
    total_tool_calls: int = 3,
    grep_calls: int = 1,
    read_file_calls: int = 1,
    localize_steps: int = 2,
    include_code_intelligence_trace: bool = True,
) -> Path:
    run_dir = base_dir / task_id / run_id
    result_path = run_dir / "result.json"
    trace_path = run_dir / "trace.json"
    write_json(
        result_path,
        {
            "task_id": task_id,
            "run_id": run_id,
            "final_status": final_status,
            "accepted_final_status": accepted_final_status,
            "incomplete_reason": "" if final_status == "success" else "no_patch",
            "summary": "demo",
            "modified_files": ["demo_pkg/hostname.py"] if enabled and not fallback_reason else [],
            "recommended_files": ["demo_pkg/hostname.py", "tests/test_hostname.py"],
            "tool_stats": {
                "total_tool_calls": total_tool_calls,
                "llm_usage": {
                    "call_count": 2,
                    "total_tokens": total_tokens,
                    "missing_usage_count": 0,
                },
                "code_intelligence": {
                    "backend": backend,
                    "enabled": enabled,
                    "available": enabled,
                    "backend_version": "codebase-memory-mcp 0.8.1" if enabled else "",
                    "backend_binary_path": "codebase-memory-mcp" if enabled else "",
                    "fallback_reason": fallback_reason,
                    "candidates": [
                        {
                            "relative_path": "demo_pkg/hostname.py",
                            "reason": "graph_search:Class:HostnameValidator",
                            "evidence": ["rank 1"],
                            "confidence": 0.95,
                        }
                    ]
                    if enabled and not fallback_reason
                    else [],
                    "compact_hints": "Graph-assisted localization hints"
                    if enabled and not fallback_reason
                    else "",
                    "metrics": {
                        "index_attempted": enabled,
                        "index_success": enabled and not fallback_reason,
                        "index_duration_sec": 0.05 if enabled and not fallback_reason else None,
                        "index_used_shadow_copy": enabled,
                        "indexed_node_count": 10 if enabled and not fallback_reason else None,
                        "indexed_edge_count": 16 if enabled and not fallback_reason else None,
                        "graph_tool_calls_total": 1 if enabled and not fallback_reason else 0,
                        "graph_search_graph_calls": 1 if enabled and not fallback_reason else 0,
                        "graph_query_duration_sec_total": 0.02 if enabled and not fallback_reason else 0,
                        "graph_result_raw_chars": 400 if enabled and not fallback_reason else 0,
                        "graph_result_compact_chars": 200 if enabled and not fallback_reason else 0,
                        "graph_compaction_ratio": 0.5 if enabled and not fallback_reason else 0,
                        "graph_candidates_count": 1 if enabled and not fallback_reason else 0,
                    },
                },
                "patch_diff_chars": 42,
            },
        },
    )
    write_json(
        trace_path,
        {
            "task_id": task_id,
            "run_id": run_id,
            "total_tool_calls": total_tool_calls,
            "steps": [
                *(
                    [
                        {
                            "phase": "understand",
                            "action_type": "code_intelligence",
                            "tool_name": backend,
                            "observation": "Graph-assisted localization hints",
                            "tool_metrics": {
                                "candidates": [
                                    {"relative_path": "demo_pkg/hostname.py"},
                                ],
                                "compact_hints": "Graph-assisted localization hints",
                            },
                        }
                    ]
                    if enabled and not fallback_reason and include_code_intelligence_trace
                    else []
                ),
                *[
                    {"phase": "localize", "action_type": "tool_call", "tool_name": "grep"}
                    for _ in range(grep_calls)
                ],
                *[
                    {"phase": "localize", "action_type": "tool_call", "tool_name": "read_file"}
                    for _ in range(read_file_calls)
                ],
                *[
                    {"phase": "localize", "action_type": "think", "tool_name": ""}
                    for _ in range(max(localize_steps - grep_calls - read_file_calls, 0))
                ],
                {"phase": "verify", "action_type": "tool_call", "tool_name": "run_tests"},
            ],
        },
    )
    return result_path


def test_build_run_snapshot_extracts_graph_and_agent_metrics(tmp_path: Path) -> None:
    result_path = make_run(
        tmp_path,
        task_id="task_graph",
        run_id="run_001",
        backend="codebase_memory_cli",
        enabled=True,
    )

    snapshot = summarize_code_intelligence_runs.build_run_snapshot(result_path=result_path)

    assert snapshot["backend"] == "codebase_memory_cli"
    assert snapshot["backend_enabled"] is True
    assert snapshot["index_success"] is True
    assert snapshot["graph_tool_calls_total"] == 1
    assert snapshot["graph_candidates_top_files"] == ["demo_pkg/hostname.py"]
    assert snapshot["source_target_files"] == ["demo_pkg/hostname.py"]
    assert snapshot["first_correct_file_rank"] == 1
    assert snapshot["correct_file_in_top_1"] is True
    assert snapshot["first_correct_source_file_rank"] == 1
    assert snapshot["source_file_in_top_1"] is True
    assert snapshot["graph_hints_generated"] is True
    assert snapshot["graph_hints_presented_to_model"] is True
    assert snapshot["graph_hint_used_in_patch"] is True
    assert snapshot["graph_hint_used_by_model"] is True
    assert snapshot["llm_total_tokens"] == 333
    assert snapshot["grep_calls"] == 1
    assert snapshot["read_file_calls"] == 1
    assert snapshot["run_tests_calls"] == 1
    assert snapshot["localize_step_count"] == 2


def test_summarize_code_intelligence_runs_writes_outputs(tmp_path: Path) -> None:
    success_result = make_run(
        tmp_path,
        task_id="task_graph",
        run_id="run_success",
        backend="codebase_memory_cli",
        enabled=True,
    )
    fallback_result = make_run(
        tmp_path,
        task_id="task_graph",
        run_id="run_fallback",
        backend="codebase_memory_cli",
        enabled=True,
        fallback_reason="backend_error",
    )

    output = summarize_code_intelligence_runs.summarize_code_intelligence_runs(
        result_paths=[success_result, fallback_result],
        cohort_label="graph_smoke",
        output_dir=tmp_path / "logs" / "summaries",
    )

    summary = output["summary"]
    assert output["summary_id"] == "code_intelligence_runs_graph_smoke_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
    assert summary["run_count"] == 2
    assert summary["aggregate"]["graph_enabled_count"] == 2
    assert summary["aggregate"]["fallback_rate"] == 0.5
    assert summary["aggregate"]["correct_file_top1_count"] == 1
    assert summary["aggregate"]["source_file_top1_count"] == 1
    assert summary["aggregate"]["average_graph_tool_calls"] == 0.5


def test_summarize_code_intelligence_runs_builds_ab_pair_deltas(tmp_path: Path) -> None:
    baseline_result = make_run(
        tmp_path,
        task_id="task_graph",
        run_id="run_baseline",
        backend="none",
        enabled=False,
        total_tokens=500,
        total_tool_calls=6,
        grep_calls=2,
        read_file_calls=3,
        localize_steps=5,
    )
    candidate_result = make_run(
        tmp_path,
        task_id="task_graph",
        run_id="run_graph",
        backend="codebase_memory_cli",
        enabled=True,
        total_tokens=350,
        total_tool_calls=4,
        grep_calls=1,
        read_file_calls=1,
        localize_steps=2,
    )

    output = summarize_code_intelligence_runs.summarize_code_intelligence_runs(
        result_paths=[baseline_result, candidate_result],
        cohort_label="graph_ab",
        output_dir=tmp_path / "logs" / "summaries",
        include_ab_pairs=True,
    )

    summary = output["summary"]
    pair = summary["ab_pairs"][0]
    assert pair["task_id"] == "task_graph"
    assert pair["baseline_run_id"] == "run_baseline"
    assert pair["candidate_run_id"] == "run_graph"
    assert pair["token_delta"] == -150
    assert pair["tool_call_delta"] == -2
    assert pair["localize_step_delta"] == -3
    assert pair["read_file_call_delta"] == -2
    assert pair["grep_call_delta"] == -1
    assert pair["candidate_graph_calls"] == 1
    assert pair["candidate_correct_file_rank"] == 1
    assert pair["candidate_correct_source_file_rank"] == 1
    assert summary["ab_aggregate"]["pair_count"] == 1
    assert summary["ab_aggregate"]["average_token_delta"] == -150
    assert summary["ab_aggregate"]["average_tool_call_delta"] == -2
    assert summary["ab_aggregate"]["candidate_correct_file_top1_count"] == 1
    assert summary["ab_aggregate"]["candidate_source_file_top1_count"] == 1
    assert summary["ab_aggregate"]["graph_hints_generated_count"] == 1
    assert summary["ab_aggregate"]["graph_hints_presented_to_model_count"] == 1
    assert summary["ab_aggregate"]["graph_hint_used_in_patch_count"] == 1
    assert summary["ab_aggregate"]["success_improved_count"] == 0
    assert summary["ab_aggregate"]["success_regressed_count"] == 0
    assert summary["ab_aggregate"]["accepted_improved_count"] == 0
    assert summary["ab_aggregate"]["accepted_regressed_count"] == 0


def test_v16_acceptance_passes_when_real_ab_metrics_meet_gate(tmp_path: Path) -> None:
    result_paths: list[Path] = []
    for index in range(8):
        task_id = f"task_{index:03d}"
        result_paths.append(
            make_run(
                tmp_path,
                task_id=task_id,
                run_id=f"{task_id}_baseline",
                backend="none",
                enabled=False,
                final_status="success",
                accepted_final_status="accepted",
                total_tokens=500,
                total_tool_calls=6,
                grep_calls=2,
                read_file_calls=3,
                localize_steps=5,
            )
        )
        result_paths.append(
            make_run(
                tmp_path,
                task_id=task_id,
                run_id=f"{task_id}_graph",
                backend="codebase_memory_cli",
                enabled=True,
                final_status="success",
                accepted_final_status="accepted",
                total_tokens=350,
                total_tool_calls=4,
                grep_calls=1,
                read_file_calls=1,
                localize_steps=2,
            )
        )

    summary = summarize_code_intelligence_runs.build_summary(
        result_paths=result_paths,
        cohort_label="v16_acceptance_pass",
        include_ab_pairs=True,
    )

    acceptance = summary["v16_acceptance"]
    assert acceptance["ready_to_judge"] is True
    assert acceptance["accepted"] is True
    assert acceptance["failed_check_ids"] == []


def test_v16_acceptance_fails_when_costs_regress(tmp_path: Path) -> None:
    result_paths: list[Path] = []
    for index in range(8):
        task_id = f"task_{index:03d}"
        result_paths.append(
            make_run(
                tmp_path,
                task_id=task_id,
                run_id=f"{task_id}_baseline",
                backend="none",
                enabled=False,
                final_status="success",
                accepted_final_status="accepted",
                total_tokens=300,
                total_tool_calls=3,
                grep_calls=1,
                read_file_calls=1,
                localize_steps=2,
            )
        )
        result_paths.append(
            make_run(
                tmp_path,
                task_id=task_id,
                run_id=f"{task_id}_graph",
                backend="codebase_memory_cli",
                enabled=True,
                final_status="success",
                accepted_final_status="accepted",
                total_tokens=450,
                total_tool_calls=5,
                grep_calls=2,
                read_file_calls=2,
                localize_steps=4,
            )
        )

    summary = summarize_code_intelligence_runs.build_summary(
        result_paths=result_paths,
        cohort_label="v16_acceptance_fail",
        include_ab_pairs=True,
    )

    acceptance = summary["v16_acceptance"]
    assert acceptance["ready_to_judge"] is True
    assert acceptance["accepted"] is False
    assert "tokens_not_increased_on_average" in acceptance["failed_check_ids"]
    assert "tool_calls_not_increased_on_average" in acceptance["failed_check_ids"]
    assert "localize_steps_not_increased_on_average" in acceptance["failed_check_ids"]


def test_v16_acceptance_allows_success_and_accepted_improvements(tmp_path: Path) -> None:
    result_paths: list[Path] = []
    for index in range(8):
        task_id = f"task_{index:03d}"
        result_paths.append(
            make_run(
                tmp_path,
                task_id=task_id,
                run_id=f"{task_id}_baseline",
                backend="none",
                enabled=False,
                final_status="incomplete",
                accepted_final_status="not_accepted",
                total_tokens=500,
                total_tool_calls=6,
                grep_calls=2,
                read_file_calls=3,
                localize_steps=5,
            )
        )
        result_paths.append(
            make_run(
                tmp_path,
                task_id=task_id,
                run_id=f"{task_id}_graph",
                backend="codebase_memory_cli",
                enabled=True,
                final_status="success",
                accepted_final_status="accepted",
                total_tokens=350,
                total_tool_calls=4,
                grep_calls=1,
                read_file_calls=1,
                localize_steps=2,
            )
        )

    summary = summarize_code_intelligence_runs.build_summary(
        result_paths=result_paths,
        cohort_label="v16_acceptance_improvement",
        include_ab_pairs=True,
    )

    assert summary["ab_aggregate"]["success_improved_count"] == 8
    assert summary["ab_aggregate"]["success_regressed_count"] == 0
    assert summary["ab_aggregate"]["accepted_improved_count"] == 8
    assert summary["ab_aggregate"]["accepted_regressed_count"] == 0
    assert summary["v16_acceptance"]["accepted"] is True
    no_regression_check = next(
        item
        for item in summary["v16_acceptance"]["checks"]
        if item["id"] == "no_success_or_acceptance_regression"
    )
    assert no_regression_check["status"] == "passed"


def test_v16_acceptance_fails_on_success_or_accepted_regression(tmp_path: Path) -> None:
    result_paths: list[Path] = []
    for index in range(8):
        task_id = f"task_{index:03d}"
        result_paths.append(
            make_run(
                tmp_path,
                task_id=task_id,
                run_id=f"{task_id}_baseline",
                backend="none",
                enabled=False,
                final_status="success",
                accepted_final_status="accepted",
                total_tokens=500,
                total_tool_calls=6,
                grep_calls=2,
                read_file_calls=3,
                localize_steps=5,
            )
        )
        result_paths.append(
            make_run(
                tmp_path,
                task_id=task_id,
                run_id=f"{task_id}_graph",
                backend="codebase_memory_cli",
                enabled=True,
                final_status="incomplete",
                accepted_final_status="not_accepted",
                total_tokens=350,
                total_tool_calls=4,
                grep_calls=1,
                read_file_calls=1,
                localize_steps=2,
            )
        )

    summary = summarize_code_intelligence_runs.build_summary(
        result_paths=result_paths,
        cohort_label="v16_acceptance_regression",
        include_ab_pairs=True,
    )

    assert summary["ab_aggregate"]["success_regressed_count"] == 8
    assert summary["ab_aggregate"]["accepted_regressed_count"] == 8
    assert summary["v16_acceptance"]["accepted"] is False
    assert "no_success_or_acceptance_regression" in summary["v16_acceptance"]["failed_check_ids"]


def test_v16_acceptance_reports_graph_hint_evidence_layers(tmp_path: Path) -> None:
    result_paths: list[Path] = []
    for index in range(8):
        task_id = f"task_{index:03d}"
        result_paths.append(
            make_run(
                tmp_path,
                task_id=task_id,
                run_id=f"{task_id}_baseline",
                backend="none",
                enabled=False,
                final_status="success",
                accepted_final_status="accepted",
                total_tokens=500,
                total_tool_calls=6,
                grep_calls=2,
                read_file_calls=3,
                localize_steps=5,
            )
        )
        graph_result = make_run(
            tmp_path,
            task_id=task_id,
            run_id=f"{task_id}_graph",
            backend="codebase_memory_cli",
            enabled=True,
            final_status="success",
            accepted_final_status="accepted",
            total_tokens=350,
            total_tool_calls=4,
            grep_calls=1,
            read_file_calls=1,
            localize_steps=2,
        )
        result = json.loads(graph_result.read_text(encoding="utf-8"))
        result["modified_files"] = []
        graph_result.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        result_paths.append(graph_result)

    summary = summarize_code_intelligence_runs.build_summary(
        result_paths=result_paths,
        cohort_label="v16_graph_hint_layers",
        include_ab_pairs=True,
    )

    assert summary["ab_aggregate"]["graph_hints_generated_count"] == 8
    assert summary["ab_aggregate"]["graph_hints_presented_to_model_count"] == 8
    assert summary["ab_aggregate"]["graph_hint_used_in_patch_count"] == 0
    assert summary["v16_acceptance"]["accepted"] is False
    graph_check = next(
        item for item in summary["v16_acceptance"]["checks"] if item["id"] == "graph_hint_used_at_least_once"
    )
    assert graph_check["observed"] == {
        "generated_count": 8,
        "presented_to_model_count": 8,
        "used_in_patch_count": 0,
        "legacy_used_by_model_count": 0,
    }


def test_build_run_snapshot_tracks_source_rank_separately_from_test_rank(tmp_path: Path) -> None:
    result_path = make_run(
        tmp_path,
        task_id="task_graph",
        run_id="run_source_rank",
        backend="codebase_memory_cli",
        enabled=True,
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["tool_stats"]["code_intelligence"]["candidates"] = [
        {"relative_path": "tests/test_hostname.py", "confidence": 0.95},
        {"relative_path": "demo_pkg/hostname.py", "confidence": 0.9},
    ]
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    snapshot = summarize_code_intelligence_runs.build_run_snapshot(result_path=result_path)

    assert snapshot["target_files"] == ["demo_pkg/hostname.py", "tests/test_hostname.py"]
    assert snapshot["source_target_files"] == ["demo_pkg/hostname.py"]
    assert snapshot["first_correct_file_rank"] == 1
    assert snapshot["first_correct_source_file_rank"] == 2
    assert snapshot["correct_file_in_top_1"] is True
    assert snapshot["source_file_in_top_1"] is False
    assert snapshot["source_file_in_top_3"] is True


def make_v16_acceptance_pair_results(
    base_dir: Path,
    *,
    pair_count: int = 8,
    candidate_tokens: int = 350,
    candidate_tool_calls: int = 4,
    candidate_grep_calls: int = 1,
    candidate_read_file_calls: int = 1,
    candidate_localize_steps: int = 2,
) -> list[Path]:
    result_paths: list[Path] = []
    for index in range(pair_count):
        task_id = f"task_{index:03d}"
        result_paths.append(
            make_run(
                base_dir,
                task_id=task_id,
                run_id=f"{task_id}_baseline",
                backend="none",
                enabled=False,
                final_status="success",
                accepted_final_status="accepted",
                total_tokens=500,
                total_tool_calls=6,
                grep_calls=2,
                read_file_calls=3,
                localize_steps=5,
            )
        )
        result_paths.append(
            make_run(
                base_dir,
                task_id=task_id,
                run_id=f"{task_id}_graph",
                backend="codebase_memory_cli",
                enabled=True,
                final_status="success",
                accepted_final_status="accepted",
                total_tokens=candidate_tokens,
                total_tool_calls=candidate_tool_calls,
                grep_calls=candidate_grep_calls,
                read_file_calls=candidate_read_file_calls,
                localize_steps=candidate_localize_steps,
            )
        )
    return result_paths


def test_main_require_v16_acceptance_fails_without_ab_pairs(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    result_paths = make_v16_acceptance_pair_results(tmp_path / "runs")
    output_dir = tmp_path / "summaries"
    argv = [
        "summarize_code_intelligence_runs.py",
        *[item for path in result_paths for item in ("--result", str(path))],
        "--cohort-label",
        "cli_without_ab_pairs",
        "--output-dir",
        str(output_dir),
        "--require-v16-acceptance",
    ]
    monkeypatch.setattr(sys, "argv", argv)

    exit_code = summarize_code_intelligence_runs.main()
    captured = capsys.readouterr()

    assert exit_code == 3
    assert "summary_json_path:" in captured.out
    summary_path = output_dir / "code_intelligence_runs_cli_without_ab_pairs_001.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "ab_pairs" not in summary
    assert "v16_acceptance" not in summary


def test_main_require_v16_acceptance_returns_3_when_acceptance_fails(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    result_paths = make_v16_acceptance_pair_results(
        tmp_path / "runs",
        candidate_tokens=650,
        candidate_tool_calls=8,
        candidate_grep_calls=3,
        candidate_read_file_calls=4,
        candidate_localize_steps=7,
    )
    output_dir = tmp_path / "summaries"
    argv = [
        "summarize_code_intelligence_runs.py",
        *[item for path in result_paths for item in ("--result", str(path))],
        "--cohort-label",
        "cli_acceptance_fail",
        "--output-dir",
        str(output_dir),
        "--ab-pairs",
        "--require-v16-acceptance",
    ]
    monkeypatch.setattr(sys, "argv", argv)

    exit_code = summarize_code_intelligence_runs.main()
    captured = capsys.readouterr()

    assert exit_code == 3
    assert "v16_acceptance_accepted: False" in captured.out
    assert "tokens_not_increased_on_average" in captured.out
    summary_path = output_dir / "code_intelligence_runs_cli_acceptance_fail_001.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["v16_acceptance"]["accepted"] is False
    assert "tokens_not_increased_on_average" in summary["v16_acceptance"]["failed_check_ids"]


def test_main_require_v16_acceptance_returns_0_when_acceptance_passes(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    result_paths = make_v16_acceptance_pair_results(tmp_path / "runs")
    output_dir = tmp_path / "summaries"
    argv = [
        "summarize_code_intelligence_runs.py",
        *[item for path in result_paths for item in ("--result", str(path))],
        "--cohort-label",
        "cli_acceptance_pass",
        "--output-dir",
        str(output_dir),
        "--ab-pairs",
        "--require-v16-acceptance",
    ]
    monkeypatch.setattr(sys, "argv", argv)

    exit_code = summarize_code_intelligence_runs.main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "v16_acceptance_accepted: True" in captured.out
    assert "v16_acceptance_failed_checks: []" in captured.out
    summary_path = output_dir / "code_intelligence_runs_cli_acceptance_pass_001.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["ab_aggregate"]["pair_count"] == 8
    assert summary["v16_acceptance"]["accepted"] is True


def test_main_require_v16_acceptance_replay_needs_targets_for_rank_metrics(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    result_paths = make_v16_acceptance_pair_results(tmp_path / "runs")
    for result_path in result_paths:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["recommended_files"] = []
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    targets_path = tmp_path / "targets.json"
    write_json(
        targets_path,
        {f"task_{index:03d}": ["demo_pkg/hostname.py", "tests/test_hostname.py"] for index in range(8)},
    )
    base_argv = [
        "summarize_code_intelligence_runs.py",
        *[item for path in result_paths for item in ("--result", str(path))],
        "--output-dir",
        str(tmp_path / "summaries"),
        "--ab-pairs",
        "--require-v16-acceptance",
    ]

    monkeypatch.setattr(
        sys,
        "argv",
        [
            *base_argv,
            "--cohort-label",
            "cli_replay_without_targets",
        ],
    )
    exit_code_without_targets = summarize_code_intelligence_runs.main()
    captured_without_targets = capsys.readouterr()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            *base_argv,
            "--cohort-label",
            "cli_replay_with_targets",
            "--targets-json",
            str(targets_path),
        ],
    )
    exit_code_with_targets = summarize_code_intelligence_runs.main()
    captured_with_targets = capsys.readouterr()

    assert exit_code_without_targets == 3
    assert "candidate_source_top1_all_pairs" in captured_without_targets.out
    assert exit_code_with_targets == 0
    assert "v16_acceptance_accepted: True" in captured_with_targets.out
    with_targets_summary = json.loads(
        (tmp_path / "summaries" / "code_intelligence_runs_cli_replay_with_targets_001.json").read_text(
            encoding="utf-8"
        )
    )
    assert with_targets_summary["ab_aggregate"]["candidate_source_file_top1_count"] == 8
    assert with_targets_summary["v16_acceptance"]["failed_check_ids"] == []

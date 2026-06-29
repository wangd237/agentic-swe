"""Summarize code intelligence metrics from agent result/trace files."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _round_float(value: float) -> float:
    return round(value, 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return _round_float(sum(values) / len(values))


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_summary_id(output_dir: Path, cohort_label: str) -> str:
    prefix = f"code_intelligence_runs_{cohort_label}_"
    existing_numbers: list[int] = []
    for path in output_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _tool_counts(trace: dict[str, Any]) -> dict[str, int]:
    counts = {
        "tool_calls_total": int(trace.get("total_tool_calls") or 0),
        "grep_calls": 0,
        "search_code_calls": 0,
        "read_file_calls": 0,
        "run_tests_calls": 0,
        "write_or_edit_calls": 0,
        "localize_step_count": 0,
    }
    for step in _as_list(trace.get("steps")):
        tool_name = step.get("tool_name") or ""
        action_type = step.get("action_type") or ""
        phase = step.get("phase") or ""
        if tool_name == "grep":
            counts["grep_calls"] += 1
        if tool_name == "search_code":
            counts["search_code_calls"] += 1
        if tool_name == "read_file":
            counts["read_file_calls"] += 1
        if tool_name == "run_tests":
            counts["run_tests_calls"] += 1
        if tool_name in {"write_file", "edit_file"}:
            counts["write_or_edit_calls"] += 1
        if phase == "localize" or action_type == "localize":
            counts["localize_step_count"] += 1
    return counts


def _graph_top_files(code_intelligence: dict[str, Any]) -> list[str]:
    candidates = _as_list(code_intelligence.get("candidates"))
    files: list[str] = []
    for candidate in candidates:
        relative_path = str(candidate.get("relative_path") or "")
        if relative_path and relative_path not in files:
            files.append(relative_path)
    return files


def _first_target_rank(top_files: list[str], target_files: list[str]) -> int | None:
    normalized_targets = {target.replace("\\", "/") for target in target_files}
    for index, path in enumerate(top_files, start=1):
        if path.replace("\\", "/") in normalized_targets:
            return index
    return None


def _is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    parts = normalized.split("/")
    name = parts[-1] if parts else normalized
    return (
        "tests" in parts
        or "test" in parts
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name == "conftest.py"
    )


def _source_files(paths: list[str]) -> list[str]:
    return [path for path in paths if not _is_test_path(path)]


def _trace_path_for_result(result_path: str | Path) -> Path:
    result = Path(result_path)
    return result.with_name("trace.json")


def _graph_hints_presented_to_model(trace: dict[str, Any]) -> bool:
    for step in _as_list(trace.get("steps")):
        if step.get("action_type") != "code_intelligence":
            continue
        observation = str(step.get("observation") or "")
        tool_metrics = step.get("tool_metrics") if isinstance(step.get("tool_metrics"), dict) else {}
        candidates = _as_list(tool_metrics.get("candidates"))
        compact_hints = str(tool_metrics.get("compact_hints") or "")
        if candidates or compact_hints or "Graph-assisted localization hints" in observation:
            return True
    return False


def build_run_snapshot(
    *,
    result_path: str | Path,
    trace_path: str | Path | None = None,
    target_files: list[str] | None = None,
) -> dict[str, Any]:
    result_file = Path(result_path)
    trace_file = Path(trace_path) if trace_path else _trace_path_for_result(result_file)
    result = _load_json(result_file)
    trace = _load_json(trace_file) if trace_file.exists() else {"steps": [], "total_tool_calls": 0}
    tool_stats = result.get("tool_stats", {})
    code_intelligence = tool_stats.get("code_intelligence", {})
    ci_metrics = code_intelligence.get("metrics", {}) if isinstance(code_intelligence, dict) else {}
    llm_usage = tool_stats.get("llm_usage", {})
    graph_top_files = _graph_top_files(code_intelligence if isinstance(code_intelligence, dict) else {})
    target_files_for_run = target_files if target_files is not None else result.get("recommended_files", [])
    first_correct_file_rank = _first_target_rank(graph_top_files, target_files_for_run)
    source_target_files = _source_files([str(path) for path in target_files_for_run])
    first_correct_source_file_rank = _first_target_rank(graph_top_files, source_target_files)
    modified_files = [str(path).replace("\\", "/") for path in _as_list(result.get("modified_files"))]
    graph_hints_generated = bool(graph_top_files or code_intelligence.get("compact_hints"))
    graph_hints_presented_to_model = _graph_hints_presented_to_model(trace)
    graph_hint_used_in_patch = bool(set(modified_files) & set(graph_top_files))
    graph_hint_used_by_model = graph_hint_used_in_patch
    counts = _tool_counts(trace)

    return {
        "task_id": result.get("task_id", ""),
        "run_id": result.get("run_id", ""),
        "result_path": str(result_file),
        "trace_path": str(trace_file) if trace_file.exists() else "",
        "backend": code_intelligence.get("backend", "none") if isinstance(code_intelligence, dict) else "none",
        "backend_enabled": bool(code_intelligence.get("enabled")) if isinstance(code_intelligence, dict) else False,
        "backend_available": bool(code_intelligence.get("available")) if isinstance(code_intelligence, dict) else False,
        "backend_version": code_intelligence.get("backend_version", "") if isinstance(code_intelligence, dict) else "",
        "backend_binary_path": code_intelligence.get("backend_binary_path", "") if isinstance(code_intelligence, dict) else "",
        "fallback_reason": code_intelligence.get("fallback_reason", "") if isinstance(code_intelligence, dict) else "",
        "index_attempted": bool(ci_metrics.get("index_attempted")),
        "index_success": bool(ci_metrics.get("index_success")),
        "index_duration_sec": ci_metrics.get("index_duration_sec"),
        "index_used_shadow_copy": bool(ci_metrics.get("index_used_shadow_copy")),
        "indexed_node_count": ci_metrics.get("indexed_node_count"),
        "indexed_edge_count": ci_metrics.get("indexed_edge_count"),
        "indexed_file_count": ci_metrics.get("indexed_file_count"),
        "graph_tool_calls_total": int(ci_metrics.get("graph_tool_calls_total") or 0),
        "graph_search_graph_calls": int(ci_metrics.get("graph_search_graph_calls") or 0),
        "graph_query_duration_sec_total": float(ci_metrics.get("graph_query_duration_sec_total") or 0.0),
        "graph_result_raw_chars": int(ci_metrics.get("graph_result_raw_chars") or 0),
        "graph_result_compact_chars": int(ci_metrics.get("graph_result_compact_chars") or 0),
        "graph_compaction_ratio": float(ci_metrics.get("graph_compaction_ratio") or 0.0),
        "graph_candidates_count": int(ci_metrics.get("graph_candidates_count") or 0),
        "graph_candidates_top_files": graph_top_files[:5],
        "target_files": target_files_for_run,
        "source_target_files": source_target_files,
        "first_correct_file_rank": first_correct_file_rank,
        "correct_file_in_top_1": first_correct_file_rank == 1,
        "correct_file_in_top_3": first_correct_file_rank is not None and first_correct_file_rank <= 3,
        "first_correct_source_file_rank": first_correct_source_file_rank,
        "source_file_in_top_1": first_correct_source_file_rank == 1,
        "source_file_in_top_3": (
            first_correct_source_file_rank is not None and first_correct_source_file_rank <= 3
        ),
        "graph_hints_generated": graph_hints_generated,
        "graph_hints_presented_to_model": graph_hints_presented_to_model,
        "graph_hint_used_in_patch": graph_hint_used_in_patch,
        "graph_hint_used_by_model": graph_hint_used_by_model,
        "llm_call_count": int(llm_usage.get("call_count") or 0),
        "llm_total_tokens": int(llm_usage.get("total_tokens") or 0),
        **counts,
        "final_status": result.get("final_status", ""),
        "accepted_final_status": result.get("accepted_final_status", ""),
        "incomplete_reason": result.get("incomplete_reason", ""),
        "evidence_quality": tool_stats.get("evidence_quality", ""),
        "verification_strength": result.get("verification_strength") or tool_stats.get("verification_strength", ""),
        "verification_level": result.get("verification_level") or tool_stats.get("verification_level", ""),
        "missing_evidence": result.get("missing_evidence") or tool_stats.get("missing_evidence", []),
        "modified_files": modified_files,
        "modified_file_count": len(modified_files),
        "patch_diff_chars": int(tool_stats.get("patch_diff_chars") or 0),
    }


def build_summary(
    *,
    result_paths: list[str | Path],
    cohort_label: str,
    target_files_by_task: dict[str, list[str]] | None = None,
    include_ab_pairs: bool = False,
    baseline_backend: str = "none",
    candidate_backend: str = "codebase_memory_cli",
) -> dict[str, Any]:
    snapshots: list[dict[str, Any]] = []
    targets = target_files_by_task or {}
    for result_path in result_paths:
        result = _load_json(result_path)
        task_id = str(result.get("task_id", ""))
        snapshots.append(
            build_run_snapshot(
                result_path=result_path,
                target_files=targets.get(task_id),
            )
        )

    graph_enabled = [item for item in snapshots if item["backend_enabled"]]
    graph_available = [item for item in graph_enabled if item["backend_available"]]
    accepted = [item for item in snapshots if item["accepted_final_status"] == "accepted"]
    success = [item for item in snapshots if item["final_status"] == "success"]
    index_durations = [
        float(item["index_duration_sec"])
        for item in graph_enabled
        if item["index_duration_sec"] is not None
    ]
    summary = {
        "created_at": _utc_timestamp(),
        "cohort_label": cohort_label,
        "run_count": len(snapshots),
        "task_ids": [item["task_id"] for item in snapshots],
        "aggregate": {
            "success_rate": _round_float(len(success) / len(snapshots)) if snapshots else 0.0,
            "accepted_success_rate": _round_float(len(accepted) / len(snapshots)) if snapshots else 0.0,
            "graph_enabled_count": len(graph_enabled),
            "graph_available_count": len(graph_available),
            "fallback_count": len([item for item in graph_enabled if item["fallback_reason"]]),
            "fallback_rate": _round_float(
                len([item for item in graph_enabled if item["fallback_reason"]]) / len(graph_enabled)
            )
            if graph_enabled
            else 0.0,
            "average_index_duration_sec": _average(index_durations),
            "average_graph_query_duration_sec": _average(
                [item["graph_query_duration_sec_total"] for item in graph_enabled]
            ),
            "average_graph_tool_calls": _average([float(item["graph_tool_calls_total"]) for item in graph_enabled]),
            "average_graph_raw_chars": _average([float(item["graph_result_raw_chars"]) for item in graph_enabled]),
            "average_graph_compact_chars": _average(
                [float(item["graph_result_compact_chars"]) for item in graph_enabled]
            ),
            "correct_file_top1_count": len([item for item in snapshots if item["correct_file_in_top_1"]]),
            "correct_file_top3_count": len([item for item in snapshots if item["correct_file_in_top_3"]]),
            "source_file_top1_count": len([item for item in snapshots if item["source_file_in_top_1"]]),
            "source_file_top3_count": len([item for item in snapshots if item["source_file_in_top_3"]]),
            "graph_hints_generated_count": len([item for item in snapshots if item["graph_hints_generated"]]),
            "graph_hints_presented_to_model_count": len(
                [item for item in snapshots if item["graph_hints_presented_to_model"]]
            ),
            "graph_hint_used_in_patch_count": len([item for item in snapshots if item["graph_hint_used_in_patch"]]),
            "graph_hint_used_by_model_count": len([item for item in snapshots if item["graph_hint_used_by_model"]]),
            "average_llm_tokens": _average([float(item["llm_total_tokens"]) for item in snapshots]),
            "average_llm_calls": _average([float(item["llm_call_count"]) for item in snapshots]),
            "average_tool_calls": _average([float(item["tool_calls_total"]) for item in snapshots]),
            "average_localize_steps": _average([float(item["localize_step_count"]) for item in snapshots]),
            "average_read_file_calls": _average([float(item["read_file_calls"]) for item in snapshots]),
            "average_grep_calls": _average([float(item["grep_calls"]) for item in snapshots]),
            "average_modified_file_count": _average([float(item["modified_file_count"]) for item in snapshots]),
            "average_patch_diff_chars": _average([float(item["patch_diff_chars"]) for item in snapshots]),
        },
        "run_snapshots": snapshots,
    }
    if include_ab_pairs:
        summary["ab_pairs"] = build_ab_pairs(
            snapshots,
            baseline_backend=baseline_backend,
            candidate_backend=candidate_backend,
        )
        summary["ab_aggregate"] = build_ab_aggregate(summary["ab_pairs"])
        summary["v16_acceptance"] = build_v16_acceptance(summary=summary)
    return summary


def _backend_matches(snapshot: dict[str, Any], backend: str) -> bool:
    if backend == "none":
        return snapshot["backend"] in {"none", ""} or not snapshot["backend_enabled"]
    return snapshot["backend"] == backend


def _numeric_delta(candidate: dict[str, Any], baseline: dict[str, Any], key: str) -> float:
    return _round_float(float(candidate.get(key) or 0) - float(baseline.get(key) or 0))


def _rank_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> int | None:
    candidate_rank = candidate.get("first_correct_file_rank")
    baseline_rank = baseline.get("first_correct_file_rank")
    if candidate_rank is None or baseline_rank is None:
        return None
    return int(candidate_rank) - int(baseline_rank)


def _source_rank_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> int | None:
    candidate_rank = candidate.get("first_correct_source_file_rank")
    baseline_rank = baseline.get("first_correct_source_file_rank")
    if candidate_rank is None or baseline_rank is None:
        return None
    return int(candidate_rank) - int(baseline_rank)


def _success_score(status: str) -> int:
    if status == "success":
        return 2
    if status.startswith("success"):
        return 1
    return 0


def _accepted_score(status: str) -> int:
    if status in {"accepted", "accepted_success"}:
        return 3
    if status.startswith("accepted") or status in {"local_smoke_success", "success_weak_verification"}:
        return 2
    if status and status != "not_accepted":
        return 1
    return 0


def _direction(candidate_score: int, baseline_score: int) -> str:
    if candidate_score > baseline_score:
        return "improved"
    if candidate_score < baseline_score:
        return "regressed"
    return "same"


def build_ab_pairs(
    snapshots: list[dict[str, Any]],
    *,
    baseline_backend: str,
    candidate_backend: str,
) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    task_ids = sorted({item["task_id"] for item in snapshots})
    for task_id in task_ids:
        task_snapshots = [item for item in snapshots if item["task_id"] == task_id]
        baseline_runs = [item for item in task_snapshots if _backend_matches(item, baseline_backend)]
        candidate_runs = [item for item in task_snapshots if _backend_matches(item, candidate_backend)]
        if not baseline_runs or not candidate_runs:
            continue
        baseline = baseline_runs[0]
        candidate = candidate_runs[0]
        success_direction = _direction(
            _success_score(candidate["final_status"]),
            _success_score(baseline["final_status"]),
        )
        accepted_direction = _direction(
            _accepted_score(candidate["accepted_final_status"]),
            _accepted_score(baseline["accepted_final_status"]),
        )
        pairs.append(
            {
                "task_id": task_id,
                "baseline_backend": baseline["backend"],
                "candidate_backend": candidate["backend"],
                "baseline_run_id": baseline["run_id"],
                "candidate_run_id": candidate["run_id"],
                "baseline_status": baseline["final_status"],
                "candidate_status": candidate["final_status"],
                "baseline_accepted": baseline["accepted_final_status"],
                "candidate_accepted": candidate["accepted_final_status"],
                "success_changed": baseline["final_status"] != candidate["final_status"],
                "accepted_changed": baseline["accepted_final_status"] != candidate["accepted_final_status"],
                "success_direction": success_direction,
                "accepted_direction": accepted_direction,
                "token_delta": _numeric_delta(candidate, baseline, "llm_total_tokens"),
                "llm_call_delta": _numeric_delta(candidate, baseline, "llm_call_count"),
                "tool_call_delta": _numeric_delta(candidate, baseline, "tool_calls_total"),
                "localize_step_delta": _numeric_delta(candidate, baseline, "localize_step_count"),
                "read_file_call_delta": _numeric_delta(candidate, baseline, "read_file_calls"),
                "grep_call_delta": _numeric_delta(candidate, baseline, "grep_calls"),
                "search_code_call_delta": _numeric_delta(candidate, baseline, "search_code_calls"),
                "modified_file_count_delta": _numeric_delta(candidate, baseline, "modified_file_count"),
                "patch_diff_chars_delta": _numeric_delta(candidate, baseline, "patch_diff_chars"),
                "candidate_graph_calls": candidate["graph_tool_calls_total"],
                "candidate_index_duration_sec": candidate["index_duration_sec"],
                "candidate_graph_query_duration_sec": candidate["graph_query_duration_sec_total"],
                "candidate_fallback_reason": candidate["fallback_reason"],
                "baseline_correct_file_rank": baseline["first_correct_file_rank"],
                "candidate_correct_file_rank": candidate["first_correct_file_rank"],
                "correct_file_rank_delta": _rank_delta(candidate, baseline),
                "candidate_correct_file_top1": candidate["correct_file_in_top_1"],
                "candidate_correct_file_top3": candidate["correct_file_in_top_3"],
                "baseline_correct_source_file_rank": baseline["first_correct_source_file_rank"],
                "candidate_correct_source_file_rank": candidate["first_correct_source_file_rank"],
                "source_file_rank_delta": _source_rank_delta(candidate, baseline),
                "candidate_source_file_top1": candidate["source_file_in_top_1"],
                "candidate_source_file_top3": candidate["source_file_in_top_3"],
                "graph_hints_generated": candidate["graph_hints_generated"],
                "graph_hints_presented_to_model": candidate["graph_hints_presented_to_model"],
                "graph_hint_used_in_patch": candidate["graph_hint_used_in_patch"],
                "graph_hint_used_by_model": candidate["graph_hint_used_by_model"],
            }
        )
    return pairs


def build_ab_aggregate(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "pair_count": len(pairs),
        "candidate_fallback_count": len([item for item in pairs if item["candidate_fallback_reason"]]),
        "candidate_fallback_rate": _round_float(
            len([item for item in pairs if item["candidate_fallback_reason"]]) / len(pairs)
        )
        if pairs
        else 0.0,
        "success_changed_count": len([item for item in pairs if item["success_changed"]]),
        "accepted_changed_count": len([item for item in pairs if item["accepted_changed"]]),
        "success_improved_count": len([item for item in pairs if item["success_direction"] == "improved"]),
        "success_regressed_count": len([item for item in pairs if item["success_direction"] == "regressed"]),
        "accepted_improved_count": len([item for item in pairs if item["accepted_direction"] == "improved"]),
        "accepted_regressed_count": len([item for item in pairs if item["accepted_direction"] == "regressed"]),
        "average_token_delta": _average([float(item["token_delta"]) for item in pairs]),
        "average_llm_call_delta": _average([float(item["llm_call_delta"]) for item in pairs]),
        "average_tool_call_delta": _average([float(item["tool_call_delta"]) for item in pairs]),
        "average_localize_step_delta": _average([float(item["localize_step_delta"]) for item in pairs]),
        "average_read_file_call_delta": _average([float(item["read_file_call_delta"]) for item in pairs]),
        "average_grep_call_delta": _average([float(item["grep_call_delta"]) for item in pairs]),
        "average_search_code_call_delta": _average([float(item["search_code_call_delta"]) for item in pairs]),
        "average_candidate_graph_calls": _average([float(item["candidate_graph_calls"]) for item in pairs]),
        "average_candidate_index_duration_sec": _average(
            [
                float(item["candidate_index_duration_sec"])
                for item in pairs
                if item["candidate_index_duration_sec"] is not None
            ]
        ),
        "candidate_correct_file_top1_count": len([item for item in pairs if item["candidate_correct_file_top1"]]),
        "candidate_correct_file_top3_count": len([item for item in pairs if item["candidate_correct_file_top3"]]),
        "candidate_source_file_top1_count": len([item for item in pairs if item["candidate_source_file_top1"]]),
        "candidate_source_file_top3_count": len([item for item in pairs if item["candidate_source_file_top3"]]),
        "graph_hints_generated_count": len([item for item in pairs if item["graph_hints_generated"]]),
        "graph_hints_presented_to_model_count": len(
            [item for item in pairs if item["graph_hints_presented_to_model"]]
        ),
        "graph_hint_used_in_patch_count": len([item for item in pairs if item["graph_hint_used_in_patch"]]),
        "graph_hint_used_by_model_count": len([item for item in pairs if item["graph_hint_used_by_model"]]),
        "average_modified_file_count_delta": _average(
            [float(item["modified_file_count_delta"]) for item in pairs]
        ),
        "average_patch_diff_chars_delta": _average([float(item["patch_diff_chars_delta"]) for item in pairs]),
    }


def _check_status(passed: bool, *, needs_real_ab: bool = True) -> str:
    if not needs_real_ab:
        return "not_applicable"
    return "passed" if passed else "failed"


def build_v16_acceptance(
    *,
    summary: dict[str, Any],
    minimum_pair_count: int = 8,
) -> dict[str, Any]:
    if "ab_pairs" not in summary:
        return {
            "ready_to_judge": False,
            "accepted": False,
            "reason": "missing_ab_pairs",
            "minimum_pair_count": minimum_pair_count,
            "checks": [
                {
                    "id": "ab_pairs_present",
                    "status": "failed",
                    "observed": 0,
                    "required": "A/B pairs generated with --ab-pairs",
                }
            ],
        }

    ab_aggregate = summary.get("ab_aggregate", {})
    pair_count = int(ab_aggregate.get("pair_count") or 0)
    candidate_fallback_rate = float(ab_aggregate.get("candidate_fallback_rate") or 0.0)
    average_token_delta = float(ab_aggregate.get("average_token_delta") or 0.0)
    average_tool_call_delta = float(ab_aggregate.get("average_tool_call_delta") or 0.0)
    average_localize_step_delta = float(ab_aggregate.get("average_localize_step_delta") or 0.0)
    average_read_file_call_delta = float(ab_aggregate.get("average_read_file_call_delta") or 0.0)
    average_grep_call_delta = float(ab_aggregate.get("average_grep_call_delta") or 0.0)
    accepted_improved_count = int(ab_aggregate.get("accepted_improved_count") or 0)
    accepted_regressed_count = int(ab_aggregate.get("accepted_regressed_count") or 0)
    success_improved_count = int(ab_aggregate.get("success_improved_count") or 0)
    success_regressed_count = int(ab_aggregate.get("success_regressed_count") or 0)
    source_top1 = int(ab_aggregate.get("candidate_source_file_top1_count") or 0)
    source_top3 = int(ab_aggregate.get("candidate_source_file_top3_count") or 0)
    graph_hints_generated = int(ab_aggregate.get("graph_hints_generated_count") or 0)
    graph_hints_presented = int(ab_aggregate.get("graph_hints_presented_to_model_count") or 0)
    graph_hint_used_in_patch = int(ab_aggregate.get("graph_hint_used_in_patch_count") or 0)
    graph_hint_used = int(ab_aggregate.get("graph_hint_used_by_model_count") or 0)

    checks = [
        {
            "id": "minimum_sample_size",
            "status": _check_status(pair_count >= minimum_pair_count),
            "observed": pair_count,
            "required": f">={minimum_pair_count} A/B pairs",
        },
        {
            "id": "candidate_no_fallback",
            "status": _check_status(candidate_fallback_rate == 0.0),
            "observed": candidate_fallback_rate,
            "required": "candidate_fallback_rate == 0.0",
        },
        {
            "id": "candidate_source_top1_all_pairs",
            "status": _check_status(pair_count > 0 and source_top1 == pair_count),
            "observed": source_top1,
            "required": "candidate source file top1 for every pair",
        },
        {
            "id": "candidate_source_top3_all_pairs",
            "status": _check_status(pair_count > 0 and source_top3 == pair_count),
            "observed": source_top3,
            "required": "candidate source file top3 for every pair",
        },
        {
            "id": "tokens_not_increased_on_average",
            "status": _check_status(average_token_delta <= 0),
            "observed": average_token_delta,
            "required": "average_token_delta <= 0",
        },
        {
            "id": "tool_calls_not_increased_on_average",
            "status": _check_status(average_tool_call_delta <= 0.5),
            "observed": average_tool_call_delta,
            "required": "average_tool_call_delta <= 0.5",
        },
        {
            "id": "localize_steps_not_increased_on_average",
            "status": _check_status(average_localize_step_delta <= 0),
            "observed": average_localize_step_delta,
            "required": "average_localize_step_delta <= 0",
        },
        {
            "id": "read_file_calls_not_increased_on_average",
            "status": _check_status(average_read_file_call_delta <= 0),
            "observed": average_read_file_call_delta,
            "required": "average_read_file_call_delta <= 0",
        },
        {
            "id": "grep_calls_not_increased_on_average",
            "status": _check_status(average_grep_call_delta <= 0),
            "observed": average_grep_call_delta,
            "required": "average_grep_call_delta <= 0",
        },
        {
            "id": "no_success_or_acceptance_regression",
            "status": _check_status(success_regressed_count == 0 and accepted_regressed_count == 0),
            "observed": {
                "success_improved_count": success_improved_count,
                "success_regressed_count": success_regressed_count,
                "accepted_improved_count": accepted_improved_count,
                "accepted_regressed_count": accepted_regressed_count,
            },
            "required": "no success/accepted status regressions; improvements are allowed",
        },
        {
            "id": "graph_hint_used_at_least_once",
            "status": _check_status(graph_hint_used > 0),
            "observed": {
                "generated_count": graph_hints_generated,
                "presented_to_model_count": graph_hints_presented,
                "used_in_patch_count": graph_hint_used_in_patch,
                "legacy_used_by_model_count": graph_hint_used,
            },
            "required": ">0 graph-assisted patch usage evidence",
        },
    ]
    failed_checks = [item for item in checks if item["status"] != "passed"]
    return {
        "ready_to_judge": pair_count >= minimum_pair_count,
        "accepted": not failed_checks,
        "reason": "all_checks_passed" if not failed_checks else "checks_failed",
        "minimum_pair_count": minimum_pair_count,
        "failed_check_ids": [item["id"] for item in failed_checks],
        "checks": checks,
    }


def build_markdown(summary: dict[str, Any]) -> str:
    aggregate = summary["aggregate"]
    rows = "\n".join(
        (
            f"| `{item['task_id']}` | `{item['backend']}` | `{item['run_id']}` | "
            f"`{item['final_status']}` | `{item['accepted_final_status']}` | "
            f"{item['llm_total_tokens']} | {item['llm_call_count']} | {item['tool_calls_total']} | "
            f"{item['graph_tool_calls_total']} | {item['index_duration_sec']} | "
            f"{item['first_correct_file_rank'] or 'N/A'} | "
            f"{item['first_correct_source_file_rank'] or 'N/A'} | "
            f"`{item['fallback_reason'] or 'none'}` |"
        )
        for item in summary["run_snapshots"]
    ) or "| N/A | N/A | N/A | N/A | N/A | 0 | 0 | 0 | 0 | N/A | N/A | N/A | N/A |"

    ab_section = ""
    if "ab_pairs" in summary:
        ab_aggregate = summary.get("ab_aggregate", {})
        v16_acceptance = summary.get("v16_acceptance", {})
        ab_rows = "\n".join(
            (
                f"| `{item['task_id']}` | `{item['baseline_run_id']}` | `{item['candidate_run_id']}` | "
                f"{item['token_delta']} | {item['llm_call_delta']} | {item['tool_call_delta']} | "
                f"{item['localize_step_delta']} | {item['read_file_call_delta']} | {item['grep_call_delta']} | "
                f"{item['candidate_graph_calls']} | {item['candidate_index_duration_sec']} | "
                f"{item['candidate_correct_file_rank'] or 'N/A'} | "
                f"{item['candidate_correct_source_file_rank'] or 'N/A'} | "
                f"`{item['candidate_fallback_reason'] or 'none'}` |"
            )
            for item in summary["ab_pairs"]
        ) or "| N/A | N/A | N/A | 0 | 0 | 0 | 0 | 0 | 0 | 0 | N/A | N/A | N/A | N/A |"
        ab_section = f"""
## A/B Pairs

- pair_count: `{ab_aggregate.get("pair_count", 0)}`
- candidate_fallback_rate: `{ab_aggregate.get("candidate_fallback_rate", 0.0)}`
- average_token_delta: `{ab_aggregate.get("average_token_delta", 0.0)}`
- average_llm_call_delta: `{ab_aggregate.get("average_llm_call_delta", 0.0)}`
- average_tool_call_delta: `{ab_aggregate.get("average_tool_call_delta", 0.0)}`
- average_localize_step_delta: `{ab_aggregate.get("average_localize_step_delta", 0.0)}`
- average_read_file_call_delta: `{ab_aggregate.get("average_read_file_call_delta", 0.0)}`
- average_grep_call_delta: `{ab_aggregate.get("average_grep_call_delta", 0.0)}`
- average_candidate_graph_calls: `{ab_aggregate.get("average_candidate_graph_calls", 0.0)}`
- average_candidate_index_duration_sec: `{ab_aggregate.get("average_candidate_index_duration_sec", 0.0)}`
- candidate_correct_file_top1_count: `{ab_aggregate.get("candidate_correct_file_top1_count", 0)}`
- candidate_source_file_top1_count: `{ab_aggregate.get("candidate_source_file_top1_count", 0)}`
- graph_hints_generated_count: `{ab_aggregate.get("graph_hints_generated_count", 0)}`
- graph_hints_presented_to_model_count: `{ab_aggregate.get("graph_hints_presented_to_model_count", 0)}`
- graph_hint_used_in_patch_count: `{ab_aggregate.get("graph_hint_used_in_patch_count", 0)}`
- graph_hint_used_by_model_count: `{ab_aggregate.get("graph_hint_used_by_model_count", 0)}`
- success_improved_count: `{ab_aggregate.get("success_improved_count", 0)}`
- success_regressed_count: `{ab_aggregate.get("success_regressed_count", 0)}`
- accepted_improved_count: `{ab_aggregate.get("accepted_improved_count", 0)}`
- accepted_regressed_count: `{ab_aggregate.get("accepted_regressed_count", 0)}`
- v16_acceptance_ready_to_judge: `{v16_acceptance.get("ready_to_judge", False)}`
- v16_acceptance_accepted: `{v16_acceptance.get("accepted", False)}`
- v16_acceptance_failed_checks: `{v16_acceptance.get("failed_check_ids", [])}`

| Task | Baseline Run | Candidate Run | Token Delta | LLM Call Delta | Tool Call Delta | Localize Delta | Read File Delta | Grep Delta | Graph Calls | Index Sec | Candidate Correct Rank | Candidate Source Rank | Candidate Fallback |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
{ab_rows}
"""

    return f"""# Code Intelligence Run Summary

## Cohort

- cohort_label: `{summary["cohort_label"]}`
- run_count: `{summary["run_count"]}`
- task_ids: `{summary["task_ids"]}`

## Aggregate

- success_rate: `{aggregate["success_rate"]}`
- accepted_success_rate: `{aggregate["accepted_success_rate"]}`
- graph_enabled_count: `{aggregate["graph_enabled_count"]}`
- graph_available_count: `{aggregate["graph_available_count"]}`
- fallback_rate: `{aggregate["fallback_rate"]}`
- average_index_duration_sec: `{aggregate["average_index_duration_sec"]}`
- average_graph_query_duration_sec: `{aggregate["average_graph_query_duration_sec"]}`
- average_graph_tool_calls: `{aggregate["average_graph_tool_calls"]}`
- average_graph_raw_chars: `{aggregate["average_graph_raw_chars"]}`
- average_graph_compact_chars: `{aggregate["average_graph_compact_chars"]}`
- correct_file_top1_count: `{aggregate["correct_file_top1_count"]}`
- correct_file_top3_count: `{aggregate["correct_file_top3_count"]}`
- source_file_top1_count: `{aggregate["source_file_top1_count"]}`
- source_file_top3_count: `{aggregate["source_file_top3_count"]}`
- average_llm_tokens: `{aggregate["average_llm_tokens"]}`
- average_llm_calls: `{aggregate["average_llm_calls"]}`
- average_tool_calls: `{aggregate["average_tool_calls"]}`

## Runs

| Task | Backend | Run ID | Status | Accepted | Tokens | LLM Calls | Tool Calls | Graph Calls | Index Sec | Correct File Rank | Source File Rank | Fallback |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
{rows}
{ab_section}
"""


def summarize_code_intelligence_runs(
    *,
    result_paths: list[str | Path],
    cohort_label: str,
    output_dir: str | Path = "logs/summaries",
    target_files_by_task: dict[str, list[str]] | None = None,
    include_ab_pairs: bool = False,
    baseline_backend: str = "none",
    candidate_backend: str = "codebase_memory_cli",
) -> dict[str, Any]:
    summary = build_summary(
        result_paths=result_paths,
        cohort_label=cohort_label,
        target_files_by_task=target_files_by_task,
        include_ab_pairs=include_ab_pairs,
        baseline_backend=baseline_backend,
        candidate_backend=candidate_backend,
    )
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    summary_id = _next_summary_id(output_directory, cohort_label)
    summary["summary_id"] = summary_id
    summary_json_path = output_directory / f"{summary_id}.json"
    summary_md_path = output_directory / f"{summary_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_markdown(summary))
    return {
        "summary_id": summary_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def _load_targets(path: str | Path | None) -> dict[str, list[str]]:
    if not path:
        return {}
    payload = _load_json(path)
    return {
        str(task_id): [str(item) for item in _as_list(files)]
        for task_id, files in payload.items()
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize code intelligence metrics from result/trace files.")
    parser.add_argument("--result", action="append", required=True, help="Path to result.json. Repeatable.")
    parser.add_argument("--cohort-label", default="manual", help="Label used in output filenames.")
    parser.add_argument("--output-dir", default="logs/summaries", help="Directory for summary JSON/Markdown.")
    parser.add_argument("--targets-json", default="", help="Optional JSON map of task_id to target file list.")
    parser.add_argument("--ab-pairs", action="store_true", help="Also compute task-level A/B deltas.")
    parser.add_argument(
        "--require-v16-acceptance",
        action="store_true",
        help="Return exit code 3 unless v16_acceptance exists and passes.",
    )
    parser.add_argument("--baseline-backend", default="none", help="Backend name used as A/B baseline.")
    parser.add_argument(
        "--candidate-backend",
        default="codebase_memory_cli",
        help="Backend name used as A/B candidate.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = summarize_code_intelligence_runs(
        result_paths=args.result,
        cohort_label=args.cohort_label,
        output_dir=args.output_dir,
        target_files_by_task=_load_targets(args.targets_json),
        include_ab_pairs=args.ab_pairs,
        baseline_backend=args.baseline_backend,
        candidate_backend=args.candidate_backend,
    )
    summary = output["summary"]
    aggregate = summary["aggregate"]
    print("=== Code Intelligence Run Summary ===")
    print(f"summary_id: {output['summary_id']}")
    print(f"run_count: {summary['run_count']}")
    print(f"graph_enabled_count: {aggregate['graph_enabled_count']}")
    print(f"fallback_rate: {aggregate['fallback_rate']}")
    print(f"average_graph_tool_calls: {aggregate['average_graph_tool_calls']}")
    print(f"correct_file_top1_count: {aggregate['correct_file_top1_count']}")
    if args.ab_pairs:
        ab_aggregate = summary.get("ab_aggregate", {})
        v16_acceptance = summary.get("v16_acceptance", {})
        print(f"ab_pair_count: {ab_aggregate.get('pair_count', 0)}")
        print(f"average_token_delta: {ab_aggregate.get('average_token_delta', 0.0)}")
        print(f"average_tool_call_delta: {ab_aggregate.get('average_tool_call_delta', 0.0)}")
        print(f"v16_acceptance_ready_to_judge: {v16_acceptance.get('ready_to_judge', False)}")
        print(f"v16_acceptance_accepted: {v16_acceptance.get('accepted', False)}")
        print(f"v16_acceptance_failed_checks: {v16_acceptance.get('failed_check_ids', [])}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    if args.require_v16_acceptance:
        v16_acceptance = summary.get("v16_acceptance", {})
        if not v16_acceptance.get("accepted", False):
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

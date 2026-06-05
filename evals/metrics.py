"""批量评测指标计算。"""

from __future__ import annotations


def _safe_average(values: list[float]) -> float:
    # 指标报告里统一保留四位小数，避免后续格式分散。
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def calculate_metrics(run_records: list[dict]) -> dict:
    # 这里按规格书里的 baseline 口径先给出最小可用指标集合。
    task_count = len(run_records)
    success_count = sum(1 for record in run_records if record["result"]["final_status"] == "success")
    test_pass_count = sum(1 for record in run_records if record["result"].get("test_exit_code") == 0)
    partial_fix_count = sum(
        1
        for record in run_records
        if record["result"]["final_status"] != "success"
        and record["result"].get("patch_applied")
        and record["result"].get("post_test_exit_code") not in (None, 0)
    )

    step_counts = [len(record["trace"].get("steps", [])) for record in run_records]
    tool_call_counts = [record["trace"].get("total_tool_calls", 0) for record in run_records]
    duration_values = [
        float(record["result"].get("duration_sec") or 0.0)
        for record in run_records
    ]
    modified_file_counts = [
        len(record["result"].get("modified_files", []))
        for record in run_records
    ]

    key_file_read_hits = 0
    test_execution_hits = 0
    repeated_search_hits = 0
    reasonable_finish_hits = 0

    for record in run_records:
        read_files = set(record["trace"].get("read_files", []))
        target_files_hint = set(record["task"].get("target_files_hint", []))
        if read_files & target_files_hint:
            key_file_read_hits += 1

        if any(step.get("tool_name") == "run_tests" for step in record["trace"].get("steps", [])):
            test_execution_hits += 1

        search_queries = [
            step.get("tool_input", {}).get("query")
            for step in record["trace"].get("steps", [])
            if step.get("tool_name") == "search_code"
        ]
        if len(search_queries) != len(set(search_queries)):
            repeated_search_hits += 1

        if record["result"].get("post_test_exit_code") is not None:
            reasonable_finish_hits += 1

    return {
        "task_count": task_count,
        "success_count": success_count,
        "success_rate": round(success_count / task_count, 4) if task_count else 0.0,
        "test_pass_count": test_pass_count,
        "test_pass_rate": round(test_pass_count / task_count, 4) if task_count else 0.0,
        "partial_fix_count": partial_fix_count,
        "partial_fix_rate": round(partial_fix_count / task_count, 4) if task_count else 0.0,
        "average_steps": _safe_average(step_counts),
        "average_tool_calls": _safe_average(tool_call_counts),
        "average_duration_sec": _safe_average(duration_values),
        "average_modified_files": _safe_average(modified_file_counts),
        "key_file_read_rate": round(key_file_read_hits / task_count, 4) if task_count else 0.0,
        "test_execution_rate": round(test_execution_hits / task_count, 4) if task_count else 0.0,
        "repeated_search_rate": round(repeated_search_hits / task_count, 4) if task_count else 0.0,
        "reasonable_finish_rate": round(reasonable_finish_hits / task_count, 4) if task_count else 0.0,
    }

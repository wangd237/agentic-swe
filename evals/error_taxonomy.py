"""规则型错误分类。"""

from __future__ import annotations


def classify_run(record: dict) -> list[str]:
    # 第一版严格走规则法，保证分类逻辑透明可解释。
    result = record["result"]
    trace = record["trace"]
    task = record["task"]

    if result["final_status"] == "success":
        return []

    labels: list[str] = []
    steps = trace.get("steps", [])
    read_files = set(trace.get("read_files", []))
    target_files_hint = set(task.get("target_files_hint", []))
    modified_files = set(result.get("modified_files", []))
    observed_failure = result.get("observed_failure", "")

    if not any(step.get("tool_name") == "run_tests" for step in steps):
        labels.append("No Test Execution")

    if target_files_hint and not (read_files & target_files_hint):
        labels.append("Wrong File Selection")

    if observed_failure and modified_files:
        if "sample_repo/parser.py" in observed_failure and "sample_repo/parser.py" not in modified_files:
            labels.append("Wrong Root Cause")

    if result.get("patch_applied") and result.get("post_test_exit_code") not in (None, 0):
        labels.append("Patch Incorrect")

    if len(modified_files) > 1:
        labels.append("Over-editing")

    search_queries = [
        step.get("tool_input", {}).get("query")
        for step in steps
        if step.get("tool_name") == "search_code"
    ]
    if len(search_queries) != len(set(search_queries)):
        labels.append("Looping / Repeated Search")

    if result.get("patch_applied") is False and result.get("post_test_exit_code") not in (None, 0):
        labels.append("Premature Finish")

    return labels


def summarize_taxonomy(run_records: list[dict]) -> dict:
    # 输出每类错误计数，以及每个任务对应的标签。
    label_counts: dict[str, int] = {}
    task_labels: dict[str, list[str]] = {}

    for record in run_records:
        labels = classify_run(record)
        task_labels[record["task"]["task_id"]] = labels
        for label in labels:
            label_counts[label] = label_counts.get(label, 0) + 1

    return {
        "label_counts": dict(sorted(label_counts.items())),
        "task_labels": task_labels,
    }

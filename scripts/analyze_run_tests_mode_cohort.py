"""汇总多个 run_tests 模式 benchmark 的结果。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_analysis_id(summary_dir: Path, cohort_label: str) -> str:
    prefix = f"run_tests_modes_cohort_{cohort_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def build_run_tests_mode_snapshot(summary: dict) -> dict:
    source_summary = summary["mode_summaries"]["source_repo"]
    persistent_summary = summary["mode_summaries"]["persistent_workspace"]
    fresh_summary = summary["mode_summaries"]["fresh_workspace"]

    source_run_tests = float(source_summary["average_run_tests_duration_sec"])
    source_command = float(source_summary["average_command_execution_duration_sec"])
    source_combined = float(source_summary["average_combined_duration_sec"])
    persistent_run_tests = float(persistent_summary["average_run_tests_duration_sec"])
    persistent_command = float(persistent_summary["average_command_execution_duration_sec"])
    persistent_combined = float(persistent_summary["average_combined_duration_sec"])
    fresh_run_tests = float(fresh_summary["average_run_tests_duration_sec"])
    fresh_command = float(fresh_summary["average_command_execution_duration_sec"])
    fresh_combined = float(fresh_summary["average_combined_duration_sec"])

    return {
        "task_id": summary["task_id"],
        "test_command": summary["test_command"],
        "repetitions": summary["repetitions"],
        "source_run_tests_avg_sec": source_run_tests,
        "persistent_run_tests_avg_sec": persistent_run_tests,
        "fresh_run_tests_avg_sec": fresh_run_tests,
        "source_command_avg_sec": source_command,
        "persistent_command_avg_sec": persistent_command,
        "fresh_command_avg_sec": fresh_command,
        "persistent_copy_avg_sec": float(persistent_summary["average_copy_duration_sec"]),
        "fresh_copy_avg_sec": float(fresh_summary["average_copy_duration_sec"]),
        "source_combined_avg_sec": source_combined,
        "persistent_combined_avg_sec": persistent_combined,
        "fresh_combined_avg_sec": fresh_combined,
        "persistent_run_tests_delta_sec": _round_float(persistent_run_tests - source_run_tests),
        "fresh_run_tests_delta_sec": _round_float(fresh_run_tests - source_run_tests),
        "persistent_command_delta_sec": _round_float(persistent_command - source_command),
        "fresh_command_delta_sec": _round_float(fresh_command - source_command),
        "persistent_combined_delta_sec": _round_float(persistent_combined - source_combined),
        "fresh_combined_delta_sec": _round_float(fresh_combined - source_combined),
    }


def build_run_tests_mode_cohort_summary(
    *,
    benchmark_summary_paths: list[str | Path],
    cohort_label: str,
) -> dict:
    summaries = [_load_json(path) for path in benchmark_summary_paths]
    task_snapshots = [build_run_tests_mode_snapshot(summary) for summary in summaries]

    persistent_run_tests_deltas = [item["persistent_run_tests_delta_sec"] for item in task_snapshots]
    fresh_run_tests_deltas = [item["fresh_run_tests_delta_sec"] for item in task_snapshots]
    persistent_command_deltas = [item["persistent_command_delta_sec"] for item in task_snapshots]
    fresh_command_deltas = [item["fresh_command_delta_sec"] for item in task_snapshots]
    persistent_combined_deltas = [item["persistent_combined_delta_sec"] for item in task_snapshots]
    fresh_combined_deltas = [item["fresh_combined_delta_sec"] for item in task_snapshots]
    fresh_copy_avgs = [item["fresh_copy_avg_sec"] for item in task_snapshots]

    ranked_fresh_combined = sorted(
        task_snapshots,
        key=lambda item: item["fresh_combined_delta_sec"],
        reverse=True,
    )

    return {
        "created_at": _utc_timestamp(),
        "cohort_label": cohort_label,
        "task_count": len(task_snapshots),
        "task_ids": [item["task_id"] for item in task_snapshots],
        "aggregate": {
            "average_persistent_run_tests_delta_sec": _average(persistent_run_tests_deltas),
            "average_fresh_run_tests_delta_sec": _average(fresh_run_tests_deltas),
            "average_persistent_command_delta_sec": _average(persistent_command_deltas),
            "average_fresh_command_delta_sec": _average(fresh_command_deltas),
            "average_persistent_combined_delta_sec": _average(persistent_combined_deltas),
            "average_fresh_combined_delta_sec": _average(fresh_combined_deltas),
            "average_fresh_copy_duration_sec": _average(fresh_copy_avgs),
            "fresh_slower_than_source_task_count": len([value for value in fresh_combined_deltas if value > 0]),
            "persistent_slower_than_source_task_count": len(
                [value for value in persistent_combined_deltas if value > 0]
            ),
        },
        "top_fresh_combined_deltas": ranked_fresh_combined,
        "task_snapshots": task_snapshots,
    }


def build_run_tests_mode_cohort_markdown(summary: dict) -> str:
    aggregate = summary["aggregate"]
    task_lines = "\n".join(
        (
            f"- `{item['task_id']}`: persistent run_tests delta=`{item['persistent_run_tests_delta_sec']}`, "
            f"fresh run_tests delta=`{item['fresh_run_tests_delta_sec']}`, "
            f"fresh copy avg=`{item['fresh_copy_avg_sec']}`, "
            f"fresh combined delta=`{item['fresh_combined_delta_sec']}`"
        )
        for item in summary["top_fresh_combined_deltas"]
    ) or "- 当前没有可汇总任务"

    return f"""# Run Tests Mode Cohort Analysis

## Cohort

- cohort_label: `{summary["cohort_label"]}`
- task_count: `{summary["task_count"]}`
- task_ids: `{summary["task_ids"]}`

## Aggregate

- average_persistent_run_tests_delta_sec: `{aggregate["average_persistent_run_tests_delta_sec"]}`
- average_fresh_run_tests_delta_sec: `{aggregate["average_fresh_run_tests_delta_sec"]}`
- average_persistent_command_delta_sec: `{aggregate["average_persistent_command_delta_sec"]}`
- average_fresh_command_delta_sec: `{aggregate["average_fresh_command_delta_sec"]}`
- average_persistent_combined_delta_sec: `{aggregate["average_persistent_combined_delta_sec"]}`
- average_fresh_combined_delta_sec: `{aggregate["average_fresh_combined_delta_sec"]}`
- average_fresh_copy_duration_sec: `{aggregate["average_fresh_copy_duration_sec"]}`
- fresh_slower_than_source_task_count: `{aggregate["fresh_slower_than_source_task_count"]}`
- persistent_slower_than_source_task_count: `{aggregate["persistent_slower_than_source_task_count"]}`

## Task Snapshots

{task_lines}
"""


def analyze_run_tests_mode_cohort(
    *,
    benchmark_summary_paths: list[str | Path],
    cohort_label: str,
    output_dir: str | Path = "logs/summaries",
) -> dict:
    summary = build_run_tests_mode_cohort_summary(
        benchmark_summary_paths=benchmark_summary_paths,
        cohort_label=cohort_label,
    )
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    analysis_id = _next_analysis_id(output_directory, cohort_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_run_tests_mode_cohort_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总多个 run_tests 模式 benchmark 的结果。")
    parser.add_argument("--benchmark-summary", action="append", required=True, help="benchmark summary JSON 路径，可重复传入")
    parser.add_argument("--cohort-label", required=True, help="cohort 标签")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析输出目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_run_tests_mode_cohort(
        benchmark_summary_paths=args.benchmark_summary,
        cohort_label=args.cohort_label,
        output_dir=args.output_dir,
    )
    summary = output["summary"]
    print("=== Run Tests Mode Cohort Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"cohort_label: {summary['cohort_label']}")
    print(f"task_count: {summary['task_count']}")
    print(f"average_fresh_combined_delta_sec: {summary['aggregate']['average_fresh_combined_delta_sec']}")
    print(f"average_fresh_copy_duration_sec: {summary['aggregate']['average_fresh_copy_duration_sec']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

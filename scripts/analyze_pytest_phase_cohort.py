"""汇总多个 pytest 分阶段 benchmark 的结果。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _round_float(value: float) -> float:
    return round(value, 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return _round_float(sum(values) / len(values))


def _average_optional(values: list[float | None]) -> float | None:
    observed_values = [value for value in values if value is not None]
    if not observed_values:
        return None
    return _round_float(sum(observed_values) / len(observed_values))


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_analysis_id(summary_dir: Path, cohort_label: str) -> str:
    prefix = f"pytest_phases_cohort_{cohort_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def build_pytest_phase_snapshot(summary: dict) -> dict:
    derived = summary["derived_metrics"]
    phases = summary["phase_summaries"]
    return {
        "task_id": summary["task_id"],
        "test_command": summary["test_command"],
        "repetitions": summary["repetitions"],
        "python_noop_avg_sec": float(phases["python_noop"]["average_command_execution_duration_sec"]),
        "pytest_version_avg_sec": float(phases["pytest_version"]["average_command_execution_duration_sec"]),
        "pytest_collect_only_avg_sec": float(phases["pytest_collect_only"]["average_command_execution_duration_sec"]),
        "pytest_full_run_avg_sec": float(phases["pytest_full_run"]["average_command_execution_duration_sec"]),
        "pytest_startup_over_python_sec": float(derived["average_pytest_startup_over_python_sec"]),
        "collect_over_pytest_startup_sec": float(derived["average_collect_over_pytest_startup_sec"]),
        "full_over_collect_sec": float(derived["average_full_over_collect_sec"]),
        "collect_first_minus_repeated_sec": derived["collect_first_minus_repeated_sec"],
        "full_first_minus_repeated_sec": derived["full_first_minus_repeated_sec"],
    }


def build_pytest_phase_cohort_summary(
    *,
    benchmark_summary_paths: list[str | Path],
    cohort_label: str,
) -> dict:
    summaries = [_load_json(path) for path in benchmark_summary_paths]
    task_snapshots = [build_pytest_phase_snapshot(summary) for summary in summaries]

    startup_deltas = [item["pytest_startup_over_python_sec"] for item in task_snapshots]
    collect_deltas = [item["collect_over_pytest_startup_sec"] for item in task_snapshots]
    full_deltas = [item["full_over_collect_sec"] for item in task_snapshots]
    collect_first_deltas = [item["collect_first_minus_repeated_sec"] for item in task_snapshots]
    full_first_deltas = [item["full_first_minus_repeated_sec"] for item in task_snapshots]

    ranked_full_over_collect = sorted(
        task_snapshots,
        key=lambda item: item["full_over_collect_sec"],
        reverse=True,
    )

    return {
        "created_at": _utc_timestamp(),
        "cohort_label": cohort_label,
        "task_count": len(task_snapshots),
        "task_ids": [item["task_id"] for item in task_snapshots],
        "aggregate": {
            "average_pytest_startup_over_python_sec": _average(startup_deltas),
            "average_collect_over_pytest_startup_sec": _average(collect_deltas),
            "average_full_over_collect_sec": _average(full_deltas),
            "average_collect_first_minus_repeated_sec": _average_optional(collect_first_deltas),
            "average_full_first_minus_repeated_sec": _average_optional(full_first_deltas),
            "full_slower_than_collect_task_count": len([value for value in full_deltas if value > 0]),
            "collect_slower_than_startup_task_count": len([value for value in collect_deltas if value > 0]),
        },
        "top_full_over_collect_deltas": ranked_full_over_collect,
        "task_snapshots": task_snapshots,
    }


def build_pytest_phase_cohort_markdown(summary: dict) -> str:
    aggregate = summary["aggregate"]
    task_lines = "\n".join(
        (
            f"- `{item['task_id']}`: startup over python=`{item['pytest_startup_over_python_sec']}`, "
            f"collect over startup=`{item['collect_over_pytest_startup_sec']}`, "
            f"full over collect=`{item['full_over_collect_sec']}`, "
            f"full first minus repeated=`{item['full_first_minus_repeated_sec']}`"
        )
        for item in summary["top_full_over_collect_deltas"]
    ) or "- 当前没有可汇总任务"

    return f"""# Pytest Phase Cohort Analysis

## Cohort

- cohort_label: `{summary["cohort_label"]}`
- task_count: `{summary["task_count"]}`
- task_ids: `{summary["task_ids"]}`

## Aggregate

- average_pytest_startup_over_python_sec: `{aggregate["average_pytest_startup_over_python_sec"]}`
- average_collect_over_pytest_startup_sec: `{aggregate["average_collect_over_pytest_startup_sec"]}`
- average_full_over_collect_sec: `{aggregate["average_full_over_collect_sec"]}`
- average_collect_first_minus_repeated_sec: `{aggregate["average_collect_first_minus_repeated_sec"]}`
- average_full_first_minus_repeated_sec: `{aggregate["average_full_first_minus_repeated_sec"]}`
- full_slower_than_collect_task_count: `{aggregate["full_slower_than_collect_task_count"]}`
- collect_slower_than_startup_task_count: `{aggregate["collect_slower_than_startup_task_count"]}`

## Task Snapshots

{task_lines}
"""


def analyze_pytest_phase_cohort(
    *,
    benchmark_summary_paths: list[str | Path],
    cohort_label: str,
    output_dir: str | Path = "logs/summaries",
) -> dict:
    summary = build_pytest_phase_cohort_summary(
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
    write_text(summary_md_path, build_pytest_phase_cohort_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总多个 pytest 分阶段 benchmark 的结果。")
    parser.add_argument("--benchmark-summary", action="append", required=True, help="benchmark summary JSON 路径，可重复传入")
    parser.add_argument("--cohort-label", required=True, help="cohort 标签")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析输出目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_pytest_phase_cohort(
        benchmark_summary_paths=args.benchmark_summary,
        cohort_label=args.cohort_label,
        output_dir=args.output_dir,
    )
    summary = output["summary"]
    aggregate = summary["aggregate"]
    print("=== Pytest Phase Cohort Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"cohort_label: {summary['cohort_label']}")
    print(f"task_count: {summary['task_count']}")
    print(f"average_pytest_startup_over_python_sec: {aggregate['average_pytest_startup_over_python_sec']}")
    print(f"average_collect_over_pytest_startup_sec: {aggregate['average_collect_over_pytest_startup_sec']}")
    print(f"average_full_over_collect_sec: {aggregate['average_full_over_collect_sec']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

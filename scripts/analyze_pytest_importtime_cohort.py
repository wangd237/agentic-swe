"""汇总多个 pytest importtime benchmark 的结果。"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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


def _average_optional(values: list[float | None]) -> float | None:
    observed_values = [value for value in values if value is not None]
    if not observed_values:
        return None
    return _round_float(sum(observed_values) / len(observed_values))


def _average_int(values: list[int]) -> int:
    if not values:
        return 0
    return round(sum(values) / len(values))


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_analysis_id(summary_dir: Path, cohort_label: str) -> str:
    prefix = f"pytest_importtime_cohort_{cohort_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def build_pytest_importtime_snapshot(summary: dict) -> dict:
    derived = summary["derived_metrics"]
    version_summary = summary["phase_summaries"]["pytest_version_importtime"]
    collect_summary = summary["phase_summaries"]["pytest_collect_importtime"]
    return {
        "task_id": summary["task_id"],
        "test_command": summary["test_command"],
        "repetitions": summary["repetitions"],
        "version_wall_avg_sec": float(version_summary["average_command_execution_duration_sec"]),
        "collect_wall_avg_sec": float(collect_summary["average_command_execution_duration_sec"]),
        "version_import_self_avg_us": int(version_summary["average_total_import_self_us"]),
        "collect_import_self_avg_us": int(collect_summary["average_total_import_self_us"]),
        "version_unique_module_avg": int(version_summary["average_unique_module_count"]),
        "collect_unique_module_avg": int(collect_summary["average_unique_module_count"]),
        "collect_wall_delta_sec": float(derived["average_collect_wall_delta_sec"]),
        "collect_import_self_delta_us": int(derived["average_collect_import_self_delta_us"]),
        "collect_unique_module_delta": int(derived["average_collect_unique_module_delta"]),
        "collect_wall_first_minus_repeated_sec": derived["collect_wall_first_minus_repeated_sec"],
        "collect_import_self_first_minus_repeated_us": derived["collect_import_self_first_minus_repeated_us"],
        "latest_collect_extra_modules_top_self": derived["latest_collect_extra_modules_top_self"],
    }


def build_pytest_importtime_cohort_summary(
    *,
    benchmark_summary_paths: list[str | Path],
    cohort_label: str,
) -> dict:
    summaries = [_load_json(path) for path in benchmark_summary_paths]
    task_snapshots = [build_pytest_importtime_snapshot(summary) for summary in summaries]

    collect_wall_deltas = [item["collect_wall_delta_sec"] for item in task_snapshots]
    collect_import_deltas = [item["collect_import_self_delta_us"] for item in task_snapshots]
    collect_module_deltas = [item["collect_unique_module_delta"] for item in task_snapshots]
    collect_first_wall_deltas = [item["collect_wall_first_minus_repeated_sec"] for item in task_snapshots]
    collect_first_import_deltas = [item["collect_import_self_first_minus_repeated_us"] for item in task_snapshots]

    extra_module_counter: Counter[str] = Counter()
    for snapshot in task_snapshots:
        for entry in snapshot["latest_collect_extra_modules_top_self"]:
            extra_module_counter[entry["module"]] += 1

    ranked_collect_import_deltas = sorted(
        task_snapshots,
        key=lambda item: item["collect_import_self_delta_us"],
        reverse=True,
    )

    return {
        "created_at": _utc_timestamp(),
        "cohort_label": cohort_label,
        "task_count": len(task_snapshots),
        "task_ids": [item["task_id"] for item in task_snapshots],
        "aggregate": {
            "average_collect_wall_delta_sec": _average(collect_wall_deltas),
            "average_collect_import_self_delta_us": _average_int(collect_import_deltas),
            "average_collect_unique_module_delta": _average_int(collect_module_deltas),
            "average_collect_wall_first_minus_repeated_sec": _average_optional(collect_first_wall_deltas),
            "average_collect_import_self_first_minus_repeated_us": _average_optional(
                [float(value) if value is not None else None for value in collect_first_import_deltas]
            ),
            "collect_slower_than_version_task_count": len([value for value in collect_wall_deltas if value > 0]),
        },
        "top_extra_modules": [
            {"module": module_name, "task_count": count}
            for module_name, count in extra_module_counter.most_common(12)
        ],
        "top_collect_import_deltas": ranked_collect_import_deltas,
        "task_snapshots": task_snapshots,
    }


def build_pytest_importtime_cohort_markdown(summary: dict) -> str:
    aggregate = summary["aggregate"]
    task_lines = "\n".join(
        (
            f"- `{item['task_id']}`: collect wall delta=`{item['collect_wall_delta_sec']}`, "
            f"collect import self delta(us)=`{item['collect_import_self_delta_us']}`, "
            f"collect module delta=`{item['collect_unique_module_delta']}`"
        )
        for item in summary["top_collect_import_deltas"]
    ) or "- 当前没有可汇总任务"
    extra_module_lines = "\n".join(
        f"- `{item['module']}`: task_count=`{item['task_count']}`"
        for item in summary["top_extra_modules"]
    ) or "- 当前没有额外模块统计"

    return f"""# Pytest Importtime Cohort Analysis

## Cohort

- cohort_label: `{summary["cohort_label"]}`
- task_count: `{summary["task_count"]}`
- task_ids: `{summary["task_ids"]}`

## Aggregate

- average_collect_wall_delta_sec: `{aggregate["average_collect_wall_delta_sec"]}`
- average_collect_import_self_delta_us: `{aggregate["average_collect_import_self_delta_us"]}`
- average_collect_unique_module_delta: `{aggregate["average_collect_unique_module_delta"]}`
- average_collect_wall_first_minus_repeated_sec: `{aggregate["average_collect_wall_first_minus_repeated_sec"]}`
- average_collect_import_self_first_minus_repeated_us: `{aggregate["average_collect_import_self_first_minus_repeated_us"]}`
- collect_slower_than_version_task_count: `{aggregate["collect_slower_than_version_task_count"]}`

## Top Extra Modules

{extra_module_lines}

## Task Snapshots

{task_lines}
"""


def analyze_pytest_importtime_cohort(
    *,
    benchmark_summary_paths: list[str | Path],
    cohort_label: str,
    output_dir: str | Path = "logs/summaries",
) -> dict:
    summary = build_pytest_importtime_cohort_summary(
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
    write_text(summary_md_path, build_pytest_importtime_cohort_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总多个 pytest importtime benchmark 的结果。")
    parser.add_argument("--benchmark-summary", action="append", required=True, help="benchmark summary JSON 路径，可重复传入")
    parser.add_argument("--cohort-label", required=True, help="cohort 标签")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析输出目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_pytest_importtime_cohort(
        benchmark_summary_paths=args.benchmark_summary,
        cohort_label=args.cohort_label,
        output_dir=args.output_dir,
    )
    summary = output["summary"]
    aggregate = summary["aggregate"]
    print("=== Pytest Importtime Cohort Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"cohort_label: {summary['cohort_label']}")
    print(f"task_count: {summary['task_count']}")
    print(f"average_collect_wall_delta_sec: {aggregate['average_collect_wall_delta_sec']}")
    print(f"average_collect_import_self_delta_us: {aggregate['average_collect_import_self_delta_us']}")
    print(f"average_collect_unique_module_delta: {aggregate['average_collect_unique_module_delta']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

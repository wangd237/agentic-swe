"""汇总多个热点任务的历史时延变化。"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from scripts.analyze_task_history import build_task_history_summary


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _round_float(value: float) -> float:
    return round(value, 4)


def _build_cohort_analysis_id(summary_dir: Path, cohort_label: str) -> str:
    prefix = f"task_history_cohort_{cohort_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _resolve_task_dirs(
    *,
    task_dirs: list[str] | None,
    task_ids: list[str] | None,
    trajectories_root: str | Path,
) -> list[Path]:
    resolved_task_dirs: list[Path] = []
    seen: set[Path] = set()

    for raw_task_dir in task_dirs or []:
        task_dir = Path(raw_task_dir).resolve()
        if task_dir not in seen:
            seen.add(task_dir)
            resolved_task_dirs.append(task_dir)

    trajectories_directory = Path(trajectories_root).resolve()
    for task_id in task_ids or []:
        task_dir = trajectories_directory / task_id
        if task_dir not in seen:
            seen.add(task_dir)
            resolved_task_dirs.append(task_dir)

    if not resolved_task_dirs:
        raise ValueError("必须至少提供一个 --task-dir 或 --task-id。")

    return resolved_task_dirs


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return _round_float(sum(values) / len(values))


def _build_task_snapshot(task_summary: dict) -> dict:
    latest_comparison = task_summary.get("latest_policy_comparison") or {}
    latest_policy_summary = task_summary.get("latest_policy_summary") or {}
    previous_policy_summary = task_summary.get("previous_policy_summary") or {}

    return {
        "task_id": task_summary["task_id"],
        "run_count": task_summary["run_count"],
        "policy_count": task_summary["policy_count"],
        "baseline_policy_id": latest_comparison.get("baseline_policy_id"),
        "improved_policy_id": latest_comparison.get("improved_policy_id"),
        "baseline_duration_average_sec": previous_policy_summary.get("duration_sec", {}).get("average"),
        "improved_duration_average_sec": latest_policy_summary.get("duration_sec", {}).get("average"),
        "duration_average_delta_sec": latest_comparison.get("duration_average_delta_sec"),
        "run_tests_average_delta_sec": latest_comparison.get("run_tests_average_delta_sec"),
        "latest_run_tests_subprocess_average_sec": latest_policy_summary.get("run_tests_subprocess_duration_sec", {}).get("average"),
        "latest_run_tests_subprocess_observed_runs": latest_policy_summary.get("run_tests_subprocess_duration_sec", {}).get(
            "observed_count", 0
        ),
        "slowest_run": task_summary.get("slowest_runs", [None])[0],
    }


def build_task_history_cohort_summary(
    *,
    task_dirs: list[str] | None = None,
    task_ids: list[str] | None = None,
    trajectories_root: str | Path = "logs/trajectories",
    cohort_label: str = "hotspots",
) -> dict:
    resolved_task_dirs = _resolve_task_dirs(
        task_dirs=task_dirs,
        task_ids=task_ids,
        trajectories_root=trajectories_root,
    )
    task_summaries = [build_task_history_summary(task_dir) for task_dir in resolved_task_dirs]
    task_snapshots = [_build_task_snapshot(task_summary) for task_summary in task_summaries]

    comparable_snapshots = [
        item
        for item in task_snapshots
        if item["duration_average_delta_sec"] is not None and item["run_tests_average_delta_sec"] is not None
    ]
    duration_deltas = [float(item["duration_average_delta_sec"]) for item in comparable_snapshots]
    run_tests_deltas = [float(item["run_tests_average_delta_sec"]) for item in comparable_snapshots]
    subprocess_observed_values = [
        float(item["latest_run_tests_subprocess_average_sec"])
        for item in task_snapshots
        if item["latest_run_tests_subprocess_average_sec"] is not None
    ]
    positive_duration_delta_count = len([value for value in duration_deltas if value > 0])

    top_regressions = sorted(
        comparable_snapshots,
        key=lambda item: float(item["duration_average_delta_sec"]),
        reverse=True,
    )

    return {
        "created_at": _utc_timestamp(),
        "cohort_label": cohort_label,
        "task_count": len(task_snapshots),
        "task_ids": [item["task_id"] for item in task_snapshots],
        "comparable_task_count": len(comparable_snapshots),
        "aggregate": {
            "average_duration_delta_sec": _average(duration_deltas),
            "average_run_tests_delta_sec": _average(run_tests_deltas),
            "positive_duration_delta_count": positive_duration_delta_count,
            "latest_run_tests_subprocess_observed_task_count": len(subprocess_observed_values),
            "latest_run_tests_subprocess_average_sec": _average(subprocess_observed_values)
            if subprocess_observed_values
            else None,
        },
        "top_regressions": top_regressions,
        "task_snapshots": task_snapshots,
    }


def build_task_history_cohort_markdown(summary: dict) -> str:
    aggregate = summary["aggregate"]
    regression_lines = "\n".join(
        (
            f"- `{item['task_id']}`: duration delta=`{item['duration_average_delta_sec']}`, "
            f"run_tests delta=`{item['run_tests_average_delta_sec']}`, "
            f"baseline=`{item['baseline_policy_id']}`, improved=`{item['improved_policy_id']}`, "
            f"latest subprocess avg=`{item['latest_run_tests_subprocess_average_sec'] or '未观测'}`"
        )
        for item in summary["top_regressions"]
    ) or "- 当前没有可比较的热点任务"

    return f"""# Task History Cohort Analysis

## Cohort

- cohort_label: `{summary["cohort_label"]}`
- task_count: `{summary["task_count"]}`
- comparable_task_count: `{summary["comparable_task_count"]}`
- task_ids: `{summary["task_ids"]}`

## Aggregate

- average_duration_delta_sec: `{aggregate["average_duration_delta_sec"]}`
- average_run_tests_delta_sec: `{aggregate["average_run_tests_delta_sec"]}`
- positive_duration_delta_count: `{aggregate["positive_duration_delta_count"]}`
- latest_run_tests_subprocess_observed_task_count: `{aggregate["latest_run_tests_subprocess_observed_task_count"]}`
- latest_run_tests_subprocess_average_sec: `{aggregate["latest_run_tests_subprocess_average_sec"] or '未观测'}`

## Top Regressions

{regression_lines}
"""


def analyze_task_history_cohort(
    *,
    task_dirs: list[str] | None = None,
    task_ids: list[str] | None = None,
    trajectories_root: str | Path = "logs/trajectories",
    output_dir: str | Path = "logs/summaries",
    cohort_label: str = "hotspots",
) -> dict:
    summary = build_task_history_cohort_summary(
        task_dirs=task_dirs,
        task_ids=task_ids,
        trajectories_root=trajectories_root,
        cohort_label=cohort_label,
    )

    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    analysis_id = _build_cohort_analysis_id(output_directory, cohort_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_task_history_cohort_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总多个热点任务的历史时延变化。")
    parser.add_argument("--task-dir", action="append", default=None, help="任务轨迹目录，可重复传入")
    parser.add_argument("--task-id", action="append", default=None, help="任务 ID，可重复传入")
    parser.add_argument("--trajectories-root", default="logs/trajectories", help="任务轨迹根目录")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析结果输出目录")
    parser.add_argument("--cohort-label", default="hotspots", help="热点集合标签")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_task_history_cohort(
        task_dirs=args.task_dir,
        task_ids=args.task_id,
        trajectories_root=args.trajectories_root,
        output_dir=args.output_dir,
        cohort_label=args.cohort_label,
    )
    summary = output["summary"]
    print("=== Task History Cohort Analysis Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"cohort_label: {summary['cohort_label']}")
    print(f"task_count: {summary['task_count']}")
    print(f"average_duration_delta_sec: {summary['aggregate']['average_duration_delta_sec']}")
    print(f"average_run_tests_delta_sec: {summary['aggregate']['average_run_tests_delta_sec']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

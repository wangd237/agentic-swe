"""批量运行多任务 pytest 策略版对照，并产出 cohort 汇总。"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from scripts.analyze_pytest_policy_pair_cohort import analyze_pytest_policy_pair_cohort
from scripts.benchmark_pytest_importtime import benchmark_pytest_importtime
from scripts.benchmark_pytest_phases import benchmark_pytest_phases
from scripts.compare_pytest_policy_pair import compare_pytest_policy_pair


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_analysis_id(summary_dir: Path, matrix_label: str) -> str:
    prefix = f"pytest_policy_pair_matrix_{matrix_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _task_stem(task_path: str | Path) -> str:
    return Path(task_path).stem.replace("task_", "task")


def build_task_matrix_record(
    *,
    task_path: str | Path,
    repo_root: str | Path,
    baseline_policy_path: str | Path,
    improved_policy_path: str | Path,
    repetitions: int,
    output_dir: str | Path,
) -> dict:
    task_label = _task_stem(task_path)

    baseline_phase = benchmark_pytest_phases(
        task_path=task_path,
        repo_root=repo_root,
        repetitions=repetitions,
        policy_path=baseline_policy_path,
        output_dir=output_dir,
        benchmark_label=f"{task_label}_baseline_phases_policy",
    )
    improved_phase = benchmark_pytest_phases(
        task_path=task_path,
        repo_root=repo_root,
        repetitions=repetitions,
        policy_path=improved_policy_path,
        output_dir=output_dir,
        benchmark_label=f"{task_label}_improved_phases_policy",
    )
    phase_compare = compare_pytest_policy_pair(
        baseline_summary_path=baseline_phase["summary_json_path"],
        improved_summary_path=improved_phase["summary_json_path"],
        output_dir=output_dir,
        compare_label=f"{task_label}_phase_pair",
    )

    baseline_importtime = benchmark_pytest_importtime(
        task_path=task_path,
        repo_root=repo_root,
        repetitions=repetitions,
        policy_path=baseline_policy_path,
        output_dir=output_dir,
        benchmark_label=f"{task_label}_baseline_importtime_policy",
    )
    improved_importtime = benchmark_pytest_importtime(
        task_path=task_path,
        repo_root=repo_root,
        repetitions=repetitions,
        policy_path=improved_policy_path,
        output_dir=output_dir,
        benchmark_label=f"{task_label}_improved_importtime_policy",
    )
    importtime_compare = compare_pytest_policy_pair(
        baseline_summary_path=baseline_importtime["summary_json_path"],
        improved_summary_path=improved_importtime["summary_json_path"],
        output_dir=output_dir,
        compare_label=f"{task_label}_importtime_pair",
    )

    return {
        "task_id": baseline_phase["summary"]["task_id"],
        "task_path": str(Path(task_path).resolve()),
        "phase": {
            "baseline_summary_path": baseline_phase["summary_json_path"],
            "improved_summary_path": improved_phase["summary_json_path"],
            "compare_summary_path": phase_compare["summary_json_path"],
            "compare_summary": phase_compare["summary"],
        },
        "importtime": {
            "baseline_summary_path": baseline_importtime["summary_json_path"],
            "improved_summary_path": improved_importtime["summary_json_path"],
            "compare_summary_path": importtime_compare["summary_json_path"],
            "compare_summary": importtime_compare["summary"],
        },
    }


def build_pytest_policy_pair_matrix_summary(
    *,
    task_paths: list[str | Path],
    repo_root: str | Path,
    baseline_policy_path: str | Path,
    improved_policy_path: str | Path,
    repetitions: int,
    output_dir: str | Path,
    matrix_label: str,
) -> dict:
    task_records = [
        build_task_matrix_record(
            task_path=task_path,
            repo_root=repo_root,
            baseline_policy_path=baseline_policy_path,
            improved_policy_path=improved_policy_path,
            repetitions=repetitions,
            output_dir=output_dir,
        )
        for task_path in task_paths
    ]

    phase_cohort = analyze_pytest_policy_pair_cohort(
        compare_summary_paths=[item["phase"]["compare_summary_path"] for item in task_records],
        cohort_label=f"{matrix_label}_phase",
        output_dir=output_dir,
    )
    importtime_cohort = analyze_pytest_policy_pair_cohort(
        compare_summary_paths=[item["importtime"]["compare_summary_path"] for item in task_records],
        cohort_label=f"{matrix_label}_importtime",
        output_dir=output_dir,
    )

    return {
        "created_at": _utc_timestamp(),
        "matrix_label": matrix_label,
        "task_count": len(task_records),
        "repetitions": repetitions,
        "repo_root": str(Path(repo_root).resolve()),
        "baseline_policy_path": str(Path(baseline_policy_path).resolve()),
        "improved_policy_path": str(Path(improved_policy_path).resolve()),
        "runtime_equivalent_task_count": sum(
            1
            for item in task_records
            if item["phase"]["compare_summary"].get("runtime_equivalent")
            and item["importtime"]["compare_summary"].get("runtime_equivalent")
        ),
        "task_records": task_records,
        "phase_cohort_summary_path": phase_cohort["summary_json_path"],
        "importtime_cohort_summary_path": importtime_cohort["summary_json_path"],
        "phase_cohort_summary": phase_cohort["summary"],
        "importtime_cohort_summary": importtime_cohort["summary"],
    }


def build_pytest_policy_pair_matrix_markdown(summary: dict) -> str:
    phase_aggregate = summary["phase_cohort_summary"]["aggregate"]
    importtime_aggregate = summary["importtime_cohort_summary"]["aggregate"]
    task_lines = "\n".join(
        (
            f"- `{item['task_id']}`: "
            f"phase collect delta=`{item['phase']['compare_summary']['deltas'].get('collect_over_pytest_startup_delta_sec')}`, "
            f"phase full delta=`{item['phase']['compare_summary']['deltas'].get('full_over_collect_delta_sec')}`, "
            f"importtime collect wall delta=`{item['importtime']['compare_summary']['deltas'].get('collect_wall_delta_sec')}`, "
            f"importtime collect import delta(us)=`{item['importtime']['compare_summary']['deltas'].get('collect_import_self_delta_us')}`"
        )
        for item in summary["task_records"]
    ) or "- 当前没有任务记录"

    return f"""# Pytest Policy Pair Matrix

## Scope

- matrix_label: `{summary["matrix_label"]}`
- task_count: `{summary["task_count"]}`
- repetitions: `{summary["repetitions"]}`
- baseline_policy_path: `{summary["baseline_policy_path"]}`
- improved_policy_path: `{summary["improved_policy_path"]}`
- runtime_equivalent_task_count: `{summary["runtime_equivalent_task_count"]}`

## Phase Cohort Aggregate

- average_pytest_startup_over_python_delta_sec: `{phase_aggregate["average_pytest_startup_over_python_delta_sec"]}`
- average_collect_over_pytest_startup_delta_sec: `{phase_aggregate["average_collect_over_pytest_startup_delta_sec"]}`
- average_full_over_collect_delta_sec: `{phase_aggregate["average_full_over_collect_delta_sec"]}`
- collect_slower_task_count: `{phase_aggregate["collect_slower_task_count"]}`
- full_slower_task_count: `{phase_aggregate["full_slower_task_count"]}`

## Importtime Cohort Aggregate

- average_collect_wall_delta_sec: `{importtime_aggregate["average_collect_wall_delta_sec"]}`
- average_collect_import_self_delta_us: `{importtime_aggregate["average_collect_import_self_delta_us"]}`
- collect_wall_slower_task_count: `{importtime_aggregate["collect_wall_slower_task_count"]}`
- collect_import_self_higher_task_count: `{importtime_aggregate["collect_import_self_higher_task_count"]}`

## Tasks

{task_lines}
"""


def run_pytest_policy_pair_matrix(
    *,
    task_paths: list[str | Path],
    repo_root: str | Path,
    baseline_policy_path: str | Path,
    improved_policy_path: str | Path,
    repetitions: int,
    output_dir: str | Path = "logs/summaries",
    matrix_label: str,
) -> dict:
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    summary = build_pytest_policy_pair_matrix_summary(
        task_paths=task_paths,
        repo_root=repo_root,
        baseline_policy_path=baseline_policy_path,
        improved_policy_path=improved_policy_path,
        repetitions=repetitions,
        output_dir=output_directory,
        matrix_label=matrix_label,
    )
    analysis_id = _next_analysis_id(output_directory, matrix_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_pytest_policy_pair_matrix_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量运行多任务 pytest 策略版对照并产出 cohort 汇总。")
    parser.add_argument("--task", action="append", required=True, help="任务 JSON 路径，可重复传入")
    parser.add_argument("--repo-root", default=".", help="仓库根目录")
    parser.add_argument("--baseline-policy", required=True, help="baseline 策略 JSON 路径")
    parser.add_argument("--improved-policy", required=True, help="improved 策略 JSON 路径")
    parser.add_argument("--repetitions", type=int, default=3, help="每个任务每条基准的重复次数")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--matrix-label", required=True, help="本轮矩阵标签")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = run_pytest_policy_pair_matrix(
        task_paths=args.task,
        repo_root=args.repo_root,
        baseline_policy_path=args.baseline_policy,
        improved_policy_path=args.improved_policy,
        repetitions=args.repetitions,
        output_dir=args.output_dir,
        matrix_label=args.matrix_label,
    )
    summary = output["summary"]
    print("=== Pytest Policy Pair Matrix Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"matrix_label: {summary['matrix_label']}")
    print(f"task_count: {summary['task_count']}")
    print(f"phase_cohort_summary_path: {summary['phase_cohort_summary_path']}")
    print(f"importtime_cohort_summary_path: {summary['importtime_cohort_summary_path']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

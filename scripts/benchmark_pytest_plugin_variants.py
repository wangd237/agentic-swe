"""对 pytest 默认插件变体的 collection 开销做基准。"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from app.schemas.task_schema import load_task
from scripts.benchmark_pytest_importtime import (
    _build_collect_only_command,
    _build_importtime_command,
    build_importtime_profile,
)
from app.tools.run_tests import run_tests


SAFE_DISABLE_PLUGIN_FLAGS = [
    "-p no:junitxml",
    "-p no:pastebin",
    "-p no:setuponly",
    "-p no:setupplan",
    "-p no:stepwise",
    "-p no:warnings",
    "-p no:faulthandler",
    "-p no:terminalprogress",
    "-p no:debugging",
    "-p no:unraisableexception",
    "-p no:threadexception",
]

PLUGIN_VARIANTS: dict[str, list[str]] = {
    "default_plugins": [],
    "light_terminal_plugins": [
        "-p no:junitxml",
        "-p no:pastebin",
        "-p no:setuponly",
        "-p no:setupplan",
        "-p no:stepwise",
        "-p no:warnings",
        "-p no:faulthandler",
        "-p no:terminalprogress",
    ],
    "debug_exception_plugins": [
        "-p no:debugging",
        "-p no:unraisableexception",
        "-p no:threadexception",
    ],
    "minimal_safe_plugins": SAFE_DISABLE_PLUGIN_FLAGS,
}


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _round_float(value: float) -> float:
    return round(value, 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return _round_float(sum(values) / len(values))


def _average_int(values: list[int]) -> int:
    if not values:
        return 0
    return round(sum(values) / len(values))


def _average_optional(values: list[float]) -> float | None:
    if not values:
        return None
    return _round_float(sum(values) / len(values))


def _next_benchmark_id(summary_dir: Path, benchmark_label: str) -> str:
    prefix = f"pytest_plugin_variants_{benchmark_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _build_collect_importtime_command(test_command: str, plugin_flags: list[str]) -> str:
    collect_command = _build_collect_only_command(test_command)
    importtime_command = _build_importtime_command(collect_command)
    return " ".join([importtime_command, *plugin_flags]).strip()


def _build_run_record(variant_name: str, run_index: int, command: str, result: dict) -> dict:
    data = result["data"]
    import_profile = build_importtime_profile(data.get("stderr", ""))
    return {
        "variant_name": variant_name,
        "run_index": run_index,
        "command": command,
        "ok": result["ok"],
        "exit_code": data.get("exit_code"),
        "command_execution_duration_sec": float(data.get("command_execution_duration_sec") or 0.0),
        "entry_count": import_profile["entry_count"],
        "unique_module_count": import_profile["unique_module_count"],
        "total_import_self_us": import_profile["total_import_self_us"],
        "top_self_imports": import_profile["top_self_imports"],
        "top_cumulative_imports": import_profile["top_cumulative_imports"],
        "module_names": import_profile["module_names"],
    }


def _build_variant_summary(variant_name: str, plugin_flags: list[str], records: list[dict]) -> dict:
    first_record = records[0] if records else None
    repeated_records = records[1:] if len(records) > 1 else []
    latest_record = records[-1] if records else None
    return {
        "variant_name": variant_name,
        "plugin_flags": plugin_flags,
        "run_count": len(records),
        "all_ok": all(record["ok"] for record in records),
        "average_command_execution_duration_sec": _average(
            [record["command_execution_duration_sec"] for record in records]
        ),
        "average_total_import_self_us": _average_int([record["total_import_self_us"] for record in records]),
        "average_unique_module_count": _average_int([record["unique_module_count"] for record in records]),
        "first_command_execution_duration_sec": first_record["command_execution_duration_sec"] if first_record else None,
        "repeated_command_execution_average_sec": _average_optional(
            [record["command_execution_duration_sec"] for record in repeated_records]
        ),
        "latest_top_self_imports": latest_record["top_self_imports"] if latest_record else [],
        "latest_top_cumulative_imports": latest_record["top_cumulative_imports"] if latest_record else [],
        "latest_module_names": latest_record["module_names"] if latest_record else [],
        "records": records,
    }


def _build_variant_delta(candidate_summary: dict, baseline_summary: dict) -> dict:
    baseline_modules = set(baseline_summary["latest_module_names"])
    candidate_modules = set(candidate_summary["latest_module_names"])
    return {
        "variant_name": candidate_summary["variant_name"],
        "disabled_plugin_flags": candidate_summary["plugin_flags"],
        "wall_delta_sec": _round_float(
            candidate_summary["average_command_execution_duration_sec"]
            - baseline_summary["average_command_execution_duration_sec"]
        ),
        "import_self_delta_us": int(
            candidate_summary["average_total_import_self_us"] - baseline_summary["average_total_import_self_us"]
        ),
        "unique_module_delta": int(
            candidate_summary["average_unique_module_count"] - baseline_summary["average_unique_module_count"]
        ),
        "removed_modules": sorted(baseline_modules - candidate_modules),
    }


def _build_derived_metrics(variant_summaries: dict[str, dict]) -> dict:
    baseline_summary = variant_summaries["default_plugins"]
    deltas = [
        _build_variant_delta(summary, baseline_summary)
        for variant_name, summary in variant_summaries.items()
        if variant_name != "default_plugins"
    ]
    ranked_by_wall_reduction = sorted(deltas, key=lambda item: item["wall_delta_sec"])
    return {
        "baseline_variant": "default_plugins",
        "variant_deltas": deltas,
        "ranked_by_wall_reduction": ranked_by_wall_reduction,
    }


def build_pytest_plugin_variant_benchmark(
    *,
    task_path: str | Path,
    repo_root: str | Path,
    repetitions: int = 3,
) -> dict:
    repository_root = Path(repo_root).resolve()
    task = load_task(task_path)
    source_repo_path = (repository_root / task.repo_path).resolve()
    if not source_repo_path.exists():
        raise FileNotFoundError(f"任务 repo 不存在: {source_repo_path}")

    variant_summaries: dict[str, dict] = {}
    for variant_name, plugin_flags in PLUGIN_VARIANTS.items():
        command = _build_collect_importtime_command(task.test_command, plugin_flags)
        records: list[dict] = []
        for run_index in range(1, repetitions + 1):
            result = run_tests(str(source_repo_path), command, timeout_sec=30)
            records.append(_build_run_record(variant_name, run_index, command, result))
        variant_summaries[variant_name] = _build_variant_summary(variant_name, plugin_flags, records)

    return {
        "created_at": _utc_timestamp(),
        "task_id": task.task_id,
        "task_path": str(Path(task_path).resolve()),
        "source_repo_path": str(source_repo_path),
        "test_command": task.test_command,
        "repetitions": repetitions,
        "variant_summaries": variant_summaries,
        "derived_metrics": _build_derived_metrics(variant_summaries),
    }


def build_pytest_plugin_variant_markdown(summary: dict) -> str:
    variant_lines = "\n".join(
        (
            f"- `{variant_name}`: wall avg=`{variant_summary['average_command_execution_duration_sec']}`, "
            f"import self avg(us)=`{variant_summary['average_total_import_self_us']}`, "
            f"module avg=`{variant_summary['average_unique_module_count']}`, "
            f"flags=`{' '.join(variant_summary['plugin_flags']) or '(none)'}`"
        )
        for variant_name, variant_summary in summary["variant_summaries"].items()
    )
    delta_lines = "\n".join(
        (
            f"- `{delta['variant_name']}`: wall delta=`{delta['wall_delta_sec']}`, "
            f"import delta(us)=`{delta['import_self_delta_us']}`, "
            f"module delta=`{delta['unique_module_delta']}`, "
            f"removed modules count=`{len(delta['removed_modules'])}`"
        )
        for delta in summary["derived_metrics"]["ranked_by_wall_reduction"]
    ) or "- 当前没有变体差值"

    return f"""# Pytest Plugin Variant Benchmark

## Task

- task_id: `{summary["task_id"]}`
- test_command: `{summary["test_command"]}`
- repetitions: `{summary["repetitions"]}`

## Variants

{variant_lines}

## Deltas vs Default

{delta_lines}
"""


def benchmark_pytest_plugin_variants(
    *,
    task_path: str | Path,
    repo_root: str | Path,
    repetitions: int = 3,
    output_dir: str | Path = "logs/summaries",
    benchmark_label: str | None = None,
) -> dict:
    summary = build_pytest_plugin_variant_benchmark(
        task_path=task_path,
        repo_root=repo_root,
        repetitions=repetitions,
    )
    label = benchmark_label or summary["task_id"]
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    benchmark_id = _next_benchmark_id(output_directory, label)
    summary["benchmark_id"] = benchmark_id

    summary_json_path = output_directory / f"{benchmark_id}.json"
    summary_md_path = output_directory / f"{benchmark_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_pytest_plugin_variant_markdown(summary))

    return {
        "benchmark_id": benchmark_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="对 pytest 默认插件变体的 collection 开销做基准。")
    parser.add_argument("--task", required=True, help="任务 JSON 路径")
    parser.add_argument("--repo-root", default=".", help="仓库根目录")
    parser.add_argument("--repetitions", type=int, default=3, help="每个变体重复次数")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--benchmark-label", default=None, help="可选输出标签")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = benchmark_pytest_plugin_variants(
        task_path=args.task,
        repo_root=args.repo_root,
        repetitions=args.repetitions,
        output_dir=args.output_dir,
        benchmark_label=args.benchmark_label,
    )
    summary = output["summary"]
    print("=== Pytest Plugin Variant Benchmark Summary ===")
    print(f"benchmark_id: {output['benchmark_id']}")
    print(f"task_id: {summary['task_id']}")
    print(f"repetitions: {summary['repetitions']}")
    for delta in summary["derived_metrics"]["ranked_by_wall_reduction"]:
        print(
            f"{delta['variant_name']}: wall_delta={delta['wall_delta_sec']}, "
            f"import_delta_us={delta['import_self_delta_us']}, "
            f"module_delta={delta['unique_module_delta']}"
        )
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

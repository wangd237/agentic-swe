"""汇总多个 pytest 插件变体 benchmark 的结果。"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
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


def _average_int(values: list[int]) -> int:
    if not values:
        return 0
    return round(sum(values) / len(values))


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_analysis_id(summary_dir: Path, cohort_label: str) -> str:
    prefix = f"pytest_plugin_variants_cohort_{cohort_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def build_pytest_plugin_variant_snapshot(summary: dict) -> dict:
    variant_deltas = {
        item["variant_name"]: item
        for item in summary["derived_metrics"]["variant_deltas"]
    }
    return {
        "task_id": summary["task_id"],
        "test_command": summary["test_command"],
        "repetitions": summary["repetitions"],
        "variant_deltas": variant_deltas,
    }


def build_pytest_plugin_variant_cohort_summary(
    *,
    benchmark_summary_paths: list[str | Path],
    cohort_label: str,
) -> dict:
    summaries = [_load_json(path) for path in benchmark_summary_paths]
    task_snapshots = [build_pytest_plugin_variant_snapshot(summary) for summary in summaries]

    variant_wall_deltas: dict[str, list[float]] = defaultdict(list)
    variant_import_deltas: dict[str, list[int]] = defaultdict(list)
    variant_module_deltas: dict[str, list[int]] = defaultdict(list)
    removed_module_counter: dict[str, Counter[str]] = defaultdict(Counter)

    for snapshot in task_snapshots:
        for variant_name, delta in snapshot["variant_deltas"].items():
            variant_wall_deltas[variant_name].append(float(delta["wall_delta_sec"]))
            variant_import_deltas[variant_name].append(int(delta["import_self_delta_us"]))
            variant_module_deltas[variant_name].append(int(delta["unique_module_delta"]))
            for module_name in delta["removed_modules"]:
                removed_module_counter[variant_name][module_name] += 1

    variant_aggregate = {
        variant_name: {
            "average_wall_delta_sec": _average(variant_wall_deltas[variant_name]),
            "average_import_delta_us": _average_int(variant_import_deltas[variant_name]),
            "average_module_delta": _average_int(variant_module_deltas[variant_name]),
            "top_removed_modules": [
                {"module": module_name, "task_count": count}
                for module_name, count in removed_module_counter[variant_name].most_common(12)
            ],
        }
        for variant_name in sorted(variant_wall_deltas)
    }

    ranked_variants = sorted(
        (
            {
                "variant_name": variant_name,
                **aggregate,
            }
            for variant_name, aggregate in variant_aggregate.items()
        ),
        key=lambda item: item["average_wall_delta_sec"],
    )

    return {
        "created_at": _utc_timestamp(),
        "cohort_label": cohort_label,
        "task_count": len(task_snapshots),
        "task_ids": [item["task_id"] for item in task_snapshots],
        "variant_aggregate": variant_aggregate,
        "ranked_variants": ranked_variants,
        "task_snapshots": task_snapshots,
    }


def build_pytest_plugin_variant_cohort_markdown(summary: dict) -> str:
    variant_lines = "\n".join(
        (
            f"- `{item['variant_name']}`: avg wall delta=`{item['average_wall_delta_sec']}`, "
            f"avg import delta(us)=`{item['average_import_delta_us']}`, "
            f"avg module delta=`{item['average_module_delta']}`"
        )
        for item in summary["ranked_variants"]
    ) or "- 当前没有可汇总变体"

    removed_module_lines = "\n".join(
        (
            f"- `{item['variant_name']}`: "
            + ", ".join(
                f"`{module['module']}` x{module['task_count']}"
                for module in item["top_removed_modules"][:6]
            )
        )
        for item in summary["ranked_variants"]
    ) or "- 当前没有 removed modules 统计"

    return f"""# Pytest Plugin Variant Cohort Analysis

## Cohort

- cohort_label: `{summary["cohort_label"]}`
- task_count: `{summary["task_count"]}`
- task_ids: `{summary["task_ids"]}`

## Ranked Variants

{variant_lines}

## Removed Modules

{removed_module_lines}
"""


def analyze_pytest_plugin_variant_cohort(
    *,
    benchmark_summary_paths: list[str | Path],
    cohort_label: str,
    output_dir: str | Path = "logs/summaries",
) -> dict:
    summary = build_pytest_plugin_variant_cohort_summary(
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
    write_text(summary_md_path, build_pytest_plugin_variant_cohort_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总多个 pytest 插件变体 benchmark 的结果。")
    parser.add_argument("--benchmark-summary", action="append", required=True, help="benchmark summary JSON 路径，可重复传入")
    parser.add_argument("--cohort-label", required=True, help="cohort 标签")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析输出目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_pytest_plugin_variant_cohort(
        benchmark_summary_paths=args.benchmark_summary,
        cohort_label=args.cohort_label,
        output_dir=args.output_dir,
    )
    summary = output["summary"]
    print("=== Pytest Plugin Variant Cohort Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"cohort_label: {summary['cohort_label']}")
    print(f"task_count: {summary['task_count']}")
    for item in summary["ranked_variants"]:
        print(
            f"{item['variant_name']}: avg_wall_delta={item['average_wall_delta_sec']}, "
            f"avg_import_delta_us={item['average_import_delta_us']}, "
            f"avg_module_delta={item['average_module_delta']}"
        )
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

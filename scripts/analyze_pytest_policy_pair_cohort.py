"""汇总多个 pytest 策略版 compare 结果。"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
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


@lru_cache(maxsize=None)
def _load_policy_runtime_signature(policy_id: str) -> dict | None:
    policy_path = REPO_ROOT / "optimization" / "policy_versions" / f"{policy_id}.json"
    if not policy_path.exists():
        return None
    payload = _load_json(policy_path)
    return {
        "pytest_additional_flags": list(payload.get("pytest_additional_flags") or []),
    }


def _summary_prefix(kind: str, cohort_label: str) -> str:
    if kind == "pytest_phases":
        return f"pytest_policy_pair_phases_cohort_{cohort_label}_"
    if kind == "pytest_importtime":
        return f"pytest_policy_pair_importtime_cohort_{cohort_label}_"
    raise ValueError(f"不支持的 summary kind: {kind}")


def _next_analysis_id(summary_dir: Path, kind: str, cohort_label: str) -> str:
    prefix = _summary_prefix(kind, cohort_label)
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _infer_kind(summaries: list[dict]) -> str:
    if not summaries:
        raise ValueError("至少需要一份 compare summary。")
    first_kind = summaries[0].get("kind")
    if first_kind not in {"pytest_phases", "pytest_importtime"}:
        raise ValueError(f"不支持的 summary kind: {first_kind}")
    if any(summary.get("kind") != first_kind for summary in summaries[1:]):
        raise ValueError("传入的 compare summary 类型不一致，不能聚合。")
    return first_kind


def _extract_runtime_signatures(summary: dict) -> tuple[dict | None, dict | None]:
    runtime_signature = summary.get("runtime_signature") or {}
    baseline_signature = runtime_signature.get("baseline")
    improved_signature = runtime_signature.get("improved")
    if baseline_signature is not None and improved_signature is not None:
        return baseline_signature, improved_signature

    baseline_policy_id = summary.get("baseline_policy_id")
    improved_policy_id = summary.get("improved_policy_id")
    if not baseline_policy_id or not improved_policy_id:
        return None, None
    return (
        _load_policy_runtime_signature(str(baseline_policy_id)),
        _load_policy_runtime_signature(str(improved_policy_id)),
    )


def _is_runtime_equivalent_summary(summary: dict) -> bool:
    runtime_equivalent = summary.get("runtime_equivalent")
    if runtime_equivalent is not None:
        return bool(runtime_equivalent)
    baseline_signature, improved_signature = _extract_runtime_signatures(summary)
    if baseline_signature is None or improved_signature is None:
        return False
    return baseline_signature == improved_signature


def build_phase_task_snapshot(summary: dict) -> dict:
    deltas = summary["deltas"]
    return {
        "task_id": summary["task_id"],
        "baseline_policy_id": summary["baseline_policy_id"],
        "improved_policy_id": summary["improved_policy_id"],
        "runtime_equivalent": _is_runtime_equivalent_summary(summary),
        "pytest_startup_over_python_delta_sec": float(deltas["pytest_startup_over_python_delta_sec"]),
        "collect_over_pytest_startup_delta_sec": float(deltas["collect_over_pytest_startup_delta_sec"]),
        "full_over_collect_delta_sec": float(deltas["full_over_collect_delta_sec"]),
        "collect_first_minus_repeated_delta_sec": float(deltas["collect_first_minus_repeated_delta_sec"]),
        "full_first_minus_repeated_delta_sec": float(deltas["full_first_minus_repeated_delta_sec"]),
    }


def build_importtime_task_snapshot(summary: dict) -> dict:
    deltas = summary["deltas"]
    return {
        "task_id": summary["task_id"],
        "baseline_policy_id": summary["baseline_policy_id"],
        "improved_policy_id": summary["improved_policy_id"],
        "runtime_equivalent": _is_runtime_equivalent_summary(summary),
        "collect_wall_delta_sec": float(deltas["collect_wall_delta_sec"]),
        "collect_import_self_delta_us": int(deltas["collect_import_self_delta_us"]),
        "collect_unique_module_delta": int(deltas["collect_unique_module_delta"]),
        "collect_wall_first_minus_repeated_delta_sec": float(deltas["collect_wall_first_minus_repeated_delta_sec"]),
        "collect_import_self_first_minus_repeated_delta_us": int(
            deltas["collect_import_self_first_minus_repeated_delta_us"]
        ),
    }


def build_phase_cohort_summary(summaries: list[dict], cohort_label: str) -> dict:
    task_snapshots = [build_phase_task_snapshot(summary) for summary in summaries]
    startup_deltas = [item["pytest_startup_over_python_delta_sec"] for item in task_snapshots]
    collect_deltas = [item["collect_over_pytest_startup_delta_sec"] for item in task_snapshots]
    full_deltas = [item["full_over_collect_delta_sec"] for item in task_snapshots]
    collect_first_deltas = [item["collect_first_minus_repeated_delta_sec"] for item in task_snapshots]
    full_first_deltas = [item["full_first_minus_repeated_delta_sec"] for item in task_snapshots]
    ranked_collect_deltas = sorted(
        task_snapshots,
        key=lambda item: item["collect_over_pytest_startup_delta_sec"],
        reverse=True,
    )

    return {
        "created_at": _utc_timestamp(),
        "kind": "pytest_phases",
        "cohort_label": cohort_label,
        "task_count": len(task_snapshots),
        "task_ids": [item["task_id"] for item in task_snapshots],
        "baseline_policy_ids": sorted({item["baseline_policy_id"] for item in task_snapshots}),
        "improved_policy_ids": sorted({item["improved_policy_id"] for item in task_snapshots}),
        "runtime_equivalent_task_count": sum(1 for item in task_snapshots if item["runtime_equivalent"]),
        "aggregate": {
            "average_pytest_startup_over_python_delta_sec": _average(startup_deltas),
            "average_collect_over_pytest_startup_delta_sec": _average(collect_deltas),
            "average_full_over_collect_delta_sec": _average(full_deltas),
            "average_collect_first_minus_repeated_delta_sec": _average_optional(collect_first_deltas),
            "average_full_first_minus_repeated_delta_sec": _average_optional(full_first_deltas),
            "startup_slower_task_count": len([value for value in startup_deltas if value > 0]),
            "collect_slower_task_count": len([value for value in collect_deltas if value > 0]),
            "full_slower_task_count": len([value for value in full_deltas if value > 0]),
        },
        "top_collect_over_pytest_startup_deltas": ranked_collect_deltas,
        "task_snapshots": task_snapshots,
    }


def build_importtime_cohort_summary(summaries: list[dict], cohort_label: str) -> dict:
    task_snapshots = [build_importtime_task_snapshot(summary) for summary in summaries]
    collect_wall_deltas = [item["collect_wall_delta_sec"] for item in task_snapshots]
    collect_import_deltas = [item["collect_import_self_delta_us"] for item in task_snapshots]
    collect_module_deltas = [item["collect_unique_module_delta"] for item in task_snapshots]
    collect_first_wall_deltas = [item["collect_wall_first_minus_repeated_delta_sec"] for item in task_snapshots]
    collect_first_import_deltas = [item["collect_import_self_first_minus_repeated_delta_us"] for item in task_snapshots]
    ranked_collect_wall_deltas = sorted(
        task_snapshots,
        key=lambda item: item["collect_wall_delta_sec"],
        reverse=True,
    )

    return {
        "created_at": _utc_timestamp(),
        "kind": "pytest_importtime",
        "cohort_label": cohort_label,
        "task_count": len(task_snapshots),
        "task_ids": [item["task_id"] for item in task_snapshots],
        "baseline_policy_ids": sorted({item["baseline_policy_id"] for item in task_snapshots}),
        "improved_policy_ids": sorted({item["improved_policy_id"] for item in task_snapshots}),
        "runtime_equivalent_task_count": sum(1 for item in task_snapshots if item["runtime_equivalent"]),
        "aggregate": {
            "average_collect_wall_delta_sec": _average(collect_wall_deltas),
            "average_collect_import_self_delta_us": round(sum(collect_import_deltas) / len(collect_import_deltas))
            if collect_import_deltas
            else 0,
            "average_collect_unique_module_delta": round(sum(collect_module_deltas) / len(collect_module_deltas))
            if collect_module_deltas
            else 0,
            "average_collect_wall_first_minus_repeated_delta_sec": _average_optional(collect_first_wall_deltas),
            "average_collect_import_self_first_minus_repeated_delta_us": _average_optional(
                [float(value) for value in collect_first_import_deltas]
            ),
            "collect_wall_slower_task_count": len([value for value in collect_wall_deltas if value > 0]),
            "collect_import_self_higher_task_count": len([value for value in collect_import_deltas if value > 0]),
        },
        "top_collect_wall_deltas": ranked_collect_wall_deltas,
        "task_snapshots": task_snapshots,
    }


def build_pytest_policy_pair_cohort_summary(
    *,
    compare_summary_paths: list[str | Path],
    cohort_label: str,
) -> dict:
    summaries = [_load_json(path) for path in compare_summary_paths]
    kind = _infer_kind(summaries)
    if kind == "pytest_phases":
        return build_phase_cohort_summary(summaries, cohort_label)
    return build_importtime_cohort_summary(summaries, cohort_label)


def build_pytest_policy_pair_cohort_markdown(summary: dict) -> str:
    if summary["kind"] == "pytest_phases":
        aggregate = summary["aggregate"]
        task_lines = "\n".join(
            (
                f"- `{item['task_id']}`: startup delta=`{item['pytest_startup_over_python_delta_sec']}`, "
                f"collect delta=`{item['collect_over_pytest_startup_delta_sec']}`, "
                f"full delta=`{item['full_over_collect_delta_sec']}`"
            )
            for item in summary["top_collect_over_pytest_startup_deltas"]
        ) or "- 当前没有可汇总任务"
        aggregate_lines = "\n".join(
            [
                f"- average_pytest_startup_over_python_delta_sec: `{aggregate['average_pytest_startup_over_python_delta_sec']}`",
                f"- average_collect_over_pytest_startup_delta_sec: `{aggregate['average_collect_over_pytest_startup_delta_sec']}`",
                f"- average_full_over_collect_delta_sec: `{aggregate['average_full_over_collect_delta_sec']}`",
                f"- average_collect_first_minus_repeated_delta_sec: `{aggregate['average_collect_first_minus_repeated_delta_sec']}`",
                f"- average_full_first_minus_repeated_delta_sec: `{aggregate['average_full_first_minus_repeated_delta_sec']}`",
                f"- startup_slower_task_count: `{aggregate['startup_slower_task_count']}`",
                f"- collect_slower_task_count: `{aggregate['collect_slower_task_count']}`",
                f"- full_slower_task_count: `{aggregate['full_slower_task_count']}`",
            ]
        )
    else:
        aggregate = summary["aggregate"]
        task_lines = "\n".join(
            (
                f"- `{item['task_id']}`: collect wall delta=`{item['collect_wall_delta_sec']}`, "
                f"collect import self delta(us)=`{item['collect_import_self_delta_us']}`, "
                f"collect module delta=`{item['collect_unique_module_delta']}`"
            )
            for item in summary["top_collect_wall_deltas"]
        ) or "- 当前没有可汇总任务"
        aggregate_lines = "\n".join(
            [
                f"- average_collect_wall_delta_sec: `{aggregate['average_collect_wall_delta_sec']}`",
                f"- average_collect_import_self_delta_us: `{aggregate['average_collect_import_self_delta_us']}`",
                f"- average_collect_unique_module_delta: `{aggregate['average_collect_unique_module_delta']}`",
                f"- average_collect_wall_first_minus_repeated_delta_sec: `{aggregate['average_collect_wall_first_minus_repeated_delta_sec']}`",
                f"- average_collect_import_self_first_minus_repeated_delta_us: `{aggregate['average_collect_import_self_first_minus_repeated_delta_us']}`",
                f"- collect_wall_slower_task_count: `{aggregate['collect_wall_slower_task_count']}`",
                f"- collect_import_self_higher_task_count: `{aggregate['collect_import_self_higher_task_count']}`",
            ]
        )

    return f"""# Pytest Policy Pair Cohort Analysis

## Cohort

- kind: `{summary["kind"]}`
- cohort_label: `{summary["cohort_label"]}`
- task_count: `{summary["task_count"]}`
- task_ids: `{summary["task_ids"]}`
- baseline_policy_ids: `{summary["baseline_policy_ids"]}`
- improved_policy_ids: `{summary["improved_policy_ids"]}`
- runtime_equivalent_task_count: `{summary["runtime_equivalent_task_count"]}`

## Aggregate

{aggregate_lines}

## Task Snapshots

{task_lines}
"""


def analyze_pytest_policy_pair_cohort(
    *,
    compare_summary_paths: list[str | Path],
    cohort_label: str,
    output_dir: str | Path = "logs/summaries",
) -> dict:
    summary = build_pytest_policy_pair_cohort_summary(
        compare_summary_paths=compare_summary_paths,
        cohort_label=cohort_label,
    )
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    analysis_id = _next_analysis_id(output_directory, summary["kind"], cohort_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_pytest_policy_pair_cohort_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总多个 pytest 策略版 compare 结果。")
    parser.add_argument("--compare-summary", action="append", required=True, help="compare summary JSON 路径，可重复传入")
    parser.add_argument("--cohort-label", required=True, help="cohort 标签")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析输出目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_pytest_policy_pair_cohort(
        compare_summary_paths=args.compare_summary,
        cohort_label=args.cohort_label,
        output_dir=args.output_dir,
    )
    summary = output["summary"]
    aggregate = summary["aggregate"]
    print("=== Pytest Policy Pair Cohort Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"kind: {summary['kind']}")
    print(f"cohort_label: {summary['cohort_label']}")
    print(f"task_count: {summary['task_count']}")
    for key, value in aggregate.items():
        print(f"{key}: {value}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

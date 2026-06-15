"""汇总多轮 pytest policy pair matrix 结果。"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
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


def _next_analysis_id(summary_dir: Path, set_label: str) -> str:
    prefix = f"pytest_policy_pair_matrix_set_{set_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


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


def _infer_runtime_equivalent_task_count(summary: dict) -> int:
    explicit_count = summary.get("runtime_equivalent_task_count")
    if explicit_count is not None:
        return int(explicit_count)
    task_records = summary.get("task_records") or []
    count = 0
    for item in task_records:
        phase_summary = ((item.get("phase") or {}).get("compare_summary")) or {}
        importtime_summary = ((item.get("importtime") or {}).get("compare_summary")) or {}
        if _is_runtime_equivalent_summary(phase_summary) and _is_runtime_equivalent_summary(importtime_summary):
            count += 1
    return count


def build_matrix_snapshot(summary: dict) -> dict:
    phase = summary["phase_cohort_summary"]["aggregate"]
    importtime = summary["importtime_cohort_summary"]["aggregate"]
    return {
        "matrix_label": summary["matrix_label"],
        "task_count": int(summary["task_count"]),
        "runtime_equivalent_task_count": _infer_runtime_equivalent_task_count(summary),
        "task_ids": [item["task_id"] for item in summary["task_records"]],
        "average_pytest_startup_over_python_delta_sec": float(
            phase["average_pytest_startup_over_python_delta_sec"]
        ),
        "average_collect_over_pytest_startup_delta_sec": float(
            phase["average_collect_over_pytest_startup_delta_sec"]
        ),
        "average_full_over_collect_delta_sec": float(phase["average_full_over_collect_delta_sec"]),
        "startup_slower_task_count": int(phase["startup_slower_task_count"]),
        "collect_slower_task_count": int(phase["collect_slower_task_count"]),
        "full_slower_task_count": int(phase["full_slower_task_count"]),
        "average_collect_wall_delta_sec": float(importtime["average_collect_wall_delta_sec"]),
        "average_collect_import_self_delta_us": float(importtime["average_collect_import_self_delta_us"]),
        "collect_wall_slower_task_count": int(importtime["collect_wall_slower_task_count"]),
        "collect_import_self_higher_task_count": int(importtime["collect_import_self_higher_task_count"]),
    }


def build_pytest_policy_pair_matrix_set_summary(
    *,
    matrix_summary_paths: list[str | Path],
    set_label: str,
) -> dict:
    summaries = [_load_json(path) for path in matrix_summary_paths]
    matrix_snapshots = [build_matrix_snapshot(summary) for summary in summaries]

    startup_values = [item["average_pytest_startup_over_python_delta_sec"] for item in matrix_snapshots]
    collect_values = [item["average_collect_over_pytest_startup_delta_sec"] for item in matrix_snapshots]
    full_values = [item["average_full_over_collect_delta_sec"] for item in matrix_snapshots]
    collect_wall_values = [item["average_collect_wall_delta_sec"] for item in matrix_snapshots]
    collect_import_values = [item["average_collect_import_self_delta_us"] for item in matrix_snapshots]
    ranked_importtime = sorted(
        matrix_snapshots,
        key=lambda item: item["average_collect_import_self_delta_us"],
        reverse=True,
    )

    return {
        "created_at": _utc_timestamp(),
        "set_label": set_label,
        "matrix_count": len(matrix_snapshots),
        "matrix_labels": [item["matrix_label"] for item in matrix_snapshots],
        "aggregate": {
            "average_startup_delta_sec": _average(startup_values),
            "average_collect_delta_sec": _average(collect_values),
            "average_full_delta_sec": _average(full_values),
            "average_collect_wall_delta_sec": _average(collect_wall_values),
            "average_collect_import_self_delta_us": _average(collect_import_values),
            "runtime_equivalent_matrix_count": len(
                [item for item in matrix_snapshots if item["runtime_equivalent_task_count"] == item["task_count"]]
            ),
            "startup_positive_matrix_count": len([value for value in startup_values if value > 0]),
            "collect_positive_matrix_count": len([value for value in collect_values if value > 0]),
            "full_positive_matrix_count": len([value for value in full_values if value > 0]),
            "collect_wall_positive_matrix_count": len([value for value in collect_wall_values if value > 0]),
            "collect_import_positive_matrix_count": len([value for value in collect_import_values if value > 0]),
        },
        "top_collect_import_matrices": ranked_importtime,
        "matrix_snapshots": matrix_snapshots,
    }


def build_pytest_policy_pair_matrix_set_markdown(summary: dict) -> str:
    aggregate = summary["aggregate"]
    matrix_lines = "\n".join(
        (
            f"- `{item['matrix_label']}`: "
            f"startup delta=`{item['average_pytest_startup_over_python_delta_sec']}`, "
            f"collect delta=`{item['average_collect_over_pytest_startup_delta_sec']}`, "
            f"full delta=`{item['average_full_over_collect_delta_sec']}`, "
            f"collect wall delta=`{item['average_collect_wall_delta_sec']}`, "
            f"collect import delta(us)=`{item['average_collect_import_self_delta_us']}`"
        )
        for item in summary["matrix_snapshots"]
    ) or "- 当前没有 matrix snapshot"

    return f"""# Pytest Policy Pair Matrix Set

## Scope

- set_label: `{summary["set_label"]}`
- matrix_count: `{summary["matrix_count"]}`
- matrix_labels: `{summary["matrix_labels"]}`

## Aggregate

- average_startup_delta_sec: `{aggregate["average_startup_delta_sec"]}`
- average_collect_delta_sec: `{aggregate["average_collect_delta_sec"]}`
- average_full_delta_sec: `{aggregate["average_full_delta_sec"]}`
- average_collect_wall_delta_sec: `{aggregate["average_collect_wall_delta_sec"]}`
- average_collect_import_self_delta_us: `{aggregate["average_collect_import_self_delta_us"]}`
- runtime_equivalent_matrix_count: `{aggregate["runtime_equivalent_matrix_count"]}`
- startup_positive_matrix_count: `{aggregate["startup_positive_matrix_count"]}`
- collect_positive_matrix_count: `{aggregate["collect_positive_matrix_count"]}`
- full_positive_matrix_count: `{aggregate["full_positive_matrix_count"]}`
- collect_wall_positive_matrix_count: `{aggregate["collect_wall_positive_matrix_count"]}`
- collect_import_positive_matrix_count: `{aggregate["collect_import_positive_matrix_count"]}`

## Matrix Snapshots

{matrix_lines}
"""


def analyze_pytest_policy_pair_matrix_set(
    *,
    matrix_summary_paths: list[str | Path],
    set_label: str,
    output_dir: str | Path = "logs/summaries",
) -> dict:
    summary = build_pytest_policy_pair_matrix_set_summary(
        matrix_summary_paths=matrix_summary_paths,
        set_label=set_label,
    )
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    analysis_id = _next_analysis_id(output_directory, set_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_pytest_policy_pair_matrix_set_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="汇总多轮 pytest policy pair matrix 结果。")
    parser.add_argument("--matrix-summary", action="append", required=True, help="matrix summary JSON 路径，可重复传入")
    parser.add_argument("--set-label", required=True, help="matrix set 标签")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_pytest_policy_pair_matrix_set(
        matrix_summary_paths=args.matrix_summary,
        set_label=args.set_label,
        output_dir=args.output_dir,
    )
    summary = output["summary"]
    aggregate = summary["aggregate"]
    print("=== Pytest Policy Pair Matrix Set Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"set_label: {summary['set_label']}")
    print(f"matrix_count: {summary['matrix_count']}")
    for key, value in aggregate.items():
        print(f"{key}: {value}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

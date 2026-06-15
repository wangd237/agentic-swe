"""对同一任务的两份 pytest benchmark 摘要做策略版本对照。"""

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


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _extract_runtime_signature(summary: dict) -> dict:
    return {
        "pytest_additional_flags": list(summary.get("pytest_additional_flags") or []),
    }


def _is_runtime_equivalent(baseline_summary: dict, improved_summary: dict) -> bool:
    return _extract_runtime_signature(baseline_summary) == _extract_runtime_signature(improved_summary)


def _next_analysis_id(summary_dir: Path, compare_label: str | None = None) -> str:
    prefix = f"pytest_policy_pair_{compare_label}_" if compare_label else "pytest_policy_pair_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _infer_summary_kind(summary: dict) -> str:
    if "phase_summaries" not in summary:
        raise ValueError("无法识别 summary 类型：缺少 phase_summaries")
    phase_keys = set(summary["phase_summaries"])
    if {"python_noop", "pytest_version", "pytest_collect_only", "pytest_full_run"} <= phase_keys:
        return "pytest_phases"
    if {"pytest_version_importtime", "pytest_collect_importtime"} <= phase_keys:
        return "pytest_importtime"
    raise ValueError(f"不支持的 summary 类型，phase keys: {sorted(phase_keys)}")


def build_phase_comparison(baseline: dict, improved: dict) -> dict:
    derived_baseline = baseline["derived_metrics"]
    derived_improved = improved["derived_metrics"]
    return {
        "kind": "pytest_phases",
        "task_id": baseline["task_id"],
        "baseline_policy_id": baseline["policy_id"],
        "improved_policy_id": improved["policy_id"],
        "baseline_summary_path": baseline["summary_path"],
        "improved_summary_path": improved["summary_path"],
        "runtime_signature": {
            "baseline": _extract_runtime_signature(baseline),
            "improved": _extract_runtime_signature(improved),
        },
        "runtime_equivalent": _is_runtime_equivalent(baseline, improved),
        "deltas": {
            "pytest_startup_over_python_delta_sec": _round_float(
                float(derived_improved["average_pytest_startup_over_python_sec"])
                - float(derived_baseline["average_pytest_startup_over_python_sec"])
            ),
            "collect_over_pytest_startup_delta_sec": _round_float(
                float(derived_improved["average_collect_over_pytest_startup_sec"])
                - float(derived_baseline["average_collect_over_pytest_startup_sec"])
            ),
            "full_over_collect_delta_sec": _round_float(
                float(derived_improved["average_full_over_collect_sec"])
                - float(derived_baseline["average_full_over_collect_sec"])
            ),
            "collect_first_minus_repeated_delta_sec": _round_float(
                float(derived_improved["collect_first_minus_repeated_sec"] or 0.0)
                - float(derived_baseline["collect_first_minus_repeated_sec"] or 0.0)
            ),
            "full_first_minus_repeated_delta_sec": _round_float(
                float(derived_improved["full_first_minus_repeated_sec"] or 0.0)
                - float(derived_baseline["full_first_minus_repeated_sec"] or 0.0)
            ),
        },
    }


def build_importtime_comparison(baseline: dict, improved: dict) -> dict:
    derived_baseline = baseline["derived_metrics"]
    derived_improved = improved["derived_metrics"]
    return {
        "kind": "pytest_importtime",
        "task_id": baseline["task_id"],
        "baseline_policy_id": baseline["policy_id"],
        "improved_policy_id": improved["policy_id"],
        "baseline_summary_path": baseline["summary_path"],
        "improved_summary_path": improved["summary_path"],
        "runtime_signature": {
            "baseline": _extract_runtime_signature(baseline),
            "improved": _extract_runtime_signature(improved),
        },
        "runtime_equivalent": _is_runtime_equivalent(baseline, improved),
        "deltas": {
            "collect_wall_delta_sec": _round_float(
                float(derived_improved["average_collect_wall_delta_sec"])
                - float(derived_baseline["average_collect_wall_delta_sec"])
            ),
            "collect_import_self_delta_us": int(
                derived_improved["average_collect_import_self_delta_us"]
                - derived_baseline["average_collect_import_self_delta_us"]
            ),
            "collect_unique_module_delta": int(
                derived_improved["average_collect_unique_module_delta"]
                - derived_baseline["average_collect_unique_module_delta"]
            ),
            "collect_wall_first_minus_repeated_delta_sec": _round_float(
                float(derived_improved["collect_wall_first_minus_repeated_sec"] or 0.0)
                - float(derived_baseline["collect_wall_first_minus_repeated_sec"] or 0.0)
            ),
            "collect_import_self_first_minus_repeated_delta_us": int(
                float(derived_improved["collect_import_self_first_minus_repeated_us"] or 0.0)
                - float(derived_baseline["collect_import_self_first_minus_repeated_us"] or 0.0)
            ),
        },
    }


def build_pytest_policy_pair_comparison(
    *,
    baseline_summary_path: str | Path,
    improved_summary_path: str | Path,
) -> dict:
    baseline_summary = _load_json(baseline_summary_path)
    improved_summary = _load_json(improved_summary_path)
    baseline_summary["summary_path"] = str(Path(baseline_summary_path).resolve())
    improved_summary["summary_path"] = str(Path(improved_summary_path).resolve())

    if baseline_summary["task_id"] != improved_summary["task_id"]:
        raise ValueError("baseline 与 improved 的 task_id 不一致，不能比较。")

    summary_kind = _infer_summary_kind(baseline_summary)
    improved_kind = _infer_summary_kind(improved_summary)
    if summary_kind != improved_kind:
        raise ValueError("baseline 与 improved 的 summary 类型不一致。")

    if summary_kind == "pytest_phases":
        comparison = build_phase_comparison(baseline_summary, improved_summary)
    else:
        comparison = build_importtime_comparison(baseline_summary, improved_summary)

    return {
        "created_at": _utc_timestamp(),
        **comparison,
    }


def build_pytest_policy_pair_markdown(summary: dict) -> str:
    delta_lines = "\n".join(
        f"- {key}: `{value}`"
        for key, value in summary["deltas"].items()
    )
    return f"""# Pytest Policy Pair Comparison

## Scope

- kind: `{summary["kind"]}`
- task_id: `{summary["task_id"]}`
- baseline_policy_id: `{summary["baseline_policy_id"]}`
- improved_policy_id: `{summary["improved_policy_id"]}`
- runtime_equivalent: `{summary["runtime_equivalent"]}`
- baseline_pytest_additional_flags: `{summary["runtime_signature"]["baseline"]["pytest_additional_flags"]}`
- improved_pytest_additional_flags: `{summary["runtime_signature"]["improved"]["pytest_additional_flags"]}`

## Deltas

{delta_lines}
"""


def compare_pytest_policy_pair(
    *,
    baseline_summary_path: str | Path,
    improved_summary_path: str | Path,
    output_dir: str | Path = "logs/summaries",
    compare_label: str | None = None,
) -> dict:
    summary = build_pytest_policy_pair_comparison(
        baseline_summary_path=baseline_summary_path,
        improved_summary_path=improved_summary_path,
    )
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    analysis_id = _next_analysis_id(output_directory, compare_label=compare_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_pytest_policy_pair_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="比较同一任务的两份 pytest benchmark 摘要。")
    parser.add_argument("--baseline-summary", required=True, help="baseline summary JSON 路径")
    parser.add_argument("--improved-summary", required=True, help="improved summary JSON 路径")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--compare-label", default=None, help="可选输出标签")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = compare_pytest_policy_pair(
        baseline_summary_path=args.baseline_summary,
        improved_summary_path=args.improved_summary,
        output_dir=args.output_dir,
        compare_label=args.compare_label,
    )
    summary = output["summary"]
    print("=== Pytest Policy Pair Comparison Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"kind: {summary['kind']}")
    print(f"task_id: {summary['task_id']}")
    print(f"baseline_policy_id: {summary['baseline_policy_id']}")
    print(f"improved_policy_id: {summary['improved_policy_id']}")
    print(f"runtime_equivalent: {summary['runtime_equivalent']}")
    for key, value in summary["deltas"].items():
        print(f"{key}: {value}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

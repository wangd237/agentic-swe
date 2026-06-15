"""基于已有 pytest policy pair 摘要重建带校准口径的聚合视图。"""

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
from scripts.analyze_pytest_policy_pair_matrix_set import analyze_pytest_policy_pair_matrix_set


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_analysis_id(summary_dir: Path, view_label: str) -> str:
    prefix = f"pytest_policy_pair_calibrated_view_{view_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def build_calibrated_view_summary(
    *,
    phase_compare_paths: list[str | Path],
    importtime_compare_paths: list[str | Path],
    matrix_summary_paths: list[str | Path],
    view_label: str,
    output_dir: str | Path = "logs/summaries",
) -> dict:
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    phase_output = analyze_pytest_policy_pair_cohort(
        compare_summary_paths=phase_compare_paths,
        cohort_label=f"{view_label}_phase_calibrated",
        output_dir=output_directory,
    )
    importtime_output = analyze_pytest_policy_pair_cohort(
        compare_summary_paths=importtime_compare_paths,
        cohort_label=f"{view_label}_importtime_calibrated",
        output_dir=output_directory,
    )
    matrix_output = analyze_pytest_policy_pair_matrix_set(
        matrix_summary_paths=matrix_summary_paths,
        set_label=f"{view_label}_triage_calibrated",
        output_dir=output_directory,
    )

    return {
        "created_at": _utc_timestamp(),
        "view_label": view_label,
        "phase_compare_count": len(phase_compare_paths),
        "importtime_compare_count": len(importtime_compare_paths),
        "matrix_summary_count": len(matrix_summary_paths),
        "phase_compare_paths": [str(Path(path).resolve()) for path in phase_compare_paths],
        "importtime_compare_paths": [str(Path(path).resolve()) for path in importtime_compare_paths],
        "matrix_summary_paths": [str(Path(path).resolve()) for path in matrix_summary_paths],
        "phase_output": {
            "analysis_id": phase_output["analysis_id"],
            "summary_json_path": phase_output["summary_json_path"],
            "summary_md_path": phase_output["summary_md_path"],
            "summary": phase_output["summary"],
        },
        "importtime_output": {
            "analysis_id": importtime_output["analysis_id"],
            "summary_json_path": importtime_output["summary_json_path"],
            "summary_md_path": importtime_output["summary_md_path"],
            "summary": importtime_output["summary"],
        },
        "matrix_output": {
            "analysis_id": matrix_output["analysis_id"],
            "summary_json_path": matrix_output["summary_json_path"],
            "summary_md_path": matrix_output["summary_md_path"],
            "summary": matrix_output["summary"],
        },
    }


def build_calibrated_view_markdown(summary: dict) -> str:
    phase_summary = summary["phase_output"]["summary"]
    importtime_summary = summary["importtime_output"]["summary"]
    matrix_summary = summary["matrix_output"]["summary"]
    return f"""# Pytest Policy Pair Calibrated View

## Scope

- view_label: `{summary["view_label"]}`
- phase_compare_count: `{summary["phase_compare_count"]}`
- importtime_compare_count: `{summary["importtime_compare_count"]}`
- matrix_summary_count: `{summary["matrix_summary_count"]}`

## Calibrated Outputs

- phase_summary_json_path: `{summary["phase_output"]["summary_json_path"]}`
- phase_runtime_equivalent_task_count: `{phase_summary["runtime_equivalent_task_count"]}`
- importtime_summary_json_path: `{summary["importtime_output"]["summary_json_path"]}`
- importtime_runtime_equivalent_task_count: `{importtime_summary["runtime_equivalent_task_count"]}`
- matrix_set_summary_json_path: `{summary["matrix_output"]["summary_json_path"]}`
- runtime_equivalent_matrix_count: `{matrix_summary["aggregate"]["runtime_equivalent_matrix_count"]}`
"""


def rebuild_pytest_policy_pair_calibrated_views(
    *,
    phase_compare_paths: list[str | Path],
    importtime_compare_paths: list[str | Path],
    matrix_summary_paths: list[str | Path],
    view_label: str,
    output_dir: str | Path = "logs/summaries",
) -> dict:
    if not phase_compare_paths:
        raise ValueError("至少需要一份 phase compare summary。")
    if not importtime_compare_paths:
        raise ValueError("至少需要一份 importtime compare summary。")
    if not matrix_summary_paths:
        raise ValueError("至少需要一份 matrix summary。")

    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    summary = build_calibrated_view_summary(
        phase_compare_paths=phase_compare_paths,
        importtime_compare_paths=importtime_compare_paths,
        matrix_summary_paths=matrix_summary_paths,
        view_label=view_label,
        output_dir=output_directory,
    )
    analysis_id = _next_analysis_id(output_directory, view_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_calibrated_view_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="基于已有 pytest policy pair 摘要重建 calibrated 聚合视图。")
    parser.add_argument("--phase-compare", action="append", required=True, help="phase compare summary JSON 路径，可重复传入")
    parser.add_argument(
        "--importtime-compare",
        action="append",
        required=True,
        help="importtime compare summary JSON 路径，可重复传入",
    )
    parser.add_argument("--matrix-summary", action="append", required=True, help="matrix summary JSON 路径，可重复传入")
    parser.add_argument("--view-label", required=True, help="本轮 calibrated 视图标签")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = rebuild_pytest_policy_pair_calibrated_views(
        phase_compare_paths=args.phase_compare,
        importtime_compare_paths=args.importtime_compare,
        matrix_summary_paths=args.matrix_summary,
        view_label=args.view_label,
        output_dir=args.output_dir,
    )
    summary = output["summary"]
    print("=== Pytest Policy Pair Calibrated View Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"view_label: {summary['view_label']}")
    print(f"phase_output: {summary['phase_output']['summary_json_path']}")
    print(f"importtime_output: {summary['importtime_output']['summary_json_path']}")
    print(f"matrix_output: {summary['matrix_output']['summary_json_path']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

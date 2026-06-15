"""按模块分组汇总 pytest importtime 中的新增 import 链。"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text


MODULE_GROUP_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("windows_ctypes", ("_ctypes", "ctypes", "ctypes.wintypes")),
    ("xml_stack", ("_elementtree", "pyexpat", "xml", "xml.")),
    ("debugging_chain", ("pdb", "bdb", "cmd", "codeop", "doctest")),
    (
        "terminal_chain",
        (
            "colorama",
            "colorama.",
            "_pytest._io",
            "_pytest._io.",
            "_pytest.terminal",
            "_pytest.terminal.",
            "_pytest.terminalprogress",
        ),
    ),
    (
        "pytest_optional_plugins",
        (
            "_pytest._argcomplete",
            "_pytest.faulthandler",
            "_pytest.helpconfig",
            "_pytest.junitxml",
            "_pytest.pastebin",
            "_pytest.setuponly",
            "_pytest.setupplan",
            "_pytest.stepwise",
            "_pytest.threadexception",
            "_pytest.tracemalloc",
            "_pytest.unittest",
            "_pytest.unraisableexception",
            "_pytest.warnings",
            "faulthandler",
        ),
    ),
    (
        "pytest_collection_core",
        (
            "_pytest.skipping",
            "_pytest.mark",
            "_pytest.python",
            "_pytest.nodes",
            "_pytest.fixtures",
            "_pytest.assertion",
        ),
    ),
    ("python_shell_chain", ("code", "codeop", "readline")),
]


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    prefix = f"pytest_import_groups_{cohort_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def classify_module_group(module_name: str) -> str:
    """把新增模块归到更高层的来源组，便于后续判断主因。"""

    for group_name, prefixes in MODULE_GROUP_RULES:
        if any(module_name == prefix or module_name.startswith(prefix) for prefix in prefixes):
            return group_name
    return "other"


def _build_extra_entries(summary: dict) -> list[dict]:
    version_record = summary["phase_summaries"]["pytest_version_importtime"]["records"][-1]
    collect_record = summary["phase_summaries"]["pytest_collect_importtime"]["records"][-1]
    version_modules = set(version_record["module_names"])
    return [
        entry
        for entry in collect_record["import_entries"]
        if entry["module"] not in version_modules
    ]


def build_pytest_import_group_snapshot(summary: dict) -> dict:
    extra_entries = _build_extra_entries(summary)
    group_totals: dict[str, dict[str, int]] = defaultdict(lambda: {"module_count": 0, "self_us": 0})
    for entry in extra_entries:
        group_name = classify_module_group(entry["module"])
        group_totals[group_name]["module_count"] += 1
        group_totals[group_name]["self_us"] += int(entry["self_us"])

    ranked_groups = sorted(
        (
            {
                "group_name": group_name,
                "module_count": totals["module_count"],
                "self_us": totals["self_us"],
            }
            for group_name, totals in group_totals.items()
        ),
        key=lambda item: (item["self_us"], item["module_count"], item["group_name"]),
        reverse=True,
    )
    return {
        "task_id": summary["task_id"],
        "collect_wall_delta_sec": float(summary["derived_metrics"]["average_collect_wall_delta_sec"]),
        "collect_import_self_delta_us": int(summary["derived_metrics"]["average_collect_import_self_delta_us"]),
        "collect_unique_module_delta": int(summary["derived_metrics"]["average_collect_unique_module_delta"]),
        "extra_entry_count": len(extra_entries),
        "group_totals": ranked_groups,
        "top_extra_entries": sorted(
            (
                {
                    "module": entry["module"],
                    "group_name": classify_module_group(entry["module"]),
                    "self_us": int(entry["self_us"]),
                    "cumulative_us": int(entry["cumulative_us"]),
                }
                for entry in extra_entries
            ),
            key=lambda item: (item["self_us"], item["cumulative_us"], item["module"]),
            reverse=True,
        )[:12],
    }


def build_pytest_import_group_summary(
    *,
    benchmark_summary_paths: list[str | Path],
    cohort_label: str,
) -> dict:
    summaries = [_load_json(path) for path in benchmark_summary_paths]
    task_snapshots = [build_pytest_import_group_snapshot(summary) for summary in summaries]

    group_self_totals: dict[str, list[int]] = defaultdict(list)
    group_module_totals: dict[str, list[int]] = defaultdict(list)
    group_presence_count: dict[str, int] = defaultdict(int)

    for snapshot in task_snapshots:
        observed_groups = {item["group_name"] for item in snapshot["group_totals"]}
        for group_name in observed_groups:
            group_presence_count[group_name] += 1
        task_group_map = {item["group_name"]: item for item in snapshot["group_totals"]}
        for group_name in list(task_group_map) + [rule_name for rule_name, _ in MODULE_GROUP_RULES] + ["other"]:
            item = task_group_map.get(group_name)
            group_self_totals[group_name].append(int(item["self_us"]) if item else 0)
            group_module_totals[group_name].append(int(item["module_count"]) if item else 0)

    ranked_groups = sorted(
        (
            {
                "group_name": group_name,
                "average_self_us": _average_int(self_values),
                "average_module_count": _average_int(group_module_totals[group_name]),
                "present_task_count": group_presence_count.get(group_name, 0),
            }
            for group_name, self_values in group_self_totals.items()
        ),
        key=lambda item: (item["average_self_us"], item["average_module_count"], item["group_name"]),
        reverse=True,
    )

    dominant_tasks = sorted(
        (
            {
                "task_id": snapshot["task_id"],
                "collect_import_self_delta_us": snapshot["collect_import_self_delta_us"],
                "dominant_group": snapshot["group_totals"][0]["group_name"] if snapshot["group_totals"] else "other",
                "dominant_group_self_us": snapshot["group_totals"][0]["self_us"] if snapshot["group_totals"] else 0,
            }
            for snapshot in task_snapshots
        ),
        key=lambda item: (item["collect_import_self_delta_us"], item["dominant_group_self_us"], item["task_id"]),
        reverse=True,
    )

    return {
        "created_at": _utc_timestamp(),
        "cohort_label": cohort_label,
        "task_count": len(task_snapshots),
        "task_ids": [snapshot["task_id"] for snapshot in task_snapshots],
        "ranked_groups": ranked_groups,
        "dominant_tasks": dominant_tasks,
        "task_snapshots": task_snapshots,
    }


def build_pytest_import_group_markdown(summary: dict) -> str:
    group_lines = "\n".join(
        (
            f"- `{item['group_name']}`: avg self(us)=`{item['average_self_us']}`, "
            f"avg modules=`{item['average_module_count']}`, present tasks=`{item['present_task_count']}`"
        )
        for item in summary["ranked_groups"]
    ) or "- 当前没有可汇总分组"
    task_lines = "\n".join(
        (
            f"- `{item['task_id']}`: import delta(us)=`{item['collect_import_self_delta_us']}`, "
            f"dominant group=`{item['dominant_group']}`, dominant self(us)=`{item['dominant_group_self_us']}`"
        )
        for item in summary["dominant_tasks"]
    ) or "- 当前没有任务快照"
    return f"""# Pytest Import Group Analysis

## Cohort

- cohort_label: `{summary["cohort_label"]}`
- task_count: `{summary["task_count"]}`
- task_ids: `{summary["task_ids"]}`

## Ranked Groups

{group_lines}

## Dominant Tasks

{task_lines}
"""


def analyze_pytest_import_groups(
    *,
    benchmark_summary_paths: list[str | Path],
    cohort_label: str,
    output_dir: str | Path = "logs/summaries",
) -> dict:
    summary = build_pytest_import_group_summary(
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
    write_text(summary_md_path, build_pytest_import_group_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按模块分组汇总 pytest importtime 中的新增 import 链。")
    parser.add_argument("--benchmark-summary", action="append", required=True, help="benchmark summary JSON 路径，可重复传入")
    parser.add_argument("--cohort-label", required=True, help="cohort 标签")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析输出目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_pytest_import_groups(
        benchmark_summary_paths=args.benchmark_summary,
        cohort_label=args.cohort_label,
        output_dir=args.output_dir,
    )
    summary = output["summary"]
    print("=== Pytest Import Group Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"cohort_label: {summary['cohort_label']}")
    print(f"task_count: {summary['task_count']}")
    for item in summary["ranked_groups"]:
        print(
            f"{item['group_name']}: avg_self_us={item['average_self_us']}, "
            f"avg_modules={item['average_module_count']}, "
            f"present_tasks={item['present_task_count']}"
        )
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

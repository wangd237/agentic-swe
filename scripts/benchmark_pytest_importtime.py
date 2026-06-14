"""对 pytest 启动与 collection 的 importtime 链路做基准。"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from app.agent.policy import load_policy_config
from app.schemas.task_schema import load_task
from app.tools.run_tests import run_tests


IMPORTTIME_PATTERN = re.compile(r"^import time:\s*(\d+)\s*\|\s*(\d+)\s*\|\s+(.+)$")
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


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
    prefix = f"pytest_importtime_{benchmark_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _build_importtime_command(command: str) -> str:
    if "-X importtime" in command:
        return command
    if command.startswith("python "):
        return command.replace("python ", "python -X importtime ", 1)
    return command


def _build_collect_only_command(test_command: str) -> str:
    if "--collect-only" in test_command:
        return test_command
    return f"{test_command} --collect-only"


def _build_phase_commands(test_command: str) -> dict[str, str]:
    # 这里只看 import 链，不再重复测 full run 本体，避免和上一轮 phase benchmark 重叠。
    version_command = _build_importtime_command("python -m pytest --version")
    collect_command = _build_importtime_command(_build_collect_only_command(test_command))
    return {
        "pytest_version_importtime": version_command,
        "pytest_collect_importtime": collect_command,
    }


def parse_importtime_entries(text: str) -> list[dict]:
    sanitized_text = ANSI_ESCAPE_PATTERN.sub("", text)
    entries: list[dict] = []
    for line in sanitized_text.splitlines():
        match = IMPORTTIME_PATTERN.match(line.strip("\r"))
        if not match:
            continue
        raw_module = match.group(3)
        normalized_module = raw_module.strip()
        entries.append(
            {
                "self_us": int(match.group(1)),
                "cumulative_us": int(match.group(2)),
                "module": normalized_module,
            }
        )
    return entries


def _select_top_entries(entries: list[dict], key: str, limit: int = 10) -> list[dict]:
    ranked_entries = sorted(entries, key=lambda item: (item[key], item["cumulative_us"], item["module"]), reverse=True)
    return [
        {
            "module": entry["module"],
            "self_us": entry["self_us"],
            "cumulative_us": entry["cumulative_us"],
        }
        for entry in ranked_entries[:limit]
    ]


def build_importtime_profile(stderr: str) -> dict:
    entries = parse_importtime_entries(stderr)
    module_counter = Counter(entry["module"] for entry in entries)
    unique_modules = sorted(module_counter)
    total_self_us = sum(entry["self_us"] for entry in entries)
    max_cumulative_us = max((entry["cumulative_us"] for entry in entries), default=0)
    return {
        "entry_count": len(entries),
        "unique_module_count": len(unique_modules),
        "total_import_self_us": total_self_us,
        "max_cumulative_us": max_cumulative_us,
        "module_names": unique_modules,
        "top_self_imports": _select_top_entries(entries, key="self_us"),
        "top_cumulative_imports": _select_top_entries(entries, key="cumulative_us"),
    }


def _build_run_record(phase_name: str, run_index: int, command: str, result: dict) -> dict:
    data = result["data"]
    import_profile = build_importtime_profile(data.get("stderr", ""))
    return {
        "phase_name": phase_name,
        "run_index": run_index,
        "command": command,
        "ok": result["ok"],
        "exit_code": data.get("exit_code"),
        "command_execution_duration_sec": float(data.get("command_execution_duration_sec") or 0.0),
        "summary_extraction_duration_sec": float(data.get("summary_extraction_duration_sec") or 0.0),
        "entry_count": import_profile["entry_count"],
        "unique_module_count": import_profile["unique_module_count"],
        "total_import_self_us": import_profile["total_import_self_us"],
        "max_cumulative_us": import_profile["max_cumulative_us"],
        "import_entries": import_profile["top_cumulative_imports"] + [
            entry
            for entry in parse_importtime_entries(data.get("stderr", ""))
            if entry not in import_profile["top_cumulative_imports"]
        ],
        "module_names": import_profile["module_names"],
        "top_self_imports": import_profile["top_self_imports"],
        "top_cumulative_imports": import_profile["top_cumulative_imports"],
    }


def _build_phase_summary(phase_name: str, command: str, records: list[dict]) -> dict:
    first_record = records[0] if records else None
    repeated_records = records[1:] if len(records) > 1 else []
    latest_record = records[-1] if records else None
    return {
        "phase_name": phase_name,
        "command": command,
        "run_count": len(records),
        "all_ok": all(record["ok"] for record in records),
        "average_command_execution_duration_sec": _average(
            [record["command_execution_duration_sec"] for record in records]
        ),
        "average_total_import_self_us": _average_int([record["total_import_self_us"] for record in records]),
        "average_unique_module_count": _average_int([record["unique_module_count"] for record in records]),
        "average_entry_count": _average_int([record["entry_count"] for record in records]),
        "first_command_execution_duration_sec": first_record["command_execution_duration_sec"] if first_record else None,
        "repeated_command_execution_average_sec": _average_optional(
            [record["command_execution_duration_sec"] for record in repeated_records]
        ),
        "first_total_import_self_us": first_record["total_import_self_us"] if first_record else None,
        "repeated_total_import_self_average_us": _average_optional(
            [float(record["total_import_self_us"]) for record in repeated_records]
        ),
        "latest_top_self_imports": latest_record["top_self_imports"] if latest_record else [],
        "latest_top_cumulative_imports": latest_record["top_cumulative_imports"] if latest_record else [],
        "latest_module_names": latest_record["module_names"] if latest_record else [],
        "records": records,
    }


def _subtract_optional(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _round_float(left - right)


def _build_collect_extra_modules(version_summary: dict, collect_summary: dict) -> list[dict]:
    version_modules = set(version_summary["latest_module_names"])
    latest_collect_record = collect_summary["records"][-1] if collect_summary["records"] else None
    if latest_collect_record is None:
        return []
    extra_entries = [
        {
            "module": entry["module"],
            "self_us": entry["self_us"],
            "cumulative_us": entry["cumulative_us"],
        }
        for entry in latest_collect_record["import_entries"]
        if entry["module"] not in version_modules
    ]
    ranked_extra_entries = sorted(
        extra_entries,
        key=lambda item: (item["self_us"], item["cumulative_us"], item["module"]),
        reverse=True,
    )
    deduplicated_entries: list[dict] = []
    seen_modules: set[str] = set()
    for entry in ranked_extra_entries:
        if entry["module"] in seen_modules:
            continue
        seen_modules.add(entry["module"])
        deduplicated_entries.append(entry)
        if len(deduplicated_entries) >= 10:
            break
    return deduplicated_entries


def _build_derived_metrics(phase_summaries: dict[str, dict]) -> dict:
    version_summary = phase_summaries["pytest_version_importtime"]
    collect_summary = phase_summaries["pytest_collect_importtime"]
    return {
        "average_collect_wall_delta_sec": _round_float(
            collect_summary["average_command_execution_duration_sec"]
            - version_summary["average_command_execution_duration_sec"]
        ),
        "average_collect_import_self_delta_us": int(
            collect_summary["average_total_import_self_us"] - version_summary["average_total_import_self_us"]
        ),
        "average_collect_unique_module_delta": int(
            collect_summary["average_unique_module_count"] - version_summary["average_unique_module_count"]
        ),
        "collect_wall_first_minus_repeated_sec": _subtract_optional(
            collect_summary["first_command_execution_duration_sec"],
            collect_summary["repeated_command_execution_average_sec"],
        ),
        "collect_import_self_first_minus_repeated_us": int(
            round(
                (collect_summary["first_total_import_self_us"] or 0.0)
                - (collect_summary["repeated_total_import_self_average_us"] or 0.0)
            )
        )
        if collect_summary["first_total_import_self_us"] is not None
        and collect_summary["repeated_total_import_self_average_us"] is not None
        else None,
        "latest_collect_extra_modules_top_self": _build_collect_extra_modules(version_summary, collect_summary),
    }


def build_pytest_importtime_benchmark(
    *,
    task_path: str | Path,
    repo_root: str | Path,
    repetitions: int = 3,
    policy_path: str | Path | None = None,
) -> dict:
    repository_root = Path(repo_root).resolve()
    task = load_task(task_path)
    policy_config = load_policy_config(policy_path)
    source_repo_path = (repository_root / task.repo_path).resolve()
    if not source_repo_path.exists():
        raise FileNotFoundError(f"任务 repo 不存在: {source_repo_path}")

    phase_commands = _build_phase_commands(task.test_command)
    phase_summaries: dict[str, dict] = {}
    for phase_name, command in phase_commands.items():
        records: list[dict] = []
        for run_index in range(1, repetitions + 1):
            result = run_tests(
                str(source_repo_path),
                command,
                timeout_sec=30,
                additional_pytest_flags=policy_config.pytest_additional_flags,
            )
            records.append(_build_run_record(phase_name, run_index, command, result))
        phase_summaries[phase_name] = _build_phase_summary(phase_name, command, records)

    return {
        "created_at": _utc_timestamp(),
        "task_id": task.task_id,
        "task_path": str(Path(task_path).resolve()),
        "source_repo_path": str(source_repo_path),
        "test_command": task.test_command,
        "repetitions": repetitions,
        "policy_id": policy_config.policy_id,
        "policy_path": str(Path(policy_path).resolve()) if policy_path is not None else None,
        "pytest_additional_flags": policy_config.pytest_additional_flags,
        "phase_summaries": phase_summaries,
        "derived_metrics": _build_derived_metrics(phase_summaries),
    }


def build_pytest_importtime_markdown(summary: dict) -> str:
    phase_lines = "\n".join(
        (
            f"- `{phase_name}`: wall avg=`{phase_summary['average_command_execution_duration_sec']}`, "
            f"import self avg(us)=`{phase_summary['average_total_import_self_us']}`, "
            f"module avg=`{phase_summary['average_unique_module_count']}`"
        )
        for phase_name, phase_summary in summary["phase_summaries"].items()
    )
    extra_module_lines = "\n".join(
        f"- `{entry['module']}`: self_us=`{entry['self_us']}`, cumulative_us=`{entry['cumulative_us']}`"
        for entry in summary["derived_metrics"]["latest_collect_extra_modules_top_self"]
    ) or "- 当前没有识别到 collect-only 新增模块"
    derived = summary["derived_metrics"]
    return f"""# Pytest Importtime Benchmark

## Task

- task_id: `{summary["task_id"]}`
- test_command: `{summary["test_command"]}`
- repetitions: `{summary["repetitions"]}`
- policy_id: `{summary["policy_id"]}`
- pytest_additional_flags: `{' '.join(summary["pytest_additional_flags"]) or '(none)'}`

## Phases

{phase_lines}

## Derived Metrics

- average_collect_wall_delta_sec: `{derived["average_collect_wall_delta_sec"]}`
- average_collect_import_self_delta_us: `{derived["average_collect_import_self_delta_us"]}`
- average_collect_unique_module_delta: `{derived["average_collect_unique_module_delta"]}`
- collect_wall_first_minus_repeated_sec: `{derived["collect_wall_first_minus_repeated_sec"]}`
- collect_import_self_first_minus_repeated_us: `{derived["collect_import_self_first_minus_repeated_us"]}`

## Latest Collect Extra Modules

{extra_module_lines}
"""


def benchmark_pytest_importtime(
    *,
    task_path: str | Path,
    repo_root: str | Path,
    repetitions: int = 3,
    policy_path: str | Path | None = None,
    output_dir: str | Path = "logs/summaries",
    benchmark_label: str | None = None,
) -> dict:
    summary = build_pytest_importtime_benchmark(
        task_path=task_path,
        repo_root=repo_root,
        repetitions=repetitions,
        policy_path=policy_path,
    )
    label = benchmark_label or summary["task_id"]
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    benchmark_id = _next_benchmark_id(output_directory, label)
    summary["benchmark_id"] = benchmark_id

    summary_json_path = output_directory / f"{benchmark_id}.json"
    summary_md_path = output_directory / f"{benchmark_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_pytest_importtime_markdown(summary))

    return {
        "benchmark_id": benchmark_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="对 pytest 启动与 collection 的 importtime 链路做基准。")
    parser.add_argument("--task", required=True, help="任务 JSON 路径")
    parser.add_argument("--repo-root", default=".", help="仓库根目录")
    parser.add_argument("--repetitions", type=int, default=3, help="每个阶段重复次数")
    parser.add_argument("--policy", default=None, help="可选策略 JSON 路径")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--benchmark-label", default=None, help="可选输出标签")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = benchmark_pytest_importtime(
        task_path=args.task,
        repo_root=args.repo_root,
        repetitions=args.repetitions,
        policy_path=args.policy,
        output_dir=args.output_dir,
        benchmark_label=args.benchmark_label,
    )
    summary = output["summary"]
    derived = summary["derived_metrics"]
    print("=== Pytest Importtime Benchmark Summary ===")
    print(f"benchmark_id: {output['benchmark_id']}")
    print(f"task_id: {summary['task_id']}")
    print(f"repetitions: {summary['repetitions']}")
    print(f"policy_id: {summary['policy_id']}")
    print(f"average_collect_wall_delta_sec: {derived['average_collect_wall_delta_sec']}")
    print(f"average_collect_import_self_delta_us: {derived['average_collect_import_self_delta_us']}")
    print(f"average_collect_unique_module_delta: {derived['average_collect_unique_module_delta']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

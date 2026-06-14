"""对 pytest 启动、collection 与 full run 做分阶段基准。"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from app.agent.policy import load_policy_config
from app.schemas.task_schema import load_task
from app.tools.run_tests import run_tests


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _round_float(value: float) -> float:
    return round(value, 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return _round_float(sum(values) / len(values))


def _average_optional(values: list[float]) -> float | None:
    if not values:
        return None
    return _round_float(sum(values) / len(values))


def _next_benchmark_id(summary_dir: Path, benchmark_label: str) -> str:
    prefix = f"pytest_phases_{benchmark_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _build_collect_only_command(test_command: str) -> str:
    if "--collect-only" in test_command:
        return test_command
    return f"{test_command} --collect-only"


def _build_phase_commands(test_command: str) -> dict[str, str]:
    # 这里采用同一解释器和同一 repo，只替换命令形态，尽量把差异收敛到 pytest 执行链本身。
    return {
        "python_noop": 'python -c "pass"',
        "pytest_version": "python -m pytest --version",
        "pytest_collect_only": _build_collect_only_command(test_command),
        "pytest_full_run": test_command,
    }


def _build_run_record(phase_name: str, run_index: int, command: str, result: dict) -> dict:
    data = result["data"]
    return {
        "phase_name": phase_name,
        "run_index": run_index,
        "command": command,
        "ok": result["ok"],
        "exit_code": data.get("exit_code"),
        "run_tests_duration_sec": float(data.get("duration_sec") or 0.0),
        "resolve_repo_path_duration_sec": float(data.get("resolve_repo_path_duration_sec") or 0.0),
        "env_setup_duration_sec": float(data.get("env_setup_duration_sec") or 0.0),
        "pre_execution_duration_sec": float(data.get("pre_execution_duration_sec") or 0.0),
        "command_execution_duration_sec": float(data.get("command_execution_duration_sec") or 0.0),
        "summary_extraction_duration_sec": float(data.get("summary_extraction_duration_sec") or 0.0),
        "subprocess_duration_sec": float(data.get("subprocess_duration_sec") or 0.0),
    }


def _build_phase_summary(phase_name: str, command: str, records: list[dict]) -> dict:
    first_record = records[0] if records else None
    repeated_records = records[1:] if len(records) > 1 else []
    return {
        "phase_name": phase_name,
        "command": command,
        "run_count": len(records),
        "all_ok": all(record["ok"] for record in records),
        "average_run_tests_duration_sec": _average([record["run_tests_duration_sec"] for record in records]),
        "average_command_execution_duration_sec": _average(
            [record["command_execution_duration_sec"] for record in records]
        ),
        "average_summary_extraction_duration_sec": _average(
            [record["summary_extraction_duration_sec"] for record in records]
        ),
        "first_run_tests_duration_sec": first_record["run_tests_duration_sec"] if first_record else None,
        "first_command_execution_duration_sec": first_record["command_execution_duration_sec"] if first_record else None,
        "repeated_run_tests_average_sec": _average_optional(
            [record["run_tests_duration_sec"] for record in repeated_records]
        ),
        "repeated_command_execution_average_sec": _average_optional(
            [record["command_execution_duration_sec"] for record in repeated_records]
        ),
        "records": records,
    }


def _subtract_optional(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return _round_float(left - right)


def _build_derived_metrics(phase_summaries: dict[str, dict]) -> dict:
    python_phase = phase_summaries["python_noop"]
    version_phase = phase_summaries["pytest_version"]
    collect_phase = phase_summaries["pytest_collect_only"]
    full_phase = phase_summaries["pytest_full_run"]
    return {
        "average_pytest_startup_over_python_sec": _round_float(
            version_phase["average_command_execution_duration_sec"]
            - python_phase["average_command_execution_duration_sec"]
        ),
        "average_collect_over_pytest_startup_sec": _round_float(
            collect_phase["average_command_execution_duration_sec"]
            - version_phase["average_command_execution_duration_sec"]
        ),
        "average_full_over_collect_sec": _round_float(
            full_phase["average_command_execution_duration_sec"]
            - collect_phase["average_command_execution_duration_sec"]
        ),
        "collect_first_minus_repeated_sec": _subtract_optional(
            collect_phase["first_command_execution_duration_sec"],
            collect_phase["repeated_command_execution_average_sec"],
        ),
        "full_first_minus_repeated_sec": _subtract_optional(
            full_phase["first_command_execution_duration_sec"],
            full_phase["repeated_command_execution_average_sec"],
        ),
    }


def build_pytest_phase_benchmark(
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


def build_pytest_phase_markdown(summary: dict) -> str:
    phase_lines = "\n".join(
        (
            f"- `{phase_name}`: command avg=`{phase_summary['average_command_execution_duration_sec']}`, "
            f"first=`{phase_summary['first_command_execution_duration_sec']}`, "
            f"repeated avg=`{phase_summary['repeated_command_execution_average_sec']}`"
        )
        for phase_name, phase_summary in summary["phase_summaries"].items()
    )
    derived = summary["derived_metrics"]
    return f"""# Pytest Phase Benchmark

## Task

- task_id: `{summary["task_id"]}`
- test_command: `{summary["test_command"]}`
- repetitions: `{summary["repetitions"]}`
- policy_id: `{summary["policy_id"]}`
- pytest_additional_flags: `{' '.join(summary["pytest_additional_flags"]) or '(none)'}`

## Phases

{phase_lines}

## Derived Metrics

- average_pytest_startup_over_python_sec: `{derived["average_pytest_startup_over_python_sec"]}`
- average_collect_over_pytest_startup_sec: `{derived["average_collect_over_pytest_startup_sec"]}`
- average_full_over_collect_sec: `{derived["average_full_over_collect_sec"]}`
- collect_first_minus_repeated_sec: `{derived["collect_first_minus_repeated_sec"]}`
- full_first_minus_repeated_sec: `{derived["full_first_minus_repeated_sec"]}`
"""


def benchmark_pytest_phases(
    *,
    task_path: str | Path,
    repo_root: str | Path,
    repetitions: int = 3,
    policy_path: str | Path | None = None,
    output_dir: str | Path = "logs/summaries",
    benchmark_label: str | None = None,
) -> dict:
    summary = build_pytest_phase_benchmark(
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
    write_text(summary_md_path, build_pytest_phase_markdown(summary))

    return {
        "benchmark_id": benchmark_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="对 pytest 启动、collection 与 full run 做分阶段基准。")
    parser.add_argument("--task", required=True, help="任务 JSON 路径")
    parser.add_argument("--repo-root", default=".", help="仓库根目录")
    parser.add_argument("--repetitions", type=int, default=3, help="每个阶段重复次数")
    parser.add_argument("--policy", default=None, help="可选策略 JSON 路径")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--benchmark-label", default=None, help="可选输出标签")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = benchmark_pytest_phases(
        task_path=args.task,
        repo_root=args.repo_root,
        repetitions=args.repetitions,
        policy_path=args.policy,
        output_dir=args.output_dir,
        benchmark_label=args.benchmark_label,
    )
    summary = output["summary"]
    derived = summary["derived_metrics"]
    print("=== Pytest Phase Benchmark Summary ===")
    print(f"benchmark_id: {output['benchmark_id']}")
    print(f"task_id: {summary['task_id']}")
    print(f"repetitions: {summary['repetitions']}")
    print(f"policy_id: {summary['policy_id']}")
    print(f"average_pytest_startup_over_python_sec: {derived['average_pytest_startup_over_python_sec']}")
    print(f"average_collect_over_pytest_startup_sec: {derived['average_collect_over_pytest_startup_sec']}")
    print(f"average_full_over_collect_sec: {derived['average_full_over_collect_sec']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

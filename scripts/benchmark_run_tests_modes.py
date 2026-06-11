"""对比不同仓库运行模式下的 run_tests 开销。"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from app.schemas.task_schema import load_task
from app.tools.run_tests import run_tests


COPY_IGNORE_DIR_NAMES = {
    ".pytest_cache",
    "__pycache__",
}


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _round_float(value: float) -> float:
    return round(value, 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return _round_float(sum(values) / len(values))


def _next_benchmark_id(summary_dir: Path, benchmark_label: str) -> str:
    prefix = f"run_tests_modes_{benchmark_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _copy_repo_to_workspace(source_repo_path: Path, workspace_path: Path) -> float:
    started_at = perf_counter()
    shutil.copytree(
        source_repo_path,
        workspace_path,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(*COPY_IGNORE_DIR_NAMES),
    )
    return _round_float(perf_counter() - started_at)


def _build_run_record(mode: str, run_index: int, result: dict, copy_duration_sec: float = 0.0) -> dict:
    data = result["data"]
    return {
        "mode": mode,
        "run_index": run_index,
        "ok": result["ok"],
        "copy_duration_sec": copy_duration_sec,
        "run_tests_duration_sec": float(data.get("duration_sec") or 0.0),
        "resolve_repo_path_duration_sec": float(data.get("resolve_repo_path_duration_sec") or 0.0),
        "env_setup_duration_sec": float(data.get("env_setup_duration_sec") or 0.0),
        "pre_execution_duration_sec": float(data.get("pre_execution_duration_sec") or 0.0),
        "command_execution_duration_sec": float(data.get("command_execution_duration_sec") or 0.0),
        "summary_extraction_duration_sec": float(data.get("summary_extraction_duration_sec") or 0.0),
        "subprocess_duration_sec": float(data.get("subprocess_duration_sec") or 0.0),
        "combined_duration_sec": _round_float(copy_duration_sec + float(data.get("duration_sec") or 0.0)),
        "exit_code": data.get("exit_code"),
    }


def _build_mode_summary(mode: str, records: list[dict]) -> dict:
    return {
        "mode": mode,
        "run_count": len(records),
        "all_ok": all(record["ok"] for record in records),
        "average_copy_duration_sec": _average([record["copy_duration_sec"] for record in records]),
        "average_run_tests_duration_sec": _average([record["run_tests_duration_sec"] for record in records]),
        "average_resolve_repo_path_duration_sec": _average(
            [record["resolve_repo_path_duration_sec"] for record in records]
        ),
        "average_env_setup_duration_sec": _average([record["env_setup_duration_sec"] for record in records]),
        "average_pre_execution_duration_sec": _average([record["pre_execution_duration_sec"] for record in records]),
        "average_command_execution_duration_sec": _average(
            [record["command_execution_duration_sec"] for record in records]
        ),
        "average_summary_extraction_duration_sec": _average(
            [record["summary_extraction_duration_sec"] for record in records]
        ),
        "average_combined_duration_sec": _average([record["combined_duration_sec"] for record in records]),
        "records": records,
    }


def build_run_tests_mode_benchmark(
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

    records_by_mode: dict[str, list[dict]] = {
        "source_repo": [],
        "persistent_workspace": [],
        "fresh_workspace": [],
    }

    for run_index in range(1, repetitions + 1):
        source_result = run_tests(str(source_repo_path), task.test_command, timeout_sec=30)
        records_by_mode["source_repo"].append(_build_run_record("source_repo", run_index, source_result))

    with TemporaryDirectory(prefix=f"{task.task_id}_persistent_") as persistent_dir:
        persistent_workspace = Path(persistent_dir) / "workspace"
        persistent_copy_duration_sec = _copy_repo_to_workspace(source_repo_path, persistent_workspace)
        for run_index in range(1, repetitions + 1):
            persistent_result = run_tests(str(persistent_workspace), task.test_command, timeout_sec=30)
            records_by_mode["persistent_workspace"].append(
                _build_run_record(
                    "persistent_workspace",
                    run_index,
                    persistent_result,
                    copy_duration_sec=persistent_copy_duration_sec if run_index == 1 else 0.0,
                )
            )

    with TemporaryDirectory(prefix=f"{task.task_id}_fresh_") as fresh_root:
        fresh_root_path = Path(fresh_root)
        for run_index in range(1, repetitions + 1):
            fresh_workspace = fresh_root_path / f"workspace_{run_index:03d}"
            copy_duration_sec = _copy_repo_to_workspace(source_repo_path, fresh_workspace)
            fresh_result = run_tests(str(fresh_workspace), task.test_command, timeout_sec=30)
            records_by_mode["fresh_workspace"].append(
                _build_run_record(
                    "fresh_workspace",
                    run_index,
                    fresh_result,
                    copy_duration_sec=copy_duration_sec,
                )
            )

    mode_summaries = {
        mode: _build_mode_summary(mode, mode_records)
        for mode, mode_records in records_by_mode.items()
    }

    return {
        "created_at": _utc_timestamp(),
        "task_id": task.task_id,
        "task_path": str(Path(task_path).resolve()),
        "source_repo_path": str(source_repo_path),
        "test_command": task.test_command,
        "repetitions": repetitions,
        "mode_summaries": mode_summaries,
    }


def build_run_tests_mode_markdown(summary: dict) -> str:
    mode_lines = "\n".join(
        (
            f"- `{mode}`: run_tests avg=`{mode_summary['average_run_tests_duration_sec']}`, "
            f"copy avg=`{mode_summary['average_copy_duration_sec']}`, "
            f"command avg=`{mode_summary['average_command_execution_duration_sec']}`, "
            f"combined avg=`{mode_summary['average_combined_duration_sec']}`"
        )
        for mode, mode_summary in summary["mode_summaries"].items()
    )

    return f"""# Run Tests Mode Benchmark

## Task

- task_id: `{summary["task_id"]}`
- test_command: `{summary["test_command"]}`
- repetitions: `{summary["repetitions"]}`

## Modes

{mode_lines}
"""


def benchmark_run_tests_modes(
    *,
    task_path: str | Path,
    repo_root: str | Path,
    repetitions: int = 3,
    output_dir: str | Path = "logs/summaries",
    benchmark_label: str | None = None,
) -> dict:
    summary = build_run_tests_mode_benchmark(
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
    write_text(summary_md_path, build_run_tests_mode_markdown(summary))

    return {
        "benchmark_id": benchmark_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="对比不同仓库运行模式下的 run_tests 开销。")
    parser.add_argument("--task", required=True, help="任务 JSON 路径")
    parser.add_argument("--repo-root", default=".", help="仓库根目录")
    parser.add_argument("--repetitions", type=int, default=3, help="每种模式重复次数")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--benchmark-label", default=None, help="可选输出标签")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = benchmark_run_tests_modes(
        task_path=args.task,
        repo_root=args.repo_root,
        repetitions=args.repetitions,
        output_dir=args.output_dir,
        benchmark_label=args.benchmark_label,
    )
    summary = output["summary"]
    print("=== Run Tests Mode Benchmark Summary ===")
    print(f"benchmark_id: {output['benchmark_id']}")
    print(f"task_id: {summary['task_id']}")
    print(f"repetitions: {summary['repetitions']}")
    for mode, mode_summary in summary["mode_summaries"].items():
        print(
            f"{mode}: run_tests_avg={mode_summary['average_run_tests_duration_sec']}, "
            f"copy_avg={mode_summary['average_copy_duration_sec']}, "
            f"combined_avg={mode_summary['average_combined_duration_sec']}"
        )
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

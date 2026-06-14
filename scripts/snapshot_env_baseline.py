"""采集当前环境的轻量基线快照，用于辅助判断时延漂移。"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text


DEFAULT_COMMAND_SPECS = [
    {
        "command_id": "python_noop",
        "description": "测量 Python 解释器空载启动开销。",
        "argv": [sys.executable, "-c", "pass"],
    },
    {
        "command_id": "pytest_version",
        "description": "测量 pytest 入口启动开销。",
        "argv": [sys.executable, "-m", "pytest", "--version"],
    },
]


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _snapshot_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def _round_float(value: float, digits: int = 4) -> float:
    return round(value, digits)


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarize_samples(
    *,
    command_id: str,
    description: str,
    argv: list[str],
    samples_sec: list[float],
    stdout_preview: str = "",
    stderr_preview: str = "",
    return_code: int = 0,
) -> dict:
    if not samples_sec:
        raise ValueError("samples_sec 不能为空。")

    mean_sec = sum(samples_sec) / len(samples_sec)
    min_sec = min(samples_sec)
    max_sec = max(samples_sec)
    std_sec = statistics.stdev(samples_sec) if len(samples_sec) >= 2 else 0.0

    return {
        "command_id": command_id,
        "description": description,
        "argv": argv,
        "sample_count": len(samples_sec),
        "samples_sec": [_round_float(value, 6) for value in samples_sec],
        "mean_sec": _round_float(mean_sec),
        "min_sec": _round_float(min_sec),
        "max_sec": _round_float(max_sec),
        "std_sec": _round_float(std_sec),
        "return_code": return_code,
        "stdout_preview": stdout_preview.strip(),
        "stderr_preview": stderr_preview.strip(),
    }


def run_command_benchmark(
    *,
    command_spec: dict,
    repetitions: int,
    cwd: Path,
) -> dict:
    samples_sec: list[float] = []
    latest_stdout = ""
    latest_stderr = ""
    latest_return_code = 0

    for _ in range(repetitions):
        started_at = time.perf_counter()
        completed = subprocess.run(
            command_spec["argv"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        duration_sec = time.perf_counter() - started_at
        samples_sec.append(duration_sec)
        latest_stdout = completed.stdout
        latest_stderr = completed.stderr
        latest_return_code = completed.returncode
        if completed.returncode != 0:
            raise RuntimeError(
                f"环境基线命令执行失败：{command_spec['command_id']} "
                f"(exit_code={completed.returncode})\n{completed.stderr.strip()}"
            )

    return summarize_samples(
        command_id=command_spec["command_id"],
        description=command_spec["description"],
        argv=list(command_spec["argv"]),
        samples_sec=samples_sec,
        stdout_preview=latest_stdout,
        stderr_preview=latest_stderr,
        return_code=latest_return_code,
    )


def build_aggregate(commands: list[dict]) -> dict:
    mean_values = [float(item["mean_sec"]) for item in commands]
    std_values = [float(item["std_sec"]) for item in commands]
    return {
        "command_count": len(commands),
        "mean_of_means_sec": _round_float(sum(mean_values) / len(mean_values)) if mean_values else 0.0,
        "max_mean_sec": _round_float(max(mean_values)) if mean_values else 0.0,
        "mean_of_stds_sec": _round_float(sum(std_values) / len(std_values)) if std_values else 0.0,
    }


def compare_snapshots(
    *,
    reference_snapshot: dict,
    current_snapshot: dict,
    reference_snapshot_path: str | Path,
) -> dict:
    reference_commands = {
        str(command["command_id"]): command
        for command in reference_snapshot.get("commands", [])
    }
    current_commands = {
        str(command["command_id"]): command
        for command in current_snapshot.get("commands", [])
    }

    per_command: list[dict] = []
    comparable_ids = sorted(set(reference_commands) & set(current_commands))
    for command_id in comparable_ids:
        reference_mean = float(reference_commands[command_id]["mean_sec"])
        current_mean = float(current_commands[command_id]["mean_sec"])
        delta_sec = current_mean - reference_mean
        ratio = (current_mean / reference_mean) if reference_mean else None
        per_command.append(
            {
                "command_id": command_id,
                "reference_mean_sec": _round_float(reference_mean),
                "current_mean_sec": _round_float(current_mean),
                "delta_sec": _round_float(delta_sec),
                "ratio": _round_float(ratio) if ratio is not None else None,
            }
        )

    deltas = [float(item["delta_sec"]) for item in per_command]
    ratios = [float(item["ratio"]) for item in per_command if item["ratio"] is not None]
    return {
        "reference_snapshot_path": str(Path(reference_snapshot_path).resolve()),
        "reference_snapshot_id": reference_snapshot.get("snapshot_id"),
        "comparable_command_count": len(per_command),
        "mean_delta_sec": _round_float(sum(deltas) / len(deltas)) if deltas else 0.0,
        "max_delta_sec": _round_float(max(deltas)) if deltas else 0.0,
        "mean_ratio": _round_float(sum(ratios) / len(ratios)) if ratios else None,
        "per_command": per_command,
    }


def build_snapshot_summary(
    *,
    repetitions: int,
    commands: list[dict],
    compare_against_path: str | Path | None = None,
) -> dict:
    summary = {
        "snapshot_id": f"env_baseline_{_snapshot_timestamp()}",
        "created_at": _utc_timestamp(),
        "repetitions": repetitions,
        "repo_root": str(REPO_ROOT),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "commands": commands,
        "aggregate": build_aggregate(commands),
        "comparison": None,
    }

    if compare_against_path is not None:
        reference_snapshot = _load_json(compare_against_path)
        summary["comparison"] = compare_snapshots(
            reference_snapshot=reference_snapshot,
            current_snapshot=summary,
            reference_snapshot_path=compare_against_path,
        )

    return summary


def build_markdown(summary: dict) -> str:
    command_lines = "\n".join(
        (
            f"### `{command['command_id']}`\n"
            f"- 描述：{command['description']}\n"
            f"- 均值：`{command['mean_sec']}`\n"
            f"- 最小值：`{command['min_sec']}`\n"
            f"- 最大值：`{command['max_sec']}`\n"
            f"- 标准差：`{command['std_sec']}`\n"
            f"- 命令：`{' '.join(command['argv'])}`"
        )
        for command in summary["commands"]
    )

    comparison = summary.get("comparison")
    if comparison:
        comparison_lines = "\n".join(
            (
                f"- `{item['command_id']}`: `{item['reference_mean_sec']}` -> "
                f"`{item['current_mean_sec']}` (delta: `{item['delta_sec']}`, ratio: `{item['ratio']}`)"
            )
            for item in comparison["per_command"]
        ) or "- 当前没有可比较命令"
        comparison_block = f"""
## Comparison

- reference_snapshot_id: `{comparison["reference_snapshot_id"]}`
- reference_snapshot_path: `{comparison["reference_snapshot_path"]}`
- comparable_command_count: `{comparison["comparable_command_count"]}`
- mean_delta_sec: `{comparison["mean_delta_sec"]}`
- max_delta_sec: `{comparison["max_delta_sec"]}`
- mean_ratio: `{comparison["mean_ratio"]}`

### Per Command

{comparison_lines}
"""
    else:
        comparison_block = """
## Comparison

- 当前未提供 `--compare-against`，所以这份快照只包含原始环境基线，不包含漂移对比。
"""

    return f"""# Environment Baseline Snapshot

## Snapshot

- snapshot_id: `{summary["snapshot_id"]}`
- created_at: `{summary["created_at"]}`
- repetitions: `{summary["repetitions"]}`
- python_executable: `{summary["python_executable"]}`
- python_version: `{summary["python_version"]}`
- platform: `{summary["platform"]}`

## Aggregate

- command_count: `{summary["aggregate"]["command_count"]}`
- mean_of_means_sec: `{summary["aggregate"]["mean_of_means_sec"]}`
- max_mean_sec: `{summary["aggregate"]["max_mean_sec"]}`
- mean_of_stds_sec: `{summary["aggregate"]["mean_of_stds_sec"]}`

## Commands

{command_lines}
{comparison_block}
"""


def snapshot_env_baseline(
    *,
    output_dir: str | Path = "logs/env_baselines",
    repetitions: int = 10,
    compare_against: str | Path | None = None,
    command_specs: list[dict] | None = None,
    cwd: str | Path = REPO_ROOT,
) -> dict:
    command_specs = command_specs or DEFAULT_COMMAND_SPECS
    working_directory = Path(cwd).resolve()
    commands = [
        run_command_benchmark(
            command_spec=command_spec,
            repetitions=repetitions,
            cwd=working_directory,
        )
        for command_spec in command_specs
    ]
    summary = build_snapshot_summary(
        repetitions=repetitions,
        commands=commands,
        compare_against_path=compare_against,
    )

    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    summary_json_path = output_directory / f"{summary['snapshot_id']}.json"
    summary_md_path = output_directory / f"{summary['snapshot_id']}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_markdown(summary))

    return {
        "snapshot_id": summary["snapshot_id"],
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="采集当前环境的轻量基线快照。")
    parser.add_argument("--output-dir", default="logs/env_baselines", help="快照输出目录")
    parser.add_argument("--repetitions", type=int, default=10, help="每条命令的重复采样次数")
    parser.add_argument(
        "--compare-against",
        default=None,
        help="可选：与历史环境快照对比，自动输出环境漂移摘要",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = snapshot_env_baseline(
        output_dir=args.output_dir,
        repetitions=args.repetitions,
        compare_against=args.compare_against,
    )
    summary = output["summary"]
    print("=== Environment Baseline Snapshot ===")
    print(f"snapshot_id: {output['snapshot_id']}")
    print(f"mean_of_means_sec: {summary['aggregate']['mean_of_means_sec']}")
    if summary.get("comparison"):
        print(f"comparison_mean_delta_sec: {summary['comparison']['mean_delta_sec']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

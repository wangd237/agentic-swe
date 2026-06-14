"""对同一策略在同一任务集上的复跑稳定性进行复核。"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.batch_runner import load_task_paths, run_batch
from app.runtime.logger import write_json, write_text
from evals.batch_eval import run_batch_eval


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_stability_recheck_id(summary_dir: Path, run_label: str | None = None) -> str:
    existing_numbers: list[int] = []
    prefix = f"stability_recheck_{run_label}_" if run_label else "stability_recheck_"
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    if run_label:
        return f"{prefix}{next_number:03d}"
    return f"stability_recheck_{next_number:03d}"


def _round_float(value: float) -> float:
    return round(value, 4)


def _classify_stability(*, mean_duration: float, std_duration: float) -> str:
    # 用变异系数衡量稳定性，避免不同任务集规模下绝对时延阈值难以复用。
    if mean_duration <= 0:
        return "stable"
    ratio = std_duration / mean_duration
    if ratio <= 0.05:
        return "stable"
    if ratio <= 0.10:
        return "borderline"
    return "unstable"


def _detect_outliers(duration_values: list[float], *, mean_duration: float, std_duration: float) -> list[dict]:
    # 使用 2σ 规则做最小异常采样识别；当样本过少或方差为 0 时不标异常。
    if len(duration_values) < 2 or std_duration <= 0:
        return []

    outliers: list[dict] = []
    threshold = 2 * std_duration
    for index, duration in enumerate(duration_values, start=1):
        deviation = duration - mean_duration
        if abs(deviation) > threshold:
            outliers.append(
                {
                    "run_index": index,
                    "average_duration_sec": _round_float(duration),
                    "deviation_sec": _round_float(deviation),
                    "threshold_sec": _round_float(threshold),
                }
            )
    return outliers


def _build_baseline_comparison(
    *,
    baseline_eval_path: Path | None,
    mean_duration: float,
    mean_success_rate: float,
    mean_test_pass_rate: float,
) -> dict | None:
    if baseline_eval_path is None:
        return None

    payload = _load_json(baseline_eval_path)
    metrics = payload.get("metrics", {})
    baseline_duration = float(metrics.get("average_duration_sec", 0.0))
    baseline_success_rate = float(metrics.get("success_rate", 0.0))
    baseline_test_pass_rate = float(metrics.get("test_pass_rate", 0.0))

    return {
        "baseline_eval_path": str(baseline_eval_path),
        "baseline_policy_id": payload.get("policy_id"),
        "baseline_source_batch_run_id": payload.get("source_batch_run_id"),
        "baseline_average_duration_sec": _round_float(baseline_duration),
        "baseline_success_rate": _round_float(baseline_success_rate),
        "baseline_test_pass_rate": _round_float(baseline_test_pass_rate),
        "mean_duration_delta_sec": _round_float(mean_duration - baseline_duration),
        "mean_success_rate_delta": _round_float(mean_success_rate - baseline_success_rate),
        "mean_test_pass_rate_delta": _round_float(mean_test_pass_rate - baseline_test_pass_rate),
    }


def _build_stability_band_check(
    *,
    baseline_eval_path: Path | None,
    mean_duration: float,
    std_duration: float,
) -> dict | None:
    # 判断给定参考 eval 是否落在本次复跑得到的稳定区间内。
    if baseline_eval_path is None:
        return None

    payload = _load_json(baseline_eval_path)
    metrics = payload.get("metrics", {})
    baseline_duration = float(metrics.get("average_duration_sec", 0.0))
    lower_bound = mean_duration - 2 * std_duration
    upper_bound = mean_duration + 2 * std_duration
    within_band = lower_bound <= baseline_duration <= upper_bound if std_duration > 0 else baseline_duration == mean_duration

    return {
        "baseline_eval_path": str(baseline_eval_path),
        "baseline_average_duration_sec": _round_float(baseline_duration),
        "lower_bound_sec": _round_float(lower_bound),
        "upper_bound_sec": _round_float(upper_bound),
        "within_band": within_band,
    }


def _build_markdown(summary: dict) -> str:
    run_lines = "\n".join(
        [
            (
                f"- run `{run['run_index']}`: batch `{run['batch_run_id']}`, eval `{run['eval_id']}`, "
                f"success_rate `{run['success_rate']}`, test_pass_rate `{run['test_pass_rate']}`, "
                f"average_duration_sec `{run['average_duration_sec']}`, average_steps `{run['average_steps']}`"
            )
            for run in summary["runs"]
        ]
    ) or "- 当前没有复跑记录"

    outlier_lines = "\n".join(
        [
            (
                f"- run `{item['run_index']}`: average_duration_sec `{item['average_duration_sec']}`, "
                f"deviation `{item['deviation_sec']}`, threshold `{item['threshold_sec']}`"
            )
            for item in summary["outliers"]
        ]
    ) or "- 当前没有检测到 outlier"

    baseline_block = ""
    baseline_comparison = summary.get("baseline_comparison")
    if baseline_comparison is not None:
        baseline_block = f"""
## Baseline Compare

- baseline_policy_id: `{baseline_comparison["baseline_policy_id"]}`
- baseline_average_duration_sec: `{baseline_comparison["baseline_average_duration_sec"]}`
- mean_duration_delta_sec: `{baseline_comparison["mean_duration_delta_sec"]}`
- mean_success_rate_delta: `{baseline_comparison["mean_success_rate_delta"]}`
- mean_test_pass_rate_delta: `{baseline_comparison["mean_test_pass_rate_delta"]}`
"""

    return f"""# Stability Recheck

## Run

- recheck_id: `{summary["recheck_id"]}`
- created_at: `{summary["created_at"]}`
- policy_id: `{summary["policy_id"]}`
- manifest_path: `{summary["manifest_path"]}`
- repetitions: `{summary["repetitions"]}`

## Per Run Metrics

{run_lines}

## Aggregate

- average_duration_mean_sec: `{summary["aggregate"]["average_duration_mean_sec"]}`
- average_duration_std_sec: `{summary["aggregate"]["average_duration_std_sec"]}`
- average_duration_min_sec: `{summary["aggregate"]["average_duration_min_sec"]}`
- average_duration_max_sec: `{summary["aggregate"]["average_duration_max_sec"]}`
- average_steps_mean: `{summary["aggregate"]["average_steps_mean"]}`
- success_rate_mean: `{summary["aggregate"]["success_rate_mean"]}`
- test_pass_rate_mean: `{summary["aggregate"]["test_pass_rate_mean"]}`
- functional_consistent: `{summary["functional_consistency"]["functional_consistent"]}`
- conclusion: `{summary["conclusion"]}`

## Outliers

{outlier_lines}
{baseline_block}
"""


def run_stability_recheck(
    *,
    repo_root: Path,
    manifest_path: Path,
    tasks_dir: Path,
    policy_path: Path,
    repetitions: int,
    output_dir: Path,
    run_label: str | None = None,
    baseline_eval_path: Path | None = None,
) -> dict:
    if repetitions <= 0:
        raise ValueError("repetitions 必须大于 0。")

    task_paths = load_task_paths(tasks_dir=tasks_dir, manifest_path=manifest_path)
    run_records: list[dict] = []
    duration_values: list[float] = []
    step_values: list[float] = []
    success_rate_values: list[float] = []
    test_pass_rate_values: list[float] = []

    for index in range(1, repetitions + 1):
        per_run_label = f"{run_label}r{index}" if run_label else None
        batch_output = run_batch(
            repo_root=repo_root,
            task_paths=task_paths,
            policy_path=policy_path,
            run_label=per_run_label,
        )
        eval_output = run_batch_eval(
            batch_summary_path=batch_output["summary_json_path"],
            output_dir=output_dir,
            run_label=per_run_label,
        )
        eval_summary = eval_output["eval_summary"]
        metrics = eval_summary["metrics"]

        duration = float(metrics["average_duration_sec"])
        average_steps = float(metrics["average_steps"])
        success_rate = float(metrics["success_rate"])
        test_pass_rate = float(metrics["test_pass_rate"])

        duration_values.append(duration)
        step_values.append(average_steps)
        success_rate_values.append(success_rate)
        test_pass_rate_values.append(test_pass_rate)

        run_records.append(
            {
                "run_index": index,
                "batch_run_id": Path(batch_output["summary_json_path"]).stem,
                "eval_id": eval_output["eval_id"],
                "batch_summary_json_path": batch_output["summary_json_path"],
                "eval_summary_json_path": eval_output["summary_json_path"],
                "success_rate": _round_float(success_rate),
                "test_pass_rate": _round_float(test_pass_rate),
                "average_duration_sec": _round_float(duration),
                "average_steps": _round_float(average_steps),
                "average_tool_calls": _round_float(float(metrics["average_tool_calls"])),
            }
        )

    mean_duration = statistics.fmean(duration_values)
    std_duration = statistics.stdev(duration_values) if len(duration_values) >= 2 else 0.0
    mean_steps = statistics.fmean(step_values)
    mean_success_rate = statistics.fmean(success_rate_values)
    mean_test_pass_rate = statistics.fmean(test_pass_rate_values)
    outliers = _detect_outliers(
        duration_values,
        mean_duration=mean_duration,
        std_duration=std_duration,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    recheck_id = _next_stability_recheck_id(output_dir, run_label=run_label)
    conclusion = _classify_stability(mean_duration=mean_duration, std_duration=std_duration)
    functional_consistent = (
        len({*success_rate_values}) == 1 and len({*test_pass_rate_values}) == 1
    )

    summary = {
        "recheck_id": recheck_id,
        "created_at": _utc_timestamp(),
        "policy_id": _load_json(run_records[-1]["eval_summary_json_path"]).get("policy_id"),
        "policy_path": str(policy_path),
        "manifest_path": str(manifest_path),
        "tasks_dir": str(tasks_dir),
        "repetitions": repetitions,
        "runs": run_records,
        "aggregate": {
            "average_duration_mean_sec": _round_float(mean_duration),
            "average_duration_std_sec": _round_float(std_duration),
            "average_duration_min_sec": _round_float(min(duration_values)),
            "average_duration_max_sec": _round_float(max(duration_values)),
            "average_steps_mean": _round_float(mean_steps),
            "success_rate_mean": _round_float(mean_success_rate),
            "test_pass_rate_mean": _round_float(mean_test_pass_rate),
        },
        "outliers": outliers,
        "outlier_count": len(outliers),
        "functional_consistency": {
            "functional_consistent": functional_consistent,
            "success_rate_values": [_round_float(value) for value in success_rate_values],
            "test_pass_rate_values": [_round_float(value) for value in test_pass_rate_values],
        },
        "conclusion": conclusion,
        "baseline_comparison": _build_baseline_comparison(
            baseline_eval_path=baseline_eval_path,
            mean_duration=mean_duration,
            mean_success_rate=mean_success_rate,
            mean_test_pass_rate=mean_test_pass_rate,
        ),
        "baseline_stability_band_check": _build_stability_band_check(
            baseline_eval_path=baseline_eval_path,
            mean_duration=mean_duration,
            std_duration=std_duration,
        ),
    }

    summary_json_path = output_dir / f"{recheck_id}.json"
    summary_md_path = output_dir / f"{recheck_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, _build_markdown(summary))

    return {
        "recheck_id": recheck_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="对同一策略做多次复跑，分析稳定性。")
    parser.add_argument("--policy", required=True, help="策略文件路径")
    parser.add_argument("--manifest", required=True, help="目标 manifest 路径")
    parser.add_argument("--tasks-dir", default="benchmarks/tasks", help="任务目录路径")
    parser.add_argument("--repetitions", type=int, default=3, help="复跑次数，默认 3")
    parser.add_argument("--baseline-eval", default=None, help="可选：用于对比的 baseline eval JSON")
    parser.add_argument("--run-label", default=None, help="本次稳定性复核的标签")
    parser.add_argument("--output-dir", default="logs/summaries", help="结果输出目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = run_stability_recheck(
        repo_root=REPO_ROOT,
        manifest_path=(REPO_ROOT / args.manifest).resolve(),
        tasks_dir=(REPO_ROOT / args.tasks_dir).resolve(),
        policy_path=(REPO_ROOT / args.policy).resolve(),
        repetitions=args.repetitions,
        output_dir=(REPO_ROOT / args.output_dir).resolve(),
        run_label=args.run_label,
        baseline_eval_path=(
            (REPO_ROOT / args.baseline_eval).resolve() if args.baseline_eval else None
        ),
    )
    summary = output["summary"]
    print("=== Stability Recheck Summary ===")
    print(f"recheck_id: {output['recheck_id']}")
    print(f"policy_id: {summary['policy_id']}")
    print(f"repetitions: {summary['repetitions']}")
    print(f"average_duration_mean_sec: {summary['aggregate']['average_duration_mean_sec']}")
    print(f"average_duration_std_sec: {summary['aggregate']['average_duration_std_sec']}")
    print(f"outlier_count: {summary['outlier_count']}")
    print(f"functional_consistent: {summary['functional_consistency']['functional_consistent']}")
    print(f"conclusion: {summary['conclusion']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

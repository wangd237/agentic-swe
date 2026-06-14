"""运行 challenge 任务集的轻量评测流水线。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.batch_runner import load_task_paths, run_batch
from evals.batch_eval import run_batch_eval
from scripts.analyze_benchmark_maturity import analyze_benchmark_maturity
from scripts.run_real_issue_eval import build_maturity_headline


def summarize_challenge_manifest(task_paths: list[Path]) -> dict[str, int]:
    return {"task_count": len(task_paths)}


def run_challenge_eval_pipeline(
    *,
    repo_root: Path,
    manifest_path: Path,
    tasks_dir: Path,
    policy_path: Path,
    run_label: str,
) -> dict:
    summaries_dir = repo_root / "logs" / "summaries"
    task_paths = load_task_paths(tasks_dir=tasks_dir, manifest_path=manifest_path)
    batch_output = run_batch(
        repo_root=repo_root,
        task_paths=task_paths,
        policy_path=policy_path,
        run_label=run_label,
    )
    batch_summary_path = Path(batch_output["summary_json_path"])
    eval_output = run_batch_eval(
        batch_summary_path=batch_summary_path,
        output_dir=summaries_dir,
        run_label=run_label,
    )
    maturity_output = analyze_benchmark_maturity(
        repo_root=repo_root,
        output_dir=summaries_dir,
        run_label="maturity",
    )
    return {
        "challenge_summary": summarize_challenge_manifest(task_paths),
        "batch_output": batch_output,
        "eval_output": eval_output,
        "maturity_output": maturity_output,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 challenge 任务集的 batch/eval 流水线。")
    parser.add_argument(
        "--manifest",
        default="benchmarks/manifests/real_issue_tasks_challenge_v1.json",
        help="challenge 任务清单路径",
    )
    parser.add_argument(
        "--tasks-dir",
        default="benchmarks/tasks",
        help="任务目录路径",
    )
    parser.add_argument(
        "--policy",
        required=True,
        help="本次运行使用的策略文件路径",
    )
    parser.add_argument(
        "--run-label",
        required=True,
        help="本次 challenge 流水线使用的 run label，例如 challengev69",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pipeline_output = run_challenge_eval_pipeline(
        repo_root=REPO_ROOT,
        manifest_path=(REPO_ROOT / args.manifest).resolve(),
        tasks_dir=(REPO_ROOT / args.tasks_dir).resolve(),
        policy_path=(REPO_ROOT / args.policy).resolve(),
        run_label=args.run_label,
    )

    print("=== Challenge Eval Pipeline Summary ===")
    print(f"manifest_task_count: {pipeline_output['challenge_summary']['task_count']}")
    print(f"batch_summary_json_path: {pipeline_output['batch_output']['summary_json_path']}")
    print(f"eval_summary_json_path: {pipeline_output['eval_output']['summary_json_path']}")
    print(build_maturity_headline(pipeline_output["maturity_output"]))
    print(f"maturity_summary_json_path: {pipeline_output['maturity_output']['summary_json_path']}")
    print("phase_status: Phase 6 challenge eval pipeline complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

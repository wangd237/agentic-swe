"""运行真实 issue 任务集的批量评测流水线。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.batch_runner import load_task_paths, run_batch
from evals.batch_eval import run_batch_eval
from evals.compare_evals import compare_eval_summaries


def load_candidate_dataset(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_candidate_by_issue(dataset: dict, repo_full_name: str, issue_number: int) -> dict | None:
    for candidate in dataset.get("candidates", []):
        if (
            candidate.get("repo_full_name") == repo_full_name
            and candidate.get("issue_number") == issue_number
        ):
            return candidate
    return None


def summarize_candidate_statuses(dataset: dict) -> dict[str, int]:
    summary: dict[str, int] = {}
    for candidate in dataset.get("candidates", []):
        status = candidate.get("status", "unknown")
        summary[status] = summary.get(status, 0) + 1
    return dict(sorted(summary.items()))


def summarize_manifest_tasks(task_paths: list[Path]) -> dict[str, int]:
    total = len(task_paths)
    semi_real_count = 0
    real_issue_count = 0
    synthetic_count = 0

    for task_path in task_paths:
        payload = json.loads(task_path.read_text(encoding="utf-8"))
        source_type = payload.get("source_type")
        if source_type == "semi_real":
            semi_real_count += 1
        elif source_type == "real_issue":
            real_issue_count += 1
        elif source_type == "synthetic":
            synthetic_count += 1

    return {
        "task_count": total,
        "semi_real_count": semi_real_count,
        "real_issue_count": real_issue_count,
        "synthetic_count": synthetic_count,
    }


def run_real_issue_eval_pipeline(
    *,
    repo_root: Path,
    manifest_path: Path,
    tasks_dir: Path,
    candidate_file: Path,
    policy_path: Path,
    run_label: str,
    compare_against_eval: Path | None = None,
    compare_label: str | None = None,
) -> dict:
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
        output_dir=repo_root / "logs" / "summaries",
        run_label=run_label,
    )

    compare_output = None
    if compare_against_eval is not None:
        compare_output = compare_eval_summaries(
            baseline_eval_path=compare_against_eval,
            improved_eval_path=eval_output["summary_json_path"],
            output_dir=repo_root / "logs" / "summaries",
            run_label=compare_label or run_label,
        )

    candidate_dataset = load_candidate_dataset(candidate_file)
    return {
        "task_summary": summarize_manifest_tasks(task_paths),
        "candidate_status_summary": summarize_candidate_statuses(candidate_dataset),
        "batch_output": batch_output,
        "eval_output": eval_output,
        "compare_output": compare_output,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行真实 issue 任务集的 batch/eval/compare 流水线。")
    parser.add_argument(
        "--manifest",
        default="benchmarks/manifests/real_issue_tasks.json",
        help="真实 issue 任务清单路径",
    )
    parser.add_argument(
        "--tasks-dir",
        default="benchmarks/tasks",
        help="任务目录路径",
    )
    parser.add_argument(
        "--candidate-file",
        default="benchmarks/real_world_candidates.json",
        help="真实 issue 候选清单路径",
    )
    parser.add_argument(
        "--policy",
        required=True,
        help="本次运行使用的策略文件路径",
    )
    parser.add_argument(
        "--run-label",
        required=True,
        help="本次真实 issue 流水线使用的 run label，例如 realissuev8",
    )
    parser.add_argument(
        "--compare-against-eval",
        default=None,
        help="可选：用于 compare 的 baseline eval JSON 路径",
    )
    parser.add_argument(
        "--compare-label",
        default=None,
        help="可选：compare 报告标签，默认复用 run-label",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pipeline_output = run_real_issue_eval_pipeline(
        repo_root=REPO_ROOT,
        manifest_path=(REPO_ROOT / args.manifest).resolve(),
        tasks_dir=(REPO_ROOT / args.tasks_dir).resolve(),
        candidate_file=(REPO_ROOT / args.candidate_file).resolve(),
        policy_path=(REPO_ROOT / args.policy).resolve(),
        run_label=args.run_label,
        compare_against_eval=(
            (REPO_ROOT / args.compare_against_eval).resolve()
            if args.compare_against_eval
            else None
        ),
        compare_label=args.compare_label,
    )

    print("=== Real Issue Eval Pipeline Summary ===")
    print(f"manifest_task_count: {pipeline_output['task_summary']['task_count']}")
    print(f"semi_real_count: {pipeline_output['task_summary']['semi_real_count']}")
    print(f"candidate_status_summary: {pipeline_output['candidate_status_summary']}")
    print(f"batch_summary_json_path: {pipeline_output['batch_output']['summary_json_path']}")
    print(f"eval_summary_json_path: {pipeline_output['eval_output']['summary_json_path']}")
    if pipeline_output["compare_output"] is not None:
        print(f"compare_summary_json_path: {pipeline_output['compare_output']['summary_json_path']}")
        print(f"compare_id: {pipeline_output['compare_output']['compare_id']}")
    else:
        print("compare_summary_json_path: None")
    print("phase_status: Phase 6 real issue eval pipeline complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

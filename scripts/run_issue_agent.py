"""运行单条 issue agent 任务。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent.executor import run_agent
from app.agent.summary import build_verification_summary_fields


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行单条 issue agent 任务。")
    parser.add_argument(
        "--task",
        required=True,
        help="任务 JSON 文件路径，例如 benchmarks/tasks/task_010.json",
    )
    parser.add_argument(
        "--policy",
        required=True,
        help="策略配置文件路径，例如 optimization/policy_versions/llm_deepseek_minimal.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_output = run_agent(
        task_path=args.task,
        repo_root=REPO_ROOT,
        policy_path=REPO_ROOT / args.policy,
    )
    task = run_output["task"]
    result = run_output["result"]
    run_paths = run_output["run_paths"]
    verification_summary = build_verification_summary_fields(result)

    print("=== Issue Agent Run Summary ===")
    print(f"task_id: {task['task_id']}")
    print(f"run_id: {result['run_id']}")
    print(f"final_status: {verification_summary['final_status']}")
    print(f"accepted_final_status: {verification_summary['accepted_final_status']}")
    print(f"verification_strength: {verification_summary['verification_strength']}")
    print(f"verification_level: {verification_summary['verification_level']}")
    print(f"evidence_quality: {verification_summary['evidence_quality']}")
    print(f"missing_evidence: {verification_summary['missing_evidence']}")
    print(f"verifier_accepted: {verification_summary['verifier_accepted']}")
    print(f"risk_level: {verification_summary['risk_level']}")
    print(f"evidence_scope: {verification_summary['evidence_scope']}")
    print(f"evidence_official_harness_required: {verification_summary['evidence_official_harness_required']}")
    print(f"policy_id: {result['tool_stats']['policy_id']}")
    print(f"agent_type: {result['tool_stats'].get('agent_type', 'unknown')}")
    print(f"llm_provider: {result['tool_stats'].get('llm_provider') or '(none)'}")
    print(f"llm_model: {result['tool_stats'].get('llm_model') or '(none)'}")
    print(f"total_tool_calls: {result['tool_stats']['total_tool_calls']}")
    print(f"trace_path: {run_paths['trace_json_path']}")
    print(f"result_path: {run_paths['result_json_path']}")
    print(f"summary_path: {run_paths['summary_md_path']}")
    return 0 if result["final_status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())

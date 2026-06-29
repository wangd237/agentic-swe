"""Run a deterministic code intelligence A/B smoke with fake LLM responses."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent.llm_agent import LLMCodeAgent
from app.agent.llm_config import LLMConfig
from app.runtime.batch_runner import load_task_paths
from app.runtime.logger import write_json, write_text
from app.schemas.task_schema import load_task
from scripts.run_code_intelligence_ab import build_graph_policy, collect_target_files_by_task
from scripts.summarize_code_intelligence_runs import summarize_code_intelligence_runs


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_smoke_id(output_dir: Path, cohort_label: str) -> str:
    prefix = f"code_intelligence_ab_smoke_{cohort_label}_"
    existing_numbers: list[int] = []
    for path in output_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


class RunTestsThenStopClient:
    """Fake LLM client that reproduces with run_tests, then stops."""

    def __init__(self, command: str, *, first_tokens: int = 111, second_tokens: int = 222) -> None:
        self.command = command
        self.first_tokens = first_tokens
        self.second_tokens = second_tokens
        self._call_count = 0

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        self._call_count += 1
        if self._call_count == 1:
            return {
                "usage": {"total_tokens": self.first_tokens},
                "content": [
                    {"type": "text", "text": "Run the task tests first."},
                    {
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "run_tests",
                        "input": {
                            "command": self.command,
                            "timeout_sec": 60,
                        },
                    },
                ],
            }
        return {
            "usage": {"total_tokens": self.second_tokens},
            "content": [{"type": "text", "text": "Stop after smoke reproduction."}],
        }


def _smoke_policy(base_policy: dict[str, Any], *, policy_id: str) -> dict[str, Any]:
    policy = dict(base_policy)
    policy["policy_id"] = policy_id
    policy["agent_type"] = "llm"
    policy["llm_provider"] = "openai_compatible"
    policy["llm_model"] = "fake-model"
    policy["llm_api_key_env"] = None
    policy["llm_base_url_env"] = None
    policy["llm_model_env"] = None
    policy["llm_base_url"] = None
    return policy


def _run_fake_llm_task(*, task_path: Path, repo_root: Path, policy_path: Path) -> dict[str, Any]:
    task = load_task(task_path)
    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=2),
        client=RunTestsThenStopClient(task.test_command),
    )
    return agent.run(task_path=task_path, repo_root=repo_root, policy_path=policy_path)


def build_markdown(summary: dict[str, Any]) -> str:
    result_lines = "\n".join(
        (
            f"- `{item['task_id']}` `{item['variant']}` -> `{item['final_status']}` "
            f"(run: `{item['run_id']}`)"
        )
        for item in summary["runs"]
    ) or "- N/A"
    outputs = summary.get("outputs", {})
    return f"""# Code Intelligence A/B Smoke

## Smoke

- smoke_id: `{summary["smoke_id"]}`
- cohort_label: `{summary["cohort_label"]}`
- task_count: `{summary["task_count"]}`
- baseline_policy_path: `{summary["baseline_policy_path"]}`
- graph_policy_path: `{summary["graph_policy_path"]}`

## Runs

{result_lines}

## Outputs

- ab_summary_json: `{outputs.get("ab_summary_json", "N/A")}`
- ab_summary_md: `{outputs.get("ab_summary_md", "N/A")}`
"""


def run_code_intelligence_ab_smoke(
    *,
    manifest: str | Path,
    tasks_dir: str | Path,
    baseline_policy_path: str | Path,
    cohort_label: str,
    codebase_memory_binary: str,
    timeout_sec: float = 30.0,
    max_results: int = 5,
    index_mode: str = "fast",
    limit: int | None = 1,
    output_dir: str | Path = "logs/summaries",
) -> dict[str, Any]:
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    smoke_id = _next_smoke_id(output_directory, cohort_label)
    baseline_policy_file = Path(baseline_policy_path).resolve()
    baseline_policy = _smoke_policy(_load_json(baseline_policy_file), policy_id=f"{smoke_id}_baseline")
    graph_policy = build_graph_policy(
        baseline_policy=baseline_policy,
        graph_policy_id=f"{smoke_id}_graph",
        codebase_memory_binary=codebase_memory_binary,
        timeout_sec=timeout_sec,
        max_results=max_results,
        index_mode=index_mode,
    )
    baseline_smoke_policy_path = output_directory / f"{smoke_id}_baseline_policy.json"
    graph_policy_path = output_directory / f"{smoke_id}_graph_policy.json"
    write_json(baseline_smoke_policy_path, baseline_policy)
    write_json(graph_policy_path, graph_policy)

    task_paths = load_task_paths(
        tasks_dir=tasks_dir,
        manifest_path=Path(manifest).resolve(),
    )
    if limit is not None:
        task_paths = task_paths[:limit]
    target_files_by_task = collect_target_files_by_task(task_paths)

    runs: list[dict[str, Any]] = []
    result_paths: list[str] = []
    for task_path in task_paths:
        for variant, policy_path in [
            ("baseline", baseline_smoke_policy_path),
            ("graph", graph_policy_path),
        ]:
            output = _run_fake_llm_task(
                task_path=Path(task_path),
                repo_root=REPO_ROOT,
                policy_path=policy_path,
            )
            result_paths.append(output["run_paths"]["result_json_path"])
            runs.append(
                {
                    "task_id": output["task"]["task_id"],
                    "variant": variant,
                    "run_id": output["result"]["run_id"],
                    "final_status": output["result"]["final_status"],
                    "accepted_final_status": output["result"].get("accepted_final_status", ""),
                    "result_path": output["run_paths"]["result_json_path"],
                    "trace_path": output["run_paths"]["trace_json_path"],
                }
            )

    ab_summary = summarize_code_intelligence_runs(
        result_paths=result_paths,
        cohort_label=f"{cohort_label}_smoke_ab",
        output_dir=output_directory,
        target_files_by_task=target_files_by_task,
        include_ab_pairs=True,
        baseline_backend="none",
        candidate_backend="codebase_memory_cli",
    )
    summary = {
        "created_at": _utc_timestamp(),
        "smoke_id": smoke_id,
        "cohort_label": cohort_label,
        "task_count": len(task_paths),
        "task_paths": [str(path) for path in task_paths],
        "target_files_by_task": target_files_by_task,
        "baseline_policy_path": str(baseline_smoke_policy_path),
        "graph_policy_path": str(graph_policy_path),
        "runs": runs,
        "outputs": {
            "ab_summary_json": ab_summary["summary_json_path"],
            "ab_summary_md": ab_summary["summary_md_path"],
        },
    }
    summary_json_path = output_directory / f"{smoke_id}.json"
    summary_md_path = output_directory / f"{smoke_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_markdown(summary))
    return {
        "smoke_id": smoke_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
        "ab_summary": ab_summary["summary"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run deterministic code intelligence A/B smoke.")
    parser.add_argument("--manifest", default="benchmarks/manifests/dev_tasks.json")
    parser.add_argument("--tasks-dir", default="benchmarks/tasks")
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--cohort-label", default="v16_ab_smoke")
    parser.add_argument("--codebase-memory-binary", required=True)
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--index-mode", default="fast")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--output-dir", default="logs/summaries")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = run_code_intelligence_ab_smoke(
        manifest=REPO_ROOT / args.manifest,
        tasks_dir=REPO_ROOT / args.tasks_dir,
        baseline_policy_path=REPO_ROOT / args.baseline_policy,
        cohort_label=args.cohort_label,
        codebase_memory_binary=args.codebase_memory_binary,
        timeout_sec=args.timeout_sec,
        max_results=args.max_results,
        index_mode=args.index_mode,
        limit=args.limit,
        output_dir=REPO_ROOT / args.output_dir,
    )
    ab_aggregate = output["ab_summary"].get("ab_aggregate", {})
    print("=== Code Intelligence A/B Smoke ===")
    print(f"smoke_id: {output['smoke_id']}")
    print(f"task_count: {output['summary']['task_count']}")
    print(f"ab_pair_count: {ab_aggregate.get('pair_count', 0)}")
    print(f"candidate_fallback_rate: {ab_aggregate.get('candidate_fallback_rate', 0.0)}")
    print(f"average_token_delta: {ab_aggregate.get('average_token_delta', 0.0)}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    print(f"ab_summary_json: {output['summary']['outputs']['ab_summary_json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

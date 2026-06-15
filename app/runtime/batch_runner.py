"""批量任务运行入口。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.agent.executor import run_agent
from app.runtime.logger import write_json, write_text
from app.schemas.task_schema import load_task


def _utc_timestamp() -> str:
    # 批量运行也统一使用 UTC 时间，便于后续做结果比较。
    return datetime.now(timezone.utc).isoformat()


def _next_batch_run_id(summary_dir: Path, run_label: str | None = None) -> str:
    # 批量运行单独维护 batch_run_xxx 编号，和单任务 run_id 语义区分开。
    existing_numbers: list[int] = []
    prefix = f"batch_run_{run_label}_" if run_label else "batch_run_"
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    if run_label:
        return f"{prefix}{next_number:03d}"
    return f"batch_run_{next_number:03d}"


def load_task_paths(tasks_dir: str | Path, manifest_path: str | Path | None = None) -> list[Path]:
    # 第一版支持两种方式：直接扫目录，或通过 manifest 显式指定任务顺序。
    resolved_tasks_dir = Path(tasks_dir).resolve()
    if manifest_path is None:
        return sorted(resolved_tasks_dir.glob("task_*.json"))

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    task_paths = [
        (resolved_tasks_dir.parent.parent / relative_path).resolve()
        for relative_path in manifest["tasks"]
    ]
    return task_paths


def run_batch(
    repo_root: str | Path,
    task_paths: list[str | Path],
    policy_path: str | Path | None = None,
    run_label: str | None = None,
) -> dict:
    # 复用单任务闭环，把多条任务结果组织成批量汇总。
    repository_root = Path(repo_root).resolve()
    summaries_dir = repository_root / "logs" / "summaries"
    summaries_dir.mkdir(parents=True, exist_ok=True)

    batch_run_id = _next_batch_run_id(summaries_dir, run_label=run_label)
    started_at = _utc_timestamp()

    task_results: list[dict] = []
    policy_id = None
    for task_path in task_paths:
        run_output = run_agent(task_path=task_path, repo_root=repository_root, policy_path=policy_path)
        task_definition = load_task(task_path)
        policy_id = run_output["result"]["tool_stats"].get("policy_id")
        task_results.append(
            {
                "task_id": task_definition.task_id,
                "task_path": str(Path(task_path).resolve()),
                "run_id": run_output["result"]["run_id"],
                "final_status": run_output["result"]["final_status"],
                "result_path": run_output["run_paths"]["result_json_path"],
                "trace_path": run_output["run_paths"]["trace_json_path"],
                "summary_path": run_output["run_paths"]["summary_md_path"],
                "patch_applied": run_output["result"].get("patch_applied", False),
                "post_test_exit_code": run_output["result"].get("post_test_exit_code"),
                "policy_id": run_output["result"]["tool_stats"].get("policy_id"),
            }
        )

    success_count = sum(1 for item in task_results if item["final_status"] == "success")
    batch_summary = {
        "batch_run_id": batch_run_id,
        "policy_id": policy_id,
        "started_at": started_at,
        "finished_at": _utc_timestamp(),
        "task_count": len(task_results),
        "success_count": success_count,
        "success_rate": round(success_count / len(task_results), 4) if task_results else 0.0,
        "tasks": task_results,
    }

    summary_json_path = summaries_dir / f"{batch_run_id}.json"
    summary_md_path = summaries_dir / f"{batch_run_id}.md"
    write_json(summary_json_path, batch_summary)

    task_lines = "\n".join(
        [
            f"- `{item['task_id']}` -> `{item['final_status']}` "
            f"(run: `{item['run_id']}`, post_test_exit_code: `{item['post_test_exit_code']}`)"
            for item in task_results
        ]
    ) or "- 无任务结果"
    summary_markdown = f"""# Batch Run Summary

## Run

- batch_run_id: `{batch_run_id}`
- task_count: `{batch_summary["task_count"]}`
- success_count: `{batch_summary["success_count"]}`
- success_rate: `{batch_summary["success_rate"]}`

## Task Results

{task_lines}
"""
    write_text(summary_md_path, summary_markdown)

    return {
        "batch_summary": batch_summary,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
    }

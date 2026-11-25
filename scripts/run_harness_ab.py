"""Paired strict/weak Harness experiment using the existing batch runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.policy_config import load_policy_config
from app.llm.config import LLMConfig
from app.runtime.batch_runner import load_task_paths, run_batch
from app.runtime.logger import write_json
from app.schemas.task_schema import load_task


def classify_result(result: dict[str, Any]) -> str:
    # Do not equate local SWE-bench smoke with official resolution.
    if result.get("accepted_final_status") == "accepted_success":
        return "accepted"
    return "not_accepted"


def result_record(result: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    stats = result.get("tool_stats", {})
    usage = stats.get("llm_usage", {})
    return {
        "outcome": classify_result(result),
        "final_status": result.get("final_status"),
        "accepted_final_status": result.get("accepted_final_status"),
        "verification_level": result.get("verifier_report", {}).get("verification_level"),
        "pre_test_exit_code": result.get("pre_test_exit_code"),
        "post_test_exit_code": result.get("post_test_exit_code"),
        "patch_applied": result.get("patch_applied"),
        "incomplete_reason": result.get("incomplete_reason"),
        "duration_sec": result.get("duration_sec"),
        "total_tokens": usage.get("total_tokens"),
        "missing_usage_count": usage.get("missing_usage_count"),
        "llm_model": stats.get("llm_model"),
        "llm_provider": stats.get("llm_provider"),
        "harness_mode": stats.get("harness_mode"),
        "result_path": entry["result_path"],
        "trace_path": entry["trace_path"],
    }


def summarize_pairs(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    cells = dict(both_accepted=0, strict_only=0, weak_only=0, neither_accepted=0)
    complete = []
    for pair in pairs:
        a, b = pair.get("strict"), pair.get("weak")
        if not a or not b or a.get("error") or b.get("error"):
            continue
        if (a.get("llm_model"), a.get("llm_provider")) != (b.get("llm_model"), b.get("llm_provider")):
            continue
        if a.get("harness_mode") != "strict" or b.get("harness_mode") != "weak":
            continue
        complete.append(pair)
        sa, wa = a["outcome"] == "accepted", b["outcome"] == "accepted"
        cell = "both_accepted" if sa and wa else "strict_only" if sa else "weak_only" if wa else "neither_accepted"
        cells[cell] += 1
    arms = {}
    for arm in ("strict", "weak"):
        rows = [p[arm] for p in complete]
        accepted = sum(r["outcome"] == "accepted" for r in rows)
        tokens = [r["total_tokens"] for r in rows if r.get("total_tokens") is not None and r.get("missing_usage_count") == 0]
        durations = [r["duration_sec"] for r in rows if r.get("duration_sec") is not None]
        arms[arm] = {
            "accepted_count": accepted,
            "accepted_rate": accepted / len(rows) if rows else None,
            "mean_reported_tokens": mean(tokens) if tokens else None,
            "complete_token_records": len(tokens),
            "mean_duration_sec": mean(durations) if durations else None,
        }
    return {
        "complete_pairs": len(complete),
        "excluded_or_incomplete_pairs": len(pairs) - len(complete),
        "matrix": cells,
        "arms": arms,
        "discordant_task_ids": [p["task_id"] for p in complete if p["strict"]["outcome"] != p["weak"]["outcome"]],
        "pairs": pairs,
        "metric_note": "Accepted success uses the existing verifier; local SWE-bench smoke is not official resolved. Token counts are reported main-loop usage, not guaranteed total billing.",
    }


def run_experiment(*, repo_root: Path, task_paths: list[Path], policy_path: Path,
                   output_dir: Path, memory_seed: Path | None = None,
                   dry_run: bool = False) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    base = load_policy_config(policy_path)
    if base.agent_type != "llm":
        raise ValueError("The base policy must select agent_type=llm")
    tasks = [load_task(p) for p in task_paths]
    if not tasks or len({t.task_id for t in tasks}) != len(tasks):
        raise ValueError("Use a non-empty cohort with unique task IDs")
    for task in tasks:
        if not (repo_root / task.repo_path).is_dir():
            raise FileNotFoundError(task.repo_path)
    # New experiment directories only: never overwrite an existing run or memory.
    output_dir.mkdir(parents=True, exist_ok=False)
    seed = memory_seed.read_bytes() if memory_seed is not None else b""
    seed_path = output_dir / "memory_seed.jsonl"
    seed_path.write_bytes(seed)
    LLMConfig.load_env_file(repo_root)
    config = LLMConfig.from_policy(base)
    write_json(output_dir / "plan.json", {
        "task_paths": [str(p.resolve()) for p in task_paths],
        "task_ids": [t.task_id for t in tasks],
        "base_policy": base.to_dict(),
        "memory_seed_sha256": hashlib.sha256(seed).hexdigest(),
        "memory_seed_source": str(memory_seed.resolve()) if memory_seed else "empty",
        "llm_model": config.model, "llm_provider": config.provider,
        "max_iterations": config.max_iterations,
        "dry_run": dry_run,
    })
    pairs = []
    for index, (task, path) in enumerate(zip(tasks, task_paths)):
        pair = {"task_id": task.task_id}
        pairs.append(pair)
        # Alternate arm order to reduce systematic provider/time ordering effects.
        order = ("strict", "weak") if index % 2 == 0 else ("weak", "strict")
        pair["order"] = list(order)
        for arm in order:
            arm_dir = output_dir / f"pair_{index + 1:04d}" / arm
            memory = arm_dir / "agent_memory" / "strategy_memory.jsonl"
            memory.parent.mkdir(parents=True)
            memory.write_bytes(seed)
            policy = base.model_copy(update={
                "policy_id": f"{base.policy_id}_{arm}",
                "harness_mode": arm,
                "run_log_root": str(arm_dir),
            })
            arm_policy = arm_dir / "policy.json"
            write_json(arm_policy, policy)
            if dry_run:
                pair[arm] = {"planned": True, "policy_path": str(arm_policy)}
                continue
            try:
                batch = run_batch(repo_root=repo_root, task_paths=[path],
                                  policy_path=arm_policy, run_label=arm,
                                  summary_dir=arm_dir / "summaries")
                entry = batch["batch_summary"]["tasks"][0]
                result = json.loads(Path(entry["result_path"]).read_text(encoding="utf-8"))
                pair[arm] = result_record(result, entry)
            except Exception as exc:
                # Keep infrastructure errors distinct from repair failures.
                pair[arm] = {"error": type(exc).__name__, "arm_dir": str(arm_dir)}
            write_json(output_dir / "progress.json", {"pairs": pairs})
    summary = {"dry_run": True, "pairs": pairs} if dry_run else summarize_pairs(pairs)
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--tasks-dir", default=REPO_ROOT / "benchmarks/tasks", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--memory-seed", type=Path, help="Optional frozen strategy-memory snapshot; defaults to empty.")
    parser.add_argument("--limit", type=int, help="Use the first N tasks in the explicit manifest.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-external-llm-data", action="store_true")
    args = parser.parse_args()
    if not args.dry_run and not args.confirm_external_llm_data:
        parser.error("Live runs send task/code/tool evidence to the configured provider; confirm explicitly.")
    if not args.manifest.is_file():
        parser.error("Manifest must exist; no implicit fallback.")
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    paths = load_task_paths(args.tasks_dir, args.manifest)
    if args.limit is not None:
        paths = paths[:args.limit]
    summary = run_experiment(repo_root=REPO_ROOT, task_paths=paths, policy_path=args.policy,
                             output_dir=args.output_dir, memory_seed=args.memory_seed, dry_run=args.dry_run)
    print(f"Summary: {args.output_dir.resolve() / 'summary.json'}")
    if not args.dry_run:
        print(json.dumps({k: v for k, v in summary.items() if k != "pairs"}, ensure_ascii=False, indent=2))
        return 0 if summary["excluded_or_incomplete_pairs"] == 0 else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

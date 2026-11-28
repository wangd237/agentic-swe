"""Serial, resumable Real Issue-only benchmark launcher. No default paid execution."""
import argparse
import hashlib
import os
import json
import pathlib
import subprocess
import time

from admission import sha
from runtime_agent_probe import run
from graph_preflight import check_graph, validate_graph_dir

P = pathlib.Path
ROOT = P(__file__).resolve().parents[2]
MANIFEST = ROOT/"benchmarks/manifests/real_issue_full_frozen_20_v1.json"
POLICY = ROOT/"optimization/policy_versions/llm_real_full_baseline_v1.json"

def read(p):
    return json.loads(p.read_text(encoding="utf-8"))

def dump(path, value):
    tmp = path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    os.replace(tmp, path)

def export_digest(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.name == ".git" or path.is_symlink():
            raise ValueError("Git metadata or symlink in public export: "+str(path))
        if path.is_file():
            digest.update(json.dumps([path.relative_to(root).as_posix(), sha(path)], ensure_ascii=False).encode("utf-8")+b"\n")
    return digest.hexdigest()

def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()

def tasks(manifest):
    data = read(manifest)
    if data["manifest_id"] != "real_issue_full_frozen_20_v1" or len(data["tasks"]) != 20:
        raise ValueError("Expected frozen Real Issue 20 manifest")
    result = {}
    for rel in data["tasks"]:
        path = (ROOT/rel).resolve()
        if path.parent != ROOT/"benchmarks/tasks/real_issue_full_v1":
            raise ValueError("Unexpected task directory")
        task = read(path)
        tid = task["task_id"]
        if not tid.startswith("real_full_") or task["source_type"] != "real_issue" or tid in result:
            raise ValueError("Invalid or duplicate Real Issue task")
        result[tid] = (task, sha(path))
    return result

def summarize(rows, count):
    solved = sum(r["status"] == "solved" for r in rows)
    failed = sum(r["status"] == "unsolved" for r in rows)
    errors = sum(r["status"] == "execution_error" for r in rows)
    completed = solved + failed
    return {"selected": count, "solved": solved, "unsolved": failed,
            "execution_errors": errors, "pending": count-len(rows),
            "completed_rate": solved/completed if completed else None,
            "repair_rate": solved/count if completed == count else None,
            "tasks": rows}

def metrics(result):
    stats = result.get("agent_tool_stats", {})
    usage = stats.get("llm_usage", {})
    return {"agent_duration_sec": result.get("agent_duration_sec"),
            "elapsed_sec": result.get("elapsed_sec"),
            "llm_calls": usage.get("call_count"),
            "total_tokens": usage.get("total_tokens"),
            "missing_usage_count": usage.get("missing_usage_count"),
            "tool_calls": stats.get("total_tool_calls"),
            "final_phase": stats.get("final_phase"),
            "incomplete_reason": stats.get("incomplete_reason")}

def result_row(result, tid, probe, policy, model, runtime):
    if (result["task_id"] != "real_"+tid.removeprefix("real_full_")
            or result["expected_model"] != model
            or result["agent_image_id"] != runtime["image_id"]
            or result["agent_tool_stats"].get("policy_id") != policy["policy_id"]
            or result["policy_sha256"] != sha(probe/"policy.json")
            or read(probe/"policy.json") != policy
            or result["final_success"] != result["evaluator_accepted"]):
        raise ValueError("Persisted pipeline result does not match batch plan")
    return {"task_id": tid, "status": "solved" if result["final_success"] else "unsolved",
            "metrics": metrics(result), "pipeline_result": str(probe/"pipeline_result.json"),
            "trace_directory": str(probe/"agent_logs"), "verdict": result["evaluator_reason"]}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--private", required=True, type=P)
    p.add_argument("--exports", required=True, type=P)
    p.add_argument("--policy", type=P, default=POLICY)
    p.add_argument("--graph-dir", type=P)
    p.add_argument("--llm-env", type=P)
    p.add_argument("--model", required=True)
    p.add_argument("--network", default="real_issue_acceptance_internal")
    p.add_argument("--label", required=True)
    p.add_argument("--task", action="append")
    p.add_argument("--check-runtime", action="store_true", help="Offline graph/runtime smoke only")
    p.add_argument("--execute", action="store_true", help="Explicitly permit paid LLM runs")
    a = p.parse_args()
    if not a.label or a.label in {".",".."} or not all(c.isalnum() or c in "-_." for c in a.label):
        p.error("Invalid label")
    all_tasks = tasks(MANIFEST)
    selected = a.task or list(all_tasks)
    if len(set(selected)) != len(selected) or not set(selected) <= set(all_tasks):
        p.error("Unknown or duplicate task")
    private, exports = a.private.resolve(), a.exports.resolve()
    if private.is_relative_to(exports) or exports.is_relative_to(private):
        p.error("Private and public exports must be separate")
    policy = read(a.policy)
    if policy.get("agent_type") != "llm":
        p.error("Expected LLM policy")
    graph = policy.get("code_intelligence_backend") == "codebase_memory_cli"
    if graph and not a.graph_dir:
        p.error("Graph-enabled policy requires --graph-dir")
    graph_dir = a.graph_dir.resolve() if graph else None
    if graph_dir and (graph_dir.is_relative_to(private) or private.is_relative_to(graph_dir)):
        p.error("Graph directory must be separate from private data")
    lock = validate_graph_dir(graph_dir) if graph else None
    if a.check_runtime or a.execute:
        if git("diff", "--name-only", "0951c74fe61bd5715ec6da0321d1e4231d098107", "--", "benchmarks/manifests/real_issue_full_frozen_20_v1.json", "benchmarks/tasks/real_issue_full_v1", "benchmarks/repos/real_issue_full_v1"):
            p.error("Frozen Real Issue data changed")
    plan = {"commit": git("rev-parse", "HEAD"), "manifest_sha256": sha(MANIFEST),
            "policy_sha256": sha(a.policy), "policy": policy, "model": a.model,
            "network": a.network, "graph": lock, "selected": selected,
            "task_hashes": {tid: all_tasks[tid][1] for tid in selected}, "runtime_locks": {}}
    for tid in selected:
        key = "real_"+tid.removeprefix("real_full_")
        root = private/key
        runtime = read(root/"agent_runtime.json")
        prep = read(root/"prepared.json")
        if prep["task_id"] != key or not (exports/key).is_dir():
            raise ValueError("Private/public task mismatch: "+tid)
        plan["runtime_locks"][tid] = {"runtime": runtime, "dependencies": sha(root/"agent_dependencies.lock.txt"),
                                        "review": sha(root/"review.json"), "validation": sha(root/"validation.json"),
                                        "export_sha256": export_digest(exports/key)}
    if a.check_runtime or a.execute:
        if git("status", "--porcelain", "--untracked-files=all", "--", "app", "tools/real_issue_admission", "benchmarks/manifests", "benchmarks/tasks/real_issue_full_v1", "optimization/policy_versions"):
            p.error("Commit all experiment changes before running")
        if graph:
            for tid in selected:
                key = "real_"+tid.removeprefix("real_full_")
                check_graph(plan["runtime_locks"][tid]["runtime"], exports/key, ROOT/"app", graph_dir, a.policy.resolve(), all_tasks[tid][0]["issue_text"])
                print("GRAPH_OK", tid, flush=True)
    if not a.execute:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0
    if git("status", "--porcelain", "--untracked-files=no"):
        p.error("Tracked worktree changes; commit experiment code first")
    if not a.llm_env or not a.llm_env.is_file() or a.network == "none":
        p.error("Paid run requires LLM env and restricted network")
    if subprocess.check_output(["docker","network","inspect",a.network,"--format","{{.Internal}}"],text=True).strip() != "true":
        p.error("Model network must be internal")
    out = private/"formal_batches"/a.label
    out.mkdir(parents=True, exist_ok=True)
    plan_path = out/"plan.json"
    if plan_path.exists() and read(plan_path) != plan:
        raise ValueError("Resume configuration drift; use new label")
    if not plan_path.exists():
        dump(plan_path, plan)
    rows = []
    for tid in selected:
        key = "real_"+tid.removeprefix("real_full_")
        root = private/key
        row_path = out/(tid+".json")
        if row_path.exists():
            row = read(row_path)
            if row["task_id"] != tid or row["status"] not in {"solved", "unsolved", "execution_error"}:
                raise ValueError("Invalid persisted task result")
            rows.append(row)
            continue
        label = "formal_"+a.label
        probe = root/"runtime_agent_probe"/label
        started = time.monotonic()
        try:
            runtime = plan["runtime_locks"][tid]["runtime"]
            if (probe/"pipeline_result.json").exists():
                result = read(probe/"pipeline_result.json")
            elif probe.exists():
                raise RuntimeError("Existing incomplete probe; inspect before rerunning with a new label")
            else:
                result = run(root, exports/key, ROOT/"app", runtime["image"], label,
                             a.llm_env.resolve(), a.network, policy, a.model, all_tasks[tid][0], graph_dir)
            row = result_row(result, tid, probe, policy, a.model, runtime)
        except Exception as exc:
            row = {"task_id": tid, "status": "execution_error", "error_type": type(exc).__name__,
                   "error": str(exc), "elapsed_sec": round(time.monotonic()-started, 3), "probe": str(probe)}
        dump(row_path, row)
        rows.append(row)
        dump(out/"summary.json", summarize(rows, len(selected)))
        print(tid, row["status"], flush=True)
    summary = summarize(rows, len(selected))
    dump(out/"summary.json", summary)
    return int(summary["execution_errors"] > 0)

if __name__ == "__main__":
    raise SystemExit(main())

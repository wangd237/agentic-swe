"""Diagnose codebase-memory-mcp CLI behavior on a local repository."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent.code_intelligence import CodebaseMemoryCliBackend
from app.runtime.logger import write_json, write_text


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _round_float(value: float) -> float:
    return round(value, 4)


def _next_diagnostic_id(output_dir: Path, run_label: str) -> str:
    prefix = f"codebase_memory_backend_{run_label}_"
    existing_numbers: list[int] = []
    for path in output_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _resolve_binary(binary: str) -> str:
    explicit_path = Path(binary)
    if explicit_path.exists():
        return str(explicit_path.resolve())
    return shutil.which(binary) or binary


def _run_cli_command(
    *,
    args: list[str],
    env: dict[str, str],
    timeout_sec: float,
) -> dict[str, Any]:
    started_at = perf_counter()
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            check=False,
            env=env,
        )
        duration_sec = _round_float(perf_counter() - started_at)
        combined_output = "\n".join(part for part in [completed.stdout or "", completed.stderr or ""] if part)
        parsed_json = CodebaseMemoryCliBackend._extract_json_object(combined_output)
        return {
            "args": args,
            "returncode": completed.returncode,
            "duration_sec": duration_sec,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "stdout_chars": len(completed.stdout or ""),
            "stderr_chars": len(completed.stderr or ""),
            "parsed_json": parsed_json,
            "ok": completed.returncode == 0,
            "error": "",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "args": args,
            "returncode": None,
            "duration_sec": _round_float(perf_counter() - started_at),
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "stdout_chars": len(exc.stdout or ""),
            "stderr_chars": len(exc.stderr or ""),
            "parsed_json": {},
            "ok": False,
            "error": "timeout",
        }
    except OSError as exc:
        return {
            "args": args,
            "returncode": None,
            "duration_sec": _round_float(perf_counter() - started_at),
            "stdout": "",
            "stderr": "",
            "stdout_chars": 0,
            "stderr_chars": 0,
            "parsed_json": {},
            "ok": False,
            "error": f"os_error:{exc.__class__.__name__}:{exc}",
        }


def _result_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(payload.get("results"), list):
        return [item for item in payload["results"] if isinstance(item, dict)]
    data = payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return [item for item in data["results"] if isinstance(item, dict)]
    return []


def _top_candidate_files(items: list[dict[str, Any]]) -> list[str]:
    files: list[str] = []
    for item in items:
        path = (
            item.get("file")
            or item.get("path")
            or item.get("file_path")
            or item.get("relative_path")
            or item.get("filename")
        )
        if path and str(path) not in files:
            files.append(str(path).replace("\\", "/"))
    return files[:5]


def diagnose_backend(
    *,
    binary: str,
    repo: str | Path,
    queries: list[str],
    timeout_sec: float,
    max_results: int,
    mode: str,
    output_dir: str | Path,
    run_label: str,
    home_root: str | Path | None = None,
) -> dict[str, Any]:
    repository = Path(repo).resolve()
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    diagnostic_id = _next_diagnostic_id(output_directory, run_label)
    binary_path = _resolve_binary(binary)
    env_home = Path(home_root).resolve() if home_root else output_directory / f"{diagnostic_id}_home"
    env = CodebaseMemoryCliBackend._default_env(env_home)

    version_record = _run_cli_command(
        args=[binary_path, "--version"],
        env=env,
        timeout_sec=timeout_sec,
    )
    index_payload: dict[str, Any] = {"repo_path": str(repository)}
    if mode:
        index_payload["mode"] = mode
    index_record = _run_cli_command(
        args=[binary_path, "cli", "index_repository", json.dumps(index_payload)],
        env=env,
        timeout_sec=timeout_sec,
    )

    search_records: list[dict[str, Any]] = []
    graph_candidates: list[dict[str, Any]] = []
    project_name = str(index_record.get("parsed_json", {}).get("project") or "")
    if index_record["ok"] and project_name:
        for query in queries:
            search_payload = {
                "project": project_name,
                "name_pattern": f".*{re.escape(query)}.*",
                "limit": max_results,
            }
            search_record = _run_cli_command(
                args=[binary_path, "cli", "search_graph", json.dumps(search_payload)],
                env=env,
                timeout_sec=timeout_sec,
            )
            search_records.append({"query": query, **search_record})
            graph_candidates.extend(_result_items(search_record.get("parsed_json", {})))

    graph_query_duration_sec_total = _round_float(sum(float(record["duration_sec"]) for record in search_records))
    graph_result_raw_chars = sum(
        int(record["stdout_chars"]) + int(record["stderr_chars"]) for record in search_records
    )
    backend_version = (version_record.get("stdout") or version_record.get("stderr") or "").strip().splitlines()
    metrics = {
        "backend": "codebase_memory_cli",
        "backend_binary_path": binary_path,
        "backend_available": bool(version_record["ok"]),
        "backend_version": backend_version[0] if backend_version else "",
        "env_home": env.get("HOME", ""),
        "env_userprofile": env.get("USERPROFILE", ""),
        "env_localappdata": env.get("LOCALAPPDATA", ""),
        "index_attempted": True,
        "index_success": bool(index_record["ok"]),
        "index_duration_sec": index_record["duration_sec"],
        "indexed_project": project_name,
        "indexed_node_count": index_record.get("parsed_json", {}).get("nodes"),
        "indexed_edge_count": index_record.get("parsed_json", {}).get("edges"),
        "indexed_file_count": index_record.get("parsed_json", {}).get("files"),
        "index_error": index_record.get("error") or index_record.get("parsed_json", {}).get("error") or "",
        "index_hint": index_record.get("parsed_json", {}).get("hint") or "",
        "graph_tool_calls_total": len(search_records),
        "graph_search_graph_calls": len(search_records),
        "graph_query_duration_sec_total": graph_query_duration_sec_total,
        "graph_result_raw_chars": graph_result_raw_chars,
        "graph_candidates_count": len(graph_candidates),
        "graph_candidates_top_files": _top_candidate_files(graph_candidates),
    }
    summary = {
        "created_at": _utc_timestamp(),
        "diagnostic_id": diagnostic_id,
        "repo": str(repository),
        "repo_exists": repository.exists(),
        "run_label": run_label,
        "queries": queries,
        "timeout_sec": timeout_sec,
        "max_results": max_results,
        "mode": mode,
        "metrics": metrics,
        "version_record": version_record,
        "index_record": index_record,
        "search_records": search_records,
    }

    summary_json_path = output_directory / f"{diagnostic_id}.json"
    summary_md_path = output_directory / f"{diagnostic_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_markdown_summary(summary))
    return {
        "diagnostic_id": diagnostic_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_markdown_summary(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    top_files = ", ".join(f"`{path}`" for path in metrics["graph_candidates_top_files"]) or "N/A"
    return f"""# Codebase Memory Backend Diagnostic

## Run

- diagnostic_id: `{summary["diagnostic_id"]}`
- repo: `{summary["repo"]}`
- mode: `{summary["mode"] or "default"}`
- queries: `{summary["queries"]}`

## Metrics

- backend_available: `{metrics["backend_available"]}`
- backend_version: `{metrics["backend_version"] or "unknown"}`
- index_success: `{metrics["index_success"]}`
- index_duration_sec: `{metrics["index_duration_sec"]}`
- indexed_project: `{metrics["indexed_project"] or "N/A"}`
- indexed_node_count: `{metrics["indexed_node_count"]}`
- indexed_edge_count: `{metrics["indexed_edge_count"]}`
- indexed_file_count: `{metrics["indexed_file_count"]}`
- graph_tool_calls_total: `{metrics["graph_tool_calls_total"]}`
- graph_query_duration_sec_total: `{metrics["graph_query_duration_sec_total"]}`
- graph_result_raw_chars: `{metrics["graph_result_raw_chars"]}`
- graph_candidates_count: `{metrics["graph_candidates_count"]}`
- graph_candidates_top_files: {top_files}
- index_error: `{metrics["index_error"] or "N/A"}`
- index_hint: `{metrics["index_hint"] or "N/A"}`

## Environment

- HOME: `{metrics["env_home"]}`
- USERPROFILE: `{metrics["env_userprofile"]}`
- LOCALAPPDATA: `{metrics["env_localappdata"]}`
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose codebase-memory-mcp CLI behavior.")
    parser.add_argument("--binary", default="codebase-memory-mcp", help="Binary name or absolute path.")
    parser.add_argument("--repo", required=True, help="Repository path to index.")
    parser.add_argument("--query", action="append", default=[], help="Optional search_graph query. Repeatable.")
    parser.add_argument("--timeout-sec", type=float, default=30.0, help="Per-command timeout.")
    parser.add_argument("--max-results", type=int, default=5, help="search_graph limit.")
    parser.add_argument("--mode", default="", help="Optional index_repository mode, e.g. fast.")
    parser.add_argument("--output-dir", default="logs/summaries", help="Directory for JSON/Markdown summaries.")
    parser.add_argument("--run-label", default="diagnostic", help="Stable label used in output filenames.")
    parser.add_argument("--home-root", default="", help="Optional isolated HOME/USERPROFILE directory.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = diagnose_backend(
        binary=args.binary,
        repo=args.repo,
        queries=args.query,
        timeout_sec=args.timeout_sec,
        max_results=args.max_results,
        mode=args.mode,
        output_dir=args.output_dir,
        run_label=args.run_label,
        home_root=args.home_root or None,
    )
    metrics = output["summary"]["metrics"]
    print("=== Codebase Memory Backend Diagnostic ===")
    print(f"diagnostic_id: {output['diagnostic_id']}")
    print(f"backend_available: {metrics['backend_available']}")
    print(f"backend_version: {metrics['backend_version'] or '(unknown)'}")
    print(f"index_success: {metrics['index_success']}")
    print(f"index_duration_sec: {metrics['index_duration_sec']}")
    print(f"graph_tool_calls_total: {metrics['graph_tool_calls_total']}")
    print(f"graph_candidates_count: {metrics['graph_candidates_count']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0 if metrics["backend_available"] and metrics["index_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

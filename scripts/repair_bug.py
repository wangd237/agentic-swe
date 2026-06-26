"""User-friendly CLI for running a local bug repair task."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent.executor import run_agent
from app.schemas.task_schema import Task


DEFAULT_POLICY_PATH = Path("optimization/policy_versions/llm_deepseek_minimal.json")
DEFAULT_USER_TASKS_DIR = Path("logs/user_tasks")
DEFAULT_GITHUB_REPOS_DIR = Path("logs/github_repos")
PYTEST_CONFIG_FILES = {
    "pytest.ini",
    ".pytest.ini",
    "pyproject.toml",
    "tox.ini",
    "setup.cfg",
}


GITHUB_REPO_URL_RE = re.compile(
    r"^(?:https?://github\.com/|git@github\.com:)(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$"
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compact_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "repair"


def _relative_to_repo_root(path: Path, repo_root: Path) -> str:
    try:
        relative_path = path.resolve().relative_to(repo_root.resolve())
    except ValueError as error:
        raise ValueError(
            f"Only repositories inside this project are supported in the MVP: {path}"
        ) from error
    return relative_path.as_posix()


def resolve_local_repo_path(repo: str | Path, repo_root: Path = REPO_ROOT) -> Path:
    repo_path = Path(repo).expanduser()
    if not repo_path.is_absolute():
        repo_path = repo_root / repo_path
    resolved = repo_path.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Repository path does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {resolved}")
    _relative_to_repo_root(resolved, repo_root)
    return resolved


def parse_github_repo_url(repo_url: str) -> tuple[str, str]:
    match = GITHUB_REPO_URL_RE.match(repo_url.strip())
    if not match:
        raise ValueError(f"Unsupported GitHub repository URL: {repo_url}")
    return match.group("owner"), match.group("repo")


def parse_github_issue_url(issue_url: str) -> tuple[str, str, int]:
    parsed = urlparse(issue_url.strip())
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
        raise ValueError(f"Unsupported GitHub issue URL: {issue_url}")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 4 or parts[2] != "issues":
        raise ValueError(f"GitHub issue URL must look like https://github.com/owner/repo/issues/123: {issue_url}")
    try:
        issue_number = int(parts[3])
    except ValueError as error:
        raise ValueError(f"GitHub issue number must be numeric: {issue_url}") from error
    return parts[0], parts[1].removesuffix(".git"), issue_number


def github_repo_url(owner: str, repo: str) -> str:
    return f"https://github.com/{owner}/{repo}"


def is_github_repo_url(value: str | Path) -> bool:
    return isinstance(value, str) and GITHUB_REPO_URL_RE.match(value.strip()) is not None


def clone_github_repo(
    repo_url: str,
    *,
    owner: str,
    repo_name: str,
    repo_root: Path = REPO_ROOT,
    clones_dir: str | Path = DEFAULT_GITHUB_REPOS_DIR,
) -> Path:
    clone_base = _resolve_project_path(clones_dir, repo_root)
    destination = clone_base / f"{_slugify(owner)}_{_slugify(repo_name)}_{_compact_timestamp()}" / "repo"
    destination.parent.mkdir(parents=True, exist_ok=False)

    completed = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(destination)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"Failed to clone GitHub repository {repo_url}: {details}")
    return destination.resolve()


def fetch_github_issue_text(
    *,
    owner: str,
    repo_name: str,
    issue_number: int,
) -> str:
    api_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}"
    request = Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "agentic-software-engineering-roadmap-repair-bug",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(f"Failed to fetch GitHub issue via public API ({api_url}): HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError(f"Failed to fetch GitHub issue via public API ({api_url}): {error.reason}") from error
    except OSError as error:
        raise RuntimeError(f"Failed to fetch GitHub issue via public API ({api_url}): {error}") from error

    title = str(payload.get("title") or "").strip()
    body = str(payload.get("body") or "").strip()
    if not title and not body:
        raise RuntimeError(f"GitHub issue payload did not include title or body: {api_url}")

    lines = [title or f"GitHub issue #{issue_number}"]
    if body:
        lines.extend(["", body])
    return "\n".join(lines)


def merge_issue_text(*, fetched_issue: str | None, user_issue: str | None) -> str:
    fetched = (fetched_issue or "").strip()
    user = (user_issue or "").strip()
    if fetched and user:
        return f"{fetched}\n\nUser supplied additional context:\n{user}"
    if fetched:
        return fetched
    if user:
        return user
    raise ValueError("Either --issue or --issue-url must be provided.")


def discover_test_command(repo_path: str | Path, explicit_test: str | None = None) -> tuple[str, str]:
    if explicit_test:
        return explicit_test, "explicit"

    path = Path(repo_path)
    has_tests_dir = (path / "tests").is_dir()
    has_test_files = any(path.glob("test_*.py")) or any(path.glob("*_test.py"))
    has_pytest_config = any((path / config_file).exists() for config_file in PYTEST_CONFIG_FILES)

    if has_tests_dir or has_test_files or has_pytest_config:
        return "python -m pytest -q", "pytest_auto"
    return "python -m pytest -q", "pytest_fallback"


def build_task_id(repo_path: Path, issue: str, requested_task_id: str | None = None) -> str:
    if requested_task_id:
        return requested_task_id
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    issue_slug = _slugify(issue)[:32].strip("_")
    return f"user_{_slugify(repo_path.name)}_{issue_slug}_{timestamp}"


def build_user_task(
    *,
    repo_path: Path,
    issue: str,
    test_command: str,
    test_source: str,
    task_id: str,
    repo_root: Path = REPO_ROOT,
    source_type: str = "user_local",
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Task:
    repo_name = repo_path.name
    task_metadata = {
        "created_at": _utc_timestamp(),
        "input_repo_path": str(repo_path),
        "test_command_source": test_source,
        "verification_strength": "normal" if test_source != "pytest_fallback" else "weak",
        "notes": (
            "No pytest configuration or tests were detected; using a minimal pytest fallback."
            if test_source == "pytest_fallback"
            else "Generated by scripts/repair_bug.py."
        ),
    }
    if metadata:
        task_metadata.update(metadata)

    payload: dict[str, Any] = {
        "task_id": task_id,
        "repo_name": repo_name,
        "repo_path": _relative_to_repo_root(repo_path, repo_root),
        "issue_title": issue.splitlines()[0][:120] or "User supplied bug report",
        "issue_text": issue,
        "test_command": test_command,
        "success_criteria": "The supplied issue is fixed and the selected verification command passes.",
        "difficulty": "unknown",
        "tags": tags or ["user", "local-repo", "python", "pytest"],
        "target_files_hint": [],
        "expected_failure_test": None,
        "max_retries": 2,
        "source_type": source_type,
        "metadata": task_metadata,
    }
    return Task.model_validate(payload)


def write_task(task: Task, *, output_dir: Path) -> Path:
    destination = output_dir / f"{task.task_id}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(task.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def _resolve_project_path(path: str | Path, repo_root: Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Python bug repair task without hand-writing task JSON.",
    )
    parser.add_argument("--repo", default=None, help="Local repository path inside this project or public GitHub repo URL.")
    parser.add_argument("--issue", default=None, help="Bug report or issue text to repair.")
    parser.add_argument("--issue-url", default=None, help="Public GitHub issue URL to fetch and repair.")
    parser.add_argument("--test", default=None, help="Verification command. Defaults to pytest auto-discovery.")
    parser.add_argument(
        "--policy",
        default=str(DEFAULT_POLICY_PATH),
        help="Policy JSON path. Defaults to optimization/policy_versions/llm_deepseek_minimal.json.",
    )
    parser.add_argument("--task-id", default=None, help="Optional stable task id for this repair run.")
    parser.add_argument(
        "--tasks-dir",
        default=str(DEFAULT_USER_TASKS_DIR),
        help="Directory where generated task JSON files are stored.",
    )
    return parser


def run_repair_bug(
    *,
    repo: str | Path | None = None,
    issue: str | None = None,
    issue_url: str | None = None,
    test: str | None = None,
    policy: str | Path = DEFAULT_POLICY_PATH,
    task_id: str | None = None,
    tasks_dir: str | Path = DEFAULT_USER_TASKS_DIR,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    issue_owner: str | None = None
    issue_repo_name: str | None = None
    issue_number: int | None = None
    fetched_issue: str | None = None
    if issue_url:
        issue_owner, issue_repo_name, issue_number = parse_github_issue_url(issue_url)
        fetched_issue = fetch_github_issue_text(
            owner=issue_owner,
            repo_name=issue_repo_name,
            issue_number=issue_number,
        )

    effective_issue = merge_issue_text(fetched_issue=fetched_issue, user_issue=issue)
    effective_repo = repo
    if effective_repo is None and issue_owner and issue_repo_name:
        effective_repo = github_repo_url(issue_owner, issue_repo_name)
    if effective_repo is None:
        raise ValueError("Either --repo or --issue-url must be provided.")

    cloned_repo_path: Path | None = None
    source_type = "user_local"
    tags = ["user", "local-repo", "python", "pytest"]
    metadata: dict[str, Any] = {}
    if is_github_repo_url(effective_repo):
        owner, repo_name = parse_github_repo_url(str(effective_repo))
        cloned_repo_path = clone_github_repo(
            str(effective_repo),
            owner=owner,
            repo_name=repo_name,
            repo_root=repo_root,
        )
        resolved_repo = cloned_repo_path
        source_type = "user_github"
        tags = ["user", "github", "python", "pytest"]
        metadata.update(
            {
                "input_repo_url": str(effective_repo),
                "cloned_repo_path": str(cloned_repo_path),
            }
        )
    else:
        resolved_repo = resolve_local_repo_path(effective_repo, repo_root=repo_root)

    if issue_url:
        metadata.update(
            {
                "issue_url": issue_url,
                "github_issue": {
                    "owner": issue_owner,
                    "repo": issue_repo_name,
                    "number": issue_number,
                },
            }
        )

    test_command, test_source = discover_test_command(resolved_repo, explicit_test=test)
    task = build_user_task(
        repo_path=resolved_repo,
        issue=effective_issue,
        test_command=test_command,
        test_source=test_source,
        task_id=build_task_id(resolved_repo, effective_issue, requested_task_id=task_id),
        repo_root=repo_root,
        source_type=source_type,
        tags=tags,
        metadata=metadata,
    )
    task_path = write_task(task, output_dir=_resolve_project_path(tasks_dir, repo_root))
    policy_path = _resolve_project_path(policy, repo_root)

    run_output = run_agent(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )
    result = run_output.get("result", {})
    run_paths = run_output.get("run_paths", {})
    return {
        "task": task.to_dict(),
        "task_path": str(task_path),
        "cloned_repo_path": str(cloned_repo_path) if cloned_repo_path is not None else "",
        "test_command_source": test_source,
        "fallback_warning": test_source == "pytest_fallback",
        "final_status": result.get("final_status", "unknown"),
        "summary_path": run_paths.get("summary_md_path", ""),
        "trace_path": run_paths.get("trace_json_path", ""),
        "result_path": run_paths.get("result_json_path", ""),
        "result": result,
        "run_paths": run_paths,
        "run_output": run_output,
    }


def print_summary(output: dict[str, Any]) -> None:
    task = output["task"]
    result = output.get("result", {})
    run_paths = output.get("run_paths", {})

    print("=== Repair Bug Run Summary ===")
    print(f"task_id: {task['task_id']}")
    print(f"repo_name: {task['repo_name']}")
    print(f"test_command: {task['test_command']}")
    if output.get("fallback_warning"):
        print("verification_note: weak fallback; no tests/ directory or pytest config was detected.")
    print(f"task_path: {output['task_path']}")
    print(f"cloned_repo_path: {output.get('cloned_repo_path', '')}")
    print(f"final_status: {output.get('final_status', result.get('final_status', 'unknown'))}")
    print(f"accepted_final_status: {result.get('accepted_final_status', 'unknown')}")
    print(f"verification_strength: {result.get('tool_stats', {}).get('verification_strength', 'unknown')}")
    verifier_report = result.get("verifier_report", {})
    if isinstance(verifier_report, dict) and verifier_report:
        print(f"verification_level: {verifier_report.get('verification_level', 'unknown')}")
        print(f"verifier_accepted: {verifier_report.get('accepted', False)}")
        print(f"risk_level: {verifier_report.get('risk_level', 'unknown')}")
    verification_evidence = result.get("verification_evidence", {})
    if isinstance(verification_evidence, dict) and verification_evidence:
        print(f"evidence_scope: {verification_evidence.get('verification_scope', 'unknown')}")
        official_harness = verification_evidence.get("official_harness", {})
        if isinstance(official_harness, dict):
            print(f"evidence_official_harness_required: {official_harness.get('required', False)}")
    print(f"incomplete_reason: {result.get('incomplete_reason') or 'none'}")
    print(f"pre_test_exit_code: {result.get('pre_test_exit_code')}")
    print(f"post_test_exit_code: {result.get('post_test_exit_code')}")
    llm_usage = result.get("tool_stats", {}).get("llm_usage", {})
    if isinstance(llm_usage, dict) and llm_usage.get("total_tokens") is not None:
        print(f"llm_total_tokens: {llm_usage.get('total_tokens')}")
    print(f"summary_path: {output.get('summary_path', run_paths.get('summary_md_path', ''))}")
    print(f"trace_path: {output.get('trace_path', run_paths.get('trace_json_path', ''))}")
    print(f"result_path: {output.get('result_path', run_paths.get('result_json_path', ''))}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = run_repair_bug(
            repo=args.repo,
            issue=args.issue,
            issue_url=args.issue_url,
            test=args.test,
            policy=args.policy,
            task_id=args.task_id,
            tasks_dir=args.tasks_dir,
        )
    except Exception as error:
        print(f"repair_bug error: {error}", file=sys.stderr)
        return 2

    print_summary(output)
    final_status = output.get("result", {}).get("final_status")
    return 0 if final_status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())

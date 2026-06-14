"""从 GitHub issue 导入候选信息，并可生成 task 草稿。"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json


def run_gh_command(args: list[str]) -> dict:
    # 统一从仓库根目录调用 gh，便于后续复用环境配置。
    result = subprocess.run(
        ["gh", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        stdout = result.stdout.decode("utf-8", errors="replace").strip()
        detail = stderr or stdout or "未知错误"
        raise RuntimeError(f"gh 命令失败：{detail}")
    stdout_text = result.stdout.decode("utf-8", errors="replace")
    return json.loads(stdout_text)


def load_candidate_dataset(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_candidate_dataset(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def timestamp_note(message: str) -> str:
    # 统一给候选备注补时间戳，后面回看筛选和推进过程更直观。
    return f"{datetime.now().isoformat(timespec='seconds')}: {message}"


def append_note(existing_notes: str, message: str) -> str:
    # 备注采用追加式记录，避免重复导入时把之前的人工结论覆盖掉。
    note_line = timestamp_note(message)
    if not existing_notes.strip():
        return note_line
    return f"{existing_notes.rstrip()}\n{note_line}"


def build_candidate_id(repo_full_name: str, issue_number: int) -> str:
    normalized_repo = repo_full_name.replace("/", "_").replace("-", "_")
    return f"{normalized_repo}_issue_{issue_number}"


def guess_difficulty(labels: list[str], title: str, body: str) -> str:
    # 先用简单启发式，后续可继续细化。
    joined = " ".join(labels + [title, body]).lower()
    if any(keyword in joined for keyword in ["easy", "good first issue", "beginner"]):
        return "easy"
    if any(keyword in joined for keyword in ["refactor", "multiple files", "complex"]):
        return "hard"
    return "medium"


def build_candidate(repo_full_name: str, issue_payload: dict) -> dict:
    return {
        "candidate_id": build_candidate_id(repo_full_name, issue_payload["number"]),
        "repo_full_name": repo_full_name,
        "repo_url": issue_payload["repository_url"],
        "issue_number": issue_payload["number"],
        "issue_title": issue_payload["title"],
        "issue_url": issue_payload["url"],
        "language": "python",
        "difficulty": guess_difficulty(
            [label["name"] for label in issue_payload.get("labels", [])],
            issue_payload["title"],
            issue_payload.get("body", "") or "",
        ),
        "status": "imported",
        "notes": timestamp_note("由 import_github_issue.py 自动导入，尚未补齐测试命令和目标文件。"),
        "labels": [label["name"] for label in issue_payload.get("labels", [])],
        "state": issue_payload.get("state", "open"),
        "created_at": issue_payload.get("createdAt"),
        "body_excerpt": (issue_payload.get("body", "") or "")[:500],
    }


def build_candidate_from_search_summary(search_candidate: dict) -> dict:
    repo_full_name = str(search_candidate["repo"]).strip()
    issue_number = int(search_candidate["issue_number"])
    labels = [str(label).strip() for label in search_candidate.get("labels", []) if str(label).strip()]
    candidate = {
        "candidate_id": build_candidate_id(repo_full_name, issue_number),
        "repo_full_name": repo_full_name,
        "repo_url": f"https://github.com/{repo_full_name}",
        "issue_number": issue_number,
        "issue_title": str(search_candidate["title"]).strip(),
        "issue_url": search_candidate["url"],
        "language": "python",
        "difficulty": search_candidate.get("estimated_difficulty", "medium"),
        "status": "imported",
        "notes": timestamp_note("由 search_candidate_issues.py 搜索结果导入，尚未完成人工筛选。"),
        "labels": labels,
        "state": search_candidate.get("state", "closed"),
        "created_at": search_candidate.get("created_at"),
        "body_excerpt": str(search_candidate.get("body_excerpt", "") or "")[:500],
    }
    overrides = {
        "why_it_fits": search_candidate.get("why_it_fits"),
        "expected_target_files": search_candidate.get("expected_target_files"),
        "expected_test_shape": search_candidate.get("expected_test_shape"),
        "risk_notes": search_candidate.get("risk_notes"),
        "recommendation": search_candidate.get("recommendation"),
    }
    return apply_candidate_overrides(candidate, overrides)


def apply_candidate_overrides(candidate: dict, overrides: dict | None) -> dict:
    if not overrides:
        return candidate

    updated_candidate = dict(candidate)
    note_messages: list[str] = []

    simple_fields = (
        "difficulty",
        "status",
    )
    for field_name in simple_fields:
        field_value = overrides.get(field_name)
        if field_value:
            updated_candidate[field_name] = field_value

    list_fields = (
        "expected_target_files",
    )
    for field_name in list_fields:
        field_value = overrides.get(field_name)
        if field_value:
            updated_candidate[field_name] = list(field_value)

    text_note_fields = (
        "why_it_fits",
        "expected_test_shape",
        "risk_notes",
        "recommendation",
    )
    for field_name in text_note_fields:
        field_value = overrides.get(field_name)
        if field_value:
            note_messages.append(f"{field_name}: {field_value}")

    extra_note = overrides.get("note")
    if extra_note:
        note_messages.append(str(extra_note))

    if note_messages:
        existing_notes = updated_candidate.get("notes", "")
        for message in note_messages:
            existing_notes = append_note(existing_notes, message)
        updated_candidate["notes"] = existing_notes

    return updated_candidate


def upsert_candidate(dataset_path: Path, candidate: dict) -> tuple[dict, str]:
    payload = load_candidate_dataset(dataset_path)
    candidates = payload["candidates"]

    for index, item in enumerate(candidates):
        if item["candidate_id"] == candidate["candidate_id"]:
            # 重复导入时保留人工维护状态，并把这次同步动作追加进备注。
            candidate["status"] = item.get("status", candidate["status"])
            candidate["notes"] = append_note(
                item.get("notes", ""),
                "重新同步 GitHub issue 元数据。",
            )
            candidates[index] = candidate
            write_candidate_dataset(dataset_path, payload)
            return candidate, "updated"

    candidates.append(candidate)
    write_candidate_dataset(dataset_path, payload)
    return candidate, "created"


def append_draft_note(dataset_path: Path, candidate_id: str) -> None:
    payload = load_candidate_dataset(dataset_path)
    for candidate in payload["candidates"]:
        if candidate["candidate_id"] == candidate_id:
            candidate["notes"] = append_note(
                candidate.get("notes", ""),
                "已生成 real_issue task 草稿，仍需人工补齐 repo_path、测试命令和目标文件。",
            )
            break
    write_candidate_dataset(dataset_path, payload)


def slugify(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return normalized or "real_issue"


def next_task_index(tasks_dir: Path) -> int:
    existing_numbers: list[int] = []
    for path in tasks_dir.glob("task_*.json"):
        suffix = path.stem.removeprefix("task_")
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    return max(existing_numbers, default=0) + 1


def build_task_payload(candidate: dict, repo_path: str, test_command: str) -> dict:
    task_index = next_task_index(REPO_ROOT / "benchmarks" / "tasks")
    task_id = f"task_{task_index:03d}"
    issue_title = candidate["issue_title"]
    issue_text = candidate.get("body_excerpt") or issue_title
    return {
        "task_id": task_id,
        "repo_name": candidate["repo_full_name"].split("/")[-1],
        "repo_path": repo_path,
        "issue_title": issue_title,
        "issue_text": issue_text,
        "test_command": test_command,
        "success_criteria": "补充真实仓库后，需要人工完善成功标准。",
        "difficulty": candidate.get("difficulty", "medium"),
        "tags": [
            "bugfix",
            "python",
            "real-issue",
            "draft",
        ],
        "target_files_hint": [],
        "expected_failure_test": None,
        "max_retries": 2,
        "source_type": "real_issue",
        "metadata": {
            "repo_full_name": candidate["repo_full_name"],
            "repo_url": candidate["repo_url"],
            "issue_number": candidate["issue_number"],
            "issue_url": candidate["issue_url"],
            "candidate_id": candidate["candidate_id"],
            "draft_status": "needs_manual_completion",
            "imported_from": "scripts/import_github_issue.py",
        },
    }


def write_task_payload(task_payload: dict) -> Path:
    task_path = REPO_ROOT / "benchmarks" / "tasks" / f"{task_payload['task_id']}.json"
    write_json(task_path, task_payload)
    return task_path


def import_issue(repo_full_name: str, issue_number: int) -> dict:
    issue_payload = run_gh_command(
        [
            "issue",
            "view",
            str(issue_number),
            "--repo",
            repo_full_name,
            "--json",
            "number,title,body,url,labels,state,createdAt",
        ]
    )
    return {
        "number": issue_payload["number"],
        "title": issue_payload["title"],
        "body": issue_payload.get("body", ""),
        "url": issue_payload["url"],
        "labels": issue_payload.get("labels", []),
        "state": issue_payload.get("state", "open"),
        "createdAt": issue_payload.get("createdAt"),
        "repository_url": f"https://github.com/{repo_full_name}",
    }


def import_issue_to_dataset(
    *,
    repo_full_name: str,
    issue_number: int,
    dataset_path: Path,
    issue_payload: dict | None = None,
    candidate_overrides: dict | None = None,
) -> dict:
    payload = issue_payload or import_issue(repo_full_name, issue_number)
    candidate = apply_candidate_overrides(
        build_candidate(repo_full_name, payload),
        candidate_overrides,
    )
    stored_candidate, operation = upsert_candidate(dataset_path, candidate)
    return {
        "candidate": stored_candidate,
        "operation": operation,
    }


def draft_task_for_candidate(
    *,
    candidate: dict,
    candidate_path: Path,
    repo_path: str,
    test_command: str,
) -> dict:
    task_payload = build_task_payload(candidate, repo_path, test_command)
    task_path = write_task_payload(task_payload)
    append_draft_note(candidate_path, candidate["candidate_id"])
    return {
        "task_payload": task_payload,
        "task_path": task_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="从 GitHub issue 导入候选信息并生成 task 草稿。")
    parser.add_argument("--repo", required=True, help="GitHub 仓库名，例如 psf/requests")
    parser.add_argument("--issue", required=True, type=int, help="Issue 编号")
    parser.add_argument(
        "--candidate-file",
        default="benchmarks/real_world_candidates.json",
        help="候选清单文件路径",
    )
    parser.add_argument(
        "--draft-task",
        action="store_true",
        help="是否同时生成 real_issue task 草稿",
    )
    parser.add_argument(
        "--repo-path",
        default="benchmarks/repos/real_issue_repo_placeholder",
        help="生成 task 草稿时使用的 repo_path 占位值",
    )
    parser.add_argument(
        "--test-command",
        default="python -m pytest -q",
        help="生成 task 草稿时使用的测试命令占位值",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    candidate_path = (REPO_ROOT / args.candidate_file).resolve()

    import_output = import_issue_to_dataset(
        repo_full_name=args.repo,
        issue_number=args.issue,
        dataset_path=candidate_path,
    )
    candidate = import_output["candidate"]

    print("=== Candidate Imported ===")
    print(f"candidate_id: {candidate['candidate_id']}")
    print(f"issue_title: {candidate['issue_title']}")
    print(f"issue_url: {candidate['issue_url']}")
    print(f"candidate_file: {candidate_path}")
    print(f"operation: {import_output['operation']}")

    if not args.draft_task:
        return 0

    draft_output = draft_task_for_candidate(
        candidate=candidate,
        candidate_path=candidate_path,
        repo_path=args.repo_path,
        test_command=args.test_command,
    )

    print("=== Draft Task Generated ===")
    print(f"task_id: {draft_output['task_payload']['task_id']}")
    print(f"task_path: {draft_output['task_path']}")
    print("draft_status: needs_manual_completion")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

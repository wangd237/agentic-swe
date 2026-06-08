"""从 real_issue 草稿生成 semi_real 任务脚手架。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.schemas.task_schema import Task, load_task


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def timestamp_note(message: str) -> str:
    # 备注统一带时间戳，方便后面回看 candidate 是怎么一步步推进的。
    return f"{datetime.now().isoformat(timespec='seconds')}: {message}"


def append_note(existing_notes: str, message: str) -> str:
    # 采用追加式记录，避免后来一次操作把前面的筛选信息抹掉。
    note_line = timestamp_note(message)
    if not existing_notes.strip():
        return note_line
    return f"{existing_notes.rstrip()}\n{note_line}"


def next_task_index(tasks_dir: Path) -> int:
    existing_numbers: list[int] = []
    for path in tasks_dir.glob("task_*.json"):
        suffix = path.stem.removeprefix("task_")
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    return max(existing_numbers, default=0) + 1


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    ensure_parent(path)
    path.write_text(content, encoding="utf-8")
    return True


def build_repo_scaffold(repo_root: Path, module_path: str, test_path: str) -> dict[str, str]:
    package_name = Path(module_path).parts[0]
    init_path = repo_root / package_name / "__init__.py"
    module_file = repo_root / module_path
    test_file = repo_root / test_path
    readme_path = repo_root / "README.md"

    write_text_if_missing(
        init_path,
        '"""semi_real 脚手架包。"""\n',
    )
    write_text_if_missing(
        module_file,
        '"""待根据真实 issue 还原的最小实现。"""\n\n'
        "# TODO: 按真实 issue 还原最小可复现逻辑。\n",
    )
    write_text_if_missing(
        test_file,
        "import unittest\n\n\n"
        "class GeneratedRegressionTests(unittest.TestCase):\n"
        '    """待根据真实 issue 补齐的回归测试。"""\n\n'
        "    def test_todo(self) -> None:\n"
        '        self.fail("TODO: 请根据真实 issue 补齐 semi_real 回归测试。")\n',
    )
    write_text_if_missing(
        readme_path,
        "# Semi-Real Scaffold\n\n"
        "这个目录由 `scripts/scaffold_semi_real_task.py` 自动生成。\n\n"
        "当前状态：\n\n"
        "- 已创建包目录、模块文件和测试文件\n"
        "- 仍需按真实 issue 手工还原最小 bug 场景\n"
        "- 完成后再把该任务加入正式 manifest\n",
    )

    return {
        "package_init": str(init_path.relative_to(repo_root)).replace("\\", "/"),
        "module_file": module_path,
        "test_file": test_path,
        "readme_file": "README.md",
    }


def normalize_tags(tags: list[str]) -> list[str]:
    ordered: list[str] = []
    for tag in tags:
        normalized = tag.strip()
        if normalized and normalized not in ordered:
            ordered.append(normalized)
    return ordered


def build_semi_real_task(
    draft_task: Task,
    repo_name: str,
    repo_path: str,
    module_path: str,
    test_path: str,
    ready: bool,
    success_criteria: str | None,
    expected_failure_test: str | None,
    extra_tags: list[str],
) -> dict:
    task_index = next_task_index(REPO_ROOT / "benchmarks" / "tasks")
    task_id = f"task_{task_index:03d}"

    tags = [tag for tag in draft_task.tags if tag not in {"draft", "real-issue"}]
    tags.append("semi-real")
    tags.extend(extra_tags)
    if not ready:
        tags.append("draft")

    metadata = dict(draft_task.metadata)
    metadata.update(
        {
            "phase_introduced": "phase_6",
            "derived_from_task": draft_task.task_id,
            "scaffolded_from": "scripts/scaffold_semi_real_task.py",
            "repo_scaffold_status": "ready" if ready else "needs_manual_completion",
        }
    )

    if not ready:
        metadata["draft_status"] = "needs_manual_completion"
    else:
        metadata.pop("draft_status", None)

    return {
        "task_id": task_id,
        "repo_name": repo_name,
        "repo_path": repo_path,
        "issue_title": draft_task.issue_title,
        "issue_text": draft_task.issue_text,
        "test_command": draft_task.test_command
        if draft_task.repo_path != "benchmarks/repos/real_issue_repo_placeholder"
        else f"python -m pytest {test_path} -q",
        "success_criteria": success_criteria or "待补充 semi_real 任务成功标准。",
        "difficulty": draft_task.difficulty,
        "tags": normalize_tags(tags),
        "target_files_hint": [module_path, test_path],
        "expected_failure_test": expected_failure_test if ready else None,
        "max_retries": draft_task.max_retries,
        "source_type": "semi_real",
        "metadata": metadata,
    }


def append_task_to_manifest(manifest_path: Path, task_path: Path) -> None:
    payload = read_json(manifest_path)
    task_entry = str(task_path.relative_to(REPO_ROOT)).replace("\\", "/")
    if task_entry not in payload["tasks"]:
        payload["tasks"].append(task_entry)
        write_json(manifest_path, payload)


def update_candidate_status(
    candidate_path: Path,
    candidate_id: str,
    status: str,
    note: str,
) -> None:
    payload = read_json(candidate_path)
    for candidate in payload.get("candidates", []):
        if candidate.get("candidate_id") != candidate_id:
            continue
        candidate["status"] = status
        candidate["notes"] = append_note(candidate.get("notes", ""), note)
        write_json(candidate_path, payload)
        return
    raise RuntimeError(f"未找到 candidate_id={candidate_id} 对应的候选记录。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="从 real_issue 草稿生成 semi_real 任务脚手架。")
    parser.add_argument("--draft-task", required=True, help="real_issue 草稿任务路径")
    parser.add_argument("--semi-repo-name", required=True, help="semi_real 本地仓库名")
    parser.add_argument(
        "--module-path",
        required=True,
        help="仓库内模块文件相对路径，例如 requests_encoding_repo/utils.py",
    )
    parser.add_argument(
        "--test-path",
        required=True,
        help="仓库内测试文件相对路径，例如 tests/test_utils.py",
    )
    parser.add_argument(
        "--candidate-file",
        default="benchmarks/real_world_candidates.json",
        help="候选清单路径",
    )
    parser.add_argument(
        "--manifest",
        default="benchmarks/manifests/real_issue_tasks.json",
        help="ready 模式下要追加的 manifest",
    )
    parser.add_argument(
        "--success-criteria",
        default=None,
        help="任务成功标准；不传时写入占位文案",
    )
    parser.add_argument(
        "--expected-failure-test",
        default=None,
        help="ready 模式下可填写预期失败测试名",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="补充标签，可重复传入",
    )
    parser.add_argument(
        "--ready",
        action="store_true",
        help="标记为可运行任务，并自动追加到 manifest",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    draft_task_path = (REPO_ROOT / args.draft_task).resolve()
    draft_task = load_task(draft_task_path)
    if draft_task.source_type != "real_issue":
        raise RuntimeError("只有 real_issue 草稿任务才能生成 semi_real 脚手架。")

    repo_root = REPO_ROOT / "benchmarks" / "repos" / args.semi_repo_name
    scaffold_files = build_repo_scaffold(repo_root, args.module_path, args.test_path)

    task_payload = build_semi_real_task(
        draft_task=draft_task,
        repo_name=args.semi_repo_name,
        repo_path=str(repo_root.relative_to(REPO_ROOT)).replace("\\", "/"),
        module_path=args.module_path,
        test_path=args.test_path,
        ready=args.ready,
        success_criteria=args.success_criteria,
        expected_failure_test=args.expected_failure_test,
        extra_tags=args.tag,
    )
    task_path = REPO_ROOT / "benchmarks" / "tasks" / f"{task_payload['task_id']}.json"
    write_json(task_path, task_payload)

    candidate_id = draft_task.metadata.get("candidate_id")
    candidate_path = (REPO_ROOT / args.candidate_file).resolve()
    if candidate_id:
        candidate_status = "accepted" if args.ready else "scaffolded"
        update_candidate_status(
            candidate_path,
            candidate_id,
            candidate_status,
            (
                f"已生成 semi_real {'可运行任务' if args.ready else '脚手架'} "
                f"{task_payload['task_id']}，仓库目录为 benchmarks/repos/{args.semi_repo_name}。"
            ),
        )

    if args.ready:
        manifest_path = (REPO_ROOT / args.manifest).resolve()
        append_task_to_manifest(manifest_path, task_path)

    print("=== Semi-Real Scaffold Generated ===")
    print(f"draft_task: {draft_task_path}")
    print(f"semi_real_task: {task_path}")
    print(f"repo_root: {repo_root}")
    print(f"module_file: {scaffold_files['module_file']}")
    print(f"test_file: {scaffold_files['test_file']}")
    print(f"ready: {args.ready}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

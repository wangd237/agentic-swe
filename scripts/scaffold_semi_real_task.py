"""从 real_issue 草稿生成 semi_real 任务脚手架。"""

from __future__ import annotations

import argparse
import json
import re
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


def build_repo_scaffold(
    repo_root: Path,
    module_path: str,
    test_path: str,
    *,
    module_content: str | None = None,
    test_content: str | None = None,
    readme_content: str | None = None,
) -> dict[str, str]:
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
        module_content
        or (
            '"""待根据真实 issue 还原的最小实现。"""\n\n'
            "# TODO: 按真实 issue 还原最小可复现逻辑。\n"
        ),
    )
    write_text_if_missing(
        test_file,
        test_content
        or (
            "import unittest\n\n\n"
            "class GeneratedRegressionTests(unittest.TestCase):\n"
            '    """待根据真实 issue 补齐的回归测试。"""\n\n'
            "    def test_todo(self) -> None:\n"
            '        self.fail("TODO: 请根据真实 issue 补齐 semi_real 回归测试。")\n'
        ),
    )
    write_text_if_missing(
        readme_path,
        readme_content
        or (
            "# Semi-Real Scaffold\n\n"
            "这个目录由 `scripts/scaffold_semi_real_task.py` 自动生成。\n\n"
            "当前状态：\n\n"
            "- 已创建包目录、模块文件和测试文件\n"
            "- 仍需按真实 issue 手工还原最小 bug 场景\n"
            "- 完成后再把该任务加入正式 manifest\n"
        ),
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


def find_candidate(candidate_path: Path, candidate_id: str) -> dict:
    payload = read_json(candidate_path)
    for candidate in payload.get("candidates", []):
        if candidate.get("candidate_id") == candidate_id:
            return candidate
    raise RuntimeError(f"未找到 candidate_id={candidate_id} 对应的候选记录。")


def ensure_candidate_ready_for_scaffold(candidate: dict, *, dry_run: bool) -> None:
    # dry-run 允许先看自动推断结果，真正落盘前再要求候选经过人工筛选。
    if dry_run:
        return
    current_status = str(candidate.get("status", "")).strip()
    if current_status not in {"screened", "accepted"}:
        raise RuntimeError(
            "只有状态为 screened 或 accepted 的候选才能生成 semi_real 脚手架；"
            f"当前 `{candidate.get('candidate_id')}` 的状态为 `{current_status or 'unknown'}`。"
        )


def task_number(task_id: str) -> int:
    suffix = task_id.removeprefix("task_")
    return int(suffix) if suffix.isdigit() else -1


def find_latest_real_issue_task(candidate_id: str) -> Task | None:
    tasks_dir = REPO_ROOT / "benchmarks" / "tasks"
    matched_tasks: list[Task] = []
    for task_path in tasks_dir.glob("task_*.json"):
        task = load_task(task_path)
        if task.source_type != "real_issue":
            continue
        if task.metadata.get("candidate_id") != candidate_id:
            continue
        matched_tasks.append(task)

    if not matched_tasks:
        return None
    matched_tasks.sort(key=lambda item: task_number(item.task_id), reverse=True)
    return matched_tasks[0]


def sanitize_tag(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return normalized


def infer_package_name(candidate: dict, semi_repo_name: str) -> str:
    repo_tail = candidate["repo_full_name"].split("/")[-1].replace("-", "_").strip()
    if repo_tail:
        return repo_tail
    return semi_repo_name


def infer_semi_repo_name(candidate: dict) -> str:
    repo_tail = candidate["repo_full_name"].split("/")[-1].replace("-", "_")
    return f"{repo_tail}_{candidate['issue_number']}_repo"


def extract_file_paths(text: str) -> list[str]:
    file_pattern = re.compile(
        r"(?:^|[\s`'\"(])(?P<path>(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:py|pyi|toml|json|txt|md))(?:$|[\s`'\":),])"
    )
    results: list[str] = []
    for match in file_pattern.finditer(text):
        path = match.group("path")
        if path not in results:
            results.append(path)
    return results


def strip_urls(text: str) -> str:
    return re.sub(r"https?://\S+", " ", text)


def extract_github_repo_paths(text: str, repo_full_name: str) -> list[str]:
    owner, repo = repo_full_name.split("/", 1)
    pattern = re.compile(
        rf"https?://github\.com/{re.escape(owner)}/{re.escape(repo)}/(?:blob|tree)/[^/\s]+/(?P<path>[A-Za-z0-9_./-]+\.(?:py|pyi|toml|json|txt|md))"
    )
    results: list[str] = []
    for match in pattern.finditer(text):
        path = match.group("path").strip()
        if path not in results:
            results.append(path)
    return results


def extract_python_symbol_paths(text: str, package_name: str) -> list[str]:
    # 当 issue 只给出 Python 符号而没有显式文件路径时，尝试把 `module.func` 还原成模块文件。
    symbol_pattern = re.compile(r"\b(?P<symbol>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)\b")
    inferred_paths: list[str] = []
    for match in symbol_pattern.finditer(text):
        symbol = match.group("symbol")
        parts = symbol.split(".")
        if len(parts) < 2:
            continue
        module_parts = parts[:-1]
        if not module_parts:
            continue
        # 过滤 Python 版本号等误命中场景。
        if all(part.isdigit() for part in module_parts):
            continue
        candidate_path = f"{package_name}/{'/'.join(module_parts)}.py"
        if candidate_path not in inferred_paths:
            inferred_paths.append(candidate_path)
    return inferred_paths


def infer_target_paths(candidate: dict, semi_repo_name: str, issue_text: str) -> tuple[str, str]:
    expected_target_files = [str(path) for path in candidate.get("expected_target_files", []) if str(path).strip()]
    package_name = infer_package_name(candidate, semi_repo_name)
    repo_url_paths = extract_github_repo_paths(issue_text, candidate["repo_full_name"]) or extract_github_repo_paths(
        candidate.get("body_excerpt", ""),
        candidate["repo_full_name"],
    )
    cleaned_issue_text = strip_urls(issue_text)
    cleaned_body_excerpt = strip_urls(candidate.get("body_excerpt", ""))
    symbol_paths = extract_python_symbol_paths(cleaned_issue_text, package_name) or extract_python_symbol_paths(
        cleaned_body_excerpt,
        package_name,
    )
    discovered_paths = (
        expected_target_files
        or repo_url_paths
        or extract_file_paths(cleaned_issue_text)
        or extract_file_paths(cleaned_body_excerpt)
        or symbol_paths
    )

    module_path: str | None = None
    test_path: str | None = None
    for path in discovered_paths:
        normalized = path.strip().lstrip("./")
        lower = normalized.lower()
        if "test" in lower and test_path is None:
            test_path = normalized
            continue
        root_level_name = Path(normalized).name.lower()
        if root_level_name in {
            "fail_case.py",
            "example.py",
            "repro.py",
            "reproducer.py",
            "foobar.py",
            "main.py",
            "app.py",
            "demo.py",
            "run.py",
            "script.py",
            "rich_script.py",
        } and "/" not in normalized and "\\" not in normalized or (
            root_level_name.endswith("_script.py") and "/" not in normalized and "\\" not in normalized
        ):
            # 这类路径更像 issue 里的最小复现脚本，不应优先当成仓库目标模块。
            if test_path is None:
                test_path = f"tests/test_{Path(normalized).stem}.py"
            continue
        if normalized.endswith(".py") and module_path is None:
            module_path = normalized

    if module_path is None:
        # 当 issue 只暴露测试线索时，优先回退到包内默认模块，避免把仓库目录名误当成 Python 包名。
        module_path = f"{package_name}/module.py"

    if test_path is None:
        test_stem = Path(module_path).stem
        test_path = f"tests/test_{test_stem}.py"

    return module_path.replace("\\", "/"), test_path.replace("\\", "/")


def infer_success_criteria(candidate: dict, module_path: str) -> str:
    title = str(candidate.get("issue_title", "")).strip()
    return (
        f"应修复 issue《{title}》中描述的错误行为；核心逻辑预计位于 `{module_path}`；"
        "并补齐 1 到 3 个稳定回归测试，确保当前错误行为消失且相邻边界不回归。"
    )


def infer_extra_tags(candidate: dict) -> list[str]:
    repo_tail = candidate["repo_full_name"].split("/")[-1].replace("-", "_").lower()
    tags = ["auto-scaffolded", repo_tail]
    for label in candidate.get("labels", []):
        normalized = sanitize_tag(str(label))
        if normalized:
            tags.append(normalized)
    return normalize_tags(tags)


def extract_code_blocks(text: str) -> list[dict[str, str]]:
    pattern = re.compile(r"```(?P<language>[^\n`]*)\n(?P<code>.*?)```", re.DOTALL)
    blocks: list[dict[str, str]] = []
    for match in pattern.finditer(text):
        blocks.append(
            {
                "language": match.group("language").strip(),
                "code": match.group("code").rstrip(),
            }
        )
    return blocks


def build_generated_module_content(candidate: dict, module_path: str) -> str:
    return (
        '"""待根据真实 issue 还原的最小实现。"""\n\n'
        f"# issue: {candidate['repo_full_name']}#{candidate['issue_number']}\n"
        f"# target_hint: {module_path}\n"
        "# TODO: review and adjust — auto-inferred from candidate metadata.\n"
        "# TODO: 请根据真实 issue 还原最小可复现逻辑。\n"
    )


def build_generated_test_content(candidate: dict, issue_text: str) -> str:
    code_blocks = extract_code_blocks(issue_text)
    snippet_lines = []
    if code_blocks:
        snippet_lines.append("ISSUE_SNIPPETS = [")
        for block in code_blocks[:3]:
            snippet_lines.append("    {")
            snippet_lines.append(f'        "language": {block["language"]!r},')
            snippet_lines.append(f'        "code": {block["code"]!r},')
            snippet_lines.append("    },")
        snippet_lines.append("]\n")
    else:
        snippet_lines.append("ISSUE_SNIPPETS = []\n")

    return (
        "import unittest\n\n\n"
        f"# issue: {candidate['repo_full_name']}#{candidate['issue_number']}\n"
        "# TODO: review and adjust — auto-extracted from issue body.\n"
        + "\n".join(snippet_lines)
        + "\n"
        "class GeneratedRegressionTests(unittest.TestCase):\n"
        '    """待根据真实 issue 补齐的回归测试。"""\n\n'
        "    def test_todo(self) -> None:\n"
        '        self.fail("TODO: review and adjust — auto-extracted from issue body. 请把 issue 描述压成稳定回归测试。")\n'
    )


def build_generated_readme(candidate: dict, module_path: str, test_path: str) -> str:
    return (
        "# Semi-Real Scaffold\n\n"
        "这个目录由 `scripts/scaffold_semi_real_task.py --from-candidate` 自动生成。\n\n"
        "当前候选：\n\n"
        f"- repo: `{candidate['repo_full_name']}`\n"
        f"- issue: `#{candidate['issue_number']}`\n"
        f"- title: `{candidate['issue_title']}`\n"
        f"- inferred module_path: `{module_path}`\n"
        f"- inferred test_path: `{test_path}`\n\n"
        "接下来需要：\n\n"
        "- 人工 review 自动推断出的模块与测试路径\n"
        "- 按真实 issue 还原最小 bug 场景\n"
        "- 把 TODO 测试改成稳定回归测试\n"
        "- 完成后再把该任务加入正式 manifest\n"
    )


def build_draft_task_from_candidate(candidate: dict) -> Task:
    payload = {
        "task_id": "task_000",
        "repo_name": candidate["repo_full_name"].split("/")[-1],
        "repo_path": "benchmarks/repos/real_issue_repo_placeholder",
        "issue_title": candidate["issue_title"],
        "issue_text": candidate.get("body_excerpt") or candidate["issue_title"],
        "test_command": "python -m pytest -q",
        "success_criteria": "补充真实仓库后，需要人工完善成功标准。",
        "difficulty": candidate.get("difficulty", "medium"),
        "tags": ["bugfix", "python", "real-issue", "draft"],
        "target_files_hint": candidate.get("expected_target_files", []),
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
            "imported_from": "scripts/scaffold_semi_real_task.py",
        },
    }
    return Task.model_validate(payload)


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
    parser.add_argument("--draft-task", default=None, help="real_issue 草稿任务路径")
    parser.add_argument("--from-candidate", default=None, help="直接从 candidate_id 自动推断脚手架参数")
    parser.add_argument("--semi-repo-name", default=None, help="semi_real 本地仓库名")
    parser.add_argument(
        "--module-path",
        default=None,
        help="仓库内模块文件相对路径，例如 requests_encoding_repo/utils.py",
    )
    parser.add_argument(
        "--test-path",
        default=None,
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印自动推断结果，不写入任务、repo 脚手架或 candidate 状态。",
    )
    return parser


def resolve_scaffold_inputs(args: argparse.Namespace) -> dict:
    candidate_path = (REPO_ROOT / args.candidate_file).resolve()
    if args.from_candidate:
        candidate = find_candidate(candidate_path, args.from_candidate)
        ensure_candidate_ready_for_scaffold(candidate, dry_run=args.dry_run)
        draft_task = find_latest_real_issue_task(args.from_candidate) or build_draft_task_from_candidate(candidate)
        semi_repo_name = args.semi_repo_name or infer_semi_repo_name(candidate)
        module_path, test_path = infer_target_paths(candidate, semi_repo_name, draft_task.issue_text)
        module_path = args.module_path or module_path
        test_path = args.test_path or test_path
        success_criteria = args.success_criteria or infer_success_criteria(candidate, module_path)
        extra_tags = normalize_tags(list(args.tag) + infer_extra_tags(candidate))
        return {
            "mode": "from-candidate",
            "candidate": candidate,
            "candidate_path": candidate_path,
            "candidate_current_status": candidate.get("status"),
            "draft_task": draft_task,
            "semi_repo_name": semi_repo_name,
            "module_path": module_path,
            "test_path": test_path,
            "success_criteria": success_criteria,
            "expected_failure_test": args.expected_failure_test,
            "extra_tags": extra_tags,
        }

    if not args.draft_task:
        raise RuntimeError("手工模式下必须提供 --draft-task，或改用 --from-candidate。")
    if not args.semi_repo_name or not args.module_path or not args.test_path:
        raise RuntimeError("手工模式下必须提供 --semi-repo-name、--module-path 和 --test-path。")

    draft_task_path = (REPO_ROOT / args.draft_task).resolve()
    draft_task = load_task(draft_task_path)
    return {
        "mode": "manual",
        "candidate": None,
        "candidate_path": candidate_path,
        "candidate_current_status": None,
        "draft_task": draft_task,
        "semi_repo_name": args.semi_repo_name,
        "module_path": args.module_path,
        "test_path": args.test_path,
        "success_criteria": args.success_criteria,
        "expected_failure_test": args.expected_failure_test,
        "extra_tags": args.tag,
    }


def main() -> int:
    args = build_parser().parse_args()
    resolved = resolve_scaffold_inputs(args)
    draft_task = resolved["draft_task"]
    if draft_task.source_type != "real_issue":
        raise RuntimeError("只有 real_issue 草稿任务才能生成 semi_real 脚手架。")

    repo_root = REPO_ROOT / "benchmarks" / "repos" / resolved["semi_repo_name"]
    candidate = resolved["candidate"]
    task_payload = build_semi_real_task(
        draft_task=draft_task,
        repo_name=resolved["semi_repo_name"],
        repo_path=str(repo_root.relative_to(REPO_ROOT)).replace("\\", "/"),
        module_path=resolved["module_path"],
        test_path=resolved["test_path"],
        ready=args.ready,
        success_criteria=resolved["success_criteria"],
        expected_failure_test=resolved["expected_failure_test"],
        extra_tags=resolved["extra_tags"],
    )
    task_path = REPO_ROOT / "benchmarks" / "tasks" / f"{task_payload['task_id']}.json"

    module_content = None
    test_content = None
    readme_content = None
    if candidate is not None:
        module_content = build_generated_module_content(candidate, resolved["module_path"])
        test_content = build_generated_test_content(candidate, draft_task.issue_text)
        readme_content = build_generated_readme(candidate, resolved["module_path"], resolved["test_path"])

    if not args.dry_run:
        scaffold_files = build_repo_scaffold(
            repo_root,
            resolved["module_path"],
            resolved["test_path"],
            module_content=module_content,
            test_content=test_content,
            readme_content=readme_content,
        )
        write_json(task_path, task_payload)
    else:
        scaffold_files = {
            "module_file": resolved["module_path"],
            "test_file": resolved["test_path"],
        }

    candidate_id = draft_task.metadata.get("candidate_id")
    candidate_path = resolved["candidate_path"]
    if candidate_id and not args.dry_run:
        current_status = candidate.get("status") if candidate is not None else None
        if args.ready:
            candidate_status = "accepted"
        elif current_status in {"accepted", "completed", "screened"}:
            candidate_status = current_status
        else:
            candidate_status = "imported"
        update_candidate_status(
            candidate_path,
            candidate_id,
            candidate_status,
            (
                f"已生成 semi_real {'可运行任务' if args.ready else '脚手架'} "
                f"{task_payload['task_id']}，仓库目录为 benchmarks/repos/{resolved['semi_repo_name']}。"
            ),
        )

    if args.ready and not args.dry_run:
        manifest_path = (REPO_ROOT / args.manifest).resolve()
        append_task_to_manifest(manifest_path, task_path)

    print("=== Semi-Real Scaffold Generated ===")
    print(f"mode: {resolved['mode']}")
    print(f"draft_task: {draft_task.task_id}")
    print(f"semi_real_task: {task_path}")
    print(f"repo_root: {repo_root}")
    print(f"module_file: {scaffold_files['module_file']}")
    print(f"test_file: {scaffold_files['test_file']}")
    print(f"ready: {args.ready}")
    print(f"dry_run: {args.dry_run}")
    if args.dry_run:
        print("candidate_status_update: skipped")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

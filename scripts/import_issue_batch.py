"""批量导入 GitHub issue 候选，并可选生成 task 草稿。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import import_github_issue


def parse_issue_number(raw_value: object) -> int:
    text = str(raw_value).strip()
    if text.startswith("#"):
        text = text[1:]
    if not text.isdigit():
        raise ValueError(f"无效的 issue 编号：{raw_value}")
    return int(text)


def load_batch_entries(input_path: Path) -> list[dict]:
    if input_path.suffix.lower() == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            raw_entries = payload.get("issues", [])
        else:
            raw_entries = payload
        entries: list[dict] = []
        for item in raw_entries:
            if not isinstance(item, dict):
                raise ValueError("JSON 批量导入文件中的每一项都必须是对象。")
            entries.append(
                {
                    "repo": item["repo"],
                    "issue": parse_issue_number(item["issue"]),
                    "draft_task": bool(item.get("draft_task", False)),
                    "repo_path": item.get("repo_path"),
                    "test_command": item.get("test_command"),
                    "candidate_overrides": item.get("candidate_overrides")
                    or {
                        key: item[key]
                        for key in (
                            "status",
                            "difficulty",
                            "why_it_fits",
                            "expected_target_files",
                            "expected_test_shape",
                            "risk_notes",
                            "recommendation",
                            "note",
                        )
                        if key in item
                    },
                }
            )
        return entries

    entries = []
    for line_number, raw_line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            raise ValueError(f"第 {line_number} 行格式无效，期望为 'owner/repo issue_number'。")
        entries.append(
            {
                "repo": parts[0],
                "issue": parse_issue_number(parts[1]),
                "draft_task": False,
                "repo_path": None,
                "test_command": None,
                "candidate_overrides": None,
            }
        )
    return entries


def import_issue_batch(
    *,
    input_path: Path,
    candidate_file: Path,
    draft_task: bool,
    repo_path: str,
    test_command: str,
) -> dict:
    entries = load_batch_entries(input_path)
    results: list[dict] = []

    for entry in entries:
        issue_output = import_github_issue.import_issue_to_dataset(
            repo_full_name=entry["repo"],
            issue_number=entry["issue"],
            dataset_path=candidate_file,
            candidate_overrides=entry.get("candidate_overrides"),
        )
        result_item = {
            "repo": entry["repo"],
            "issue": entry["issue"],
            "candidate_id": issue_output["candidate"]["candidate_id"],
            "operation": issue_output["operation"],
            "candidate_status": issue_output["candidate"]["status"],
            "draft_task_generated": False,
        }

        should_draft = draft_task or entry.get("draft_task", False)
        if should_draft:
            draft_output = import_github_issue.draft_task_for_candidate(
                candidate=issue_output["candidate"],
                candidate_path=candidate_file,
                repo_path=entry.get("repo_path") or repo_path,
                test_command=entry.get("test_command") or test_command,
            )
            result_item["draft_task_generated"] = True
            result_item["task_id"] = draft_output["task_payload"]["task_id"]
            result_item["task_path"] = str(draft_output["task_path"])

        results.append(result_item)

    created_count = sum(1 for item in results if item["operation"] == "created")
    updated_count = sum(1 for item in results if item["operation"] == "updated")
    draft_task_count = sum(1 for item in results if item["draft_task_generated"])
    return {
        "input_path": str(input_path),
        "candidate_file": str(candidate_file),
        "total_count": len(results),
        "created_count": created_count,
        "updated_count": updated_count,
        "draft_task_count": draft_task_count,
        "results": results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量导入 GitHub issue 候选，并可选生成 task 草稿。")
    parser.add_argument("--input", required=True, help="批量导入文件，支持 txt 或 json")
    parser.add_argument(
        "--candidate-file",
        default="benchmarks/real_world_candidates.json",
        help="候选清单文件路径",
    )
    parser.add_argument(
        "--draft-task",
        action="store_true",
        help="是否为所有导入项生成 real_issue task 草稿",
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
    output = import_issue_batch(
        input_path=(REPO_ROOT / args.input).resolve(),
        candidate_file=(REPO_ROOT / args.candidate_file).resolve(),
        draft_task=args.draft_task,
        repo_path=args.repo_path,
        test_command=args.test_command,
    )

    print("=== Issue Batch Import Summary ===")
    print(f"input_path: {output['input_path']}")
    print(f"candidate_file: {output['candidate_file']}")
    print(f"total_count: {output['total_count']}")
    print(f"created_count: {output['created_count']}")
    print(f"updated_count: {output['updated_count']}")
    print(f"draft_task_count: {output['draft_task_count']}")
    for item in output["results"]:
        task_id = item.get("task_id", "None")
        print(
            f"- {item['repo']}#{item['issue']} -> {item['candidate_id']} "
            f"(operation: {item['operation']}, status: {item['candidate_status']}, "
            f"draft_task_generated: {item['draft_task_generated']}, task_id: {task_id})"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

"""校验 benchmark 任务定义和真实 issue 候选清单。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.schemas.task_schema import load_task


def validate_task_files(tasks_dir: Path) -> list[str]:
    # 逐个用 schema 校验任务文件，输出可读错误列表。
    errors: list[str] = []
    for task_path in sorted(tasks_dir.glob("task_*.json")):
        try:
            task = load_task(task_path)
        except Exception as error:  # noqa: BLE001
            errors.append(f"{task_path.name}: schema 校验失败 -> {error}")
            continue

        if task.source_type not in {"synthetic", "semi_real", "real_issue"}:
            errors.append(
                f"{task_path.name}: source_type 必须是 synthetic / semi_real / real_issue 之一。"
            )

        if task.source_type != "synthetic":
            required_metadata_keys = {"repo_url", "issue_url"}
            missing_keys = sorted(required_metadata_keys - set(task.metadata))
            if missing_keys:
                errors.append(
                    f"{task_path.name}: 非 synthetic 任务必须在 metadata 中提供 {', '.join(missing_keys)}。"
                )
    return errors


def validate_candidate_file(candidate_path: Path) -> list[str]:
    # 候选清单先做最小结构检查，避免后续人工补充时格式漂移。
    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    if "candidates" not in payload or not isinstance(payload["candidates"], list):
        errors.append("real_world_candidates.json: 缺少 candidates 列表。")
        return errors

    for index, candidate in enumerate(payload["candidates"], start=1):
        for key in [
            "candidate_id",
            "repo_full_name",
            "repo_url",
            "issue_number",
            "issue_title",
            "issue_url",
            "language",
            "status",
            "notes",
        ]:
            if key not in candidate:
                errors.append(f"candidate #{index}: 缺少字段 `{key}`。")

        if candidate.get("status") not in {
            "to_review",
            "accepted",
            "rejected",
            "drafted",
        }:
            errors.append(
                f"candidate #{index}: status 必须是 to_review / accepted / rejected / drafted 之一。"
            )
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="校验任务定义和真实 issue 候选清单。")
    parser.add_argument(
        "--tasks-dir",
        default="benchmarks/tasks",
        help="任务目录，默认 benchmarks/tasks",
    )
    parser.add_argument(
        "--candidate-file",
        default="benchmarks/real_world_candidates.json",
        help="真实 issue 候选清单路径",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    tasks_dir = (REPO_ROOT / args.tasks_dir).resolve()
    candidate_file = (REPO_ROOT / args.candidate_file).resolve()

    errors = validate_task_files(tasks_dir)
    if candidate_file.exists():
        errors.extend(validate_candidate_file(candidate_file))

    if errors:
        print("=== Validation Failed ===")
        for error in errors:
            print(f"- {error}")
        return 1

    print("=== Validation Passed ===")
    print(f"validated_tasks_dir: {tasks_dir}")
    print(f"validated_candidate_file: {candidate_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

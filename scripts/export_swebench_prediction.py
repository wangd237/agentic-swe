"""Export one agent run patch as a SWE-bench prediction JSONL row."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.schemas.task_schema import load_task


def build_prediction_row(
    *,
    task_path: Path,
    run_dir: Path,
    model_name_or_path: str,
    patch_path: Path | None = None,
) -> dict[str, Any]:
    task = load_task(task_path)
    instance_id = task.metadata.get("swebench_instance_id")
    if task.source_type != "swe_bench_lite" or not instance_id:
        raise RuntimeError(f"任务不是 SWE-bench Lite 导入任务，缺少 metadata.swebench_instance_id: {task_path}")

    resolved_patch_path = patch_path or run_dir / "patch.diff"
    if not resolved_patch_path.exists():
        raise RuntimeError(f"未找到 agent run patch.diff: {resolved_patch_path}")
    model_patch = resolved_patch_path.read_text(encoding="utf-8")
    if not model_patch.strip():
        raise RuntimeError(f"patch.diff 为空，无法导出 SWE-bench prediction: {resolved_patch_path}")

    return {
        "instance_id": str(instance_id),
        "model_name_or_path": model_name_or_path,
        "model_patch": model_patch,
    }


def write_prediction_jsonl(row: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="将一次 agent run 的 patch.diff 导出为 SWE-bench prediction JSONL。")
    parser.add_argument("--task", type=Path, required=True, help="本项目 SWE-bench Lite task JSON 路径。")
    parser.add_argument("--run-dir", type=Path, required=True, help="agent run 目录，默认读取其中的 patch.diff。")
    parser.add_argument("--output", type=Path, required=True, help="输出 JSONL 路径。")
    parser.add_argument("--model-name", default="agentic-swe-local", help="写入 model_name_or_path 的名称。")
    parser.add_argument("--patch", type=Path, default=None, help="可选：显式指定 patch 文件路径。")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    row = build_prediction_row(
        task_path=args.task,
        run_dir=args.run_dir,
        model_name_or_path=args.model_name,
        patch_path=args.patch,
    )
    write_prediction_jsonl(row, args.output)
    print(f"exported prediction: {args.output}")
    print(f"instance_id: {row['instance_id']}")
    print(f"patch_chars: {len(row['model_patch'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

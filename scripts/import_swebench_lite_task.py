"""Import one SWE-bench Lite instance as a lightweight local agent task."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from app.schemas.task_schema import build_task


DATASET_NAME = "princeton-nlp/SWE-bench_Lite"
DEFAULT_CONFIG = "default"
DEFAULT_SPLIT = "dev"


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_").lower()
    return normalized or "swebench_lite_instance"


def diff_paths(diff_text: str) -> list[str]:
    paths: list[str] = []
    for match in re.finditer(r"^diff --git a/(.+?) b/(.+?)$", diff_text, flags=re.MULTILINE):
        for path in match.groups():
            if path not in paths and not path.startswith("tests/"):
                paths.append(path)
    return paths


def parse_json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [str(item) for item in payload]


def build_pytest_command(instance: dict[str, Any]) -> str:
    fail_to_pass = parse_json_list(instance.get("FAIL_TO_PASS"))
    if fail_to_pass:
        return "python -m pytest -q " + " ".join(fail_to_pass)
    return "python -m pytest -q"


def load_instance_from_json_path(path: Path, *, index: int, instance_id: str | None = None) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        payload = json.loads(text)
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict) and isinstance(payload.get("instances"), list):
            rows = payload["instances"]
        else:
            rows = [payload]

    if instance_id:
        for row in rows:
            if row.get("instance_id") == instance_id:
                return row
        raise RuntimeError(f"本地数据中未找到 instance_id={instance_id}")
    if index < 0 or index >= len(rows):
        raise RuntimeError(f"index 超出范围: {index}; 本地数据共有 {len(rows)} 条")
    return rows[index]


def load_instance_from_hf_rows_api(
    *,
    split: str,
    index: int,
    instance_id: str | None = None,
    config: str = DEFAULT_CONFIG,
) -> dict[str, Any]:
    if instance_id:
        # rows API does not provide direct lookup; fetch a small dev split window and filter.
        offset = 0
        length = 100
    else:
        offset = index
        length = 1

    query = urlencode(
        {
            "dataset": DATASET_NAME,
            "config": config,
            "split": split,
            "offset": offset,
            "length": length,
        }
    )
    url = f"https://datasets-server.huggingface.co/rows?{query}"
    with urlopen(url, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    rows = [item["row"] for item in payload.get("rows", [])]
    if instance_id:
        for row in rows:
            if row.get("instance_id") == instance_id:
                return row
        raise RuntimeError(f"{split} split 前 {length} 条中未找到 instance_id={instance_id}")
    if not rows:
        raise RuntimeError(f"未从 HuggingFace rows API 读取到 SWE-bench Lite 数据: {url}")
    return rows[0]


def build_task_payload(instance: dict[str, Any], *, repo_relative_path: str, task_id: str) -> dict[str, Any]:
    instance_id = str(instance["instance_id"])
    repo_full_name = str(instance["repo"])
    problem_statement = str(instance.get("problem_statement", "")).strip()
    hints_text = str(instance.get("hints_text", "") or "").strip()
    patch_text = str(instance.get("patch", "") or "")
    test_patch_text = str(instance.get("test_patch", "") or "")
    fail_to_pass = parse_json_list(instance.get("FAIL_TO_PASS"))
    pass_to_pass = parse_json_list(instance.get("PASS_TO_PASS"))
    target_files_hint = diff_paths(patch_text) or diff_paths(test_patch_text)
    issue_text = problem_statement
    if hints_text:
        issue_text = f"{issue_text}\n\nHints from SWE-bench:\n{hints_text}"

    return {
        "task_id": task_id,
        "repo_name": slugify(repo_full_name),
        "repo_path": repo_relative_path.replace("\\", "/"),
        "issue_title": f"SWE-bench Lite: {instance_id}",
        "issue_text": issue_text,
        "test_command": build_pytest_command(instance),
        "success_criteria": (
            "Lightweight smoke run: generate a patch for this SWE-bench Lite instance. "
            "Official scoring still requires SWE-bench harness evaluation."
        ),
        "difficulty": "medium",
        "tags": ["swe-bench", "swe-bench-lite", "real-issue", "python"],
        "target_files_hint": target_files_hint,
        "source_type": "swe_bench_lite",
        "metadata": {
            "swebench_dataset": DATASET_NAME,
            "swebench_instance_id": instance_id,
            "repo_full_name": repo_full_name,
            "base_commit": instance.get("base_commit"),
            "version": instance.get("version"),
            "created_at": instance.get("created_at"),
            "fail_to_pass": fail_to_pass,
            "pass_to_pass": pass_to_pass,
            "official_harness_required": True,
        },
    }


def run_git(args: list[str], *, cwd: Path) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} 失败: {detail}")


def clone_repo_at_base_commit(instance: dict[str, Any], destination: Path) -> None:
    repo_full_name = str(instance["repo"])
    base_commit = str(instance.get("base_commit") or "").strip()
    if not base_commit:
        raise RuntimeError("SWE-bench instance 缺少 base_commit，无法 checkout。")
    if destination.exists():
        raise RuntimeError(f"目标 repo 已存在，避免覆盖: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    run_git(["clone", "--no-tags", f"https://github.com/{repo_full_name}.git", str(destination)], cwd=REPO_ROOT)
    run_git(["checkout", base_commit], cwd=destination)


def import_swebench_lite_task(
    *,
    split: str = DEFAULT_SPLIT,
    index: int = 0,
    instance_id: str | None = None,
    dataset_path: Path | None = None,
    output_dir: Path | None = None,
    repos_dir: Path | None = None,
    artifacts_dir: Path | None = None,
    clone: bool = True,
) -> dict[str, Any]:
    instance = (
        load_instance_from_json_path(dataset_path, index=index, instance_id=instance_id)
        if dataset_path
        else load_instance_from_hf_rows_api(split=split, index=index, instance_id=instance_id)
    )
    swebench_id = str(instance["instance_id"])
    slug = slugify(swebench_id)
    task_id = f"swe_lite_{slug}"
    output_dir = output_dir or REPO_ROOT / "benchmarks" / "tasks" / "swebench_lite"
    repos_dir = repos_dir or REPO_ROOT / "benchmarks" / "repos" / "swebench_lite"
    artifacts_dir = artifacts_dir or REPO_ROOT / "benchmarks" / "swebench_lite"
    repo_dir = repos_dir / slug
    try:
        repo_task_path = str(repo_dir.resolve().relative_to(REPO_ROOT))
    except ValueError:
        repo_task_path = str(repo_dir.resolve())

    task_payload = build_task_payload(
        instance,
        repo_relative_path=repo_task_path,
        task_id=task_id,
    )
    build_task(task_payload)

    if clone:
        clone_repo_at_base_commit(instance, repo_dir)

    task_path = output_dir / f"{task_id}.json"
    write_json(task_path, task_payload)
    instance_artifacts_dir = artifacts_dir / slug
    write_json(instance_artifacts_dir / "instance.json", instance)
    if instance.get("patch"):
        write_text(instance_artifacts_dir / "gold.patch", str(instance["patch"]))
    if instance.get("test_patch"):
        write_text(instance_artifacts_dir / "test.patch", str(instance["test_patch"]))

    return {
        "task_path": str(task_path),
        "repo_path": str(repo_dir),
        "instance_id": swebench_id,
        "repo_full_name": instance["repo"],
        "base_commit": instance.get("base_commit"),
        "cloned": clone,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="导入一个 SWE-bench Lite instance 为本项目轻量 task。")
    parser.add_argument("--split", default=DEFAULT_SPLIT, help="HuggingFace split，默认 dev。")
    parser.add_argument("--index", type=int, default=0, help="split 内的行号，默认 0。")
    parser.add_argument("--instance-id", default=None, help="指定 SWE-bench instance_id。")
    parser.add_argument("--dataset-path", type=Path, default=None, help="可选本地 JSON/JSONL 数据文件。")
    parser.add_argument("--output-dir", type=Path, default=None, help="task JSON 输出目录。")
    parser.add_argument("--repos-dir", type=Path, default=None, help="repo clone 输出目录。")
    parser.add_argument("--artifacts-dir", type=Path, default=None, help="instance/gold patch/test patch 输出目录。")
    parser.add_argument("--no-clone", action="store_true", help="只生成 task/artifacts，不 clone GitHub repo。")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = import_swebench_lite_task(
        split=args.split,
        index=args.index,
        instance_id=args.instance_id,
        dataset_path=args.dataset_path,
        output_dir=args.output_dir,
        repos_dir=args.repos_dir,
        artifacts_dir=args.artifacts_dir,
        clone=not args.no_clone,
    )
    print("=== SWE-bench Lite Import Summary ===")
    print(f"instance_id: {result['instance_id']}")
    print(f"repo_full_name: {result['repo_full_name']}")
    print(f"base_commit: {result['base_commit']}")
    print(f"cloned: {result['cloned']}")
    print(f"task_path: {result['task_path']}")
    print(f"repo_path: {result['repo_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""校验 challenge shortlist 不要和正式主集口径冲突。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


CHALLENGE_SECTION_START_CANDIDATES = (
    "## 下一条最值得补的 challenge 候选",
    "## 当前最值得补的 challenge 候选",
)
CHALLENGE_SECTION_END = "## 当前推荐推进顺序"
ISSUE_REF_PATTERN = re.compile(r"`([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)`")
CANDIDATE_HEADING_PATTERN = re.compile(r"^###\s+(?:\d+\.\s+)?`([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)`", re.MULTILINE)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_formal_issue_index(*, repo_root: Path, formal_manifest_path: Path) -> dict[tuple[str, int], dict]:
    manifest_payload = _load_json(formal_manifest_path)
    issue_index: dict[tuple[str, int], dict] = {}

    for relative_task_path in manifest_payload.get("tasks", []):
        task_path = (repo_root / relative_task_path).resolve()
        if not task_path.exists():
            continue
        task_payload = _load_json(task_path)
        metadata = task_payload.get("metadata", {})
        repo_full_name = str(metadata.get("repo_full_name", "")).strip()
        issue_number = metadata.get("issue_number")
        if not repo_full_name or not isinstance(issue_number, int):
            continue
        issue_index[(repo_full_name, issue_number)] = {
            "task_id": str(task_payload.get("task_id", "")).strip(),
            "issue_url": str(metadata.get("issue_url", "")).strip(),
        }
    return issue_index


def _load_manifest_issue_refs(*, repo_root: Path, manifest_path: Path) -> set[tuple[str, int]]:
    if not manifest_path.exists():
        return set()

    manifest_payload = _load_json(manifest_path)
    issue_refs: set[tuple[str, int]] = set()
    for relative_task_path in manifest_payload.get("tasks", []):
        task_path = (repo_root / relative_task_path).resolve()
        if not task_path.exists():
            continue
        task_payload = _load_json(task_path)
        metadata = task_payload.get("metadata", {})
        repo_full_name = str(metadata.get("repo_full_name", "")).strip()
        issue_number = metadata.get("issue_number")
        if not repo_full_name or not isinstance(issue_number, int):
            continue
        issue_refs.add((repo_full_name, issue_number))
    return issue_refs


def _extract_candidate_issue_refs(shortlist_text: str) -> list[tuple[str, int]]:
    start_index = -1
    for section_heading in CHALLENGE_SECTION_START_CANDIDATES:
        heading_index = shortlist_text.find(section_heading)
        if heading_index == -1:
            continue
        if start_index == -1 or heading_index < start_index:
            start_index = heading_index
    if start_index == -1:
        return []

    end_index = shortlist_text.find(CHALLENGE_SECTION_END, start_index)
    section_text = shortlist_text[start_index:] if end_index == -1 else shortlist_text[start_index:end_index]

    ordered_refs: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for repo_full_name, issue_number_text in CANDIDATE_HEADING_PATTERN.findall(section_text):
        issue_ref = (repo_full_name, int(issue_number_text))
        if issue_ref in seen:
            continue
        seen.add(issue_ref)
        ordered_refs.append(issue_ref)
    return ordered_refs


def summarize_challenge_shortlist(
    shortlist_path: Path,
    *,
    repo_root: Path | None = None,
    challenge_manifest_path: Path | None = None,
) -> dict:
    # 这里只总结“下一条 challenge 候选”区段，避免把已落地 challenge 题和说明性引用混进追踪口径。
    shortlist_text = shortlist_path.read_text(encoding="utf-8")
    candidate_issue_refs = _extract_candidate_issue_refs(shortlist_text)
    existing_challenge_issue_refs: set[tuple[str, int]] = set()
    if repo_root is not None and challenge_manifest_path is not None:
        existing_challenge_issue_refs = _load_manifest_issue_refs(
            repo_root=repo_root,
            manifest_path=challenge_manifest_path,
        )
        candidate_issue_refs = [
            issue_ref
            for issue_ref in candidate_issue_refs
            if issue_ref not in existing_challenge_issue_refs
        ]
    next_candidate = None
    if candidate_issue_refs:
        repo_full_name, issue_number = candidate_issue_refs[0]
        next_candidate = {
            "repo_full_name": repo_full_name,
            "issue_number": issue_number,
            "issue_ref": f"{repo_full_name}#{issue_number}",
        }

    return {
        "candidate_issue_refs": candidate_issue_refs,
        "candidate_count": len(candidate_issue_refs),
        "is_empty": len(candidate_issue_refs) == 0,
        "next_candidate": next_candidate,
        "filtered_existing_challenge_issue_refs": sorted(existing_challenge_issue_refs),
    }


def validate_challenge_shortlist(
    *,
    repo_root: Path,
    shortlist_path: Path,
    formal_manifest_path: Path,
) -> list[str]:
    # 只校验“候选区段”里的 issue，不干扰“已落地 challenge 题”或解释性引用。
    shortlist_text = shortlist_path.read_text(encoding="utf-8")
    candidate_issue_refs = _extract_candidate_issue_refs(shortlist_text)
    formal_issue_index = _load_formal_issue_index(
        repo_root=repo_root,
        formal_manifest_path=formal_manifest_path,
    )

    errors: list[str] = []
    for repo_full_name, issue_number in candidate_issue_refs:
        matched_formal = formal_issue_index.get((repo_full_name, issue_number))
        if matched_formal is None:
            continue
        errors.append(
            "challenge shortlist 候选与正式主集冲突："
            f"`{repo_full_name}#{issue_number}` 已在正式 manifest，"
            f"对应 `{matched_formal['task_id']}`。"
        )
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="校验 challenge shortlist 不要与正式主集冲突。")
    parser.add_argument(
        "--shortlist",
        default="docs/challenge_shortlist.md",
        help="challenge shortlist 文档路径，默认 docs/challenge_shortlist.md",
    )
    parser.add_argument(
        "--formal-manifest",
        default="benchmarks/manifests/real_issue_tasks.json",
        help="正式主集 manifest 路径，默认 benchmarks/manifests/real_issue_tasks.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    shortlist_path = (REPO_ROOT / args.shortlist).resolve()
    formal_manifest_path = (REPO_ROOT / args.formal_manifest).resolve()

    errors = validate_challenge_shortlist(
        repo_root=REPO_ROOT,
        shortlist_path=shortlist_path,
        formal_manifest_path=formal_manifest_path,
    )

    if errors:
        print("=== Challenge Shortlist Validation Failed ===")
        for error in errors:
            print(f"- {error}")
        return 1

    print("=== Challenge Shortlist Validation Passed ===")
    print(f"validated_shortlist: {shortlist_path}")
    print(f"validated_formal_manifest: {formal_manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

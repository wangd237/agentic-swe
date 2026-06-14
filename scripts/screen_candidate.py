"""对真实 issue 候选做最小版人工筛选。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_candidate_dataset(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_candidate_dataset(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def timestamp_note(message: str) -> str:
    # 候选筛选过程保留时间戳，便于后面回看是谁在什么阶段做了判断。
    return f"{datetime.now().isoformat(timespec='seconds')}: {message}"


def append_note(existing_notes: str, message: str) -> str:
    note_line = timestamp_note(message)
    if not existing_notes.strip():
        return note_line
    return f"{existing_notes.rstrip()}\n{note_line}"


def find_candidate(payload: dict, candidate_id: str) -> dict:
    for candidate in payload.get("candidates", []):
        if candidate.get("candidate_id") == candidate_id:
            return candidate
    raise RuntimeError(f"未找到 candidate_id={candidate_id} 对应的候选记录。")


def filter_candidates_by_status(payload: dict, statuses: list[str]) -> list[dict]:
    allowed = {status.strip() for status in statuses if status.strip()}
    return [
        candidate
        for candidate in payload.get("candidates", [])
        if str(candidate.get("status", "")).strip() in allowed
    ]


def build_prompt(candidate: dict) -> str:
    body_excerpt = str(candidate.get("body_excerpt", "")).strip().replace("\r", "")
    shortened_excerpt = body_excerpt[:400]
    return (
        "\n=== Candidate Screening ===\n"
        f"candidate_id: {candidate.get('candidate_id')}\n"
        f"repo: {candidate.get('repo_full_name')}#{candidate.get('issue_number')}\n"
        f"title: {candidate.get('issue_title')}\n"
        f"current_status: {candidate.get('status')}\n"
        f"url: {candidate.get('issue_url')}\n"
        f"body_excerpt: {shortened_excerpt}\n\n"
        "输入 y 标记为 screened，输入 n 标记为 blocked，输入 s 跳过： "
    )


def apply_decision(candidate: dict, decision: str) -> tuple[str, str]:
    normalized = decision.strip().lower()
    if normalized == "y":
        return "screened", "人工筛选通过，已标记为 screened。"
    if normalized == "n":
        return "blocked", "人工筛选未通过，已标记为 blocked。"
    if normalized == "s":
        return str(candidate.get("status", "unknown")), "本次人工筛选选择跳过，状态保持不变。"
    raise RuntimeError("只支持 y / n / s 三种输入。")


def set_candidate_status(candidate_path: Path, candidate_id: str, status: str, note: str) -> None:
    payload = load_candidate_dataset(candidate_path)
    candidate = find_candidate(payload, candidate_id)
    candidate["status"] = status
    candidate["notes"] = append_note(candidate.get("notes", ""), note)
    write_candidate_dataset(candidate_path, payload)


def apply_screening_to_candidate(candidate: dict, decision: str) -> tuple[str, str, str]:
    previous_status = str(candidate.get("status", "unknown"))
    next_status, note = apply_decision(candidate, decision)
    candidate["status"] = next_status
    candidate["notes"] = append_note(candidate.get("notes", ""), note)
    return previous_status, next_status, note


def parse_status_filters(raw_values: list[str]) -> list[str]:
    parsed: list[str] = []
    for raw_value in raw_values:
        for item in raw_value.split(","):
            normalized = item.strip()
            if normalized and normalized not in parsed:
                parsed.append(normalized)
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="对真实 issue 候选做最小版人工筛选。")
    parser.add_argument(
        "--candidate-id",
        default=None,
        help="要筛选的 candidate_id",
    )
    parser.add_argument(
        "--candidate-file",
        default="benchmarks/real_world_candidates.json",
        help="候选清单文件路径",
    )
    parser.add_argument(
        "--status",
        action="append",
        default=[],
        help="批量模式下筛选哪些状态的候选，默认 imported，可重复传入，也可逗号分隔。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="批量模式下最多处理多少条候选。",
    )
    parser.add_argument(
        "--decision",
        choices=["y", "n", "s"],
        default=None,
        help="可选：直接传入筛选结论，便于非交互验证或批量统一处理。",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    candidate_path = (REPO_ROOT / args.candidate_file).resolve()
    payload = load_candidate_dataset(candidate_path)

    if args.candidate_id:
        candidate = find_candidate(payload, args.candidate_id)
        decision = args.decision or input(build_prompt(candidate))
        previous_status, next_status, _note = apply_screening_to_candidate(candidate, decision)
        write_candidate_dataset(candidate_path, payload)

        print("=== Candidate Screened ===")
        print(f"candidate_id: {candidate['candidate_id']}")
        print(f"previous_status: {previous_status}")
        print(f"current_status: {next_status}")
        print(f"candidate_file: {candidate_path}")
        return 0

    statuses = parse_status_filters(args.status) or ["imported"]
    candidates = filter_candidates_by_status(payload, statuses)
    if args.limit is not None:
        candidates = candidates[: args.limit]

    if not candidates:
        print("=== Candidate Screening Batch ===")
        print(f"matched_count: 0")
        print(f"candidate_file: {candidate_path}")
        return 0

    screened_count = 0
    blocked_count = 0
    skipped_count = 0
    processed_items: list[tuple[str, str, str]] = []
    for candidate in candidates:
        decision = args.decision or input(build_prompt(candidate))
        previous_status, next_status, _note = apply_screening_to_candidate(candidate, decision)
        processed_items.append((candidate["candidate_id"], previous_status, next_status))
        if next_status == "screened":
            screened_count += 1
        elif next_status == "blocked":
            blocked_count += 1
        else:
            skipped_count += 1

    write_candidate_dataset(candidate_path, payload)

    print("=== Candidate Screening Batch ===")
    print(f"matched_count: {len(candidates)}")
    print(f"screened_count: {screened_count}")
    print(f"blocked_count: {blocked_count}")
    print(f"skipped_count: {skipped_count}")
    print(f"candidate_file: {candidate_path}")
    for candidate_id, previous_status, next_status in processed_items:
        print(f"- {candidate_id}: {previous_status} -> {next_status}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

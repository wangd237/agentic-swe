"""把 candidate_search 结果导入到真实 issue 候选池。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import import_github_issue


def load_search_summary(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def import_search_results(
    *,
    search_result_path: Path,
    candidate_file: Path,
    recommendation_filter: list[str] | None = None,
    issue_number_filter: list[int] | None = None,
    limit: int | None = None,
) -> dict:
    summary = load_search_summary(search_result_path)
    raw_candidates = list(summary.get("candidates", []))

    if recommendation_filter:
        allowed = {item.strip().lower() for item in recommendation_filter if item.strip()}
        raw_candidates = [
            item
            for item in raw_candidates
            if str(item.get("recommendation", "")).strip().lower() in allowed
        ]

    if issue_number_filter:
        allowed_issue_numbers = set(issue_number_filter)
        raw_candidates = [
            item
            for item in raw_candidates
            if int(item.get("issue_number", -1)) in allowed_issue_numbers
        ]

    if limit is not None:
        raw_candidates = raw_candidates[:limit]

    results: list[dict] = []
    for item in raw_candidates:
        candidate = import_github_issue.build_candidate_from_search_summary(item)
        stored_candidate, operation = import_github_issue.upsert_candidate(candidate_file, candidate)
        results.append(
            {
                "candidate_id": stored_candidate["candidate_id"],
                "repo": stored_candidate["repo_full_name"],
                "issue_number": stored_candidate["issue_number"],
                "status": stored_candidate["status"],
                "recommendation": item.get("recommendation"),
                "operation": operation,
            }
        )

    created_count = sum(1 for item in results if item["operation"] == "created")
    updated_count = sum(1 for item in results if item["operation"] == "updated")
    return {
        "search_result_path": str(search_result_path),
        "candidate_file": str(candidate_file),
        "imported_count": len(results),
        "created_count": created_count,
        "updated_count": updated_count,
        "results": results,
    }


def parse_recommendation_filter(raw_values: list[str]) -> list[str]:
    parsed: list[str] = []
    for raw_value in raw_values:
        for item in raw_value.split(","):
            normalized = item.strip().lower()
            if normalized and normalized not in parsed:
                parsed.append(normalized)
    return parsed


def parse_issue_number_filter(raw_values: list[str]) -> list[int]:
    parsed: list[int] = []
    for raw_value in raw_values:
        for item in raw_value.split(","):
            normalized = item.strip()
            if not normalized:
                continue
            issue_number = int(normalized.lstrip("#"))
            if issue_number not in parsed:
                parsed.append(issue_number)
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="把 candidate_search 结果导入到真实 issue 候选池。")
    parser.add_argument(
        "--search-result",
        required=True,
        help="search_candidate_issues.py 生成的 JSON 结果路径",
    )
    parser.add_argument(
        "--candidate-file",
        default="benchmarks/real_world_candidates.json",
        help="真实 issue 候选清单路径",
    )
    parser.add_argument(
        "--recommendation",
        action="append",
        default=[],
        help="只导入指定 recommendation 级别，可重复传入，也可逗号分隔，例如 high,medium",
    )
    parser.add_argument(
        "--issue-number",
        action="append",
        default=[],
        help="只导入指定 issue 编号，可重复传入，也可逗号分隔，例如 82,88 或 #82",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="只导入前 N 条搜索结果",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = import_search_results(
        search_result_path=(REPO_ROOT / args.search_result).resolve(),
        candidate_file=(REPO_ROOT / args.candidate_file).resolve(),
        recommendation_filter=parse_recommendation_filter(args.recommendation),
        issue_number_filter=parse_issue_number_filter(args.issue_number),
        limit=args.limit,
    )

    print("=== Search Results Imported ===")
    print(f"search_result_path: {output['search_result_path']}")
    print(f"candidate_file: {output['candidate_file']}")
    print(f"imported_count: {output['imported_count']}")
    print(f"created_count: {output['created_count']}")
    print(f"updated_count: {output['updated_count']}")
    for item in output["results"]:
        print(
            f"- {item['repo']}#{item['issue_number']} -> {item['candidate_id']} "
            f"(operation: {item['operation']}, status: {item['status']}, recommendation: {item['recommendation']})"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

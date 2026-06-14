"""分析正式 benchmark 的缺陷覆盖分布与后续扩容缺口。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text


TARGET_FAMILY_SPECS = [
    {
        "family": "并发与协程",
        "priority": 1,
        "target_min_count": 2,
        "recommended_ecosystems": ["asyncio", "trio", "anyio"],
        "why_now": "roadmap 已明确把并发/协程 bug 视为当前 0 覆盖的高价值扩容方向。",
    },
    {
        "family": "文件路径与 IO",
        "priority": 2,
        "target_min_count": 2,
        "recommended_ecosystems": ["pathlib", "watchfiles", "fsspec"],
        "why_now": "当前任务集中几乎没有直接围绕路径处理、文件读写或 IO 边界的缺陷。",
    },
    {
        "family": "状态机与生命周期",
        "priority": 3,
        "target_min_count": 3,
        "recommended_ecosystems": ["transitions", "automaton", "pytest", "click"],
        "why_now": "这类问题很适合最小复现，也能提升 benchmark 对真实状态演进 bug 的覆盖。",
    },
    {
        "family": "序列化与反序列化",
        "priority": 4,
        "target_min_count": 6,
        "recommended_ecosystems": ["pyyaml", "orjson", "msgspec", "tomlkit"],
        "why_now": "issue_sourcing_spec 明确偏好配置、字符串与序列化类 bug，这也是 benchmark 最容易持续扩容的方向之一。",
    },
    {
        "family": "数值与计算语义",
        "priority": 5,
        "target_min_count": 4,
        "recommended_ecosystems": ["decimal", "fractions", "packaging", "jsonschema"],
        "why_now": "当前已覆盖少量数值语义问题，但仍不足以形成一个稳定的子类 benchmark。",
    },
    {
        "family": "解析与字符串语义",
        "priority": 6,
        "target_min_count": 8,
        "recommended_ecosystems": ["dateutil", "packaging", "requests", "pytest"],
        "why_now": "这是 issue_sourcing_spec 当前最欢迎的方向，但现有覆盖已经不算薄，需要继续补但不必排在最前。",
    },
    {
        "family": "继承、优先级与控制流",
        "priority": 7,
        "target_min_count": 8,
        "recommended_ecosystems": ["pydantic", "attrs", "jinja", "pytest"],
        "why_now": "这类问题是系统的强项之一，后续扩容更适合追求新生态而不是单纯重复同类语义。",
    },
]


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_summary_id(summary_dir: Path, run_label: str | None = None) -> str:
    existing_numbers: list[int] = []
    prefix = f"defect_coverage_{run_label}_" if run_label else "defect_coverage_"
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    if run_label:
        return f"{prefix}{next_number:03d}"
    return f"defect_coverage_{next_number:03d}"


def _canonical_repo_name(task_payload: dict) -> str:
    metadata = task_payload.get("metadata", {})
    repo_full_name = metadata.get("repo_full_name")
    if isinstance(repo_full_name, str) and repo_full_name.strip():
        return repo_full_name.strip()
    repo_url = metadata.get("repo_url")
    if isinstance(repo_url, str) and "github.com/" in repo_url:
        return repo_url.rstrip("/").split("github.com/", 1)[1]
    return str(task_payload.get("repo_name", "unknown")).strip()


def _parse_registry_rows(registry_path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    table_pattern = re.compile(
        r"^\|\s*`(?P<task_id>task_\d+)`\s*\|\s*`(?P<issue>[^`]+)`\s*\|\s*`(?P<repo>[^`]+)`\s*\|\s*(?P<defect>.+?)\s*\|\s*`(?P<policy>[^`]+)`\s*\|\s*(?P<frozen>.+?)\s*\|$"
    )

    for line in registry_path.read_text(encoding="utf-8").splitlines():
        match = table_pattern.match(line.strip())
        if match is None:
            continue
        rows[match.group("task_id")] = {
            "issue": match.group("issue").strip(),
            "semi_real_repo": match.group("repo").strip(),
            "defect_type": match.group("defect").strip(),
            "first_pass_version": match.group("policy").strip(),
            "frozen_sets": match.group("frozen").strip(),
        }
    return rows


def _normalize_text(text: str) -> str:
    return text.lower().replace("`", "").replace("_", " ").replace("-", " ")


def _infer_defect_family(*, defect_type: str, tags: list[str], issue_title: str) -> str:
    haystack = " ".join([_normalize_text(defect_type), _normalize_text(issue_title), " ".join(_normalize_text(tag) for tag in tags)])

    rules = [
        # 先判定最窄且最不希望被其它关键词误吸附的家族。
        ("数据库与事务", ["sqlite", "事务", "commit", "database", "delete where"]),
        ("并发与协程", ["deadlock", "race condition", "asyncio", "trio", "anyio", "event loop", "并发", "协程调度"]),
        ("文件路径与 IO", ["pathlib", "watchfiles", "fsspec", "文件路径", "路径拼接", "文件读写", "文件系统", "io boundary", "io error"]),
        ("继承、优先级与控制流", ["继承", "validator", "priority", "closest marker", "分支", "control flow", "undeclared", "extend", "alias", "without context"]),
        ("数值与计算语义", ["multipleof", "float", "integer", "fraction", "数值", "dev+local", "prerelease", "negative int", "可整除", "zero denominator"]),
        ("序列化与反序列化", ["serialize", "serialization", "toml", "inline table", "array", "comment", "dotted", "out of order", "aot", "scalar", "container", "key 规范化", "metadata file"]),
        ("解析与字符串语义", ["parse", "parser", "hostname", "token", "quoted", "charset", "marker expression", "normalized name", "specifier", "url scheme", "year", "time string", "requirement", "marker.evaluate", "version normalization"]),
        ("格式化与渲染", ["format", "formatting", "ansi", "newline", "indent", "usage", "timezone", "render", "build:", "wheel metadata", "show_pos", "log_time_format"]),
        ("状态机与生命周期", ["lifecycle", "filter", "progressbar", "state", "生命周期", "caplog", "warning", "pickle", "repr", "default none"]),
    ]
    for family, keywords in rules:
        if any(keyword in haystack for keyword in keywords):
            return family
    return "其他语义"


def _infer_priority_from_issue_spec(defect_family: str) -> tuple[str, str]:
    mapping = {
        "解析与字符串语义": ("high", "符合 issue_sourcing_spec 中“解析类 / 字符串处理类 bug”优先方向。"),
        "格式化与渲染": ("high", "符合 issue_sourcing_spec 中“格式化类 bug”优先方向。"),
        "序列化与反序列化": ("high", "符合 issue_sourcing_spec 中“容器 / 序列化 / 配置类 bug”优先方向。"),
        "继承、优先级与控制流": ("high", "符合 issue_sourcing_spec 中“继承 / 优先级 / 控制流”优先方向。"),
        "并发与协程": ("medium", "roadmap 明确建议补齐，但当前 issue_sourcing_spec 中尚未成为主力来源。"),
        "文件路径与 IO": ("medium", "roadmap 建议补齐，且这类问题通常边界清晰、适合最小化。"),
        "状态机与生命周期": ("medium", "这类问题对 benchmark 很有价值，但需要优先挑单模块、单函数即可修复的 issue。"),
        "数值与计算语义": ("medium", "现有覆盖偏少，适合继续补，但优先级略低于 0 覆盖领域。"),
        "数据库与事务": ("low", "当前不是 issue_sourcing_spec 的最优先方向，且生态依赖有时更重。"),
        "其他语义": ("low", "尚未映射到明确的高优先级来源方向。"),
    }
    return mapping.get(defect_family, ("low", "当前未命中优先方向映射。"))


def _load_manifest_tasks(*, repo_root: Path, manifest_path: Path) -> list[dict]:
    manifest_payload = _load_json(manifest_path)
    task_entries: list[dict] = []
    for task_relative_path in manifest_payload.get("tasks", []):
        task_path = (repo_root / task_relative_path).resolve()
        payload = _load_json(task_path)
        payload["_task_path"] = str(task_path)
        task_entries.append(payload)
    return task_entries


def _build_task_records(*, task_payloads: list[dict], registry_rows: dict[str, dict]) -> list[dict]:
    task_records: list[dict] = []
    for payload in task_payloads:
        task_id = str(payload.get("task_id"))
        registry_row = registry_rows.get(task_id, {})
        defect_type = str(registry_row.get("defect_type") or payload.get("issue_title") or "unknown").strip()
        tags = [str(tag) for tag in payload.get("tags", [])]
        family = _infer_defect_family(defect_type=defect_type, tags=tags, issue_title=str(payload.get("issue_title", "")))
        task_records.append(
            {
                "task_id": task_id,
                "repo_full_name": _canonical_repo_name(payload),
                "issue_title": payload.get("issue_title"),
                "defect_type": defect_type,
                "defect_family": family,
                "tags": tags,
                "difficulty": payload.get("difficulty"),
                "source_type": payload.get("source_type"),
                "registry_issue": registry_row.get("issue"),
                "first_pass_version": registry_row.get("first_pass_version"),
            }
        )
    return task_records


def _summarize_family_coverage(task_records: list[dict]) -> dict:
    family_counts = Counter(record["defect_family"] for record in task_records)
    ecosystem_family_counter: dict[str, Counter] = defaultdict(Counter)
    ecosystem_counts = Counter(record["repo_full_name"] for record in task_records)
    exact_defect_counts = Counter(record["defect_type"] for record in task_records)

    for record in task_records:
        ecosystem_family_counter[record["repo_full_name"]][record["defect_family"]] += 1

    ecosystem_family_matrix: dict[str, dict[str, int]] = {
        ecosystem: dict(sorted(counter.items()))
        for ecosystem, counter in sorted(ecosystem_family_counter.items())
    }

    top_families = [
        {"family": family, "count": count}
        for family, count in family_counts.most_common()
    ]
    top_ecosystems = [
        {"ecosystem": ecosystem, "count": count}
        for ecosystem, count in ecosystem_counts.most_common()
    ]
    exact_duplicates = [
        {"defect_type": defect_type, "count": count}
        for defect_type, count in exact_defect_counts.most_common()
        if count > 1
    ]

    return {
        "family_counts": dict(sorted(family_counts.items())),
        "top_families": top_families,
        "ecosystem_counts": dict(sorted(ecosystem_counts.items())),
        "top_ecosystems": top_ecosystems,
        "ecosystem_family_matrix": ecosystem_family_matrix,
        "exact_defect_type_count": len(exact_defect_counts),
        "exact_defect_type_duplicates": exact_duplicates,
    }


def _build_gap_recommendations(*, family_counts: dict[str, int]) -> list[dict]:
    recommendations: list[dict] = []
    for spec in TARGET_FAMILY_SPECS:
        family = spec["family"]
        current_count = int(family_counts.get(family, 0))
        gap = max(spec["target_min_count"] - current_count, 0)
        source_priority, source_reason = _infer_priority_from_issue_spec(family)
        if gap == 0 and current_count > 0:
            status = "covered"
        elif current_count == 0:
            status = "missing"
        else:
            status = "underrepresented"

        recommendations.append(
            {
                "family": family,
                "priority_rank": spec["priority"],
                "source_priority": source_priority,
                "current_count": current_count,
                "target_min_count": spec["target_min_count"],
                "gap": gap,
                "status": status,
                "recommended_ecosystems": spec["recommended_ecosystems"],
                "why_now": spec["why_now"],
                "source_priority_reason": source_reason,
            }
        )

    recommendations.sort(
        key=lambda item: (
            0 if item["status"] == "missing" else 1 if item["status"] == "underrepresented" else 2,
            item["priority_rank"],
            -item["gap"],
        )
    )
    return recommendations


def _build_summary(
    *,
    manifest_path: Path,
    registry_path: Path,
    task_records: list[dict],
    family_summary: dict,
    gap_recommendations: list[dict],
) -> dict:
    missing_or_underrepresented = [
        item for item in gap_recommendations if item["status"] in {"missing", "underrepresented"}
    ]

    return {
        "created_at": _utc_timestamp(),
        "formal_manifest_path": str(manifest_path),
        "benchmark_registry_path": str(registry_path),
        "task_count": len(task_records),
        "ecosystem_count": len(family_summary["ecosystem_counts"]),
        "family_coverage": family_summary,
        "gap_recommendations": gap_recommendations,
        "high_value_missing_or_underrepresented": missing_or_underrepresented,
        "task_records": task_records,
        "analysis_notes": [
            "缺陷类型主真相来自 docs/benchmark_registry.md 的“缺陷类型”列。",
            "family 级分类是为了把近乎全唯一的 defect_type 压缩成可决策的扩容方向。",
            "优先级排序综合参考了 docs/issue_sourcing_spec.md 与 docs/v2_roadmap.md 的扩容建议。",
        ],
    }


def _build_markdown(summary: dict) -> str:
    top_family_lines = "\n".join(
        [f"- `{item['family']}`: `{item['count']}`" for item in summary["family_coverage"]["top_families"][:8]]
    ) or "- 当前没有 family 统计"

    top_ecosystem_lines = "\n".join(
        [f"- `{item['ecosystem']}`: `{item['count']}`" for item in summary["family_coverage"]["top_ecosystems"][:8]]
    ) or "- 当前没有 ecosystem 统计"

    recommendation_lines = "\n".join(
        [
            (
                f"- `{item['family']}`: status=`{item['status']}`, current=`{item['current_count']}`, "
                f"target_min=`{item['target_min_count']}`, gap=`{item['gap']}`, "
                f"recommended_ecosystems=`{', '.join(item['recommended_ecosystems'])}`\n"
                f"  - why_now: {item['why_now']}\n"
                f"  - source_priority_reason: {item['source_priority_reason']}"
            )
            for item in summary["high_value_missing_or_underrepresented"][:8]
        ]
    ) or "- 当前没有缺口建议"

    exact_duplicate_lines = "\n".join(
        [
            f"- `{item['defect_type']}`: `{item['count']}`"
            for item in summary["family_coverage"]["exact_defect_type_duplicates"][:8]
        ]
    ) or "- 当前 exact defect type 基本全部唯一，family 级统计更有分析价值。"

    matrix_rows = []
    for ecosystem, family_counts in list(summary["family_coverage"]["ecosystem_family_matrix"].items())[:12]:
        family_brief = ", ".join([f"{family}={count}" for family, count in sorted(family_counts.items())])
        matrix_rows.append(f"- `{ecosystem}`: {family_brief}")
    matrix_block = "\n".join(matrix_rows) or "- 当前没有 matrix 数据"

    return f"""# Defect Coverage Analysis

## Snapshot

- created_at: `{summary["created_at"]}`
- formal_manifest_path: `{summary["formal_manifest_path"]}`
- benchmark_registry_path: `{summary["benchmark_registry_path"]}`
- task_count: `{summary["task_count"]}`
- ecosystem_count: `{summary["ecosystem_count"]}`

## Top Covered Families

{top_family_lines}

## Top Ecosystems

{top_ecosystem_lines}

## Exact Defect Type Notes

{exact_duplicate_lines}

## Ecosystem x Family Matrix

{matrix_block}

## High Value Gaps

{recommendation_lines}

## Notes

{chr(10).join(f"- {note}" for note in summary["analysis_notes"])}
"""


def run_defect_coverage_analysis(
    *,
    repo_root: Path,
    manifest_path: Path,
    registry_path: Path,
    output_dir: Path,
) -> dict:
    registry_rows = _parse_registry_rows(registry_path)
    task_payloads = _load_manifest_tasks(repo_root=repo_root, manifest_path=manifest_path)
    task_records = _build_task_records(task_payloads=task_payloads, registry_rows=registry_rows)
    family_summary = _summarize_family_coverage(task_records)
    gap_recommendations = _build_gap_recommendations(family_counts=family_summary["family_counts"])
    return _build_summary(
        manifest_path=manifest_path,
        registry_path=registry_path,
        task_records=task_records,
        family_summary=family_summary,
        gap_recommendations=gap_recommendations,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="分析正式 benchmark 的缺陷覆盖分布。")
    parser.add_argument(
        "--manifest",
        default="benchmarks/manifests/real_issue_tasks.json",
        help="正式任务 manifest 路径。",
    )
    parser.add_argument(
        "--benchmark-registry",
        default="docs/benchmark_registry.md",
        help="benchmark 注册表路径。",
    )
    parser.add_argument(
        "--output-dir",
        default="logs/summaries",
        help="分析报告输出目录。",
    )
    parser.add_argument(
        "--run-label",
        default=None,
        help="可选标签，用于区分多次分析结果。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = (REPO_ROOT / args.manifest).resolve()
    registry_path = (REPO_ROOT / args.benchmark_registry).resolve()
    output_dir = (REPO_ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    analysis_id = _next_summary_id(output_dir, run_label=args.run_label)
    summary = run_defect_coverage_analysis(
        repo_root=REPO_ROOT,
        manifest_path=manifest_path,
        registry_path=registry_path,
        output_dir=output_dir,
    )

    json_path = output_dir / f"{analysis_id}.json"
    md_path = output_dir / f"{analysis_id}.md"
    write_json(json_path, summary)
    write_text(md_path, _build_markdown(summary))

    top_gap = summary["high_value_missing_or_underrepresented"][0] if summary["high_value_missing_or_underrepresented"] else None
    print(f"defect_coverage: tasks={summary['task_count']} ecosystems={summary['ecosystem_count']}")
    if top_gap is not None:
        print(
            "top_gap:",
            f"family={top_gap['family']}",
            f"status={top_gap['status']}",
            f"gap={top_gap['gap']}",
        )
    print(f"summary_json: {json_path}")
    print(f"summary_md: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

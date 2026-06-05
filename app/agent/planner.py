"""Agent 规划器占位实现。"""

import re
from pathlib import Path

from app.schemas.task_schema import Task


def create_initial_plan(task: Task) -> list[str]:
    # Phase 1 仍然保持简单显式规划，避免观察阶段无界搜索。
    return [
        f"理解任务：{task.issue_title}",
        "定位候选文件",
        "读取更多上下文",
        "生成并验证修复方案",
    ]


def derive_search_queries(task: Task) -> list[str]:
    # 观察型 Agent 先从 issue 文本和测试名里提取最可能有价值的标识符。
    raw_candidates = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", f"{task.issue_title}\n{task.issue_text}")
    prioritized_candidates = [
        candidate
        for candidate in raw_candidates
        if "_" in candidate or candidate.lower().startswith("test")
    ]

    if task.expected_failure_test:
        prioritized_candidates.append(task.expected_failure_test.split(".")[-1])

    seen: set[str] = set()
    queries: list[str] = []
    hint_candidates = [
        Path(relative_path).stem
        for relative_path in task.target_files_hint
        if "/" not in relative_path and "\\" not in relative_path
    ]

    for candidate in prioritized_candidates + hint_candidates:
        normalized_candidate = candidate.strip()
        if not normalized_candidate or normalized_candidate in seen:
            continue
        seen.add(normalized_candidate)
        queries.append(normalized_candidate)

    return queries[:5]

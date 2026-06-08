"""Task 数据结构定义。"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Task(BaseModel):
    # 用 pydantic 接住任务边界数据，后续 phase 扩展字段时更容易保持一致。
    model_config = ConfigDict(extra="forbid")

    task_id: str
    repo_name: str
    repo_path: str
    issue_title: str
    issue_text: str
    test_command: str
    success_criteria: str
    difficulty: str
    tags: list[str]
    target_files_hint: list[str] = Field(default_factory=list)
    expected_failure_test: str | None = None
    max_retries: int | None = None
    source_type: str = "synthetic"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        # 统一通过 model_dump 输出，便于日志和 JSON 落盘。
        return self.model_dump(mode="json")


def build_task(payload: dict[str, Any]) -> Task:
    # 所有字段校验统一交给 pydantic，减少手写校验分叉。
    return Task.model_validate(payload)


def load_task(path: str | Path) -> Task:
    # Phase 1 开始，任务加载除了读文件，也承担结构校验职责。
    task_path = Path(path)
    payload = json.loads(task_path.read_text(encoding="utf-8"))
    return build_task(payload)

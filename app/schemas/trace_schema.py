"""Trace 数据结构定义。"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TraceStep(BaseModel):
    # Trace step 统一结构有助于后续做批量评测和错误分类。
    model_config = ConfigDict(extra="forbid")

    step_index: int
    action_type: str
    tool_name: str | None = None
    tool_input: dict[str, Any] = Field(default_factory=dict)
    tool_output_summary: str = ""
    observation: str = ""
    decision: str = ""
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class Trace(BaseModel):
    # 当前先保留最关键字段，后续 phase 再继续加统计信息。
    model_config = ConfigDict(extra="forbid")

    task_id: str
    run_id: str
    steps: list[TraceStep] = Field(default_factory=list)
    final_status: str = "not_started"
    total_tool_calls: int = 0
    read_files: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

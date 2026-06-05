"""Result 数据结构定义。"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Result(BaseModel):
    # Result 是单次运行的主结果入口，后续评测脚本会优先读取它。
    model_config = ConfigDict(extra="forbid")

    task_id: str
    run_id: str
    final_status: str
    summary: str
    test_command: str = ""
    test_exit_code: int | None = None
    pre_test_exit_code: int | None = None
    post_test_exit_code: int | None = None
    pre_test_summary: str = ""
    post_test_summary: str = ""
    test_summary: str = ""
    observed_failure: str = ""
    patch_applied: bool = False
    patch_summary: str = ""
    modified_files: list[str] = Field(default_factory=list)
    duration_sec: float | None = None
    tool_stats: dict[str, Any] = Field(default_factory=dict)
    recommended_files: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

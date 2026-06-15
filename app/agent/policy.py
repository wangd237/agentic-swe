"""Agent 策略配置。"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class PolicyConfig(BaseModel):
    # policy 作为独立配置对象，方便 baseline / improved 实验复现。
    model_config = ConfigDict(extra="forbid")

    policy_id: str
    description: str
    max_steps: int = 12
    max_retries: int = 2
    max_patch_files: int = 1
    agent_type: str = "rule_based"
    patch_strategy: str = "baseline"
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_api_key_env: str | None = None
    llm_base_url_env: str | None = None
    llm_model_env: str | None = None
    llm_base_url: str | None = None
    llm_max_output_tokens: int | None = None
    llm_max_context_chars: int | None = None
    pytest_additional_flags: list[str] = []

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")


DEFAULT_POLICY = PolicyConfig(
    policy_id="inline_default",
    description="默认内联策略配置。",
)


def load_policy_config(path: str | Path | None = None) -> PolicyConfig:
    # 不传 path 时使用默认配置；传入时从 JSON 读取，支持后续实验切换。
    if path is None:
        return DEFAULT_POLICY
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return PolicyConfig.model_validate(payload)

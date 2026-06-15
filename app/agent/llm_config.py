"""LLM Agent 配置。"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class LLMConfig(BaseModel):
    """描述 LLM agent 运行所需的最小配置。"""

    model_config = ConfigDict(extra="forbid")

    provider: str = "openai_compatible"
    model: str = "default"
    api_key_env: str = "LLM_API_KEY"
    base_url_env: str = "LLM_BASE_URL"
    model_env: str = "LLM_MODEL"
    default_base_url: str = ""
    max_iterations: int = 16
    max_output_tokens: int = 8000
    max_tool_chars: int = 4000
    max_context_chars: int = 80000
    temperature: float = 0.0

    @staticmethod
    def load_env_file(repo_root: str | Path | None = None) -> None:
        """把仓库根目录 `.env` 中的变量补进当前进程环境。"""

        root = Path(repo_root).resolve() if repo_root else Path.cwd()
        env_path = root / ".env"
        if not env_path.exists():
            return
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

    @classmethod
    def from_policy(cls, policy_config: object) -> "LLMConfig":
        """从 policy 中抽取 LLM provider / model，其他参数沿用默认值。"""

        provider = getattr(policy_config, "llm_provider", None) or cls().provider
        model_env = getattr(policy_config, "llm_model_env", None) or cls().model_env
        model = getattr(policy_config, "llm_model", None) or os.environ.get(model_env, "").strip() or cls().model
        return cls(
            provider=provider,
            model=model,
            api_key_env=getattr(policy_config, "llm_api_key_env", None)
            or cls().api_key_env,
            base_url_env=getattr(policy_config, "llm_base_url_env", None)
            or cls().base_url_env,
            model_env=model_env,
            default_base_url=getattr(policy_config, "llm_base_url", None)
            or cls().default_base_url,
            max_output_tokens=getattr(policy_config, "llm_max_output_tokens", None)
            or cls().max_output_tokens,
            max_iterations=getattr(policy_config, "max_steps", None)
            or cls().max_iterations,
            max_context_chars=getattr(policy_config, "llm_max_context_chars", None)
            or cls().max_context_chars,
        )

    def require_api_key(self) -> str:
        """读取并校验 API key。"""

        api_key = os.environ.get(self.api_key_env, "").strip()
        if not api_key:
            raise RuntimeError(
                f"未检测到 `{self.api_key_env}`，无法运行 LLM agent。"
            )
        return api_key

    def resolve_base_url(self) -> str:
        """读取 provider 的 OpenAI-compatible base URL。"""

        base_url = os.environ.get(self.base_url_env, "").strip() or self.default_base_url
        if not base_url:
            raise RuntimeError(
                f"未检测到 `{self.base_url_env}`，也没有在 policy 中配置 `llm_base_url`。"
            )
        return base_url


DEFAULT_LLM_CONFIG = LLMConfig()

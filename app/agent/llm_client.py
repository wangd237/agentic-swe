"""OpenAI-compatible Chat Completions adapter for the coding agent."""

from __future__ import annotations

import json
from typing import Any

from app.agent.llm_config import DEFAULT_LLM_CONFIG, LLMConfig


class OpenAICompatibleChatClient:
    """OpenAI-compatible Chat Completions 轻量适配器。"""

    def __init__(self, llm_config: LLMConfig | None = None) -> None:
        self.llm_config = llm_config or DEFAULT_LLM_CONFIG
        self._client: Any | None = None

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client

        api_key = self.llm_config.require_api_key()
        try:
            from openai import OpenAI
        except ImportError as error:
            raise RuntimeError(
                "未安装 `openai` 依赖，无法运行 OpenAI-compatible LLM agent。"
            ) from error

        self._client = OpenAI(
            api_key=api_key,
            base_url=self.llm_config.resolve_base_url(),
            timeout=self.llm_config.timeout_sec,
            max_retries=self.llm_config.client_max_retries,
        )
        return self._client

    @staticmethod
    def _tools_to_openai(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {"type": "object"}),
                },
            }
            for tool in tools
        ]

    @staticmethod
    def _messages_to_openai(
        *,
        system_prompt: str,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        converted: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
        ]
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if isinstance(content, str):
                converted.append({"role": role, "content": content})
                continue

            if role == "assistant":
                text_parts: list[str] = []
                tool_calls: list[dict[str, Any]] = []
                for block in content:
                    if block.get("type") == "text" and block.get("text"):
                        text_parts.append(block["text"])
                    if block.get("type") == "tool_use":
                        tool_calls.append(
                            {
                                "id": block.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": block.get("name", ""),
                                    "arguments": json.dumps(
                                        block.get("input", {}),
                                        ensure_ascii=False,
                                    ),
                                },
                            }
                        )
                converted.append(
                    {
                        "role": "assistant",
                        "content": "\n".join(text_parts) or None,
                        **({"tool_calls": tool_calls} if tool_calls else {}),
                    }
                )
                # 协议兑底：content=None 且无 tool_calls 的 assistant 消息
                # 违反 OpenAI 协议（'content or tool_calls must be set'）。
                # 无论上游如何构造，这里保证不发出非法消息。
                if converted[-1]["content"] is None and "tool_calls" not in converted[-1]:
                    converted[-1]["content"] = "(empty assistant response)"
                continue

            for block in content:
                if block.get("type") != "tool_result":
                    continue
                converted.append(
                    {
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id", ""),
                        "content": block.get("content", ""),
                    }
                )
        return converted

    @staticmethod
    def _usage_value(usage: Any, key: str) -> int | None:
        if usage is None:
            return None
        if isinstance(usage, dict):
            value = usage.get(key)
        else:
            value = getattr(usage, key, None)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _normalize_usage(cls, usage: Any) -> dict[str, int]:
        # ADR-0002 Step 1：保留 prompt/cache 细分字段，供 token 偏差观测与缓存命中率统计。
        # total_tokens 缺失时用 prompt+completion 兑底；细分字段缺失时省略，不臆造 0。
        total_tokens = cls._usage_value(usage, "total_tokens")
        prompt_tokens = cls._usage_value(usage, "prompt_tokens")
        completion_tokens = cls._usage_value(usage, "completion_tokens")
        if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
            total_tokens = prompt_tokens + completion_tokens
        normalized: dict[str, int] = {}
        if total_tokens is not None:
            normalized["total_tokens"] = total_tokens
        if prompt_tokens is not None:
            normalized["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            normalized["completion_tokens"] = completion_tokens
        # DeepSeek 扩展字段：命中缓存的输入 token 与未命中的输入 token。
        cache_hit = cls._usage_value(usage, "prompt_cache_hit_tokens")
        cache_miss = cls._usage_value(usage, "prompt_cache_miss_tokens")
        if cache_hit is not None:
            normalized["prompt_cache_hit_tokens"] = cache_hit
        if cache_miss is not None:
            normalized["prompt_cache_miss_tokens"] = cache_miss
        return normalized

    @staticmethod
    def _normalize_openai_response(response: Any) -> dict[str, Any]:
        message = response.choices[0].message
        content: list[dict[str, Any]] = []
        if message.content:
            content.append({"type": "text", "text": message.content})
        for tool_call in message.tool_calls or []:
            try:
                tool_input = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                tool_input = {}
            content.append(
                {
                    "type": "tool_use",
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "input": tool_input,
                }
            )
        normalized = {"content": content}
        usage = OpenAICompatibleChatClient._normalize_usage(getattr(response, "usage", None))
        if usage:
            normalized["usage"] = usage
        return normalized

    def create_message(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        client = self._ensure_client()
        response = client.chat.completions.create(
            model=self.llm_config.model,
            temperature=self.llm_config.temperature,
            max_tokens=self.llm_config.max_output_tokens,
            messages=self._messages_to_openai(
                system_prompt=system_prompt,
                messages=messages,
            ),
            tools=self._tools_to_openai(tools),
        )
        return self._normalize_openai_response(response)

"""Message compaction and context window helpers for the coding agent."""

from __future__ import annotations

import json
from typing import Any, Callable


class AgentContextMixin:
    """Context-management methods shared with LLMCodeAgent."""

    @staticmethod
    def _message_char_estimate(messages: list[dict[str, Any]]) -> int:
        return sum(len(json.dumps(message, ensure_ascii=False)) for message in messages)

    @staticmethod
    def _summarize_message_for_context(message: dict[str, Any]) -> str:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        if isinstance(content, str):
            compact = content.replace("\n", " ").strip()
            return f"{role}: {compact[:300]}"

        parts: list[str] = []
        for block in content if isinstance(content, list) else []:
            block_type = block.get("type")
            if block_type == "text":
                text = str(block.get("text", "")).replace("\n", " ").strip()
                parts.append(f"text={text[:200]}")
            elif block_type == "tool_use":
                parts.append(
                    f"tool_use name={block.get('name', '')} id={block.get('id', '')} input={block.get('input', {})}"
                )
            elif block_type == "tool_result":
                result_text = str(block.get("content", "")).replace("\n", " ").strip()
                parts.append(f"tool_result id={block.get('tool_use_id', '')} content={result_text[:300]}")
        return f"{role}: " + " | ".join(parts)

    @staticmethod
    def _microcompact_messages(
        messages: list[dict[str, Any]],
        *,
        max_chars: int,
    ) -> list[dict[str, Any]]:
        """Truncate oversized tool results before they bloat the context window."""
        if not messages:
            return messages
        max_chars *= 2
        last = messages[-1]
        if last.get("role") != "user":
            return messages
        content = last.get("content", [])
        if not isinstance(content, list):
            return messages
        truncated: list[dict[str, Any]] = []
        for block in content:
            if block.get("type") == "tool_result" and isinstance(block.get("content"), str):
                text = str(block["content"])
                if len(text) > max_chars:
                    block = {**block, "content": text[:max_chars] + "\n...[truncated]"}
            truncated.append(block)
        messages[-1] = {**last, "content": truncated}
        return messages

    @classmethod
    def _estimate_context_tokens(
        cls,
        messages: list[dict[str, Any]],
        *,
        measured_prompt_tokens: int | None,
        measured_message_chars: int | None = None,
    ) -> int:
        """估算当前上下文 token 数。

        ADR-0002 Step 2：优先用最近一次 API 实测 prompt_tokens 做锚点校准
        （实测值覆盖了 system prompt + 工具 schema，比纯字符估算准）；
        无锚点时（首次调用前）退回 chars/2.5 保守估算——实测稳态比值
        2.45（范围 1.93~3.10），2.5 居中且偏保守（高估 token → 提前压缩，
        安全方向）。
        """
        current_chars = cls._message_char_estimate(messages)
        if measured_prompt_tokens is not None:
            if measured_message_chars is None:
                return measured_prompt_tokens
            # An old prompt_tokens reading cannot remain constant as messages grow.
            # Anchor fixed system/schema overhead to the last API observation,
            # and price the changed message suffix with the calibrated heuristic.
            return max(0, round(measured_prompt_tokens + (current_chars - measured_message_chars) / 2.5))
        return round(current_chars / 2.5)

    @classmethod
    def _compress_messages_if_needed(
        cls,
        messages: list[dict[str, Any]],
        *,
        max_context_chars: int,
        context_window_tokens: int = 1_000_000,
        reserve_tokens: int = 16_000,
        measured_prompt_tokens: int | None = None,
        measured_message_chars: int | None = None,
        trigger_tokens: int | None = None,
        summary_builder: Callable[[list[dict[str, Any]]], str] | None = None,
        keep_recent: int = 3,
    ) -> tuple[list[dict[str, Any]], bool, int, int]:
        before_chars = cls._message_char_estimate(messages)
        # ADR-0002 Step 2：token 级判定取代字符阈值。实测（3 任务 46 调用）
        # 证明 80K chars 仅占 1M 窗口的 3.7%，旧阈值在长任务里人为触发
        # 过早压缩，丢失 PATCH 阶段上下文。
        estimated_tokens = cls._estimate_context_tokens(
            messages,
            measured_prompt_tokens=measured_prompt_tokens,
            measured_message_chars=measured_message_chars,
        )
        token_budget = context_window_tokens - reserve_tokens
        if trigger_tokens is not None:
            token_budget = min(token_budget, trigger_tokens)
        if (
            estimated_tokens <= token_budget
            or len(messages) <= keep_recent + 1
        ):
            return messages, False, before_chars, before_chars

        leading_message = messages[0]
        # 配对保护：recent 边界不能切在 assistant(tool_calls) 与其 tool_result 之间。
        # 否则摘要掉 assistant 后，保留的 tool_result 前面没有 tool_calls，
        # 严格校验的 API（DeepSeek 官方）会报 400：
        # "Messages with role 'tool' must be a response to a preceding message
        # with 'tool_calls'"。
        # 若 recent 首条是含 tool_result 的 user 消息，则把紧邻其前的 assistant
        # 一并保留（不进摘要）。
        split_index = max(1, len(messages) - keep_recent)
        while (
            split_index > 1
            and cls._message_starts_with_tool_result(messages[split_index])
        ):
            split_index -= 1
        recent_messages = messages[split_index:]
        middle_messages = messages[1:split_index]
        # The summary builder receives a complete prefix, including the task and
        # any previous checkpoint. No dangling tool result crosses this boundary.
        summary = ""
        if summary_builder is not None:
            summary = summary_builder([leading_message, *middle_messages]).strip()
        if summary:
            summary_content = "Earlier context has been summarized. Key findings so far:\n" + summary
        else:
            summary_lines = [
                cls._summarize_message_for_context(message)
                for message in middle_messages
            ]
            summary_content = (
                "Earlier context has been summarized. Key findings so far:\n"
                + "\n".join(f"- {line}" for line in summary_lines)
            )
        summary_message = {"role": "system", "content": summary_content}
        compressed_messages = [leading_message, summary_message, *recent_messages]
        after_chars = cls._message_char_estimate(compressed_messages)
        # Never replace history with a checkpoint that actually expands context.
        if after_chars >= before_chars:
            return messages, False, before_chars, before_chars
        return compressed_messages, True, before_chars, after_chars

    @staticmethod
    def _message_starts_with_tool_result(message: dict[str, Any]) -> bool:
        """消息是否以 tool_result 开头（即它是某轮工具调用的结果消息）。"""
        if message.get("role") != "user":
            return False
        content = message.get("content")
        if not isinstance(content, list) or not content:
            return False
        return content[0].get("type") == "tool_result"

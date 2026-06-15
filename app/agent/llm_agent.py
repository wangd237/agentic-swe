"""最小 LLM coding agent。"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from time import perf_counter
from typing import Any

from app.agent.base import BaseAgent
from app.agent.llm_config import DEFAULT_LLM_CONFIG, LLMConfig
from app.agent.llm_prompts import build_system_prompt, build_user_prompt
from app.agent.policy import load_policy_config
from app.agent.tool_definitions import build_tool_definitions
from app.agent.tool_executor import ToolExecutor
from app.runtime.harness import COPY_IGNORE_DIR_NAMES, build_run_paths, copy_repo_to_workspace, next_run_id
from app.runtime.logger import write_json, write_text
from app.schemas.result_schema import Result
from app.schemas.task_schema import load_task
from app.schemas.trace_schema import Trace, TraceStep


READ_ONLY_TOOL_NAMES = {"list_files", "search_code", "grep", "read_file", "show_diff"}
WRITE_TOOL_NAMES = {"write_file", "edit_file"}
ANTI_LOOP_MESSAGE = (
    "你似乎在同一个修复方向上循环：最近连续多次修改同一个文件，"
    "且编辑模式高度相似。请退一步重新读取相关代码或测试，验证你的核心假设；"
    "如果涉及第三方库行为，优先用 python_repl 查询实际行为，然后再修改。"
)


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
        return {"content": content}

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


class LLMCodeAgent(BaseAgent):
    """基于工具调用循环的最小 coding agent。"""

    def __init__(
        self,
        *,
        llm_config: LLMConfig | None = None,
        client: Any | None = None,
    ) -> None:
        self.llm_config = llm_config or DEFAULT_LLM_CONFIG
        self.client = client

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_assistant_blocks(response: dict[str, Any]) -> list[dict[str, Any]]:
        content = response.get("content", [])
        normalized: list[dict[str, Any]] = []
        for block in content:
            block_type = block.get("type")
            if block_type == "text":
                normalized.append({"type": "text", "text": block.get("text", "")})
            elif block_type == "tool_use":
                normalized.append(
                    {
                        "type": "tool_use",
                        "id": block.get("id", ""),
                        "name": block.get("name", ""),
                        "input": block.get("input", {}),
                    }
                )
        return normalized

    @staticmethod
    def _extract_text(content_blocks: list[dict[str, Any]]) -> str:
        texts = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
        return "\n".join(part for part in texts if part).strip()

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

    @classmethod
    def _compress_messages_if_needed(
        cls,
        messages: list[dict[str, Any]],
        *,
        max_context_chars: int,
        keep_recent: int = 3,
    ) -> tuple[list[dict[str, Any]], bool, int, int]:
        before_chars = cls._message_char_estimate(messages)
        if before_chars <= max_context_chars or len(messages) <= keep_recent + 1:
            return messages, False, before_chars, before_chars

        leading_message = messages[0]
        recent_messages = messages[-keep_recent:]
        middle_messages = messages[1:-keep_recent]
        summary_lines = [
            cls._summarize_message_for_context(message)
            for message in middle_messages
        ]
        summary_message = {
            "role": "system",
            "content": (
                "Earlier context has been summarized. Key findings so far:\n"
                + "\n".join(f"- {line}" for line in summary_lines)
            ),
        }
        compressed_messages = [leading_message, summary_message, *recent_messages]
        after_chars = cls._message_char_estimate(compressed_messages)
        return compressed_messages, True, before_chars, after_chars

    def _append_tool_trace_step(
        self,
        *,
        trace: Trace,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: dict[str, Any],
        duration_sec: float,
        decision: str,
        parallel_group_id: str | None = None,
    ) -> None:
        tool_metrics = {
            "ok": tool_result.get("ok", False),
        }
        if parallel_group_id:
            tool_metrics["parallel_group_id"] = parallel_group_id
        trace.steps.append(
            TraceStep(
                step_index=len(trace.steps) + 1,
                action_type="tool_call",
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output_summary=tool_result.get("summary", ""),
                observation=ToolExecutor.summarize_for_model(
                    tool_result,
                    max_chars=min(600, self.llm_config.max_tool_chars),
                ),
                decision=decision,
                timestamp=self._utc_timestamp(),
                duration_sec=duration_sec,
                tool_metrics=tool_metrics,
            )
        )
        trace.total_tool_calls += 1

    @staticmethod
    def _tool_use_blocks(assistant_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [block for block in assistant_blocks if block.get("type") == "tool_use"]

    @staticmethod
    def _partition_tool_batches(tool_blocks: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        batches: list[list[dict[str, Any]]] = []
        current_read_only_batch: list[dict[str, Any]] = []
        for block in tool_blocks:
            if block.get("name") in READ_ONLY_TOOL_NAMES:
                current_read_only_batch.append(block)
                continue
            if current_read_only_batch:
                batches.append(current_read_only_batch)
                current_read_only_batch = []
            batches.append([block])
        if current_read_only_batch:
            batches.append(current_read_only_batch)
        return batches

    @staticmethod
    def _execute_tool_block(
        *,
        tool_executor: ToolExecutor,
        block: dict[str, Any],
    ) -> dict[str, Any]:
        tool_name = block["name"]
        tool_input = block.get("input", {})
        tool_started_at = perf_counter()
        tool_result = tool_executor.execute(tool_name, tool_input)
        tool_duration_sec = round(perf_counter() - tool_started_at, 4)
        return {
            "block": block,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_result": tool_result,
            "tool_duration_sec": tool_duration_sec,
        }

    @staticmethod
    def _model_reported_incomplete(text: str) -> bool:
        normalized_text = text.lower()
        incomplete_markers = [
            "未完成",
            "无法完成",
            "不能完成",
            "还需要继续",
            "需要继续",
            "没有全部完成",
            "not complete",
            "incomplete",
            "cannot complete",
            "unable to complete",
        ]
        return any(marker in normalized_text for marker in incomplete_markers)

    @staticmethod
    def _write_signature(tool_name: str, tool_input: dict[str, Any]) -> dict[str, str] | None:
        if tool_name not in WRITE_TOOL_NAMES:
            return None
        relative_path = str(tool_input.get("relative_path", "")).replace("\\", "/")
        if not relative_path:
            return None
        return {
            "tool_name": tool_name,
            "relative_path": relative_path,
            "old_string": str(tool_input.get("old_string", "")),
            "new_string": str(tool_input.get("new_string", "")),
            "content": str(tool_input.get("content", "")),
        }

    @staticmethod
    def _is_similar_text(left: str, right: str, *, threshold: float = 0.8) -> bool:
        if not left or not right:
            return left == right
        return SequenceMatcher(None, left, right).ratio() >= threshold

    @classmethod
    def _detect_repeated_write_loop(cls, write_history: list[dict[str, str]]) -> bool:
        if len(write_history) < 3:
            return False
        recent_writes = write_history[-3:]
        relative_paths = {entry["relative_path"] for entry in recent_writes}
        if len(relative_paths) != 1:
            return False

        old_strings = [entry.get("old_string", "") for entry in recent_writes]
        if all(old_strings) and len(set(old_strings)) == 1:
            return True

        new_texts = [
            entry.get("new_string") or entry.get("content") or ""
            for entry in recent_writes
        ]
        first_text = new_texts[0]
        return all(
            cls._is_similar_text(first_text, text)
            for text in new_texts[1:]
        )

    @staticmethod
    def _inject_context_diff_into_failure(
        *,
        tool_result: dict[str, Any],
        diff_result: dict[str, Any],
        max_chars: int,
    ) -> None:
        failure_summary = tool_result.get("data", {}).get("failure_summary")
        if not failure_summary or tool_result.get("ok", False):
            return
        diff_text = diff_result.get("data", {}).get("diff_text", "")
        if not diff_text:
            return
        if len(diff_text) > max_chars:
            diff_text = f"{diff_text[:max_chars]}\n...<truncated>"
        failure_summary["context_diff"] = diff_text
        failure_summary["context_diff_changed_files"] = diff_result.get("data", {}).get("changed_files", [])

    @staticmethod
    def _classify_final_state(
        *,
        patch_applied: bool,
        last_test_exit_code: int | None,
        verified_generation: int | None,
        workspace_generation: int,
        ever_used_tool: bool,
        max_iterations_reached: bool,
        model_reported_incomplete: bool,
    ) -> tuple[str, str]:
        if model_reported_incomplete and not max_iterations_reached:
            return "incomplete", "task_incomplete"
        if (
            patch_applied
            and last_test_exit_code == 0
            and verified_generation == workspace_generation
        ):
            return "success", ""
        if not ever_used_tool:
            return "stopped_without_verification", "no_tool_calls"
        if max_iterations_reached:
            return "incomplete", "max_iterations"
        if not patch_applied:
            return "incomplete", "no_patch"
        if last_test_exit_code is not None and last_test_exit_code != 0:
            return "incomplete", "failed_tests"
        if last_test_exit_code is None:
            return "incomplete", "no_tests_run"
        if verified_generation != workspace_generation:
            return "incomplete", "unverified_patch"
        return "incomplete", "unknown"

    def run(
        self,
        *,
        task_path: str | Path,
        repo_root: str | Path,
        policy_path: str | Path | None = None,
    ) -> dict:
        started_at = perf_counter()
        repository_root = Path(repo_root).resolve()
        task = load_task(task_path)
        policy_config = load_policy_config(policy_path)
        LLMConfig.load_env_file(repository_root)
        if self.llm_config == DEFAULT_LLM_CONFIG:
            self.llm_config = LLMConfig.from_policy(policy_config)
        if self.client is None:
            self.client = OpenAICompatibleChatClient(self.llm_config)
        source_repo_path = (repository_root / task.repo_path).resolve()

        if not source_repo_path.exists():
            raise FileNotFoundError(f"任务 repo 不存在: {source_repo_path}")

        task_runs_dir = repository_root / "logs" / "trajectories" / task.task_id
        run_id = next_run_id(task_runs_dir)
        run_paths = build_run_paths(repository_root / "logs" / "trajectories", task.task_id, run_id)
        run_paths.run_dir.mkdir(parents=True, exist_ok=True)

        workspace_copy_started_at = perf_counter()
        copy_repo_to_workspace(source_repo_path, run_paths.workspace_dir)
        workspace_copy_duration_sec = round(perf_counter() - workspace_copy_started_at, 4)

        trace = Trace(task_id=task.task_id, run_id=run_id, started_at=self._utc_timestamp())
        trace.steps.append(
            TraceStep(
                step_index=1,
                action_type="workspace_prep",
                tool_name="copy_workspace",
                tool_input={
                    "source_repo_path": str(source_repo_path),
                    "workspace_path": str(run_paths.workspace_dir),
                },
                tool_output_summary="已完成 benchmark repo 到工作副本的复制。",
                observation="LLM agent 将在隔离 workspace 中运行。",
                decision="继续进入工具观察与修复阶段。",
                timestamp=self._utc_timestamp(),
                duration_sec=workspace_copy_duration_sec,
                tool_metrics={"ignored_dir_count": len(COPY_IGNORE_DIR_NAMES)},
            )
        )
        write_json(run_paths.task_json_path, task)

        tool_executor = ToolExecutor(
            repo_path=run_paths.workspace_dir,
            original_repo_path=source_repo_path,
            policy_config=policy_config,
            test_command=task.test_command,
        )
        system_prompt = build_system_prompt()
        tools = build_tool_definitions()
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": build_user_prompt(task),
            }
        ]

        final_summary = ""
        final_status = "incomplete"
        last_test_exit_code: int | None = None
        last_test_summary = ""
        workspace_generation = 0
        verified_generation: int | None = None
        ever_used_tool = False
        pending_auto_verification = False
        max_iterations_reached = True
        write_history: list[dict[str, str]] = []
        anti_loop_injected = False

        def compress_context_if_needed(reason: str) -> None:
            nonlocal messages
            messages, compressed, before_chars, after_chars = self._compress_messages_if_needed(
                messages,
                max_context_chars=self.llm_config.max_context_chars,
            )
            if not compressed:
                return
            trace.steps.append(
                TraceStep(
                    step_index=len(trace.steps) + 1,
                    action_type="context_compression",
                    tool_name=None,
                    tool_input={"reason": reason},
                    tool_output_summary=f"上下文从 {before_chars} 字符压缩到 {after_chars} 字符。",
                    observation="旧消息已压缩为摘要，保留初始任务输入和最近对话。",
                    decision="继续 LLM 循环，避免上下文超过安全阈值。",
                    timestamp=self._utc_timestamp(),
                    duration_sec=None,
                    tool_metrics={
                        "before_chars": before_chars,
                        "after_chars": after_chars,
                        "max_context_chars": self.llm_config.max_context_chars,
                    },
                )
            )

        for iteration_index in range(self.llm_config.max_iterations):
            response_started_at = perf_counter()
            response = self.client.create_message(
                system_prompt=system_prompt,
                messages=messages,
                tools=tools,
            )
            response_duration_sec = round(perf_counter() - response_started_at, 4)
            assistant_blocks = self._normalize_assistant_blocks(response)
            assistant_text = self._extract_text(assistant_blocks)
            tool_blocks = self._tool_use_blocks(assistant_blocks)

            trace.steps.append(
                TraceStep(
                    step_index=len(trace.steps) + 1,
                    action_type="llm_response",
                    tool_name=None,
                    tool_input={"iteration_index": iteration_index + 1},
                    tool_output_summary=assistant_text[:400] or "模型返回了工具调用。",
                    observation=f"模型在第 {iteration_index + 1} 轮给出响应。",
                    decision="解析工具调用并继续执行。",
                    timestamp=self._utc_timestamp(),
                    duration_sec=response_duration_sec,
                    tool_metrics={"content_block_count": len(assistant_blocks)},
                )
            )
            if assistant_text and tool_blocks:
                trace.steps.append(
                    TraceStep(
                        step_index=len(trace.steps) + 1,
                        action_type="planning",
                        tool_name=None,
                        tool_input={"iteration_index": iteration_index + 1},
                        tool_output_summary=assistant_text[:400],
                        observation=assistant_text,
                        decision="模型在调用工具前给出计划，随后执行同轮工具调用。",
                        timestamp=self._utc_timestamp(),
                        duration_sec=None,
                        tool_metrics={"planned_tool_count": len(tool_blocks)},
                    )
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_blocks,
                }
            )
            compress_context_if_needed("assistant_response")

            tool_results_for_model: list[dict[str, Any]] = []
            if tool_blocks:
                ever_used_tool = True
            parallel_group_counter = 0
            for batch in self._partition_tool_batches(tool_blocks):
                parallel_group_id: str | None = None
                if len(batch) > 1 and all(block.get("name") in READ_ONLY_TOOL_NAMES for block in batch):
                    parallel_group_counter += 1
                    parallel_group_id = f"iter_{iteration_index + 1}_parallel_{parallel_group_counter}"
                    batch_results: list[dict[str, Any] | None] = [None] * len(batch)
                    with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                        future_to_index = {
                            executor.submit(
                                self._execute_tool_block,
                                tool_executor=tool_executor,
                                block=block,
                            ): index
                            for index, block in enumerate(batch)
                        }
                        for future in as_completed(future_to_index):
                            batch_results[future_to_index[future]] = future.result()
                    executed_results = [result for result in batch_results if result is not None]
                else:
                    executed_results = [
                        self._execute_tool_block(
                            tool_executor=tool_executor,
                            block=block,
                        )
                        for block in batch
                    ]

                for executed in executed_results:
                    block = executed["block"]
                    tool_name = executed["tool_name"]
                    tool_input = executed["tool_input"]
                    tool_result = executed["tool_result"]
                    tool_duration_sec = executed["tool_duration_sec"]

                    if tool_name == "read_file" and tool_result.get("ok"):
                        relative_path = tool_result["data"].get("relative_path", "")
                        if relative_path and relative_path not in trace.read_files:
                            trace.read_files.append(relative_path)
                    if tool_name == "run_tests":
                        last_test_exit_code = tool_result.get("data", {}).get("exit_code")
                        last_test_summary = tool_result.get("summary", "")
                        verified_generation = workspace_generation
                        if (
                            last_test_exit_code not in {0, None}
                            and workspace_generation > 0
                        ):
                            diff_result_for_failure = tool_executor.execute("show_diff", {})
                            self._inject_context_diff_into_failure(
                                tool_result=tool_result,
                                diff_result=diff_result_for_failure,
                                max_chars=self.llm_config.max_tool_chars,
                            )
                    if tool_name in {"write_file", "edit_file", "undo"} and tool_result.get("ok"):
                        workspace_generation += 1
                        pending_auto_verification = True
                    write_signature = self._write_signature(tool_name, tool_input)
                    if write_signature and tool_result.get("ok"):
                        write_history.append(write_signature)

                    self._append_tool_trace_step(
                        trace=trace,
                        tool_name=tool_name,
                        tool_input=tool_input,
                        tool_result=tool_result,
                        duration_sec=tool_duration_sec,
                        decision="将工具结果回喂给模型继续决策。",
                        parallel_group_id=parallel_group_id,
                    )

                    anti_loop_message_for_model = ""
                    if (
                        write_signature
                        and tool_result.get("ok")
                        and not anti_loop_injected
                        and self._detect_repeated_write_loop(write_history)
                    ):
                        anti_loop_injected = True
                        trace.steps.append(
                            TraceStep(
                                step_index=len(trace.steps) + 1,
                                action_type="anti_loop",
                                tool_name=None,
                                tool_input={"recent_writes": write_history[-3:]},
                                tool_output_summary="检测到连续相似写操作，已注入反循环提醒。",
                                observation=ANTI_LOOP_MESSAGE,
                                decision="提醒模型重新验证假设，而不是继续相同修改方向。",
                                timestamp=self._utc_timestamp(),
                                duration_sec=None,
                                tool_metrics={
                                    "recent_write_count": 3,
                                    "relative_path": write_history[-1]["relative_path"],
                                },
                            )
                        )
                        anti_loop_message_for_model = f"\n\nANTI_LOOP_NOTICE: {ANTI_LOOP_MESSAGE}"

                    tool_results_for_model.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.get("id", ""),
                            "content": ToolExecutor.summarize_for_model(
                                tool_result,
                                max_chars=self.llm_config.max_tool_chars,
                            ) + anti_loop_message_for_model,
                        }
                    )

            if tool_results_for_model:
                messages.append(
                    {
                        "role": "user",
                        "content": tool_results_for_model,
                    }
                )
                compress_context_if_needed("tool_results")
                continue

            if pending_auto_verification and verified_generation != workspace_generation:
                diff_input: dict[str, Any] = {}
                diff_started_at = perf_counter()
                diff_result_for_model = tool_executor.execute("show_diff", diff_input)
                diff_duration_sec = round(perf_counter() - diff_started_at, 4)
                self._append_tool_trace_step(
                    trace=trace,
                    tool_name="show_diff",
                    tool_input=diff_input,
                    tool_result=diff_result_for_model,
                    duration_sec=diff_duration_sec,
                    decision="模型停止前存在未验证改动，先查看 diff 再自动运行测试。",
                )

                tool_input = {
                    "timeout_sec": 120,
                }
                tool_started_at = perf_counter()
                tool_result = tool_executor.execute("run_tests", tool_input)
                tool_duration_sec = round(perf_counter() - tool_started_at, 4)
                last_test_exit_code = tool_result.get("data", {}).get("exit_code")
                last_test_summary = tool_result.get("summary", "")
                verified_generation = workspace_generation
                pending_auto_verification = False
                if last_test_exit_code not in {0, None}:
                    self._inject_context_diff_into_failure(
                        tool_result=tool_result,
                        diff_result=diff_result_for_model,
                        max_chars=self.llm_config.max_tool_chars,
                    )
                self._append_tool_trace_step(
                    trace=trace,
                    tool_name="run_tests",
                    tool_input=tool_input,
                    tool_result=tool_result,
                    duration_sec=tool_duration_sec,
                    decision="模型停止前存在未验证改动，自动运行测试并把结果回喂给模型。",
                )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "你刚才停止了，但当前 workspace 存在尚未由模型确认的改动。"
                            "系统已自动执行 show_diff 和 run_tests。请根据下面结果继续修正，"
                            "或者在测试通过时给出最终结论。\n\n"
                            "show_diff:\n"
                            f"{ToolExecutor.summarize_for_model(diff_result_for_model, max_chars=self.llm_config.max_tool_chars)}\n\n"
                            "run_tests:\n"
                            f"{ToolExecutor.summarize_for_model(tool_result, max_chars=self.llm_config.max_tool_chars)}"
                        ),
                    }
                )
                compress_context_if_needed("auto_verification")
                continue

            final_summary = assistant_text or "模型结束了当前任务。"
            max_iterations_reached = False
            break

        diff_result = tool_executor.execute("show_diff", {})
        patch_text = diff_result.get("data", {}).get("diff_text", "")
        write_text(run_paths.patch_diff_path, patch_text)
        patch_applied = bool(diff_result.get("data", {}).get("changed_files"))
        final_status, incomplete_reason = self._classify_final_state(
            patch_applied=patch_applied,
            last_test_exit_code=last_test_exit_code,
            verified_generation=verified_generation,
            workspace_generation=workspace_generation,
            ever_used_tool=ever_used_tool,
            max_iterations_reached=max_iterations_reached,
            model_reported_incomplete=self._model_reported_incomplete(final_summary),
        )

        duration_sec = round(perf_counter() - started_at, 4)
        trace.final_status = final_status
        trace.finished_at = self._utc_timestamp()
        context_compression_steps = [
            step for step in trace.steps
            if step.action_type == "context_compression"
        ]

        result = Result(
            task_id=task.task_id,
            run_id=run_id,
            final_status=final_status,
            incomplete_reason=incomplete_reason,
            summary=final_summary or "LLM agent 运行结束。",
            test_command=task.test_command,
            test_exit_code=last_test_exit_code,
            post_test_exit_code=last_test_exit_code,
            post_test_summary=last_test_summary,
            test_summary=last_test_summary or final_summary or "",
            patch_applied=patch_applied,
            patch_summary=diff_result.get("summary", ""),
            modified_files=diff_result.get("data", {}).get("changed_files", []),
            duration_sec=duration_sec,
            tool_stats={
                "policy_id": policy_config.policy_id,
                "agent_type": policy_config.agent_type,
                "llm_provider": self.llm_config.provider,
                "llm_model": self.llm_config.model,
                "total_tool_calls": trace.total_tool_calls,
                "max_iterations": self.llm_config.max_iterations,
                "max_iterations_reached": max_iterations_reached,
                "workspace_generation": workspace_generation,
                "verified_generation": verified_generation,
                "incomplete_reason": incomplete_reason,
                "context_compression_count": len(context_compression_steps),
            },
            recommended_files=trace.read_files[:],
        )

        write_json(run_paths.trace_json_path, trace)
        write_json(run_paths.result_json_path, result)
        write_text(
            run_paths.summary_md_path,
            (
                "# LLM Agent Run Summary\n\n"
                f"- task_id: `{task.task_id}`\n"
                f"- run_id: `{run_id}`\n"
                f"- final_status: `{final_status}`\n"
                f"- agent_type: `{policy_config.agent_type}`\n"
                f"- policy_id: `{policy_config.policy_id}`\n"
                f"- llm_provider: `{self.llm_config.provider}`\n"
                f"- llm_model: `{self.llm_config.model}`\n"
                f"- total_tool_calls: `{trace.total_tool_calls}`\n"
                f"- incomplete_reason: `{incomplete_reason or 'none'}`\n"
                f"- summary: {final_summary or '无'}\n"
            ),
        )

        return {
            "task": task.to_dict(),
            "result": result.to_dict(),
            "trace": trace.to_dict(),
            "run_paths": run_paths.to_dict(),
        }


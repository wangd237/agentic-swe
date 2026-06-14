"""最小 LLM coding agent。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
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

    def _append_tool_trace_step(
        self,
        *,
        trace: Trace,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: dict[str, Any],
        duration_sec: float,
        decision: str,
    ) -> None:
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
                tool_metrics={
                    "ok": tool_result.get("ok", False),
                },
            )
        )
        trace.total_tool_calls += 1

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

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_blocks,
                }
            )

            tool_results_for_model: list[dict[str, Any]] = []
            used_tool = False
            for block in assistant_blocks:
                if block.get("type") != "tool_use":
                    continue
                used_tool = True
                ever_used_tool = True
                tool_name = block["name"]
                tool_input = block.get("input", {})
                tool_started_at = perf_counter()
                tool_result = tool_executor.execute(tool_name, tool_input)
                tool_duration_sec = round(perf_counter() - tool_started_at, 4)

                if tool_name == "read_file" and tool_result.get("ok"):
                    relative_path = tool_result["data"].get("relative_path", "")
                    if relative_path and relative_path not in trace.read_files:
                        trace.read_files.append(relative_path)
                if tool_name == "run_tests":
                    last_test_exit_code = tool_result.get("data", {}).get("exit_code")
                    last_test_summary = tool_result.get("summary", "")
                    verified_generation = workspace_generation
                if tool_name == "write_file" and tool_result.get("ok"):
                    workspace_generation += 1
                    pending_auto_verification = True

                self._append_tool_trace_step(
                    trace=trace,
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_result=tool_result,
                    duration_sec=tool_duration_sec,
                    decision="将工具结果回喂给模型继续决策。",
                )

                tool_results_for_model.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.get("id", ""),
                        "content": ToolExecutor.summarize_for_model(
                            tool_result,
                            max_chars=self.llm_config.max_tool_chars,
                        ),
                    }
                )

            if tool_results_for_model:
                messages.append(
                    {
                        "role": "user",
                        "content": tool_results_for_model,
                    }
                )
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
                continue

            final_summary = assistant_text or "模型结束了当前任务。"
            if last_test_exit_code == 0 and verified_generation == workspace_generation:
                final_status = "success"
            else:
                final_status = "incomplete" if ever_used_tool else "stopped_without_verification"
            break

        diff_result = tool_executor.execute("show_diff", {})
        patch_text = diff_result.get("data", {}).get("diff_text", "")
        write_text(run_paths.patch_diff_path, patch_text)

        duration_sec = round(perf_counter() - started_at, 4)
        trace.final_status = final_status
        trace.finished_at = self._utc_timestamp()

        result = Result(
            task_id=task.task_id,
            run_id=run_id,
            final_status=final_status,
            summary=final_summary or "LLM agent 运行结束。",
            test_command=task.test_command,
            test_exit_code=last_test_exit_code,
            post_test_exit_code=last_test_exit_code,
            post_test_summary=last_test_summary,
            test_summary=last_test_summary or final_summary or "",
            patch_applied=bool(diff_result.get("data", {}).get("changed_files")),
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
                f"- summary: {final_summary or '无'}\n"
            ),
        )

        return {
            "task": task.to_dict(),
            "result": result.to_dict(),
            "trace": trace.to_dict(),
            "run_paths": run_paths.to_dict(),
        }


"""Phase-aware tool policy for the LLM repair agent."""

from __future__ import annotations

from typing import Any

from app.agent.memory import AgentState, PhaseName


WRITE_TOOLS = {"edit_file", "write_file"}
MIN_LOCALIZATION_OVERRIDE_REASON_CHARS = 20

ALLOWED_TOOLS_BY_PHASE: dict[PhaseName, set[str]] = {
    "understand": {"list_files", "grep", "search_code", "read_file", "run_tests"},
    "reproduce": {"grep", "search_code", "search_graph", "run_tests", "read_file", "show_diff"},
    "localize": {"grep", "search_code", "search_graph", "read_file", "python_repl", "run_tests"},
    "patch": {"grep", "search_code", "read_file", "edit_file", "write_file", "show_diff", "undo", "run_tests"},
    "verify": {"run_tests", "show_diff", "read_file", "undo"},
    "final": {"show_diff"},
}


def tool_policy_error(*, tool_name: str, message: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": False,
        "tool_name": tool_name,
        "summary": f"工具策略阻止：{message}",
        "data": {
            "tool_input": tool_input,
            "policy_blocked": True,
        },
        "error": {
            "type": "tool_policy_violation",
            "message": message,
        },
    }


class ToolPolicy:
    """Small gatekeeper that turns agent phases into enforceable constraints."""

    def validate(self, *, state: AgentState, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any] | None:
        allowed_tools = set(ALLOWED_TOOLS_BY_PHASE[state.phase])
        if self.is_patch_recovery_state(state):
            allowed_tools.update(WRITE_TOOLS)
        if tool_name not in allowed_tools:
            return tool_policy_error(
                tool_name=tool_name,
                tool_input=tool_input,
                message=f"`{tool_name}` is not allowed during `{state.phase}` phase.",
            )

        if tool_name in WRITE_TOOLS and not self.can_patch(state):
            return tool_policy_error(
                tool_name=tool_name,
                tool_input=tool_input,
                message=(
                    "PATCH gate is closed. Run tests or explicitly mark weak/static reproduction evidence "
                    "and gather localization evidence before editing files."
                ),
            )

        if tool_name == "run_tests" and self.requires_diff_before_tests(state):
            return tool_policy_error(
                tool_name=tool_name,
                tool_input=tool_input,
                message=(
                    "A patch is pending verification. Call show_diff before running tests."
                ),
            )

        if tool_name in WRITE_TOOLS:
            relative_path = str(tool_input.get("relative_path", "")).replace("\\", "/")
            candidate_paths = {
                candidate.relative_path
                for candidate in state.localization_candidates
            }
            if relative_path and relative_path not in candidate_paths:
                override_reason = str(tool_input.get("localization_override_reason", "")).strip()
                if len(override_reason) >= MIN_LOCALIZATION_OVERRIDE_REASON_CHARS:
                    return None
                return tool_policy_error(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    message=(
                        f"`{relative_path}` must be a localization candidate before it can be modified. "
                        "Provide a specific localization_override_reason to override this gate."
                    ),
                )

        if tool_name == "search_graph":
            if state.search_graph_calls >= 3:
                return tool_policy_error(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    message=(
                        "search_graph 已被调用 3 次，达到单次 run 上限。"
                        "请基于已有搜索结果和已读文件做出定位判断。"
                    ),
                )
            state.record_search_graph_call()

        return None

    @staticmethod
    def can_patch(state: AgentState) -> bool:
        has_patch_entry_evidence = (
            state.has_reproduction_evidence
            or state.reproduction_evidence_kind == "weak_static"
        )
        return (
            state.phase in {"patch", "localize"}
            and has_patch_entry_evidence
            and bool(state.localization_candidates)
            and (state.phase == "patch" or ToolPolicy.is_patch_recovery_state(state))
        )

    @staticmethod
    def is_patch_recovery_state(state: AgentState) -> bool:
        return (
            state.phase == "localize"
            and state.workspace_generation > 0
            and state.has_reproduction_evidence
            and bool(state.localization_candidates)
        )

    @staticmethod
    def requires_diff_before_tests(state: AgentState) -> bool:
        return (
            state.workspace_generation > 0
            and state.diff_observed_generation != state.workspace_generation
        )


def next_phase_after_tool(*, state: AgentState, tool_name: str, tool_result: dict[str, Any]) -> PhaseName:
    """Advance the lightweight state machine from observed tool evidence."""

    if tool_name == "run_tests":
        if state.has_reproduction_evidence and state.localization_candidates:
            return "patch"
        if state.phase in {"understand", "reproduce"}:
            return "localize"
        if state.phase == "patch":
            return "verify"
        return state.phase

    if tool_name in {"grep", "search_code", "search_graph", "read_file", "python_repl"}:
        if state.has_reproduction_evidence and state.localization_candidates:
            return "patch"
        if state.phase == "understand":
            return "reproduce"
        return state.phase

    if tool_name in WRITE_TOOLS and tool_result.get("ok"):
        return "verify"

    if tool_name == "show_diff" and state.phase == "verify":
        return "verify"

    return state.phase

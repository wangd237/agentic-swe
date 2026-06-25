"""Phase-aware LLM tool schema routing."""

from __future__ import annotations

from app.agent.memory import AgentState, PhaseName
from app.agent.tool_definitions import build_tool_definitions
from app.agent.tool_policy import ALLOWED_TOOLS_BY_PHASE, ToolPolicy


SCHEMA_STRATEGY_PHASE_FILTERED = "phase_filtered"
SCHEMA_STRATEGY_PHASE_STATE_FILTERED = "phase_state_filtered"


def build_tools_for_phase(phase: PhaseName) -> list[dict]:
    """Return only the tool schemas visible to the model for the current phase."""

    allowed_tool_names = ALLOWED_TOOLS_BY_PHASE[phase]
    return [
        tool
        for tool in build_tool_definitions()
        if tool["name"] in allowed_tool_names
    ]


def build_tools_for_state(state: AgentState) -> list[dict]:
    """Return phase tools after applying deterministic state gates."""

    visible_tool_names = set(ALLOWED_TOOLS_BY_PHASE[state.phase])
    if ToolPolicy.is_patch_recovery_state(state):
        visible_tool_names.update({"edit_file", "write_file", "show_diff", "undo"})
    if state.workspace_generation <= 0:
        visible_tool_names.discard("undo")
    if state.phase == "verify" and ToolPolicy.requires_diff_before_tests(state):
        visible_tool_names.discard("run_tests")

    return [
        tool
        for tool in build_tool_definitions()
        if tool["name"] in visible_tool_names
    ]


def tool_names(tools: list[dict]) -> list[str]:
    """Return tool names in the same order as the schema payload."""

    return [str(tool["name"]) for tool in tools]

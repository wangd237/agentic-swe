from __future__ import annotations

from app.agent.memory import AgentState


def test_agent_state_remembers_deduped_trimmed_hypotheses() -> None:
    state = AgentState()

    state.remember_hypothesis("  first   hypothesis  ")
    state.remember_hypothesis("first hypothesis")
    state.remember_hypothesis("x" * 600, max_chars=20)

    assert state.hypotheses == [
        "first hypothesis",
        ("x" * 17) + "...",
    ]

"""Tests for lightweight exploration stagnation detection and checkpoint delivery."""

from app.agent.exploration import ExplorationMonitor
from app.agent.llm_client import OpenAICompatibleChatClient
from app.agent.llm_prompts import EXPLORATION_CHECKPOINT_MESSAGE


def _observe(monitor: ExplorationMonitor, name: str, **kwargs: object) -> None:
    monitor.observe(name, kwargs, {"ok": True, "data": {}})


def test_checkpoint_detects_repeated_search_without_overreacting_to_short_exploration() -> None:
    monitor = ExplorationMonitor()
    for i in range(4):
        _observe(monitor, "read_file", relative_path=f"pkg/file_{i}.py")
    assert not monitor.should_trigger()
    _observe(monitor, "read_file", relative_path="pkg/file_1.py")
    assert not monitor.should_trigger()
    _observe(monitor, "read_file", relative_path="pkg/file_1.py")
    assert monitor.should_trigger()
    assert monitor.consecutive_calls == 6
    assert monitor.repeated_calls == 2
    monitor.mark_triggered()
    assert not monitor.should_trigger()


def test_checkpoint_catches_long_search_without_exact_duplicates() -> None:
    monitor = ExplorationMonitor()
    for i in range(7):
        _observe(monitor, "search_code", query=f"symbol_{i}")
    assert not monitor.should_trigger()
    _observe(monitor, "grep", pattern="different")
    assert monitor.should_trigger()


def test_verification_resets_stagnation_counter_and_blocked_reads_are_ignored() -> None:
    monitor = ExplorationMonitor()
    for _ in range(5):
        _observe(monitor, "read_file", relative_path="pkg/file.py")
    monitor.observe(
        "read_file",
        {"relative_path": "pkg/file.py"},
        {"ok": False, "data": {"policy_blocked": True}},
    )
    assert monitor.consecutive_calls == 5
    _observe(monitor, "run_tests")
    assert monitor.consecutive_calls == 0
    assert not monitor.should_trigger()


def test_checkpoint_in_tool_result_is_transmitted_to_openai_client() -> None:
    tool_result = {
        "type": "tool_result",
        "tool_use_id": "search_1",
        "content": "Found relevant function",
    }
    tool_result["content"] += "\n\n" + EXPLORATION_CHECKPOINT_MESSAGE
    converted = OpenAICompatibleChatClient._messages_to_openai(
        system_prompt="System",
        messages=[
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "search_1", "name": "search_code",
                     "input": {"query": "bug"}},
                ],
            },
            {"role": "user", "content": [tool_result]},
        ],
    )
    assert converted[-1]["role"] == "tool"
    assert "EXPLORATION_CHECKPOINT" in converted[-1]["content"]
    assert converted[-1]["tool_call_id"] == "search_1"

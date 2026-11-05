"""Context summary tests independent of the live LLM provider."""

from app.llm.context import AgentContextMixin


def test_semantic_summary_preserves_prefix_and_recent_tool_pair():
    task = {"role": "user", "content": "Fix config.py error"}
    old = [{"role": "assistant", "content": "Investigate: " + "x" * 1800},
           {"role": "user", "content": "Earlier evidence: " + "y" * 1800}]
    call = {"role": "assistant", "content": [{"type": "tool_use", "id": "abc", "name": "read_file", "input": {"relative_path": "config.py"}}]}
    result = {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "abc", "content": "Current read evidence"}]}
    recent = {"role": "assistant", "content": "Need a focused fix"}
    captured = []

    def summarize(prefix):
        captured.append(prefix)
        return "## Confirmed findings\n- config.py is the relevant file."

    messages = [task, *old, call, result, recent]
    compressed, changed, before, after = AgentContextMixin._compress_messages_if_needed(
        messages,
        max_context_chars=1,
        context_window_tokens=200,
        reserve_tokens=32,
        measured_prompt_tokens=None,
        summary_builder=summarize,
    )
    assert changed and after < before
    assert captured == [[task, *old]]
    assert compressed == [task, {"role": "system", "content": "Earlier context has been summarized. Key findings so far:\n" + summarize([])}, call, result, recent]


def test_compaction_never_expands_history():
    task = {"role": "user", "content": "issue"}
    messages = [task, {"role": "assistant", "content": "a"}, {"role": "assistant", "content": "b"},
                {"role": "assistant", "content": "c"}, {"role": "assistant", "content": "d"}]
    compressed, changed, before, after = AgentContextMixin._compress_messages_if_needed(
        messages, max_context_chars=1, context_window_tokens=20, reserve_tokens=1,
        summary_builder=lambda prefix: "a much longer summary " * 500,
    )
    assert not changed and before == after and compressed == messages


def test_token_anchor_accounts_for_new_messages():
    first = [{"role": "user", "content": "hello"}]
    second = [*first, {"role": "user", "content": "new" * 1000}]
    baseline = AgentContextMixin._message_char_estimate(first)
    estimate = AgentContextMixin._estimate_context_tokens(second, measured_prompt_tokens=100, measured_message_chars=baseline)
    assert estimate > 1000

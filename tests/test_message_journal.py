"""Regression tests for append-only message-surface persistence."""

import json

import pytest

from app.runtime.message_journal import MessageJournal


def test_journal_appends_and_replays_compaction_without_losing_original(tmp_path):
    path = tmp_path / "messages.jsonl"
    journal = MessageJournal(path)
    first = {"role": "user", "content": "repair bug"}
    call = {"role": "assistant", "content": [{"type": "tool_use", "id": "tc1", "name": "read_file", "input": {"relative_path": "a.py"}}]}
    result = {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tc1", "content": "200 lines of code"}]}
    messages = [first, call, result]
    journal.sync(messages)
    assert MessageJournal.replay(path) == messages

    summary = {"role": "system", "content": "Confirmed: a.py read. Next inspect parser."}
    compacted = [first, summary]
    journal.sync(compacted, reason="context_compaction", metadata={"method": "llm"})
    assert MessageJournal.replay(path) == compacted

    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [event["seq"] for event in events] == list(range(1, len(events) + 1))
    assert events[-1]["op"] == "replace"
    assert events[-1]["reason"] == "context_compaction"
    assert events[-1]["delete_count"] == 2
    assert any(event.get("message") == result for event in events)
    journal.sync(compacted)
    assert len(path.read_text(encoding="utf-8").splitlines()) == len(events)


def test_journal_replays_message_rewrites_and_ignores_torn_tail(tmp_path):
    path = tmp_path / "messages.jsonl"
    journal = MessageJournal(path)
    journal.sync([{"role": "user", "content": "original"}])
    journal.sync([{"role": "user", "content": "edited"}], reason="budget_notice")
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"seq":3,"op":"append"')
    assert MessageJournal.replay(path) == [{"role": "user", "content": "edited"}]


def test_journal_rejects_invalid_middle_record(tmp_path):
    path = tmp_path / "messages.jsonl"
    path.write_text('{"seq":1,"op":"unknown"}\n', encoding="utf-8")
    with pytest.raises(ValueError):
        MessageJournal.replay(path)

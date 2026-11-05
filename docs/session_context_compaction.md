# Session journal and context compaction

The coding agent now uses three distinct records:

- `trace.json`: execution/verification diagnostics, written at run end.
- `messages.jsonl`: append-only log of *model-visible* message changes.
- `strategy_memory.jsonl`: distilled cross-run repair experiences.

## Journal format

`app/runtime/message_journal.py` records `append` events for new messages and
`replace` events for in-place edits, tool-result pruning and context
compaction. Each event has a monotonic `seq`. A replacement records the old
active-surface slice (`start`, `delete_count`) and the new messages, but
the original appended events remain in the log. A compaction replacement
includes `reason=context_compaction` and metadata describing whether it
used the LLM or rules. `MessageJournal.replay(path)` reconstructs the active
surface and tolerates an incomplete last JSONL row.

This is a lightweight replay mechanism, **not** full crash-resume: reproducing
workspace changes, git state and in-flight tool execution is out of scope.
The journal writes the messages after model-facing tool output summarization;
large full tool outputs still live under `tool_outputs/*.json`.

## Compaction

At the configured token trigger, the agent first trims oversized tool results.
It then retains the initial task and most recent complete tool-call/result
pairs, asking the same configured model to distill the earlier *complete*
history. The summarizer cannot call tools and must produce a structured
checkpoint with important files, evidence, failed approaches, and next step.
Any error or empty summary falls back to the rule-based checkpoint. No
compaction is committed if the replacement is not smaller.

Optional fields in a policy JSON:

```json
{
  "llm_compaction_mode": "llm",
  "llm_compaction_trigger_tokens": 32000,
  "llm_compaction_max_output_tokens": 2048
}
```

`llm_compaction_trigger_tokens` is a cost-oriented soft cap; the effective
trigger is the smaller of this value and
`context_window_tokens - reserve_tokens`. Omit it to retain the old
window-pressure trigger. Set mode to `rules` to avoid extra LLM calls.
Model usage from summarization is an auxiliary cost, not included in the
existing agent-step usage counters.

## Caveats

- Keep complete tool-call/result pairs together at compaction boundaries.
- Trace and journal may contain sensitive source code. Treat logs as private.
- The journal records active-surface changes but does not itself drive
  the live `messages` list or restore an interrupted run.
- Cost and fix-quality A/B evaluations are required before treating this as
  a proven token or success-rate improvement.

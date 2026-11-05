# Context footprint audit

This work adds a read-only diagnostic script for existing Agent traces. It does not modify tool outputs or Agent decisions.

Run from the repository root:

```bash
python scripts/analyze_context_footprint.py --include-evidence
python scripts/analyze_context_footprint.py --root logs/trajectories --context-window-tokens 131072 --threshold-ratio 0.80
```

Output: logs/summaries/context_footprint/{report.md,summary.json,runs.csv,tool_calls.csv,tool_summary.csv,prompt_deltas.csv}.

The analysis reports per-tool invocation counts, raw/visible result sizes when observed, P50/P95 and coverage, prompt token deltas between calls, context-compression events and descriptive task outcome groups.

New runs record raw_result_chars, prepared_tool_result_chars and model_visible_chars as metadata. The actual model-visible metric is measured at the outbound model call, after context compaction, not from trace.observation. No prompts or full tool outputs are copied into reports.

Older traces often lack the raw result and actual model-visible size; unknown data remains empty instead of substituting the limited trace preview. Full raw output may be recovered from referenced tool_outputs spills. Prompt deltas are not tool-specific token cost, because other messages and schemas can also change. Outcome associations are observational, not causal.

Only provide a window size if it matches the model(s) under analysis; otherwise cross-model utilization is misleading.

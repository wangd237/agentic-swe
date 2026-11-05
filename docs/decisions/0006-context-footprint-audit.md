# Context footprint audit

This work adds a read-only diagnostic script for existing Agent traces. It does not modify tool outputs or Agent decisions.

Run from the repository root:

```bash
python scripts/analyze_context_footprint.py --include-evidence
python scripts/analyze_context_footprint.py --root logs/trajectories --context-window-tokens 131072 --threshold-ratio 0.80
```

Output: logs/summaries/context_footprint/{report.md,summary.json,runs.csv,tool_calls.csv,tool_summary.csv,prompt_deltas.csv}.

The analysis reports per-tool invocation counts, raw/visible result sizes when observed, P50/P95 and coverage, repeated tool-result characters in outgoing requests, prompt token deltas, context-compression events and descriptive task outcome groups.

New runs record raw_result_chars, prepared_tool_result_chars and model_visible_chars as metadata. Each LLM response also records request_tool_result_chars, request_tool_result_count and request_tool_result_chars_by_tool, allowing repeated historical tool results to be counted across subsequent requests. The actual model-visible metric is measured at the outbound model call, after context compaction, not from trace.observation. No prompts or full tool outputs are copied into reports.

Older traces often lack the raw result and actual model-visible size; unknown data remains empty instead of substituting the limited trace preview. Full raw output may be recovered from referenced tool_outputs spills. Prompt deltas are not tool-specific token cost, because other messages and schemas can also change. Repeated outbound tool-result characters are useful to locate cumulative context growth but are NOT token counts. Outcome associations are observational, not causal.

Only provide a window size if it matches the model(s) under analysis; otherwise cross-model utilization is misleading.

## Preliminary repository evidence observation (2026-11-05)

The GitHub connector successfully parsed 17 of the 19 checked-in trace files in this review (13 semi-real and 4 real-issue runs; two other large traces were not fully available through the connector). The local script can read those files directly from a checkout.

- 236 recorded tool calls: read_file 82, run_tests 55, grep 26, edit_file 26, list_files 22, show_diff 20, search_code 3, undo 1, python_repl 1.
- Four accessible real-issue runs had 118 tool calls; read_file alone represented 54 calls. This is a frequency observation, not a token-cost ranking.
- The 4 real-issue runs provide 74 prompt_tokens measurements; their largest prompt was 40,600 tokens. None recorded a context_compression event.
- The 13 older semi-real traces have 66 LLM response events but no recorded prompt_tokens values. They cannot support precise usage-threshold evaluation.

Do not infer tool-result size from these counts. In particular, legacy traces contain only short audit previews and often lack the full model-visible result. To rank tools by actual returned volume, run this analyzer on fresh telemetry-bearing local logs and inspect its coverage columns.

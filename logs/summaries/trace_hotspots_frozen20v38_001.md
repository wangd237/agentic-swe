# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v37_001`
- improved_batch_run_id: `batch_run_frozen20v38_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5687`
- improved_average_duration_sec: `0.5427`
- average_duration_delta_sec: `-0.026`

## Top Task Regressions

- `task_024`: `0.5584` -> `0.5641` (delta: `0.0057`, dominant_tool: `run_tests`, dominant_delta: `0.0042`)

## Top Tool Regressions

- 当前没有检测到工具级时延回升

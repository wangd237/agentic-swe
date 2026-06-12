# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v44_002`
- improved_batch_run_id: `batch_run_frozen20v45_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.528`
- improved_average_duration_sec: `0.512`
- average_duration_delta_sec: `-0.016`

## Top Task Regressions

- `task_030`: `0.4967` -> `0.5302` (delta: `0.0335`, dominant_tool: `run_tests`, dominant_delta: `0.0209`)
- `task_040`: `0.5279` -> `0.542` (delta: `0.0141`, dominant_tool: `search_code`, dominant_delta: `0.0097`)
- `task_038`: `0.5179` -> `0.5281` (delta: `0.0102`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0078`)
- `task_036`: `0.5186` -> `0.5246` (delta: `0.006`, dominant_tool: `search_code`, dominant_delta: `0.0062`)
- `task_042`: `0.5179` -> `0.5239` (delta: `0.006`, dominant_tool: `run_tests`, dominant_delta: `0.0043`)
- `task_032`: `0.5054` -> `0.507` (delta: `0.0016`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0078`)

## Top Tool Regressions

- 当前没有检测到工具级时延回升

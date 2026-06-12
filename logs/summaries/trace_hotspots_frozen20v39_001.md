# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v38_001`
- improved_batch_run_id: `batch_run_frozen20v39_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5427`
- improved_average_duration_sec: `0.5443`
- average_duration_delta_sec: `0.0016`

## Top Task Regressions

- `task_008`: `0.5208` -> `0.5499` (delta: `0.0291`, dominant_tool: `run_tests`, dominant_delta: `0.0185`)
- `task_016`: `0.5342` -> `0.5583` (delta: `0.0241`, dominant_tool: `run_tests`, dominant_delta: `0.0242`)
- `task_040`: `0.5359` -> `0.557` (delta: `0.0211`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0103`)
- `task_017`: `0.5481` -> `0.5686` (delta: `0.0205`, dominant_tool: `run_tests`, dominant_delta: `0.0185`)
- `task_010`: `0.5409` -> `0.5578` (delta: `0.0169`, dominant_tool: `run_tests`, dominant_delta: `0.0151`)
- `task_036`: `0.5074` -> `0.5208` (delta: `0.0134`, dominant_tool: `run_tests`, dominant_delta: `0.0113`)
- `task_013`: `0.5253` -> `0.5363` (delta: `0.011`, dominant_tool: `run_tests`, dominant_delta: `0.0135`)
- `task_019`: `0.5425` -> `0.5505` (delta: `0.008`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0095`)
- `task_038`: `0.5383` -> `0.5439` (delta: `0.0056`, dominant_tool: `run_tests`, dominant_delta: `0.0075`)
- `task_024`: `0.5641` -> `0.569` (delta: `0.0049`, dominant_tool: `run_tests`, dominant_delta: `0.0052`)

## Top Tool Regressions

- `unattributed_overhead`: baseline avg `0.0121` -> improved avg `0.0134` (total delta: `0.026`)
- `search_code`: baseline avg `0.0063` -> improved avg `0.0071` (total delta: `0.0157`)
- `copy_workspace`: baseline avg `0.0021` -> improved avg `0.0022` (total delta: `0.0032`)
- `list_files`: baseline avg `0.0007` -> improved avg `0.0007` (total delta: `0.0006`)

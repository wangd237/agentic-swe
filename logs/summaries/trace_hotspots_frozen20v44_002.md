# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v43_001`
- improved_batch_run_id: `batch_run_frozen20v44_002`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5291`
- improved_average_duration_sec: `0.528`
- average_duration_delta_sec: `-0.0011`

## Top Task Regressions

- `task_046`: `0.5159` -> `0.5559` (delta: `0.04`, dominant_tool: `run_tests`, dominant_delta: `0.0309`)
- `task_024`: `0.5141` -> `0.5368` (delta: `0.0227`, dominant_tool: `run_tests`, dominant_delta: `0.0213`)
- `task_028`: `0.5147` -> `0.5347` (delta: `0.02`, dominant_tool: `run_tests`, dominant_delta: `0.0142`)
- `task_016`: `0.5344` -> `0.5482` (delta: `0.0138`, dominant_tool: `run_tests`, dominant_delta: `0.0197`)
- `task_026`: `0.5344` -> `0.548` (delta: `0.0136`, dominant_tool: `run_tests`, dominant_delta: `0.0153`)
- `task_044`: `0.5207` -> `0.5333` (delta: `0.0126`, dominant_tool: `search_code`, dominant_delta: `0.0049`)
- `task_034`: `0.5134` -> `0.525` (delta: `0.0116`, dominant_tool: `copy_workspace`, dominant_delta: `0.0146`)
- `task_022`: `0.5129` -> `0.5178` (delta: `0.0049`, dominant_tool: `run_tests`, dominant_delta: `0.0057`)
- `task_019`: `0.5402` -> `0.5435` (delta: `0.0033`, dominant_tool: `run_tests`, dominant_delta: `0.0139`)

## Top Tool Regressions

- `unattributed_overhead`: baseline avg `0.0117` -> improved avg `0.0125` (total delta: `0.0163`)
- `copy_workspace`: baseline avg `0.0025` -> improved avg `0.0033` (total delta: `0.0159`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0013` (total delta: `0.0007`)
- `list_files`: baseline avg `0.0007` -> improved avg `0.0007` (total delta: `0.0006`)

# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v36_001`
- improved_batch_run_id: `batch_run_frozen20v37_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5386`
- improved_average_duration_sec: `0.5687`
- average_duration_delta_sec: `0.0301`

## Top Task Regressions

- `task_022`: `0.5138` -> `0.5829` (delta: `0.0691`, dominant_tool: `run_tests`, dominant_delta: `0.0663`)
- `task_026`: `0.5386` -> `0.6076` (delta: `0.069`, dominant_tool: `run_tests`, dominant_delta: `0.057`)
- `task_046`: `0.5315` -> `0.5803` (delta: `0.0488`, dominant_tool: `run_tests`, dominant_delta: `0.0396`)
- `task_010`: `0.5405` -> `0.5867` (delta: `0.0462`, dominant_tool: `run_tests`, dominant_delta: `0.0467`)
- `task_019`: `0.5319` -> `0.5739` (delta: `0.042`, dominant_tool: `run_tests`, dominant_delta: `0.0293`)
- `task_013`: `0.5292` -> `0.5692` (delta: `0.04`, dominant_tool: `run_tests`, dominant_delta: `0.0428`)
- `task_006`: `0.53` -> `0.5687` (delta: `0.0387`, dominant_tool: `run_tests`, dominant_delta: `0.042`)
- `task_038`: `0.5319` -> `0.5628` (delta: `0.0309`, dominant_tool: `run_tests`, dominant_delta: `0.0498`)
- `task_016`: `0.5236` -> `0.5534` (delta: `0.0298`, dominant_tool: `run_tests`, dominant_delta: `0.0242`)
- `task_008`: `0.5335` -> `0.5613` (delta: `0.0278`, dominant_tool: `run_tests`, dominant_delta: `0.0264`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.511` -> improved avg `0.5414` (total delta: `0.6094`)
- `unattributed_overhead`: baseline avg `0.0119` -> improved avg `0.0129` (total delta: `0.0201`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0014` (total delta: `0.0047`)
- `show_diff`: baseline avg `0.0024` -> improved avg `0.0026` (total delta: `0.0037`)
- `read_file`: baseline avg `0.001` -> improved avg `0.0011` (total delta: `0.0017`)

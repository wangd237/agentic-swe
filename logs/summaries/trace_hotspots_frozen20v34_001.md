# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v33_001`
- improved_batch_run_id: `batch_run_frozen20v34_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5379`
- improved_average_duration_sec: `0.5368`
- average_duration_delta_sec: `-0.0011`

## Top Task Regressions

- `task_036`: `0.5054` -> `0.5634` (delta: `0.058`, dominant_tool: `run_tests`, dominant_delta: `0.0446`)
- `task_038`: `0.5131` -> `0.55` (delta: `0.0369`, dominant_tool: `run_tests`, dominant_delta: `0.0188`)
- `task_024`: `0.5432` -> `0.5701` (delta: `0.0269`, dominant_tool: `run_tests`, dominant_delta: `0.0233`)
- `task_034`: `0.5135` -> `0.5402` (delta: `0.0267`, dominant_tool: `run_tests`, dominant_delta: `0.0338`)
- `task_032`: `0.5209` -> `0.5431` (delta: `0.0222`, dominant_tool: `run_tests`, dominant_delta: `0.0225`)
- `task_030`: `0.519` -> `0.5359` (delta: `0.0169`, dominant_tool: `run_tests`, dominant_delta: `0.0309`)
- `task_028`: `0.5521` -> `0.5671` (delta: `0.015`, dominant_tool: `run_tests`, dominant_delta: `0.0214`)
- `task_040`: `0.5149` -> `0.5275` (delta: `0.0126`, dominant_tool: `run_tests`, dominant_delta: `0.0145`)
- `task_019`: `0.5447` -> `0.5538` (delta: `0.0091`, dominant_tool: `run_tests`, dominant_delta: `0.0157`)
- `task_022`: `0.5482` -> `0.5573` (delta: `0.0091`, dominant_tool: `run_tests`, dominant_delta: `0.0113`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.4978` -> improved avg `0.5076` (total delta: `0.1962`)
- `copy_workspace`: baseline avg `0.0021` -> improved avg `0.0023` (total delta: `0.0037`)
- `show_diff`: baseline avg `0.0025` -> improved avg `0.0025` (total delta: `0.0012`)
- `read_file`: baseline avg `0.001` -> improved avg `0.0011` (total delta: `0.0011`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0012` (total delta: `0.0003`)

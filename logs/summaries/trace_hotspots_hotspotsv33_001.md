# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_hotspotsv32baseline_001`
- improved_batch_run_id: `batch_run_hotspotsv33_001`
- common_task_count: `4`
- baseline_average_duration_sec: `0.5589`
- improved_average_duration_sec: `0.5569`
- average_duration_delta_sec: `-0.002`

## Top Task Regressions

- `task_038`: `0.5357` -> `0.5473` (delta: `0.0116`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0148`)
- `task_040`: `0.5529` -> `0.554` (delta: `0.0011`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.01`)

## Top Tool Regressions

- `unattributed_overhead`: baseline avg `0.0057` -> improved avg `0.0149` (total delta: `0.0365`)
- `search_code`: baseline avg `0.0227` -> improved avg `0.0253` (total delta: `0.0104`)
- `copy_workspace`: baseline avg `0.0017` -> improved avg `0.0019` (total delta: `0.0007`)
- `show_diff`: baseline avg `0.0015` -> improved avg `0.0016` (total delta: `0.0003`)
- `read_file`: baseline avg `0.0008` -> improved avg `0.0009` (total delta: `0.0002`)
- `list_files`: baseline avg `0.0004` -> improved avg `0.0004` (total delta: `0.0001`)
- `rule_based_patch`: baseline avg `0.0008` -> improved avg `0.0009` (total delta: `0.0001`)

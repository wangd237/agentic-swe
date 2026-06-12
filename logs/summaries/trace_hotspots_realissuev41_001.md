# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev40_001`
- improved_batch_run_id: `batch_run_realissuev41_001`
- common_task_count: `37`
- baseline_average_duration_sec: `0.5717`
- improved_average_duration_sec: `0.5177`
- average_duration_delta_sec: `-0.054`

## Top Task Regressions

- `task_032`: `0.5456` -> `0.5494` (delta: `0.0038`, dominant_tool: `search_code`, dominant_delta: `0.025`)

## Top Tool Regressions

- `show_diff`: baseline avg `0.0015` -> improved avg `0.0024` (total delta: `0.0334`)
- `unattributed_overhead`: baseline avg `0.0114` -> improved avg `0.0119` (total delta: `0.0185`)
- `rule_based_patch`: baseline avg `0.0008` -> improved avg `0.0012` (total delta: `0.0148`)
- `read_file`: baseline avg `0.0008` -> improved avg `0.0011` (total delta: `0.0113`)
- `copy_workspace`: baseline avg `0.002` -> improved avg `0.0022` (total delta: `0.0055`)
- `list_files`: baseline avg `0.0004` -> improved avg `0.0006` (total delta: `0.0054`)

# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev37_001`
- improved_batch_run_id: `batch_run_realissuev38_001`
- common_task_count: `34`
- baseline_average_duration_sec: `0.6038`
- improved_average_duration_sec: `0.5539`
- average_duration_delta_sec: `-0.0499`

## Top Task Regressions

- `task_061`: `0.5511` -> `0.5613` (delta: `0.0102`, dominant_tool: `search_code`, dominant_delta: `0.0126`)

## Top Tool Regressions

- `search_code`: baseline avg `0.0075` -> improved avg `0.0156` (total delta: `0.2771`)
- `read_file`: baseline avg `0.0011` -> improved avg `0.0012` (total delta: `0.0019`)

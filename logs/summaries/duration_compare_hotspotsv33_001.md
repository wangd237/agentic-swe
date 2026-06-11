# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_hotspotsv32baseline_001`
- improved_batch_run_id: `batch_run_hotspotsv33_001`
- created_at: `2026-06-11T14:33:36.560561+00:00`

## Task Set

- baseline_task_count: `4`
- improved_task_count: `4`
- common_task_count: `4`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5589`
- improved_average_duration_sec_all: `0.5569`
- baseline_average_duration_sec_common: `0.5589`
- improved_average_duration_sec_common: `0.5569`
- common_average_delta_sec: `-0.002`
- baseline_total_duration_sec_common: `2.2356`
- improved_total_duration_sec_common: `2.2274`

## Top Regressions

- `task_038`: `0.5357` -> `0.5473` (delta: `0.0116`, tool_calls: `8` -> `8`)
- `task_040`: `0.5529` -> `0.554` (delta: `0.0011`, tool_calls: `12` -> `12`)

## Top Improvements

- `task_036`: `0.5867` -> `0.5702` (delta: `-0.0165`, tool_calls: `8` -> `8`)
- `task_034`: `0.5603` -> `0.5559` (delta: `-0.0044`, tool_calls: `11` -> `11`)

# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v44_002`
- improved_batch_run_id: `batch_run_frozen20v45_001`
- created_at: `2026-06-12T04:04:40.646787+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.528`
- improved_average_duration_sec_all: `0.512`
- baseline_average_duration_sec_common: `0.528`
- improved_average_duration_sec_common: `0.512`
- common_average_delta_sec: `-0.016`
- baseline_total_duration_sec_common: `10.5604`
- improved_total_duration_sec_common: `10.2395`

## Top Regressions

- `task_030`: `0.4967` -> `0.5302` (delta: `0.0335`, tool_calls: `8` -> `8`)
- `task_040`: `0.5279` -> `0.542` (delta: `0.0141`, tool_calls: `12` -> `12`)
- `task_038`: `0.5179` -> `0.5281` (delta: `0.0102`, tool_calls: `8` -> `8`)
- `task_036`: `0.5186` -> `0.5246` (delta: `0.006`, tool_calls: `8` -> `8`)
- `task_042`: `0.5179` -> `0.5239` (delta: `0.006`, tool_calls: `10` -> `10`)
- `task_032`: `0.5054` -> `0.507` (delta: `0.0016`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_026`: `0.548` -> `0.4899` (delta: `-0.0581`, tool_calls: `9` -> `9`)
- `task_013`: `0.5549` -> `0.5005` (delta: `-0.0544`, tool_calls: `9` -> `9`)
- `task_016`: `0.5482` -> `0.5018` (delta: `-0.0464`, tool_calls: `12` -> `12`)
- `task_024`: `0.5368` -> `0.4959` (delta: `-0.0409`, tool_calls: `9` -> `9`)
- `task_019`: `0.5435` -> `0.5027` (delta: `-0.0408`, tool_calls: `10` -> `10`)
- `task_028`: `0.5347` -> `0.5036` (delta: `-0.0311`, tool_calls: `8` -> `8`)
- `task_046`: `0.5559` -> `0.5335` (delta: `-0.0224`, tool_calls: `8` -> `8`)
- `task_006`: `0.5262` -> `0.5069` (delta: `-0.0193`, tool_calls: `9` -> `9`)
- `task_034`: `0.525` -> `0.5078` (delta: `-0.0172`, tool_calls: `11` -> `11`)
- `task_008`: `0.5465` -> `0.5295` (delta: `-0.017`, tool_calls: `9` -> `9`)

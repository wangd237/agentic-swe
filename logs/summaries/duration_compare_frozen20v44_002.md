# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v43_001`
- improved_batch_run_id: `batch_run_frozen20v44_002`
- created_at: `2026-06-12T03:51:59.793809+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5291`
- improved_average_duration_sec_all: `0.528`
- baseline_average_duration_sec_common: `0.5291`
- improved_average_duration_sec_common: `0.528`
- common_average_delta_sec: `-0.0011`
- baseline_total_duration_sec_common: `10.5813`
- improved_total_duration_sec_common: `10.5604`

## Top Regressions

- `task_046`: `0.5159` -> `0.5559` (delta: `0.04`, tool_calls: `8` -> `8`)
- `task_024`: `0.5141` -> `0.5368` (delta: `0.0227`, tool_calls: `9` -> `9`)
- `task_028`: `0.5147` -> `0.5347` (delta: `0.02`, tool_calls: `8` -> `8`)
- `task_016`: `0.5344` -> `0.5482` (delta: `0.0138`, tool_calls: `12` -> `12`)
- `task_026`: `0.5344` -> `0.548` (delta: `0.0136`, tool_calls: `9` -> `9`)
- `task_044`: `0.5207` -> `0.5333` (delta: `0.0126`, tool_calls: `8` -> `8`)
- `task_034`: `0.5134` -> `0.525` (delta: `0.0116`, tool_calls: `11` -> `11`)
- `task_022`: `0.5129` -> `0.5178` (delta: `0.0049`, tool_calls: `9` -> `9`)
- `task_019`: `0.5402` -> `0.5435` (delta: `0.0033`, tool_calls: `10` -> `10`)

## Top Improvements

- `task_010`: `0.5197` -> `0.4951` (delta: `-0.0246`, tool_calls: `9` -> `9`)
- `task_038`: `0.5411` -> `0.5179` (delta: `-0.0232`, tool_calls: `8` -> `8`)
- `task_013`: `0.576` -> `0.5549` (delta: `-0.0211`, tool_calls: `9` -> `9`)
- `task_017`: `0.5291` -> `0.5101` (delta: `-0.019`, tool_calls: `10` -> `10`)
- `task_032`: `0.5242` -> `0.5054` (delta: `-0.0188`, tool_calls: `9` -> `9`)
- `task_030`: `0.5127` -> `0.4967` (delta: `-0.016`, tool_calls: `8` -> `8`)
- `task_036`: `0.5342` -> `0.5186` (delta: `-0.0156`, tool_calls: `8` -> `8`)
- `task_008`: `0.559` -> `0.5465` (delta: `-0.0125`, tool_calls: `9` -> `9`)
- `task_042`: `0.5279` -> `0.5179` (delta: `-0.01`, tool_calls: `10` -> `10`)
- `task_040`: `0.5293` -> `0.5279` (delta: `-0.0014`, tool_calls: `12` -> `12`)

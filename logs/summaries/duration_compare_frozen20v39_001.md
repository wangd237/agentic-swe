# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v38_001`
- improved_batch_run_id: `batch_run_frozen20v39_001`
- created_at: `2026-06-12T02:14:33.997459+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5427`
- improved_average_duration_sec_all: `0.5443`
- baseline_average_duration_sec_common: `0.5427`
- improved_average_duration_sec_common: `0.5443`
- common_average_delta_sec: `0.0016`
- baseline_total_duration_sec_common: `10.8533`
- improved_total_duration_sec_common: `10.8853`

## Top Regressions

- `task_008`: `0.5208` -> `0.5499` (delta: `0.0291`, tool_calls: `9` -> `9`)
- `task_016`: `0.5342` -> `0.5583` (delta: `0.0241`, tool_calls: `12` -> `12`)
- `task_040`: `0.5359` -> `0.557` (delta: `0.0211`, tool_calls: `12` -> `12`)
- `task_017`: `0.5481` -> `0.5686` (delta: `0.0205`, tool_calls: `10` -> `10`)
- `task_010`: `0.5409` -> `0.5578` (delta: `0.0169`, tool_calls: `9` -> `9`)
- `task_036`: `0.5074` -> `0.5208` (delta: `0.0134`, tool_calls: `8` -> `8`)
- `task_013`: `0.5253` -> `0.5363` (delta: `0.011`, tool_calls: `9` -> `9`)
- `task_019`: `0.5425` -> `0.5505` (delta: `0.008`, tool_calls: `10` -> `10`)
- `task_038`: `0.5383` -> `0.5439` (delta: `0.0056`, tool_calls: `8` -> `8`)
- `task_024`: `0.5641` -> `0.569` (delta: `0.0049`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_006`: `0.5617` -> `0.5211` (delta: `-0.0406`, tool_calls: `9` -> `9`)
- `task_028`: `0.5381` -> `0.5173` (delta: `-0.0208`, tool_calls: `8` -> `8`)
- `task_046`: `0.5637` -> `0.5466` (delta: `-0.0171`, tool_calls: `8` -> `8`)
- `task_030`: `0.5382` -> `0.5231` (delta: `-0.0151`, tool_calls: `8` -> `8`)
- `task_022`: `0.5457` -> `0.5332` (delta: `-0.0125`, tool_calls: `9` -> `9`)
- `task_042`: `0.5479` -> `0.5397` (delta: `-0.0082`, tool_calls: `10` -> `10`)
- `task_026`: `0.5697` -> `0.5627` (delta: `-0.007`, tool_calls: `9` -> `9`)
- `task_034`: `0.5465` -> `0.543` (delta: `-0.0035`, tool_calls: `11` -> `11`)
- `task_032`: `0.5453` -> `0.5438` (delta: `-0.0015`, tool_calls: `9` -> `9`)

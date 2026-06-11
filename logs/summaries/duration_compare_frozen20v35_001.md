# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v34_001`
- improved_batch_run_id: `batch_run_frozen20v35_001`
- created_at: `2026-06-11T16:08:07.204628+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5368`
- improved_average_duration_sec_all: `0.5402`
- baseline_average_duration_sec_common: `0.5368`
- improved_average_duration_sec_common: `0.5402`
- common_average_delta_sec: `0.0034`
- baseline_total_duration_sec_common: `10.7363`
- improved_total_duration_sec_common: `10.8038`

## Top Regressions

- `task_017`: `0.4802` -> `0.5856` (delta: `0.1054`, tool_calls: `10` -> `10`)
- `task_008`: `0.5112` -> `0.5423` (delta: `0.0311`, tool_calls: `9` -> `9`)
- `task_013`: `0.5143` -> `0.5417` (delta: `0.0274`, tool_calls: `9` -> `9`)
- `task_010`: `0.5156` -> `0.5425` (delta: `0.0269`, tool_calls: `9` -> `9`)
- `task_019`: `0.5538` -> `0.5741` (delta: `0.0203`, tool_calls: `10` -> `10`)
- `task_026`: `0.531` -> `0.5453` (delta: `0.0143`, tool_calls: `9` -> `9`)
- `task_016`: `0.5222` -> `0.5354` (delta: `0.0132`, tool_calls: `12` -> `12`)
- `task_040`: `0.5275` -> `0.5331` (delta: `0.0056`, tool_calls: `12` -> `12`)
- `task_042`: `0.5492` -> `0.5521` (delta: `0.0029`, tool_calls: `10` -> `10`)
- `task_034`: `0.5402` -> `0.5423` (delta: `0.0021`, tool_calls: `11` -> `11`)

## Top Improvements

- `task_022`: `0.5573` -> `0.5084` (delta: `-0.0489`, tool_calls: `9` -> `9`)
- `task_024`: `0.5701` -> `0.531` (delta: `-0.0391`, tool_calls: `9` -> `9`)
- `task_036`: `0.5634` -> `0.5381` (delta: `-0.0253`, tool_calls: `8` -> `8`)
- `task_032`: `0.5431` -> `0.5186` (delta: `-0.0245`, tool_calls: `9` -> `9`)
- `task_046`: `0.5497` -> `0.5375` (delta: `-0.0122`, tool_calls: `8` -> `8`)
- `task_030`: `0.5359` -> `0.5255` (delta: `-0.0104`, tool_calls: `8` -> `8`)
- `task_038`: `0.55` -> `0.5403` (delta: `-0.0097`, tool_calls: `8` -> `8`)
- `task_028`: `0.5671` -> `0.56` (delta: `-0.0071`, tool_calls: `8` -> `8`)
- `task_044`: `0.548` -> `0.545` (delta: `-0.003`, tool_calls: `8` -> `8`)
- `task_006`: `0.5065` -> `0.505` (delta: `-0.0015`, tool_calls: `9` -> `9`)

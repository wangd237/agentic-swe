# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v33_001`
- improved_batch_run_id: `batch_run_frozen20v34_001`
- created_at: `2026-06-11T15:47:47.259093+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5379`
- improved_average_duration_sec_all: `0.5368`
- baseline_average_duration_sec_common: `0.5379`
- improved_average_duration_sec_common: `0.5368`
- common_average_delta_sec: `-0.0011`
- baseline_total_duration_sec_common: `10.7571`
- improved_total_duration_sec_common: `10.7363`

## Top Regressions

- `task_036`: `0.5054` -> `0.5634` (delta: `0.058`, tool_calls: `8` -> `8`)
- `task_038`: `0.5131` -> `0.55` (delta: `0.0369`, tool_calls: `8` -> `8`)
- `task_024`: `0.5432` -> `0.5701` (delta: `0.0269`, tool_calls: `9` -> `9`)
- `task_034`: `0.5135` -> `0.5402` (delta: `0.0267`, tool_calls: `11` -> `11`)
- `task_032`: `0.5209` -> `0.5431` (delta: `0.0222`, tool_calls: `9` -> `9`)
- `task_030`: `0.519` -> `0.5359` (delta: `0.0169`, tool_calls: `8` -> `8`)
- `task_028`: `0.5521` -> `0.5671` (delta: `0.015`, tool_calls: `8` -> `8`)
- `task_040`: `0.5149` -> `0.5275` (delta: `0.0126`, tool_calls: `12` -> `12`)
- `task_019`: `0.5447` -> `0.5538` (delta: `0.0091`, tool_calls: `10` -> `10`)
- `task_022`: `0.5482` -> `0.5573` (delta: `0.0091`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_017`: `0.5444` -> `0.4802` (delta: `-0.0642`, tool_calls: `10` -> `10`)
- `task_010`: `0.5597` -> `0.5156` (delta: `-0.0441`, tool_calls: `9` -> `9`)
- `task_008`: `0.5546` -> `0.5112` (delta: `-0.0434`, tool_calls: `9` -> `9`)
- `task_006`: `0.5439` -> `0.5065` (delta: `-0.0374`, tool_calls: `9` -> `9`)
- `task_013`: `0.544` -> `0.5143` (delta: `-0.0297`, tool_calls: `9` -> `9`)
- `task_026`: `0.5515` -> `0.531` (delta: `-0.0205`, tool_calls: `9` -> `9`)
- `task_016`: `0.5335` -> `0.5222` (delta: `-0.0113`, tool_calls: `12` -> `12`)
- `task_042`: `0.5536` -> `0.5492` (delta: `-0.0044`, tool_calls: `10` -> `10`)
- `task_046`: `0.5522` -> `0.5497` (delta: `-0.0025`, tool_calls: `8` -> `8`)

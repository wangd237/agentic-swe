# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev36_001`
- improved_batch_run_id: `batch_run_realissuev37_001`
- created_at: `2026-06-12T01:18:34.883045+00:00`

## Task Set

- baseline_task_count: `33`
- improved_task_count: `34`
- common_task_count: `33`
- added_task_ids: `['task_069']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5312`
- improved_average_duration_sec_all: `0.6038`
- baseline_average_duration_sec_common: `0.5312`
- improved_average_duration_sec_common: `0.6046`
- common_average_delta_sec: `0.0734`
- baseline_total_duration_sec_common: `17.5291`
- improved_total_duration_sec_common: `19.9533`

## Top Regressions

- `task_056`: `0.6763` -> `0.8408` (delta: `0.1645`, tool_calls: `10` -> `10`)
- `task_022`: `0.5243` -> `0.6456` (delta: `0.1213`, tool_calls: `9` -> `9`)
- `task_017`: `0.5314` -> `0.6378` (delta: `0.1064`, tool_calls: `10` -> `10`)
- `task_050`: `0.4919` -> `0.5899` (delta: `0.098`, tool_calls: `8` -> `8`)
- `task_059`: `0.4914` -> `0.5891` (delta: `0.0977`, tool_calls: `8` -> `8`)
- `task_006`: `0.5154` -> `0.6043` (delta: `0.0889`, tool_calls: `9` -> `9`)
- `task_067`: `0.4954` -> `0.584` (delta: `0.0886`, tool_calls: `10` -> `10`)
- `task_052`: `0.5096` -> `0.594` (delta: `0.0844`, tool_calls: `12` -> `12`)
- `task_016`: `0.5238` -> `0.6076` (delta: `0.0838`, tool_calls: `12` -> `12`)
- `task_028`: `0.5235` -> `0.6071` (delta: `0.0836`, tool_calls: `8` -> `8`)

## Top Improvements

- 当前没有检测到公共任务上的时延改善

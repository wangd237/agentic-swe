# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev48_001`
- improved_batch_run_id: `batch_run_realissuev49_001`
- created_at: `2026-06-12T07:14:37.228955+00:00`

## Task Set

- baseline_task_count: `45`
- improved_task_count: `46`
- common_task_count: `45`
- added_task_ids: `['task_093']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5234`
- improved_average_duration_sec_all: `0.5869`
- baseline_average_duration_sec_common: `0.5234`
- improved_average_duration_sec_common: `0.5882`
- common_average_delta_sec: `0.0648`
- baseline_total_duration_sec_common: `23.5542`
- improved_total_duration_sec_common: `26.4692`

## Top Regressions

- `task_087`: `0.4878` -> `0.6227` (delta: `0.1349`, tool_calls: `9` -> `9`)
- `task_089`: `0.459` -> `0.5853` (delta: `0.1263`, tool_calls: `9` -> `9`)
- `task_056`: `0.7733` -> `0.8884` (delta: `0.1151`, tool_calls: `10` -> `10`)
- `task_010`: `0.5148` -> `0.628` (delta: `0.1132`, tool_calls: `9` -> `9`)
- `task_058`: `0.5043` -> `0.6137` (delta: `0.1094`, tool_calls: `10` -> `10`)
- `task_022`: `0.5316` -> `0.6399` (delta: `0.1083`, tool_calls: `9` -> `9`)
- `task_052`: `0.5007` -> `0.6082` (delta: `0.1075`, tool_calls: `12` -> `12`)
- `task_050`: `0.5008` -> `0.6023` (delta: `0.1015`, tool_calls: `8` -> `8`)
- `task_006`: `0.523` -> `0.6236` (delta: `0.1006`, tool_calls: `9` -> `9`)
- `task_042`: `0.5276` -> `0.627` (delta: `0.0994`, tool_calls: `10` -> `10`)

## Top Improvements

- 当前没有检测到公共任务上的时延改善

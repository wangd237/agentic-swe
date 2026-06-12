# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v48_001`
- improved_batch_run_id: `batch_run_frozen20v49_001`
- created_at: `2026-06-12T07:14:37.083134+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5287`
- improved_average_duration_sec_all: `0.5972`
- baseline_average_duration_sec_common: `0.5287`
- improved_average_duration_sec_common: `0.5972`
- common_average_delta_sec: `0.0685`
- baseline_total_duration_sec_common: `10.5745`
- improved_total_duration_sec_common: `11.9444`

## Top Regressions

- `task_008`: `0.5165` -> `0.6453` (delta: `0.1288`, tool_calls: `9` -> `9`)
- `task_022`: `0.5314` -> `0.6407` (delta: `0.1093`, tool_calls: `9` -> `9`)
- `task_013`: `0.4934` -> `0.598` (delta: `0.1046`, tool_calls: `9` -> `9`)
- `task_010`: `0.5063` -> `0.6102` (delta: `0.1039`, tool_calls: `9` -> `9`)
- `task_042`: `0.5286` -> `0.6295` (delta: `0.1009`, tool_calls: `10` -> `10`)
- `task_006`: `0.5207` -> `0.6167` (delta: `0.096`, tool_calls: `9` -> `9`)
- `task_016`: `0.4862` -> `0.5737` (delta: `0.0875`, tool_calls: `12` -> `12`)
- `task_036`: `0.5201` -> `0.598` (delta: `0.0779`, tool_calls: `8` -> `8`)
- `task_040`: `0.5338` -> `0.6099` (delta: `0.0761`, tool_calls: `12` -> `12`)
- `task_038`: `0.5552` -> `0.6214` (delta: `0.0662`, tool_calls: `8` -> `8`)

## Top Improvements

- 当前没有检测到公共任务上的时延改善

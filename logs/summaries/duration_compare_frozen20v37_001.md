# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v36_001`
- improved_batch_run_id: `batch_run_frozen20v37_001`
- created_at: `2026-06-12T01:18:34.784954+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5386`
- improved_average_duration_sec_all: `0.5687`
- baseline_average_duration_sec_common: `0.5386`
- improved_average_duration_sec_common: `0.5687`
- common_average_delta_sec: `0.0301`
- baseline_total_duration_sec_common: `10.7712`
- improved_total_duration_sec_common: `11.3739`

## Top Regressions

- `task_022`: `0.5138` -> `0.5829` (delta: `0.0691`, tool_calls: `9` -> `9`)
- `task_026`: `0.5386` -> `0.6076` (delta: `0.069`, tool_calls: `9` -> `9`)
- `task_046`: `0.5315` -> `0.5803` (delta: `0.0488`, tool_calls: `8` -> `8`)
- `task_010`: `0.5405` -> `0.5867` (delta: `0.0462`, tool_calls: `9` -> `9`)
- `task_019`: `0.5319` -> `0.5739` (delta: `0.042`, tool_calls: `10` -> `10`)
- `task_013`: `0.5292` -> `0.5692` (delta: `0.04`, tool_calls: `9` -> `9`)
- `task_006`: `0.53` -> `0.5687` (delta: `0.0387`, tool_calls: `9` -> `9`)
- `task_038`: `0.5319` -> `0.5628` (delta: `0.0309`, tool_calls: `8` -> `8`)
- `task_016`: `0.5236` -> `0.5534` (delta: `0.0298`, tool_calls: `12` -> `12`)
- `task_008`: `0.5335` -> `0.5613` (delta: `0.0278`, tool_calls: `9` -> `9`)

## Top Improvements

- 当前没有检测到公共任务上的时延改善

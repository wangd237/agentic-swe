# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v53r1_001`
- improved_batch_run_id: `batch_run_frozen20v54r2_001`
- created_at: `2026-06-12T08:47:57.128985+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.7361`
- improved_average_duration_sec_all: `0.6697`
- baseline_average_duration_sec_common: `0.7361`
- improved_average_duration_sec_common: `0.6697`
- common_average_delta_sec: `-0.0664`
- baseline_total_duration_sec_common: `14.722`
- improved_total_duration_sec_common: `13.395`

## Top Regressions

- 当前没有检测到公共任务上的时延回升

## Top Improvements

- `task_019`: `0.8239` -> `0.6824` (delta: `-0.1415`, tool_calls: `10` -> `10`)
- `task_036`: `0.7698` -> `0.6565` (delta: `-0.1133`, tool_calls: `8` -> `8`)
- `task_017`: `0.7709` -> `0.6651` (delta: `-0.1058`, tool_calls: `10` -> `10`)
- `task_030`: `0.7424` -> `0.6433` (delta: `-0.0991`, tool_calls: `8` -> `8`)
- `task_013`: `0.752` -> `0.6583` (delta: `-0.0937`, tool_calls: `9` -> `9`)
- `task_026`: `0.7434` -> `0.6563` (delta: `-0.0871`, tool_calls: `9` -> `9`)
- `task_028`: `0.7358` -> `0.6669` (delta: `-0.0689`, tool_calls: `8` -> `8`)
- `task_044`: `0.7627` -> `0.6959` (delta: `-0.0668`, tool_calls: `8` -> `8`)
- `task_024`: `0.7252` -> `0.66` (delta: `-0.0652`, tool_calls: `9` -> `9`)
- `task_040`: `0.7331` -> `0.6731` (delta: `-0.06`, tool_calls: `12` -> `12`)

# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v40_001`
- improved_batch_run_id: `batch_run_frozen20v41_001`
- created_at: `2026-06-12T02:41:46.409879+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5682`
- improved_average_duration_sec_all: `0.5185`
- baseline_average_duration_sec_common: `0.5682`
- improved_average_duration_sec_common: `0.5185`
- common_average_delta_sec: `-0.0497`
- baseline_total_duration_sec_common: `11.3637`
- improved_total_duration_sec_common: `10.3694`

## Top Regressions

- 当前没有检测到公共任务上的时延回升

## Top Improvements

- `task_013`: `0.605` -> `0.5085` (delta: `-0.0965`, tool_calls: `9` -> `9`)
- `task_036`: `0.5795` -> `0.4882` (delta: `-0.0913`, tool_calls: `8` -> `8`)
- `task_030`: `0.5645` -> `0.4824` (delta: `-0.0821`, tool_calls: `8` -> `8`)
- `task_010`: `0.5677` -> `0.4945` (delta: `-0.0732`, tool_calls: `9` -> `9`)
- `task_042`: `0.582` -> `0.5187` (delta: `-0.0633`, tool_calls: `10` -> `10`)
- `task_017`: `0.5709` -> `0.5107` (delta: `-0.0602`, tool_calls: `10` -> `10`)
- `task_032`: `0.5962` -> `0.5387` (delta: `-0.0575`, tool_calls: `9` -> `9`)
- `task_008`: `0.5611` -> `0.5083` (delta: `-0.0528`, tool_calls: `9` -> `9`)
- `task_046`: `0.5913` -> `0.5404` (delta: `-0.0509`, tool_calls: `8` -> `8`)
- `task_006`: `0.5489` -> `0.5031` (delta: `-0.0458`, tool_calls: `9` -> `9`)

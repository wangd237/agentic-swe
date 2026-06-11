# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v32_001`
- improved_batch_run_id: `batch_run_frozen20v33_001`
- created_at: `2026-06-11T14:43:39.612852+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.6774`
- improved_average_duration_sec_all: `0.5379`
- baseline_average_duration_sec_common: `0.6774`
- improved_average_duration_sec_common: `0.5379`
- common_average_delta_sec: `-0.1395`
- baseline_total_duration_sec_common: `13.5473`
- improved_total_duration_sec_common: `10.7571`

## Top Regressions

- 当前没有检测到公共任务上的时延回升

## Top Improvements

- `task_040`: `0.9456` -> `0.5149` (delta: `-0.4307`, tool_calls: `12` -> `12`)
- `task_034`: `0.7888` -> `0.5135` (delta: `-0.2753`, tool_calls: `11` -> `11`)
- `task_036`: `0.77` -> `0.5054` (delta: `-0.2646`, tool_calls: `8` -> `8`)
- `task_038`: `0.754` -> `0.5131` (delta: `-0.2409`, tool_calls: `8` -> `8`)
- `task_032`: `0.7213` -> `0.5209` (delta: `-0.2004`, tool_calls: `9` -> `9`)
- `task_024`: `0.7012` -> `0.5432` (delta: `-0.158`, tool_calls: `9` -> `9`)
- `task_008`: `0.7109` -> `0.5546` (delta: `-0.1563`, tool_calls: `9` -> `9`)
- `task_026`: `0.7076` -> `0.5515` (delta: `-0.1561`, tool_calls: `9` -> `9`)
- `task_042`: `0.7014` -> `0.5536` (delta: `-0.1478`, tool_calls: `10` -> `10`)
- `task_030`: `0.6324` -> `0.519` (delta: `-0.1134`, tool_calls: `8` -> `8`)

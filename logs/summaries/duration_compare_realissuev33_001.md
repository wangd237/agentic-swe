# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev32_001`
- improved_batch_run_id: `batch_run_realissuev33_001`
- created_at: `2026-06-11T15:01:35.182341+00:00`

## Task Set

- baseline_task_count: `30`
- improved_task_count: `30`
- common_task_count: `30`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.6778`
- improved_average_duration_sec_all: `0.5423`
- baseline_average_duration_sec_common: `0.6778`
- improved_average_duration_sec_common: `0.5423`
- common_average_delta_sec: `-0.1355`
- baseline_total_duration_sec_common: `20.3351`
- improved_total_duration_sec_common: `16.268`

## Top Regressions

- 当前没有检测到公共任务上的时延回升

## Top Improvements

- `task_040`: `0.9463` -> `0.5522` (delta: `-0.3941`, tool_calls: `12` -> `12`)
- `task_034`: `0.8038` -> `0.5437` (delta: `-0.2601`, tool_calls: `11` -> `11`)
- `task_036`: `0.7715` -> `0.5351` (delta: `-0.2364`, tool_calls: `8` -> `8`)
- `task_038`: `0.747` -> `0.5241` (delta: `-0.2229`, tool_calls: `8` -> `8`)
- `task_008`: `0.711` -> `0.5034` (delta: `-0.2076`, tool_calls: `9` -> `9`)
- `task_032`: `0.7152` -> `0.5206` (delta: `-0.1946`, tool_calls: `9` -> `9`)
- `task_024`: `0.7012` -> `0.5107` (delta: `-0.1905`, tool_calls: `9` -> `9`)
- `task_050`: `0.7151` -> `0.5316` (delta: `-0.1835`, tool_calls: `8` -> `8`)
- `task_061`: `0.7119` -> `0.5397` (delta: `-0.1722`, tool_calls: `8` -> `8`)
- `task_026`: `0.7075` -> `0.5362` (delta: `-0.1713`, tool_calls: `9` -> `9`)

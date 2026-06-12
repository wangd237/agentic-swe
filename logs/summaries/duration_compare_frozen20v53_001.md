# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v52_001`
- improved_batch_run_id: `batch_run_frozen20v53r1_001`
- created_at: `2026-06-12T08:27:51.068561+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.6732`
- improved_average_duration_sec_all: `0.7361`
- baseline_average_duration_sec_common: `0.6732`
- improved_average_duration_sec_common: `0.7361`
- common_average_delta_sec: `0.0629`
- baseline_total_duration_sec_common: `13.4637`
- improved_total_duration_sec_common: `14.722`

## Top Regressions

- `task_019`: `0.662` -> `0.8239` (delta: `0.1619`, tool_calls: `10` -> `10`)
- `task_017`: `0.6709` -> `0.7709` (delta: `0.1`, tool_calls: `10` -> `10`)
- `task_013`: `0.6527` -> `0.752` (delta: `0.0993`, tool_calls: `9` -> `9`)
- `task_022`: `0.6447` -> `0.734` (delta: `0.0893`, tool_calls: `9` -> `9`)
- `task_044`: `0.6743` -> `0.7627` (delta: `0.0884`, tool_calls: `8` -> `8`)
- `task_030`: `0.6679` -> `0.7424` (delta: `0.0745`, tool_calls: `8` -> `8`)
- `task_040`: `0.6603` -> `0.7331` (delta: `0.0728`, tool_calls: `12` -> `12`)
- `task_036`: `0.7028` -> `0.7698` (delta: `0.067`, tool_calls: `8` -> `8`)
- `task_038`: `0.6635` -> `0.7266` (delta: `0.0631`, tool_calls: `8` -> `8`)
- `task_028`: `0.6781` -> `0.7358` (delta: `0.0577`, tool_calls: `8` -> `8`)

## Top Improvements

- 当前没有检测到公共任务上的时延改善

# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v50_001`
- improved_batch_run_id: `batch_run_frozen20v51_002`
- created_at: `2026-06-12T07:37:52.925992+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5672`
- improved_average_duration_sec_all: `0.7361`
- baseline_average_duration_sec_common: `0.5672`
- improved_average_duration_sec_common: `0.7361`
- common_average_delta_sec: `0.1689`
- baseline_total_duration_sec_common: `11.3444`
- improved_total_duration_sec_common: `14.7213`

## Top Regressions

- `task_038`: `0.5823` -> `1.004` (delta: `0.4217`, tool_calls: `8` -> `8`)
- `task_040`: `0.5755` -> `0.8582` (delta: `0.2827`, tool_calls: `12` -> `12`)
- `task_006`: `0.5848` -> `0.86` (delta: `0.2752`, tool_calls: `9` -> `9`)
- `task_044`: `0.5549` -> `0.7711` (delta: `0.2162`, tool_calls: `8` -> `8`)
- `task_042`: `0.549` -> `0.7481` (delta: `0.1991`, tool_calls: `10` -> `10`)
- `task_013`: `0.5095` -> `0.6966` (delta: `0.1871`, tool_calls: `9` -> `9`)
- `task_010`: `0.5189` -> `0.7042` (delta: `0.1853`, tool_calls: `9` -> `9`)
- `task_017`: `0.5677` -> `0.7122` (delta: `0.1445`, tool_calls: `10` -> `10`)
- `task_030`: `0.5803` -> `0.7219` (delta: `0.1416`, tool_calls: `8` -> `8`)
- `task_032`: `0.578` -> `0.7175` (delta: `0.1395`, tool_calls: `9` -> `9`)

## Top Improvements

- 当前没有检测到公共任务上的时延改善

# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v49_001`
- improved_batch_run_id: `batch_run_frozen20v50_001`
- created_at: `2026-06-12T07:24:16.509719+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5972`
- improved_average_duration_sec_all: `0.5672`
- baseline_average_duration_sec_common: `0.5972`
- improved_average_duration_sec_common: `0.5672`
- common_average_delta_sec: `-0.03`
- baseline_total_duration_sec_common: `11.9444`
- improved_total_duration_sec_common: `11.3444`

## Top Regressions

- `task_032`: `0.545` -> `0.578` (delta: `0.033`, tool_calls: `9` -> `9`)
- `task_028`: `0.5539` -> `0.5778` (delta: `0.0239`, tool_calls: `8` -> `8`)
- `task_024`: `0.5855` -> `0.593` (delta: `0.0075`, tool_calls: `9` -> `9`)
- `task_034`: `0.5715` -> `0.578` (delta: `0.0065`, tool_calls: `11` -> `11`)

## Top Improvements

- `task_010`: `0.6102` -> `0.5189` (delta: `-0.0913`, tool_calls: `9` -> `9`)
- `task_013`: `0.598` -> `0.5095` (delta: `-0.0885`, tool_calls: `9` -> `9`)
- `task_042`: `0.6295` -> `0.549` (delta: `-0.0805`, tool_calls: `10` -> `10`)
- `task_022`: `0.6407` -> `0.5808` (delta: `-0.0599`, tool_calls: `9` -> `9`)
- `task_008`: `0.6453` -> `0.5977` (delta: `-0.0476`, tool_calls: `9` -> `9`)
- `task_044`: `0.5958` -> `0.5549` (delta: `-0.0409`, tool_calls: `8` -> `8`)
- `task_038`: `0.6214` -> `0.5823` (delta: `-0.0391`, tool_calls: `8` -> `8`)
- `task_026`: `0.588` -> `0.5522` (delta: `-0.0358`, tool_calls: `9` -> `9`)
- `task_016`: `0.5737` -> `0.539` (delta: `-0.0347`, tool_calls: `12` -> `12`)
- `task_040`: `0.6099` -> `0.5755` (delta: `-0.0344`, tool_calls: `12` -> `12`)

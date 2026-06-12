# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v45_001`
- improved_batch_run_id: `batch_run_frozen20v46_001`
- created_at: `2026-06-12T04:31:11.221283+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.512`
- improved_average_duration_sec_all: `0.5321`
- baseline_average_duration_sec_common: `0.512`
- improved_average_duration_sec_common: `0.5321`
- common_average_delta_sec: `0.0201`
- baseline_total_duration_sec_common: `10.2395`
- improved_total_duration_sec_common: `10.641`

## Top Regressions

- `task_019`: `0.5027` -> `0.5556` (delta: `0.0529`, tool_calls: `10` -> `10`)
- `task_022`: `0.5012` -> `0.5535` (delta: `0.0523`, tool_calls: `9` -> `9`)
- `task_026`: `0.4899` -> `0.5379` (delta: `0.048`, tool_calls: `9` -> `9`)
- `task_016`: `0.5018` -> `0.5497` (delta: `0.0479`, tool_calls: `12` -> `12`)
- `task_013`: `0.5005` -> `0.544` (delta: `0.0435`, tool_calls: `9` -> `9`)
- `task_036`: `0.5246` -> `0.568` (delta: `0.0434`, tool_calls: `8` -> `8`)
- `task_010`: `0.4819` -> `0.5096` (delta: `0.0277`, tool_calls: `9` -> `9`)
- `task_024`: `0.4959` -> `0.5232` (delta: `0.0273`, tool_calls: `9` -> `9`)
- `task_017`: `0.5022` -> `0.5293` (delta: `0.0271`, tool_calls: `10` -> `10`)
- `task_032`: `0.507` -> `0.5288` (delta: `0.0218`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_038`: `0.5281` -> `0.5129` (delta: `-0.0152`, tool_calls: `8` -> `8`)
- `task_040`: `0.542` -> `0.5303` (delta: `-0.0117`, tool_calls: `12` -> `12`)
- `task_044`: `0.5263` -> `0.5154` (delta: `-0.0109`, tool_calls: `8` -> `8`)
- `task_008`: `0.5295` -> `0.5238` (delta: `-0.0057`, tool_calls: `9` -> `9`)

# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v46_001`
- improved_batch_run_id: `batch_run_frozen20v47_001`
- created_at: `2026-06-12T04:44:51.956027+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5321`
- improved_average_duration_sec_all: `0.5374`
- baseline_average_duration_sec_common: `0.5321`
- improved_average_duration_sec_common: `0.5374`
- common_average_delta_sec: `0.0053`
- baseline_total_duration_sec_common: `10.641`
- improved_total_duration_sec_common: `10.7478`

## Top Regressions

- `task_044`: `0.5154` -> `0.5456` (delta: `0.0302`, tool_calls: `8` -> `8`)
- `task_010`: `0.5096` -> `0.537` (delta: `0.0274`, tool_calls: `9` -> `9`)
- `task_006`: `0.52` -> `0.5457` (delta: `0.0257`, tool_calls: `9` -> `9`)
- `task_008`: `0.5238` -> `0.5481` (delta: `0.0243`, tool_calls: `9` -> `9`)
- `task_026`: `0.5379` -> `0.5581` (delta: `0.0202`, tool_calls: `9` -> `9`)
- `task_042`: `0.5377` -> `0.5564` (delta: `0.0187`, tool_calls: `10` -> `10`)
- `task_022`: `0.5535` -> `0.565` (delta: `0.0115`, tool_calls: `9` -> `9`)
- `task_034`: `0.5102` -> `0.5197` (delta: `0.0095`, tool_calls: `11` -> `11`)
- `task_038`: `0.5129` -> `0.522` (delta: `0.0091`, tool_calls: `8` -> `8`)
- `task_032`: `0.5288` -> `0.5362` (delta: `0.0074`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_036`: `0.568` -> `0.5326` (delta: `-0.0354`, tool_calls: `8` -> `8`)
- `task_016`: `0.5497` -> `0.5272` (delta: `-0.0225`, tool_calls: `12` -> `12`)
- `task_019`: `0.5556` -> `0.5375` (delta: `-0.0181`, tool_calls: `10` -> `10`)
- `task_030`: `0.5389` -> `0.5322` (delta: `-0.0067`, tool_calls: `8` -> `8`)
- `task_017`: `0.5293` -> `0.5278` (delta: `-0.0015`, tool_calls: `10` -> `10`)
- `task_013`: `0.544` -> `0.5429` (delta: `-0.0011`, tool_calls: `9` -> `9`)
- `task_024`: `0.5232` -> `0.5227` (delta: `-0.0005`, tool_calls: `9` -> `9`)
- `task_046`: `0.5342` -> `0.5341` (delta: `-0.0001`, tool_calls: `8` -> `8`)

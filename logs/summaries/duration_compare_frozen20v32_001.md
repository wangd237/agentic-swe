# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v31_001`
- improved_batch_run_id: `batch_run_frozen20v32_001`
- created_at: `2026-06-11T05:44:55.425181+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.6122`
- improved_average_duration_sec_all: `0.6774`
- baseline_average_duration_sec_common: `0.6122`
- improved_average_duration_sec_common: `0.6774`
- common_average_delta_sec: `0.0652`
- baseline_total_duration_sec_common: `12.2444`
- improved_total_duration_sec_common: `13.5473`

## Top Regressions

- `task_040`: `0.6213` -> `0.9456` (delta: `0.3243`, tool_calls: `12` -> `12`)
- `task_038`: `0.5846` -> `0.754` (delta: `0.1694`, tool_calls: `8` -> `8`)
- `task_036`: `0.6084` -> `0.77` (delta: `0.1616`, tool_calls: `8` -> `8`)
- `task_034`: `0.6275` -> `0.7888` (delta: `0.1613`, tool_calls: `11` -> `11`)
- `task_032`: `0.5983` -> `0.7213` (delta: `0.123`, tool_calls: `9` -> `9`)
- `task_026`: `0.5993` -> `0.7076` (delta: `0.1083`, tool_calls: `9` -> `9`)
- `task_024`: `0.6149` -> `0.7012` (delta: `0.0863`, tool_calls: `9` -> `9`)
- `task_008`: `0.6284` -> `0.7109` (delta: `0.0825`, tool_calls: `9` -> `9`)
- `task_042`: `0.6392` -> `0.7014` (delta: `0.0622`, tool_calls: `10` -> `10`)
- `task_022`: `0.5931` -> `0.6432` (delta: `0.0501`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_016`: `0.6009` -> `0.557` (delta: `-0.0439`, tool_calls: `12` -> `12`)
- `task_013`: `0.625` -> `0.5818` (delta: `-0.0432`, tool_calls: `9` -> `9`)
- `task_006`: `0.6287` -> `0.6039` (delta: `-0.0248`, tool_calls: `9` -> `9`)
- `task_017`: `0.6057` -> `0.5973` (delta: `-0.0084`, tool_calls: `10` -> `10`)

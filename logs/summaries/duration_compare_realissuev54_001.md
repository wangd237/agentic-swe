# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev53r1_001`
- improved_batch_run_id: `batch_run_realissuev54r2_001`
- created_at: `2026-06-12T08:47:57.000732+00:00`

## Task Set

- baseline_task_count: `50`
- improved_task_count: `51`
- common_task_count: `50`
- added_task_ids: `['task_103']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.7143`
- improved_average_duration_sec_all: `0.6544`
- baseline_average_duration_sec_common: `0.7143`
- improved_average_duration_sec_common: `0.655`
- common_average_delta_sec: `-0.0593`
- baseline_total_duration_sec_common: `35.7134`
- improved_total_duration_sec_common: `32.7486`

## Top Regressions

- `task_008`: `0.7103` -> `0.7293` (delta: `0.019`, tool_calls: `9` -> `9`)
- `task_063`: `0.6651` -> `0.6699` (delta: `0.0048`, tool_calls: `8` -> `8`)

## Top Improvements

- `task_019`: `0.8258` -> `0.6836` (delta: `-0.1422`, tool_calls: `10` -> `10`)
- `task_036`: `0.772` -> `0.6549` (delta: `-0.1171`, tool_calls: `8` -> `8`)
- `task_017`: `0.7689` -> `0.6657` (delta: `-0.1032`, tool_calls: `10` -> `10`)
- `task_058`: `0.7247` -> `0.6282` (delta: `-0.0965`, tool_calls: `10` -> `10`)
- `task_081`: `0.7014` -> `0.605` (delta: `-0.0964`, tool_calls: `9` -> `9`)
- `task_030`: `0.7398` -> `0.6435` (delta: `-0.0963`, tool_calls: `8` -> `8`)
- `task_006`: `0.7457` -> `0.6516` (delta: `-0.0941`, tool_calls: `9` -> `9`)
- `task_013`: `0.7518` -> `0.6581` (delta: `-0.0937`, tool_calls: `9` -> `9`)
- `task_026`: `0.7482` -> `0.6545` (delta: `-0.0937`, tool_calls: `9` -> `9`)
- `task_085`: `0.7346` -> `0.6419` (delta: `-0.0927`, tool_calls: `9` -> `9`)

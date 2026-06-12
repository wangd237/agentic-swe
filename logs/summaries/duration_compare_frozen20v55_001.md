# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v54r2_001`
- improved_batch_run_id: `batch_run_frozen20v55r1_001`
- created_at: `2026-06-12T09:15:04.763117+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.6697`
- improved_average_duration_sec_all: `0.7042`
- baseline_average_duration_sec_common: `0.6697`
- improved_average_duration_sec_common: `0.7042`
- common_average_delta_sec: `0.0345`
- baseline_total_duration_sec_common: `13.395`
- improved_total_duration_sec_common: `14.0835`

## Top Regressions

- `task_042`: `0.6881` -> `0.8598` (delta: `0.1717`, tool_calls: `10` -> `10`)
- `task_017`: `0.6651` -> `0.7419` (delta: `0.0768`, tool_calls: `10` -> `10`)
- `task_032`: `0.6517` -> `0.7211` (delta: `0.0694`, tool_calls: `9` -> `9`)
- `task_040`: `0.6731` -> `0.7382` (delta: `0.0651`, tool_calls: `12` -> `12`)
- `task_046`: `0.6459` -> `0.7108` (delta: `0.0649`, tool_calls: `8` -> `8`)
- `task_026`: `0.6563` -> `0.7199` (delta: `0.0636`, tool_calls: `9` -> `9`)
- `task_006`: `0.6604` -> `0.7138` (delta: `0.0534`, tool_calls: `9` -> `9`)
- `task_013`: `0.6583` -> `0.6991` (delta: `0.0408`, tool_calls: `9` -> `9`)
- `task_019`: `0.6824` -> `0.723` (delta: `0.0406`, tool_calls: `10` -> `10`)
- `task_024`: `0.66` -> `0.6917` (delta: `0.0317`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_008`: `0.6729` -> `0.6096` (delta: `-0.0633`, tool_calls: `9` -> `9`)
- `task_022`: `0.7231` -> `0.678` (delta: `-0.0451`, tool_calls: `9` -> `9`)
- `task_016`: `0.6933` -> `0.6908` (delta: `-0.0025`, tool_calls: `12` -> `12`)

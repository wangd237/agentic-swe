# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev40_001`
- improved_batch_run_id: `batch_run_realissuev41_001`
- created_at: `2026-06-12T02:41:46.196408+00:00`

## Task Set

- baseline_task_count: `37`
- improved_task_count: `38`
- common_task_count: `37`
- added_task_ids: `['task_077']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5717`
- improved_average_duration_sec_all: `0.5173`
- baseline_average_duration_sec_common: `0.5717`
- improved_average_duration_sec_common: `0.5177`
- common_average_delta_sec: `-0.054`
- baseline_total_duration_sec_common: `21.1541`
- improved_total_duration_sec_common: `19.1561`

## Top Regressions

- `task_032`: `0.5456` -> `0.5494` (delta: `0.0038`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_010`: `0.6` -> `0.499` (delta: `-0.101`, tool_calls: `9` -> `9`)
- `task_042`: `0.5893` -> `0.4985` (delta: `-0.0908`, tool_calls: `10` -> `10`)
- `task_036`: `0.6004` -> `0.5144` (delta: `-0.086`, tool_calls: `8` -> `8`)
- `task_008`: `0.5775` -> `0.4929` (delta: `-0.0846`, tool_calls: `9` -> `9`)
- `task_073`: `0.5929` -> `0.5097` (delta: `-0.0832`, tool_calls: `8` -> `8`)
- `task_054`: `0.5677` -> `0.4896` (delta: `-0.0781`, tool_calls: `10` -> `10`)
- `task_034`: `0.5712` -> `0.4965` (delta: `-0.0747`, tool_calls: `11` -> `11`)
- `task_058`: `0.5696` -> `0.502` (delta: `-0.0676`, tool_calls: `10` -> `10`)
- `task_048`: `0.5695` -> `0.5037` (delta: `-0.0658`, tool_calls: `10` -> `10`)
- `task_017`: `0.5638` -> `0.4986` (delta: `-0.0652`, tool_calls: `10` -> `10`)

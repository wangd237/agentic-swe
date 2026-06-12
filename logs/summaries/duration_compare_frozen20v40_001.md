# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v39_001`
- improved_batch_run_id: `batch_run_frozen20v40_001`
- created_at: `2026-06-12T02:26:16.796128+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5443`
- improved_average_duration_sec_all: `0.5682`
- baseline_average_duration_sec_common: `0.5443`
- improved_average_duration_sec_common: `0.5682`
- common_average_delta_sec: `0.0239`
- baseline_total_duration_sec_common: `10.8853`
- improved_total_duration_sec_common: `11.3637`

## Top Regressions

- `task_013`: `0.5363` -> `0.605` (delta: `0.0687`, tool_calls: `9` -> `9`)
- `task_036`: `0.5208` -> `0.5795` (delta: `0.0587`, tool_calls: `8` -> `8`)
- `task_032`: `0.5438` -> `0.5962` (delta: `0.0524`, tool_calls: `9` -> `9`)
- `task_046`: `0.5466` -> `0.5913` (delta: `0.0447`, tool_calls: `8` -> `8`)
- `task_042`: `0.5397` -> `0.582` (delta: `0.0423`, tool_calls: `10` -> `10`)
- `task_030`: `0.5231` -> `0.5645` (delta: `0.0414`, tool_calls: `8` -> `8`)
- `task_028`: `0.5173` -> `0.5568` (delta: `0.0395`, tool_calls: `8` -> `8`)
- `task_022`: `0.5332` -> `0.5652` (delta: `0.032`, tool_calls: `9` -> `9`)
- `task_006`: `0.5211` -> `0.5489` (delta: `0.0278`, tool_calls: `9` -> `9`)
- `task_038`: `0.5439` -> `0.5618` (delta: `0.0179`, tool_calls: `8` -> `8`)

## Top Improvements

- `task_024`: `0.569` -> `0.5557` (delta: `-0.0133`, tool_calls: `9` -> `9`)

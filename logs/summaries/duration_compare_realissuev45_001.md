# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev44_002`
- improved_batch_run_id: `batch_run_realissuev45_001`
- created_at: `2026-06-12T04:04:40.680513+00:00`

## Task Set

- baseline_task_count: `41`
- improved_task_count: `42`
- common_task_count: `41`
- added_task_ids: `['task_085']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5173`
- improved_average_duration_sec_all: `0.5175`
- baseline_average_duration_sec_common: `0.5173`
- improved_average_duration_sec_common: `0.5181`
- common_average_delta_sec: `0.0008`
- baseline_total_duration_sec_common: `21.2113`
- improved_total_duration_sec_common: `21.2414`

## Top Regressions

- `task_056`: `0.7427` -> `0.7867` (delta: `0.044`, tool_calls: `10` -> `10`)
- `task_071`: `0.4782` -> `0.514` (delta: `0.0358`, tool_calls: `8` -> `8`)
- `task_073`: `0.493` -> `0.5265` (delta: `0.0335`, tool_calls: `8` -> `8`)
- `task_077`: `0.4767` -> `0.5093` (delta: `0.0326`, tool_calls: `9` -> `9`)
- `task_030`: `0.4966` -> `0.5287` (delta: `0.0321`, tool_calls: `8` -> `8`)
- `task_083`: `0.4614` -> `0.4821` (delta: `0.0207`, tool_calls: `8` -> `8`)
- `task_048`: `0.5042` -> `0.523` (delta: `0.0188`, tool_calls: `10` -> `10`)
- `task_058`: `0.5153` -> `0.534` (delta: `0.0187`, tool_calls: `10` -> `10`)
- `task_006`: `0.4995` -> `0.515` (delta: `0.0155`, tool_calls: `9` -> `9`)
- `task_040`: `0.5248` -> `0.5402` (delta: `0.0154`, tool_calls: `12` -> `12`)

## Top Improvements

- `task_016`: `0.5485` -> `0.4983` (delta: `-0.0502`, tool_calls: `12` -> `12`)
- `task_013`: `0.5556` -> `0.507` (delta: `-0.0486`, tool_calls: `9` -> `9`)
- `task_019`: `0.5434` -> `0.4977` (delta: `-0.0457`, tool_calls: `10` -> `10`)
- `task_008`: `0.5465` -> `0.5109` (delta: `-0.0356`, tool_calls: `9` -> `9`)
- `task_046`: `0.5538` -> `0.5185` (delta: `-0.0353`, tool_calls: `8` -> `8`)
- `task_028`: `0.5356` -> `0.5054` (delta: `-0.0302`, tool_calls: `8` -> `8`)
- `task_026`: `0.5473` -> `0.5213` (delta: `-0.026`, tool_calls: `9` -> `9`)
- `task_024`: `0.535` -> `0.5168` (delta: `-0.0182`, tool_calls: `9` -> `9`)
- `task_034`: `0.5258` -> `0.5087` (delta: `-0.0171`, tool_calls: `11` -> `11`)
- `task_050`: `0.5009` -> `0.4892` (delta: `-0.0117`, tool_calls: `8` -> `8`)

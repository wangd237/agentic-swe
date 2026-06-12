# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev43_001`
- improved_batch_run_id: `batch_run_realissuev44_002`
- created_at: `2026-06-12T03:51:59.756524+00:00`

## Task Set

- baseline_task_count: `40`
- improved_task_count: `41`
- common_task_count: `40`
- added_task_ids: `['task_083']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5241`
- improved_average_duration_sec_all: `0.5173`
- baseline_average_duration_sec_common: `0.5241`
- improved_average_duration_sec_common: `0.5187`
- common_average_delta_sec: `-0.0054`
- baseline_total_duration_sec_common: `20.9649`
- improved_total_duration_sec_common: `20.7499`

## Top Regressions

- `task_046`: `0.5133` -> `0.5538` (delta: `0.0405`, tool_calls: `8` -> `8`)
- `task_034`: `0.5068` -> `0.5258` (delta: `0.019`, tool_calls: `11` -> `11`)
- `task_028`: `0.5172` -> `0.5356` (delta: `0.0184`, tool_calls: `8` -> `8`)
- `task_024`: `0.5171` -> `0.535` (delta: `0.0179`, tool_calls: `9` -> `9`)
- `task_016`: `0.5338` -> `0.5485` (delta: `0.0147`, tool_calls: `12` -> `12`)
- `task_026`: `0.5331` -> `0.5473` (delta: `0.0142`, tool_calls: `9` -> `9`)
- `task_065`: `0.5164` -> `0.526` (delta: `0.0096`, tool_calls: `8` -> `8`)
- `task_044`: `0.523` -> `0.5321` (delta: `0.0091`, tool_calls: `8` -> `8`)
- `task_050`: `0.4918` -> `0.5009` (delta: `0.0091`, tool_calls: `8` -> `8`)
- `task_057`: `0.4963` -> `0.5043` (delta: `0.008`, tool_calls: `10` -> `10`)

## Top Improvements

- `task_048`: `0.552` -> `0.5042` (delta: `-0.0478`, tool_calls: `10` -> `10`)
- `task_059`: `0.539` -> `0.4997` (delta: `-0.0393`, tool_calls: `8` -> `8`)
- `task_032`: `0.536` -> `0.5055` (delta: `-0.0305`, tool_calls: `9` -> `9`)
- `task_006`: `0.5257` -> `0.4995` (delta: `-0.0262`, tool_calls: `9` -> `9`)
- `task_038`: `0.5429` -> `0.5176` (delta: `-0.0253`, tool_calls: `8` -> `8`)
- `task_010`: `0.5197` -> `0.495` (delta: `-0.0247`, tool_calls: `9` -> `9`)
- `task_056`: `0.7661` -> `0.7427` (delta: `-0.0234`, tool_calls: `10` -> `10`)
- `task_013`: `0.5766` -> `0.5556` (delta: `-0.021`, tool_calls: `9` -> `9`)
- `task_017`: `0.5289` -> `0.5105` (delta: `-0.0184`, tool_calls: `10` -> `10`)
- `task_073`: `0.5108` -> `0.493` (delta: `-0.0178`, tool_calls: `8` -> `8`)

# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev54r2_001`
- improved_batch_run_id: `batch_run_realissuev55r1_001`
- created_at: `2026-06-12T09:15:04.736292+00:00`

## Task Set

- baseline_task_count: `51`
- improved_task_count: `52`
- common_task_count: `51`
- added_task_ids: `['task_105']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.6544`
- improved_average_duration_sec_all: `0.6784`
- baseline_average_duration_sec_common: `0.6544`
- improved_average_duration_sec_common: `0.6795`
- common_average_delta_sec: `0.0251`
- baseline_total_duration_sec_common: `33.3739`
- improved_total_duration_sec_common: `34.6554`

## Top Regressions

- `task_042`: `0.6928` -> `0.8588` (delta: `0.166`, tool_calls: `10` -> `10`)
- `task_017`: `0.6657` -> `0.7498` (delta: `0.0841`, tool_calls: `10` -> `10`)
- `task_006`: `0.6516` -> `0.7341` (delta: `0.0825`, tool_calls: `9` -> `9`)
- `task_046`: `0.6425` -> `0.7098` (delta: `0.0673`, tool_calls: `8` -> `8`)
- `task_040`: `0.6726` -> `0.7377` (delta: `0.0651`, tool_calls: `12` -> `12`)
- `task_095`: `0.6344` -> `0.6977` (delta: `0.0633`, tool_calls: `11` -> `11`)
- `task_010`: `0.651` -> `0.7129` (delta: `0.0619`, tool_calls: `9` -> `9`)
- `task_026`: `0.6545` -> `0.7157` (delta: `0.0612`, tool_calls: `9` -> `9`)
- `task_032`: `0.6617` -> `0.7205` (delta: `0.0588`, tool_calls: `9` -> `9`)
- `task_052`: `0.6339` -> `0.6808` (delta: `0.0469`, tool_calls: `12` -> `12`)

## Top Improvements

- `task_059`: `0.6994` -> `0.636` (delta: `-0.0634`, tool_calls: `8` -> `8`)
- `task_008`: `0.7293` -> `0.6772` (delta: `-0.0521`, tool_calls: `9` -> `9`)
- `task_050`: `0.6798` -> `0.633` (delta: `-0.0468`, tool_calls: `8` -> `8`)
- `task_022`: `0.7216` -> `0.6815` (delta: `-0.0401`, tool_calls: `9` -> `9`)
- `task_063`: `0.6699` -> `0.6471` (delta: `-0.0228`, tool_calls: `8` -> `8`)
- `task_089`: `0.6461` -> `0.6347` (delta: `-0.0114`, tool_calls: `9` -> `9`)
- `task_097`: `0.677` -> `0.6659` (delta: `-0.0111`, tool_calls: `11` -> `11`)
- `task_079`: `0.6232` -> `0.6131` (delta: `-0.0101`, tool_calls: `9` -> `9`)
- `task_061`: `0.6548` -> `0.6474` (delta: `-0.0074`, tool_calls: `8` -> `8`)
- `task_016`: `0.6934` -> `0.6876` (delta: `-0.0058`, tool_calls: `12` -> `12`)

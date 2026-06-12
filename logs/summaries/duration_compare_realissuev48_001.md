# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev47_001`
- improved_batch_run_id: `batch_run_realissuev48_001`
- created_at: `2026-06-12T04:54:16.554935+00:00`

## Task Set

- baseline_task_count: `44`
- improved_task_count: `45`
- common_task_count: `44`
- added_task_ids: `['task_091']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5234`
- improved_average_duration_sec_all: `0.5234`
- baseline_average_duration_sec_common: `0.5234`
- improved_average_duration_sec_common: `0.5241`
- common_average_delta_sec: `0.0007`
- baseline_total_duration_sec_common: `23.0291`
- improved_total_duration_sec_common: `23.0609`

## Top Regressions

- `task_038`: `0.5233` -> `0.5564` (delta: `0.0331`, tool_calls: `8` -> `8`)
- `task_060`: `0.485` -> `0.5153` (delta: `0.0303`, tool_calls: `8` -> `8`)
- `task_067`: `0.5044` -> `0.5346` (delta: `0.0302`, tool_calls: `10` -> `10`)
- `task_046`: `0.5336` -> `0.5609` (delta: `0.0273`, tool_calls: `8` -> `8`)
- `task_079`: `0.5011` -> `0.5277` (delta: `0.0266`, tool_calls: `9` -> `9`)
- `task_056`: `0.7477` -> `0.7733` (delta: `0.0256`, tool_calls: `10` -> `10`)
- `task_061`: `0.4976` -> `0.5232` (delta: `0.0256`, tool_calls: `8` -> `8`)
- `task_069`: `0.4869` -> `0.5108` (delta: `0.0239`, tool_calls: `8` -> `8`)
- `task_087`: `0.4644` -> `0.4878` (delta: `0.0234`, tool_calls: `9` -> `9`)
- `task_063`: `0.4817` -> `0.5013` (delta: `0.0196`, tool_calls: `8` -> `8`)

## Top Improvements

- `task_052`: `0.5345` -> `0.5007` (delta: `-0.0338`, tool_calls: `12` -> `12`)
- `task_042`: `0.5546` -> `0.5276` (delta: `-0.027`, tool_calls: `10` -> `10`)
- `task_058`: `0.5281` -> `0.5043` (delta: `-0.0238`, tool_calls: `10` -> `10`)
- `task_034`: `0.5283` -> `0.5047` (delta: `-0.0236`, tool_calls: `11` -> `11`)
- `task_010`: `0.5368` -> `0.5148` (delta: `-0.022`, tool_calls: `9` -> `9`)
- `task_022`: `0.5527` -> `0.5316` (delta: `-0.0211`, tool_calls: `9` -> `9`)
- `task_048`: `0.5232` -> `0.5031` (delta: `-0.0201`, tool_calls: `10` -> `10`)
- `task_075`: `0.5236` -> `0.5042` (delta: `-0.0194`, tool_calls: `10` -> `10`)
- `task_065`: `0.5209` -> `0.5032` (delta: `-0.0177`, tool_calls: `8` -> `8`)
- `task_059`: `0.502` -> `0.4857` (delta: `-0.0163`, tool_calls: `8` -> `8`)

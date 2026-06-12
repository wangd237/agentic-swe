# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev52_001`
- improved_batch_run_id: `batch_run_realissuev53r1_001`
- created_at: `2026-06-12T08:27:51.005368+00:00`

## Task Set

- baseline_task_count: `49`
- improved_task_count: `50`
- common_task_count: `49`
- added_task_ids: `['task_101']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.6618`
- improved_average_duration_sec_all: `0.7143`
- baseline_average_duration_sec_common: `0.6618`
- improved_average_duration_sec_common: `0.7153`
- common_average_delta_sec: `0.0535`
- baseline_total_duration_sec_common: `32.4299`
- improved_total_duration_sec_common: `35.0493`

## Top Regressions

- `task_019`: `0.6636` -> `0.8258` (delta: `0.1622`, tool_calls: `10` -> `10`)
- `task_085`: `0.6286` -> `0.7346` (delta: `0.106`, tool_calls: `9` -> `9`)
- `task_071`: `0.6243` -> `0.7268` (delta: `0.1025`, tool_calls: `8` -> `8`)
- `task_048`: `0.649` -> `0.7511` (delta: `0.1021`, tool_calls: `10` -> `10`)
- `task_013`: `0.6522` -> `0.7518` (delta: `0.0996`, tool_calls: `9` -> `9`)
- `task_017`: `0.6697` -> `0.7689` (delta: `0.0992`, tool_calls: `10` -> `10`)
- `task_056`: `0.8042` -> `0.901` (delta: `0.0968`, tool_calls: `10` -> `10`)
- `task_054`: `0.6096` -> `0.7051` (delta: `0.0955`, tool_calls: `10` -> `10`)
- `task_058`: `0.6311` -> `0.7247` (delta: `0.0936`, tool_calls: `10` -> `10`)
- `task_061`: `0.6102` -> `0.7014` (delta: `0.0912`, tool_calls: `8` -> `8`)

## Top Improvements

- `task_095`: `0.804` -> `0.6877` (delta: `-0.1163`, tool_calls: `11` -> `11`)
- `task_093`: `0.781` -> `0.706` (delta: `-0.075`, tool_calls: `10` -> `10`)
- `task_057`: `0.7234` -> `0.6747` (delta: `-0.0487`, tool_calls: `10` -> `10`)
- `task_089`: `0.6964` -> `0.6596` (delta: `-0.0368`, tool_calls: `9` -> `9`)

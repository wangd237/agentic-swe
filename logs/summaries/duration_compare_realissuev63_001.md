# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev62r2_001`
- improved_batch_run_id: `batch_run_realissuev63r2_001`
- created_at: `2026-06-12T12:33:32.737310+00:00`

## Task Set

- baseline_task_count: `59`
- improved_task_count: `60`
- common_task_count: `59`
- added_task_ids: `['task_121']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5424`
- improved_average_duration_sec_all: `0.5411`
- baseline_average_duration_sec_common: `0.5424`
- improved_average_duration_sec_common: `0.5419`
- common_average_delta_sec: `-0.0005`
- baseline_total_duration_sec_common: `31.9992`
- improved_total_duration_sec_common: `31.9711`

## Top Regressions

- `task_058`: `0.5458` -> `0.6102` (delta: `0.0644`, tool_calls: `10` -> `10`)
- `task_008`: `0.5414` -> `0.5856` (delta: `0.0442`, tool_calls: `9` -> `9`)
- `task_050`: `0.5141` -> `0.5554` (delta: `0.0413`, tool_calls: `8` -> `8`)
- `task_010`: `0.5614` -> `0.5957` (delta: `0.0343`, tool_calls: `9` -> `9`)
- `task_099`: `0.4767` -> `0.5015` (delta: `0.0248`, tool_calls: `9` -> `9`)
- `task_042`: `0.5608` -> `0.5849` (delta: `0.0241`, tool_calls: `10` -> `10`)
- `task_040`: `0.561` -> `0.5829` (delta: `0.0219`, tool_calls: `12` -> `12`)
- `task_113`: `0.497` -> `0.5151` (delta: `0.0181`, tool_calls: `8` -> `8`)
- `task_085`: `0.4929` -> `0.5108` (delta: `0.0179`, tool_calls: `9` -> `9`)
- `task_026`: `0.5646` -> `0.582` (delta: `0.0174`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_063`: `0.6338` -> `0.516` (delta: `-0.1178`, tool_calls: `8` -> `8`)
- `task_079`: `0.5877` -> `0.5313` (delta: `-0.0564`, tool_calls: `9` -> `9`)
- `task_083`: `0.5298` -> `0.4919` (delta: `-0.0379`, tool_calls: `8` -> `8`)
- `task_081`: `0.5556` -> `0.5194` (delta: `-0.0362`, tool_calls: `9` -> `9`)
- `task_111`: `0.5066` -> `0.4715` (delta: `-0.0351`, tool_calls: `10` -> `10`)
- `task_028`: `0.5984` -> `0.5646` (delta: `-0.0338`, tool_calls: `8` -> `8`)
- `task_093`: `0.5297` -> `0.4968` (delta: `-0.0329`, tool_calls: `10` -> `10`)
- `task_117`: `0.546` -> `0.5169` (delta: `-0.0291`, tool_calls: `10` -> `11`)
- `task_087`: `0.5299` -> `0.5073` (delta: `-0.0226`, tool_calls: `9` -> `9`)
- `task_056`: `0.7885` -> `0.7683` (delta: `-0.0202`, tool_calls: `10` -> `10`)

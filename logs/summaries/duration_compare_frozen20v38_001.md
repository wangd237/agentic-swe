# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v37_001`
- improved_batch_run_id: `batch_run_frozen20v38_001`
- created_at: `2026-06-12T02:03:14.951629+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5687`
- improved_average_duration_sec_all: `0.5427`
- baseline_average_duration_sec_common: `0.5687`
- improved_average_duration_sec_common: `0.5427`
- common_average_delta_sec: `-0.026`
- baseline_total_duration_sec_common: `11.3739`
- improved_total_duration_sec_common: `10.8533`

## Top Regressions

- `task_024`: `0.5584` -> `0.5641` (delta: `0.0057`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_036`: `0.5643` -> `0.5074` (delta: `-0.0569`, tool_calls: `8` -> `8`)
- `task_010`: `0.5867` -> `0.5409` (delta: `-0.0458`, tool_calls: `9` -> `9`)
- `task_013`: `0.5692` -> `0.5253` (delta: `-0.0439`, tool_calls: `9` -> `9`)
- `task_008`: `0.5613` -> `0.5208` (delta: `-0.0405`, tool_calls: `9` -> `9`)
- `task_040`: `0.575` -> `0.5359` (delta: `-0.0391`, tool_calls: `12` -> `12`)
- `task_026`: `0.6076` -> `0.5697` (delta: `-0.0379`, tool_calls: `9` -> `9`)
- `task_022`: `0.5829` -> `0.5457` (delta: `-0.0372`, tool_calls: `9` -> `9`)
- `task_019`: `0.5739` -> `0.5425` (delta: `-0.0314`, tool_calls: `10` -> `10`)
- `task_030`: `0.5666` -> `0.5382` (delta: `-0.0284`, tool_calls: `8` -> `8`)
- `task_038`: `0.5628` -> `0.5383` (delta: `-0.0245`, tool_calls: `8` -> `8`)

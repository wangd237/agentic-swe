# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v47_001`
- improved_batch_run_id: `batch_run_frozen20v48_001`
- created_at: `2026-06-12T04:54:16.887852+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5374`
- improved_average_duration_sec_all: `0.5287`
- baseline_average_duration_sec_common: `0.5374`
- improved_average_duration_sec_common: `0.5287`
- common_average_delta_sec: `-0.0087`
- baseline_total_duration_sec_common: `10.7478`
- improved_total_duration_sec_common: `10.5745`

## Top Regressions

- `task_038`: `0.522` -> `0.5552` (delta: `0.0332`, tool_calls: `8` -> `8`)
- `task_046`: `0.5341` -> `0.5623` (delta: `0.0282`, tool_calls: `8` -> `8`)
- `task_044`: `0.5456` -> `0.5565` (delta: `0.0109`, tool_calls: `8` -> `8`)
- `task_024`: `0.5227` -> `0.533` (delta: `0.0103`, tool_calls: `9` -> `9`)
- `task_019`: `0.5375` -> `0.5464` (delta: `0.0089`, tool_calls: `10` -> `10`)
- `task_034`: `0.5197` -> `0.5285` (delta: `0.0088`, tool_calls: `11` -> `11`)
- `task_017`: `0.5278` -> `0.5313` (delta: `0.0035`, tool_calls: `10` -> `10`)
- `task_028`: `0.5242` -> `0.5259` (delta: `0.0017`, tool_calls: `8` -> `8`)
- `task_040`: `0.5328` -> `0.5338` (delta: `0.001`, tool_calls: `12` -> `12`)
- `task_030`: `0.5322` -> `0.5327` (delta: `0.0005`, tool_calls: `8` -> `8`)

## Top Improvements

- `task_013`: `0.5429` -> `0.4934` (delta: `-0.0495`, tool_calls: `9` -> `9`)
- `task_016`: `0.5272` -> `0.4862` (delta: `-0.041`, tool_calls: `12` -> `12`)
- `task_022`: `0.565` -> `0.5314` (delta: `-0.0336`, tool_calls: `9` -> `9`)
- `task_008`: `0.5481` -> `0.5165` (delta: `-0.0316`, tool_calls: `9` -> `9`)
- `task_010`: `0.537` -> `0.5063` (delta: `-0.0307`, tool_calls: `9` -> `9`)
- `task_042`: `0.5564` -> `0.5286` (delta: `-0.0278`, tool_calls: `10` -> `10`)
- `task_006`: `0.5457` -> `0.5207` (delta: `-0.025`, tool_calls: `9` -> `9`)
- `task_032`: `0.5362` -> `0.5189` (delta: `-0.0173`, tool_calls: `9` -> `9`)
- `task_036`: `0.5326` -> `0.5201` (delta: `-0.0125`, tool_calls: `8` -> `8`)
- `task_026`: `0.5581` -> `0.5468` (delta: `-0.0113`, tool_calls: `9` -> `9`)

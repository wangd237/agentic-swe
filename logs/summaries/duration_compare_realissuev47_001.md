# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev46_001`
- improved_batch_run_id: `batch_run_realissuev47_001`
- created_at: `2026-06-12T04:44:51.388939+00:00`

## Task Set

- baseline_task_count: `43`
- improved_task_count: `44`
- common_task_count: `43`
- added_task_ids: `['task_089']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5243`
- improved_average_duration_sec_all: `0.5234`
- baseline_average_duration_sec_common: `0.5243`
- improved_average_duration_sec_common: `0.5245`
- common_average_delta_sec: `0.0002`
- baseline_total_duration_sec_common: `22.545`
- improved_total_duration_sec_common: `22.5547`

## Top Regressions

- `task_044`: `0.5153` -> `0.5476` (delta: `0.0323`, tool_calls: `8` -> `8`)
- `task_052`: `0.5025` -> `0.5345` (delta: `0.032`, tool_calls: `12` -> `12`)
- `task_010`: `0.5094` -> `0.5368` (delta: `0.0274`, tool_calls: `9` -> `9`)
- `task_067`: `0.478` -> `0.5044` (delta: `0.0264`, tool_calls: `10` -> `10`)
- `task_008`: `0.5223` -> `0.5481` (delta: `0.0258`, tool_calls: `9` -> `9`)
- `task_065`: `0.4957` -> `0.5209` (delta: `0.0252`, tool_calls: `8` -> `8`)
- `task_026`: `0.5359` -> `0.5578` (delta: `0.0219`, tool_calls: `9` -> `9`)
- `task_040`: `0.5139` -> `0.5323` (delta: `0.0184`, tool_calls: `12` -> `12`)
- `task_058`: `0.5109` -> `0.5281` (delta: `0.0172`, tool_calls: `10` -> `10`)
- `task_034`: `0.5114` -> `0.5283` (delta: `0.0169`, tool_calls: `11` -> `11`)

## Top Improvements

- `task_056`: `0.7863` -> `0.7477` (delta: `-0.0386`, tool_calls: `10` -> `10`)
- `task_060`: `0.5225` -> `0.485` (delta: `-0.0375`, tool_calls: `8` -> `8`)
- `task_036`: `0.5682` -> `0.5321` (delta: `-0.0361`, tool_calls: `8` -> `8`)
- `task_087`: `0.4885` -> `0.4644` (delta: `-0.0241`, tool_calls: `9` -> `9`)
- `task_063`: `0.5054` -> `0.4817` (delta: `-0.0237`, tool_calls: `8` -> `8`)
- `task_016`: `0.5503` -> `0.5273` (delta: `-0.023`, tool_calls: `12` -> `12`)
- `task_071`: `0.5275` -> `0.5053` (delta: `-0.0222`, tool_calls: `8` -> `8`)
- `task_019`: `0.5549` -> `0.5369` (delta: `-0.018`, tool_calls: `10` -> `10`)
- `task_069`: `0.5042` -> `0.4869` (delta: `-0.0173`, tool_calls: `8` -> `8`)
- `task_032`: `0.5418` -> `0.5258` (delta: `-0.016`, tool_calls: `9` -> `9`)

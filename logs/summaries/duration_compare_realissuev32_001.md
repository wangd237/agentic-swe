# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev31_001`
- improved_batch_run_id: `batch_run_realissuev32_001`
- created_at: `2026-06-11T05:44:55.455534+00:00`

## Task Set

- baseline_task_count: `29`
- improved_task_count: `30`
- common_task_count: `29`
- added_task_ids: `['task_061']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.6115`
- improved_average_duration_sec_all: `0.6778`
- baseline_average_duration_sec_common: `0.6115`
- improved_average_duration_sec_common: `0.6767`
- common_average_delta_sec: `0.0652`
- baseline_total_duration_sec_common: `17.7334`
- improved_total_duration_sec_common: `19.6232`

## Top Regressions

- `task_040`: `0.6213` -> `0.9463` (delta: `0.325`, tool_calls: `12` -> `12`)
- `task_034`: `0.6275` -> `0.8038` (delta: `0.1763`, tool_calls: `11` -> `11`)
- `task_036`: `0.6087` -> `0.7715` (delta: `0.1628`, tool_calls: `8` -> `8`)
- `task_038`: `0.5843` -> `0.747` (delta: `0.1627`, tool_calls: `8` -> `8`)
- `task_050`: `0.5778` -> `0.7151` (delta: `0.1373`, tool_calls: `8` -> `8`)
- `task_048`: `0.5912` -> `0.7246` (delta: `0.1334`, tool_calls: `10` -> `10`)
- `task_032`: `0.5983` -> `0.7152` (delta: `0.1169`, tool_calls: `9` -> `9`)
- `task_026`: `0.5993` -> `0.7075` (delta: `0.1082`, tool_calls: `9` -> `9`)
- `task_052`: `0.6041` -> `0.7033` (delta: `0.0992`, tool_calls: `12` -> `12`)
- `task_024`: `0.6149` -> `0.7012` (delta: `0.0863`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_016`: `0.6091` -> `0.557` (delta: `-0.0521`, tool_calls: `12` -> `12`)
- `task_013`: `0.6166` -> `0.5819` (delta: `-0.0347`, tool_calls: `9` -> `9`)
- `task_056`: `0.8566` -> `0.8386` (delta: `-0.018`, tool_calls: `10` -> `10`)
- `task_017`: `0.6119` -> `0.5971` (delta: `-0.0148`, tool_calls: `10` -> `10`)
- `task_057`: `0.5981` -> `0.5835` (delta: `-0.0146`, tool_calls: `10` -> `10`)

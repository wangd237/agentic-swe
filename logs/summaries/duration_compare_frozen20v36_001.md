# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v35_001`
- improved_batch_run_id: `batch_run_frozen20v36_001`
- created_at: `2026-06-11T16:23:16.090519+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5402`
- improved_average_duration_sec_all: `0.5386`
- baseline_average_duration_sec_common: `0.5402`
- improved_average_duration_sec_common: `0.5386`
- common_average_delta_sec: `-0.0016`
- baseline_total_duration_sec_common: `10.8038`
- improved_total_duration_sec_common: `10.7712`

## Top Regressions

- `task_040`: `0.5331` -> `0.5747` (delta: `0.0416`, tool_calls: `12` -> `12`)
- `task_024`: `0.531` -> `0.5571` (delta: `0.0261`, tool_calls: `9` -> `9`)
- `task_006`: `0.505` -> `0.53` (delta: `0.025`, tool_calls: `9` -> `9`)
- `task_032`: `0.5186` -> `0.5422` (delta: `0.0236`, tool_calls: `9` -> `9`)
- `task_030`: `0.5255` -> `0.5402` (delta: `0.0147`, tool_calls: `8` -> `8`)
- `task_036`: `0.5381` -> `0.5517` (delta: `0.0136`, tool_calls: `8` -> `8`)
- `task_022`: `0.5084` -> `0.5138` (delta: `0.0054`, tool_calls: `9` -> `9`)
- `task_034`: `0.5423` -> `0.5453` (delta: `0.003`, tool_calls: `11` -> `11`)

## Top Improvements

- `task_019`: `0.5741` -> `0.5319` (delta: `-0.0422`, tool_calls: `10` -> `10`)
- `task_028`: `0.56` -> `0.524` (delta: `-0.036`, tool_calls: `8` -> `8`)
- `task_017`: `0.5856` -> `0.5532` (delta: `-0.0324`, tool_calls: `10` -> `10`)
- `task_013`: `0.5417` -> `0.5292` (delta: `-0.0125`, tool_calls: `9` -> `9`)
- `task_016`: `0.5354` -> `0.5236` (delta: `-0.0118`, tool_calls: `12` -> `12`)
- `task_042`: `0.5521` -> `0.5427` (delta: `-0.0094`, tool_calls: `10` -> `10`)
- `task_044`: `0.545` -> `0.5356` (delta: `-0.0094`, tool_calls: `8` -> `8`)
- `task_008`: `0.5423` -> `0.5335` (delta: `-0.0088`, tool_calls: `9` -> `9`)
- `task_038`: `0.5403` -> `0.5319` (delta: `-0.0084`, tool_calls: `8` -> `8`)
- `task_026`: `0.5453` -> `0.5386` (delta: `-0.0067`, tool_calls: `9` -> `9`)

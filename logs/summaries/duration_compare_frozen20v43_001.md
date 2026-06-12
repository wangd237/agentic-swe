# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v42_001`
- improved_batch_run_id: `batch_run_frozen20v43_001`
- created_at: `2026-06-12T03:24:29.452612+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5186`
- improved_average_duration_sec_all: `0.5291`
- baseline_average_duration_sec_common: `0.5186`
- improved_average_duration_sec_common: `0.5291`
- common_average_delta_sec: `0.0105`
- baseline_total_duration_sec_common: `10.3713`
- improved_total_duration_sec_common: `10.5813`

## Top Regressions

- `task_013`: `0.5152` -> `0.576` (delta: `0.0608`, tool_calls: `9` -> `9`)
- `task_008`: `0.5031` -> `0.559` (delta: `0.0559`, tool_calls: `9` -> `9`)
- `task_038`: `0.4983` -> `0.5411` (delta: `0.0428`, tool_calls: `8` -> `8`)
- `task_016`: `0.4982` -> `0.5344` (delta: `0.0362`, tool_calls: `12` -> `12`)
- `task_026`: `0.5087` -> `0.5344` (delta: `0.0257`, tool_calls: `9` -> `9`)
- `task_036`: `0.5135` -> `0.5342` (delta: `0.0207`, tool_calls: `8` -> `8`)
- `task_032`: `0.5049` -> `0.5242` (delta: `0.0193`, tool_calls: `9` -> `9`)
- `task_017`: `0.519` -> `0.5291` (delta: `0.0101`, tool_calls: `10` -> `10`)
- `task_044`: `0.5115` -> `0.5207` (delta: `0.0092`, tool_calls: `8` -> `8`)
- `task_040`: `0.5211` -> `0.5293` (delta: `0.0082`, tool_calls: `12` -> `12`)

## Top Improvements

- `task_006`: `0.5579` -> `0.5274` (delta: `-0.0305`, tool_calls: `9` -> `9`)
- `task_022`: `0.5246` -> `0.5129` (delta: `-0.0117`, tool_calls: `9` -> `9`)
- `task_034`: `0.5251` -> `0.5134` (delta: `-0.0117`, tool_calls: `11` -> `11`)
- `task_028`: `0.5261` -> `0.5147` (delta: `-0.0114`, tool_calls: `8` -> `8`)
- `task_010`: `0.5274` -> `0.5197` (delta: `-0.0077`, tool_calls: `9` -> `9`)
- `task_024`: `0.5189` -> `0.5141` (delta: `-0.0048`, tool_calls: `9` -> `9`)
- `task_030`: `0.5158` -> `0.5127` (delta: `-0.0031`, tool_calls: `8` -> `8`)
- `task_046`: `0.519` -> `0.5159` (delta: `-0.0031`, tool_calls: `8` -> `8`)

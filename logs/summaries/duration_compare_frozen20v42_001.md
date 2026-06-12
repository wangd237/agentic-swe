# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v41_001`
- improved_batch_run_id: `batch_run_frozen20v42_001`
- created_at: `2026-06-12T03:04:48.499453+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5185`
- improved_average_duration_sec_all: `0.5186`
- baseline_average_duration_sec_common: `0.5185`
- improved_average_duration_sec_common: `0.5186`
- common_average_delta_sec: `0.0001`
- baseline_total_duration_sec_common: `10.3694`
- improved_total_duration_sec_common: `10.3713`

## Top Regressions

- `task_006`: `0.5031` -> `0.5579` (delta: `0.0548`, tool_calls: `9` -> `9`)
- `task_030`: `0.4824` -> `0.5158` (delta: `0.0334`, tool_calls: `8` -> `8`)
- `task_010`: `0.4945` -> `0.5274` (delta: `0.0329`, tool_calls: `9` -> `9`)
- `task_036`: `0.4882` -> `0.5135` (delta: `0.0253`, tool_calls: `8` -> `8`)
- `task_034`: `0.5092` -> `0.5251` (delta: `0.0159`, tool_calls: `11` -> `11`)
- `task_017`: `0.5107` -> `0.519` (delta: `0.0083`, tool_calls: `10` -> `10`)
- `task_042`: `0.5187` -> `0.5259` (delta: `0.0072`, tool_calls: `10` -> `10`)
- `task_013`: `0.5085` -> `0.5152` (delta: `0.0067`, tool_calls: `9` -> `9`)
- `task_019`: `0.5319` -> `0.5371` (delta: `0.0052`, tool_calls: `10` -> `10`)
- `task_022`: `0.5231` -> `0.5246` (delta: `0.0015`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_032`: `0.5387` -> `0.5049` (delta: `-0.0338`, tool_calls: `9` -> `9`)
- `task_016`: `0.5267` -> `0.4982` (delta: `-0.0285`, tool_calls: `12` -> `12`)
- `task_038`: `0.5254` -> `0.4983` (delta: `-0.0271`, tool_calls: `8` -> `8`)
- `task_024`: `0.5439` -> `0.5189` (delta: `-0.025`, tool_calls: `9` -> `9`)
- `task_046`: `0.5404` -> `0.519` (delta: `-0.0214`, tool_calls: `8` -> `8`)
- `task_026`: `0.5274` -> `0.5087` (delta: `-0.0187`, tool_calls: `9` -> `9`)
- `task_028`: `0.5396` -> `0.5261` (delta: `-0.0135`, tool_calls: `8` -> `8`)
- `task_040`: `0.5323` -> `0.5211` (delta: `-0.0112`, tool_calls: `12` -> `12`)
- `task_008`: `0.5083` -> `0.5031` (delta: `-0.0052`, tool_calls: `9` -> `9`)
- `task_044`: `0.5164` -> `0.5115` (delta: `-0.0049`, tool_calls: `8` -> `8`)

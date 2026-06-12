# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev41_001`
- improved_batch_run_id: `batch_run_realissuev42_001`
- created_at: `2026-06-12T03:04:47.919522+00:00`

## Task Set

- baseline_task_count: `38`
- improved_task_count: `39`
- common_task_count: `38`
- added_task_ids: `['task_079']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5173`
- improved_average_duration_sec_all: `0.5157`
- baseline_average_duration_sec_common: `0.5173`
- improved_average_duration_sec_common: `0.5165`
- common_average_delta_sec: `-0.0008`
- baseline_total_duration_sec_common: `19.6572`
- improved_total_duration_sec_common: `19.6275`

## Top Regressions

- `task_006`: `0.4834` -> `0.5571` (delta: `0.0737`, tool_calls: `9` -> `9`)
- `task_010`: `0.499` -> `0.5316` (delta: `0.0326`, tool_calls: `9` -> `9`)
- `task_034`: `0.4965` -> `0.5249` (delta: `0.0284`, tool_calls: `11` -> `11`)
- `task_042`: `0.4985` -> `0.5257` (delta: `0.0272`, tool_calls: `10` -> `10`)
- `task_017`: `0.4986` -> `0.52` (delta: `0.0214`, tool_calls: `10` -> `10`)
- `task_019`: `0.5179` -> `0.5376` (delta: `0.0197`, tool_calls: `10` -> `10`)
- `task_054`: `0.4896` -> `0.5073` (delta: `0.0177`, tool_calls: `10` -> `10`)
- `task_065`: `0.4868` -> `0.5035` (delta: `0.0167`, tool_calls: `8` -> `8`)
- `task_048`: `0.5037` -> `0.5191` (delta: `0.0154`, tool_calls: `10` -> `10`)
- `task_077`: `0.5011` -> `0.5145` (delta: `0.0134`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_067`: `0.5463` -> `0.5012` (delta: `-0.0451`, tool_calls: `10` -> `10`)
- `task_032`: `0.5494` -> `0.5088` (delta: `-0.0406`, tool_calls: `9` -> `9`)
- `task_071`: `0.5366` -> `0.5003` (delta: `-0.0363`, tool_calls: `8` -> `8`)
- `task_069`: `0.5248` -> `0.4948` (delta: `-0.03`, tool_calls: `8` -> `8`)
- `task_073`: `0.5097` -> `0.4828` (delta: `-0.0269`, tool_calls: `8` -> `8`)
- `task_056`: `0.7121` -> `0.6864` (delta: `-0.0257`, tool_calls: `10` -> `10`)
- `task_024`: `0.5356` -> `0.5139` (delta: `-0.0217`, tool_calls: `9` -> `9`)
- `task_046`: `0.5317` -> `0.5149` (delta: `-0.0168`, tool_calls: `8` -> `8`)
- `task_050`: `0.5186` -> `0.5018` (delta: `-0.0168`, tool_calls: `8` -> `8`)
- `task_063`: `0.5219` -> `0.5074` (delta: `-0.0145`, tool_calls: `8` -> `8`)

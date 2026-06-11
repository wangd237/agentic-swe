# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev33_001`
- improved_batch_run_id: `batch_run_realissuev34_001`
- created_at: `2026-06-11T15:47:47.175009+00:00`

## Task Set

- baseline_task_count: `30`
- improved_task_count: `31`
- common_task_count: `30`
- added_task_ids: `['task_063']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5423`
- improved_average_duration_sec_all: `0.5391`
- baseline_average_duration_sec_common: `0.5423`
- improved_average_duration_sec_common: `0.5409`
- common_average_delta_sec: `-0.0014`
- baseline_total_duration_sec_common: `16.268`
- improved_total_duration_sec_common: `16.2273`

## Top Regressions

- `task_024`: `0.5107` -> `0.5701` (delta: `0.0594`, tool_calls: `9` -> `9`)
- `task_028`: `0.5137` -> `0.567` (delta: `0.0533`, tool_calls: `8` -> `8`)
- `task_022`: `0.5136` -> `0.5574` (delta: `0.0438`, tool_calls: `9` -> `9`)
- `task_019`: `0.5118` -> `0.5538` (delta: `0.042`, tool_calls: `10` -> `10`)
- `task_046`: `0.5207` -> `0.5493` (delta: `0.0286`, tool_calls: `8` -> `8`)
- `task_032`: `0.5206` -> `0.5488` (delta: `0.0282`, tool_calls: `9` -> `9`)
- `task_038`: `0.5241` -> `0.5513` (delta: `0.0272`, tool_calls: `8` -> `8`)
- `task_036`: `0.5351` -> `0.5612` (delta: `0.0261`, tool_calls: `8` -> `8`)
- `task_017`: `0.5094` -> `0.5353` (delta: `0.0259`, tool_calls: `10` -> `10`)
- `task_016`: `0.5138` -> `0.5375` (delta: `0.0237`, tool_calls: `12` -> `12`)

## Top Improvements

- `task_060`: `0.5866` -> `0.5027` (delta: `-0.0839`, tool_calls: `8` -> `8`)
- `task_059`: `0.5734` -> `0.5099` (delta: `-0.0635`, tool_calls: `8` -> `8`)
- `task_048`: `0.5882` -> `0.5292` (delta: `-0.059`, tool_calls: `10` -> `10`)
- `task_054`: `0.5702` -> `0.5219` (delta: `-0.0483`, tool_calls: `10` -> `10`)
- `task_056`: `0.7169` -> `0.6704` (delta: `-0.0465`, tool_calls: `10` -> `10`)
- `task_052`: `0.5859` -> `0.5415` (delta: `-0.0444`, tool_calls: `12` -> `12`)
- `task_057`: `0.5697` -> `0.5407` (delta: `-0.029`, tool_calls: `10` -> `10`)
- `task_040`: `0.5522` -> `0.5268` (delta: `-0.0254`, tool_calls: `12` -> `12`)
- `task_058`: `0.5465` -> `0.5223` (delta: `-0.0242`, tool_calls: `10` -> `10`)
- `task_061`: `0.5397` -> `0.5181` (delta: `-0.0216`, tool_calls: `8` -> `8`)

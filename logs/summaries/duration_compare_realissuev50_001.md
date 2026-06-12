# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev49_001`
- improved_batch_run_id: `batch_run_realissuev50_001`
- created_at: `2026-06-12T07:24:16.373990+00:00`

## Task Set

- baseline_task_count: `46`
- improved_task_count: `47`
- common_task_count: `46`
- added_task_ids: `['task_095']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5869`
- improved_average_duration_sec_all: `0.5583`
- baseline_average_duration_sec_common: `0.5869`
- improved_average_duration_sec_common: `0.5592`
- common_average_delta_sec: `-0.0277`
- baseline_total_duration_sec_common: `26.998`
- improved_total_duration_sec_common: `25.7228`

## Top Regressions

- `task_091`: `0.5228` -> `0.5552` (delta: `0.0324`, tool_calls: `11` -> `11`)
- `task_028`: `0.5543` -> `0.5853` (delta: `0.031`, tool_calls: `8` -> `8`)
- `task_093`: `0.5288` -> `0.5587` (delta: `0.0299`, tool_calls: `10` -> `10`)
- `task_077`: `0.5189` -> `0.548` (delta: `0.0291`, tool_calls: `9` -> `9`)
- `task_034`: `0.5492` -> `0.578` (delta: `0.0288`, tool_calls: `11` -> `11`)
- `task_032`: `0.5639` -> `0.5767` (delta: `0.0128`, tool_calls: `9` -> `9`)
- `task_073`: `0.5511` -> `0.561` (delta: `0.0099`, tool_calls: `8` -> `8`)
- `task_024`: `0.5852` -> `0.5945` (delta: `0.0093`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_087`: `0.6227` -> `0.5228` (delta: `-0.0999`, tool_calls: `9` -> `9`)
- `task_042`: `0.627` -> `0.5322` (delta: `-0.0948`, tool_calls: `10` -> `10`)
- `task_056`: `0.8884` -> `0.7972` (delta: `-0.0912`, tool_calls: `10` -> `10`)
- `task_089`: `0.5853` -> `0.4992` (delta: `-0.0861`, tool_calls: `9` -> `9`)
- `task_052`: `0.6082` -> `0.5404` (delta: `-0.0678`, tool_calls: `12` -> `12`)
- `task_079`: `0.59` -> `0.5265` (delta: `-0.0635`, tool_calls: `9` -> `9`)
- `task_022`: `0.6399` -> `0.578` (delta: `-0.0619`, tool_calls: `9` -> `9`)
- `task_013`: `0.5983` -> `0.538` (delta: `-0.0603`, tool_calls: `9` -> `9`)
- `task_058`: `0.6137` -> `0.555` (delta: `-0.0587`, tool_calls: `10` -> `10`)
- `task_010`: `0.628` -> `0.5707` (delta: `-0.0573`, tool_calls: `9` -> `9`)

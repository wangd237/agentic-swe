# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev45_001`
- improved_batch_run_id: `batch_run_realissuev46_001`
- created_at: `2026-06-12T04:31:10.997293+00:00`

## Task Set

- baseline_task_count: `42`
- improved_task_count: `43`
- common_task_count: `42`
- added_task_ids: `['task_087']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5175`
- improved_average_duration_sec_all: `0.5243`
- baseline_average_duration_sec_common: `0.5175`
- improved_average_duration_sec_common: `0.5252`
- common_average_delta_sec: `0.0077`
- baseline_total_duration_sec_common: `21.7371`
- improved_total_duration_sec_common: `22.0565`

## Top Regressions

- `task_019`: `0.4977` -> `0.5549` (delta: `0.0572`, tool_calls: `10` -> `10`)
- `task_016`: `0.4983` -> `0.5503` (delta: `0.052`, tool_calls: `12` -> `12`)
- `task_036`: `0.5245` -> `0.5682` (delta: `0.0437`, tool_calls: `8` -> `8`)
- `task_013`: `0.507` -> `0.5443` (delta: `0.0373`, tool_calls: `9` -> `9`)
- `task_032`: `0.5069` -> `0.5418` (delta: `0.0349`, tool_calls: `9` -> `9`)
- `task_022`: `0.5201` -> `0.5541` (delta: `0.034`, tool_calls: `9` -> `9`)
- `task_060`: `0.4913` -> `0.5225` (delta: `0.0312`, tool_calls: `8` -> `8`)
- `task_042`: `0.5239` -> `0.5534` (delta: `0.0295`, tool_calls: `10` -> `10`)
- `task_079`: `0.4907` -> `0.5161` (delta: `0.0254`, tool_calls: `9` -> `9`)
- `task_017`: `0.5045` -> `0.5285` (delta: `0.024`, tool_calls: `10` -> `10`)

## Top Improvements

- `task_065`: `0.5315` -> `0.4957` (delta: `-0.0358`, tool_calls: `8` -> `8`)
- `task_044`: `0.542` -> `0.5153` (delta: `-0.0267`, tool_calls: `8` -> `8`)
- `task_040`: `0.5402` -> `0.5139` (delta: `-0.0263`, tool_calls: `12` -> `12`)
- `task_067`: `0.5029` -> `0.478` (delta: `-0.0249`, tool_calls: `10` -> `10`)
- `task_058`: `0.534` -> `0.5109` (delta: `-0.0231`, tool_calls: `10` -> `10`)
- `task_081`: `0.4995` -> `0.4797` (delta: `-0.0198`, tool_calls: `9` -> `9`)
- `task_052`: `0.5214` -> `0.5025` (delta: `-0.0189`, tool_calls: `12` -> `12`)
- `task_073`: `0.5265` -> `0.5092` (delta: `-0.0173`, tool_calls: `8` -> `8`)
- `task_038`: `0.529` -> `0.513` (delta: `-0.016`, tool_calls: `8` -> `8`)
- `task_054`: `0.5185` -> `0.5029` (delta: `-0.0156`, tool_calls: `10` -> `10`)

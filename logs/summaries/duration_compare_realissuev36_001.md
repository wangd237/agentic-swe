# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev35_001`
- improved_batch_run_id: `batch_run_realissuev36_001`
- created_at: `2026-06-11T16:23:16.076611+00:00`

## Task Set

- baseline_task_count: `32`
- improved_task_count: `33`
- common_task_count: `32`
- added_task_ids: `['task_067']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.535`
- improved_average_duration_sec_all: `0.5312`
- baseline_average_duration_sec_common: `0.535`
- improved_average_duration_sec_common: `0.5323`
- common_average_delta_sec: `-0.0027`
- baseline_total_duration_sec_common: `17.1203`
- improved_total_duration_sec_common: `17.0337`

## Top Regressions

- `task_040`: `0.5368` -> `0.5738` (delta: `0.037`, tool_calls: `12` -> `12`)
- `task_032`: `0.5116` -> `0.5412` (delta: `0.0296`, tool_calls: `9` -> `9`)
- `task_024`: `0.5293` -> `0.5549` (delta: `0.0256`, tool_calls: `9` -> `9`)
- `task_063`: `0.4911` -> `0.5096` (delta: `0.0185`, tool_calls: `8` -> `8`)
- `task_065`: `0.5007` -> `0.517` (delta: `0.0163`, tool_calls: `8` -> `8`)
- `task_030`: `0.525` -> `0.5406` (delta: `0.0156`, tool_calls: `8` -> `8`)
- `task_036`: `0.5386` -> `0.5526` (delta: `0.014`, tool_calls: `8` -> `8`)
- `task_022`: `0.5108` -> `0.5243` (delta: `0.0135`, tool_calls: `9` -> `9`)
- `task_056`: `0.6692` -> `0.6763` (delta: `0.0071`, tool_calls: `10` -> `10`)
- `task_057`: `0.5046` -> `0.5112` (delta: `0.0066`, tool_calls: `10` -> `10`)

## Top Improvements

- `task_017`: `0.5854` -> `0.5314` (delta: `-0.054`, tool_calls: `10` -> `10`)
- `task_028`: `0.5615` -> `0.5235` (delta: `-0.038`, tool_calls: `8` -> `8`)
- `task_019`: `0.5742` -> `0.5405` (delta: `-0.0337`, tool_calls: `10` -> `10`)
- `task_059`: `0.5173` -> `0.4914` (delta: `-0.0259`, tool_calls: `8` -> `8`)
- `task_054`: `0.525` -> `0.511` (delta: `-0.014`, tool_calls: `10` -> `10`)
- `task_060`: `0.5333` -> `0.5194` (delta: `-0.0139`, tool_calls: `8` -> `8`)
- `task_013`: `0.5416` -> `0.5289` (delta: `-0.0127`, tool_calls: `9` -> `9`)
- `task_016`: `0.5356` -> `0.5238` (delta: `-0.0118`, tool_calls: `12` -> `12`)
- `task_008`: `0.5425` -> `0.5335` (delta: `-0.009`, tool_calls: `9` -> `9`)
- `task_044`: `0.544` -> `0.5352` (delta: `-0.0088`, tool_calls: `8` -> `8`)

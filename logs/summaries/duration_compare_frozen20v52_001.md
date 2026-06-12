# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v51_002`
- improved_batch_run_id: `batch_run_frozen20v52_001`
- created_at: `2026-06-12T08:01:34.846008+00:00`

## Task Set

- baseline_task_count: `20`
- improved_task_count: `20`
- common_task_count: `20`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.7361`
- improved_average_duration_sec_all: `0.6732`
- baseline_average_duration_sec_common: `0.7361`
- improved_average_duration_sec_common: `0.6732`
- common_average_delta_sec: `-0.0629`
- baseline_total_duration_sec_common: `14.7213`
- improved_total_duration_sec_common: `13.4637`

## Top Regressions

- `task_016`: `0.6716` -> `0.6919` (delta: `0.0203`, tool_calls: `12` -> `12`)
- `task_036`: `0.6888` -> `0.7028` (delta: `0.014`, tool_calls: `8` -> `8`)
- `task_026`: `0.6801` -> `0.6901` (delta: `0.01`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_038`: `1.004` -> `0.6635` (delta: `-0.3405`, tool_calls: `8` -> `8`)
- `task_040`: `0.8582` -> `0.6603` (delta: `-0.1979`, tool_calls: `12` -> `12`)
- `task_006`: `0.86` -> `0.6852` (delta: `-0.1748`, tool_calls: `9` -> `9`)
- `task_044`: `0.7711` -> `0.6743` (delta: `-0.0968`, tool_calls: `8` -> `8`)
- `task_008`: `0.7371` -> `0.6816` (delta: `-0.0555`, tool_calls: `9` -> `9`)
- `task_042`: `0.7481` -> `0.693` (delta: `-0.0551`, tool_calls: `10` -> `10`)
- `task_030`: `0.7219` -> `0.6679` (delta: `-0.054`, tool_calls: `8` -> `8`)
- `task_032`: `0.7175` -> `0.6682` (delta: `-0.0493`, tool_calls: `9` -> `9`)
- `task_013`: `0.6966` -> `0.6527` (delta: `-0.0439`, tool_calls: `9` -> `9`)
- `task_019`: `0.7041` -> `0.662` (delta: `-0.0421`, tool_calls: `10` -> `10`)

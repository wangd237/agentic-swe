# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev50_001`
- improved_batch_run_id: `batch_run_realissuev51_002`
- created_at: `2026-06-12T07:37:52.832116+00:00`

## Task Set

- baseline_task_count: `47`
- improved_task_count: `48`
- common_task_count: `47`
- added_task_ids: `['task_097']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5583`
- improved_average_duration_sec_all: `0.6987`
- baseline_average_duration_sec_common: `0.5583`
- improved_average_duration_sec_common: `0.6995`
- common_average_delta_sec: `0.1412`
- baseline_total_duration_sec_common: `26.241`
- improved_total_duration_sec_common: `32.8775`

## Top Regressions

- `task_038`: `0.581` -> `1.0054` (delta: `0.4244`, tool_calls: `8` -> `8`)
- `task_040`: `0.5931` -> `0.8578` (delta: `0.2647`, tool_calls: `12` -> `12`)
- `task_006`: `0.599` -> `0.8391` (delta: `0.2401`, tool_calls: `9` -> `9`)
- `task_042`: `0.5322` -> `0.7492` (delta: `0.217`, tool_calls: `10` -> `10`)
- `task_044`: `0.5582` -> `0.7729` (delta: `0.2147`, tool_calls: `8` -> `8`)
- `task_065`: `0.5368` -> `0.7177` (delta: `0.1809`, tool_calls: `8` -> `8`)
- `task_083`: `0.5001` -> `0.6658` (delta: `0.1657`, tool_calls: `8` -> `8`)
- `task_067`: `0.53` -> `0.6915` (delta: `0.1615`, tool_calls: `10` -> `10`)
- `task_073`: `0.561` -> `0.7206` (delta: `0.1596`, tool_calls: `8` -> `8`)
- `task_063`: `0.5434` -> `0.7021` (delta: `0.1587`, tool_calls: `8` -> `8`)

## Top Improvements

- 当前没有检测到公共任务上的时延改善

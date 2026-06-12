# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev51_002`
- improved_batch_run_id: `batch_run_realissuev52_001`
- created_at: `2026-06-12T08:01:34.816344+00:00`

## Task Set

- baseline_task_count: `48`
- improved_task_count: `49`
- common_task_count: `48`
- added_task_ids: `['task_099']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.6987`
- improved_average_duration_sec_all: `0.6618`
- baseline_average_duration_sec_common: `0.6987`
- improved_average_duration_sec_common: `0.663`
- common_average_delta_sec: `-0.0357`
- baseline_total_duration_sec_common: `33.5378`
- improved_total_duration_sec_common: `31.8251`

## Top Regressions

- `task_095`: `0.6371` -> `0.804` (delta: `0.1669`, tool_calls: `11` -> `11`)
- `task_093`: `0.6493` -> `0.781` (delta: `0.1317`, tool_calls: `10` -> `10`)
- `task_089`: `0.6099` -> `0.6964` (delta: `0.0865`, tool_calls: `9` -> `9`)
- `task_057`: `0.6515` -> `0.7234` (delta: `0.0719`, tool_calls: `10` -> `10`)
- `task_026`: `0.6693` -> `0.6933` (delta: `0.024`, tool_calls: `9` -> `9`)
- `task_091`: `0.6273` -> `0.6465` (delta: `0.0192`, tool_calls: `11` -> `11`)
- `task_087`: `0.6205` -> `0.6373` (delta: `0.0168`, tool_calls: `9` -> `9`)
- `task_036`: `0.6871` -> `0.7028` (delta: `0.0157`, tool_calls: `8` -> `8`)
- `task_016`: `0.6794` -> `0.6935` (delta: `0.0141`, tool_calls: `12` -> `12`)

## Top Improvements

- `task_038`: `1.0054` -> `0.6634` (delta: `-0.342`, tool_calls: `8` -> `8`)
- `task_040`: `0.8578` -> `0.6604` (delta: `-0.1974`, tool_calls: `12` -> `12`)
- `task_006`: `0.8391` -> `0.6653` (delta: `-0.1738`, tool_calls: `9` -> `9`)
- `task_044`: `0.7729` -> `0.6757` (delta: `-0.0972`, tool_calls: `8` -> `8`)
- `task_065`: `0.7177` -> `0.6246` (delta: `-0.0931`, tool_calls: `8` -> `8`)
- `task_056`: `0.8854` -> `0.8042` (delta: `-0.0812`, tool_calls: `10` -> `10`)
- `task_061`: `0.6799` -> `0.6102` (delta: `-0.0697`, tool_calls: `8` -> `8`)
- `task_067`: `0.6915` -> `0.6235` (delta: `-0.068`, tool_calls: `10` -> `10`)
- `task_063`: `0.7021` -> `0.6347` (delta: `-0.0674`, tool_calls: `8` -> `8`)
- `task_077`: `0.6805` -> `0.6131` (delta: `-0.0674`, tool_calls: `9` -> `9`)

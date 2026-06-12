# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev37_001`
- improved_batch_run_id: `batch_run_realissuev38_001`
- created_at: `2026-06-12T02:03:14.919152+00:00`

## Task Set

- baseline_task_count: `34`
- improved_task_count: `35`
- common_task_count: `34`
- added_task_ids: `['task_071']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.6038`
- improved_average_duration_sec_all: `0.553`
- baseline_average_duration_sec_common: `0.6038`
- improved_average_duration_sec_common: `0.5539`
- common_average_delta_sec: `-0.0499`
- baseline_total_duration_sec_common: `20.5296`
- improved_total_duration_sec_common: `18.8327`

## Top Regressions

- `task_061`: `0.5511` -> `0.5613` (delta: `0.0102`, tool_calls: `8` -> `8`)

## Top Improvements

- `task_056`: `0.8408` -> `0.7285` (delta: `-0.1123`, tool_calls: `10` -> `10`)
- `task_017`: `0.6378` -> `0.5311` (delta: `-0.1067`, tool_calls: `10` -> `10`)
- `task_024`: `0.6314` -> `0.5426` (delta: `-0.0888`, tool_calls: `9` -> `9`)
- `task_022`: `0.6456` -> `0.5624` (delta: `-0.0832`, tool_calls: `9` -> `9`)
- `task_016`: `0.6076` -> `0.5249` (delta: `-0.0827`, tool_calls: `12` -> `12`)
- `task_010`: `0.6147` -> `0.5381` (delta: `-0.0766`, tool_calls: `9` -> `9`)
- `task_038`: `0.5995` -> `0.5283` (delta: `-0.0712`, tool_calls: `8` -> `8`)
- `task_046`: `0.6151` -> `0.5459` (delta: `-0.0692`, tool_calls: `8` -> `8`)
- `task_054`: `0.5755` -> `0.5082` (delta: `-0.0673`, tool_calls: `10` -> `10`)
- `task_019`: `0.6192` -> `0.5536` (delta: `-0.0656`, tool_calls: `10` -> `10`)

# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev38_001`
- improved_batch_run_id: `batch_run_realissuev39_001`
- created_at: `2026-06-12T02:14:33.775357+00:00`

## Task Set

- baseline_task_count: `35`
- improved_task_count: `36`
- common_task_count: `35`
- added_task_ids: `['task_073']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.553`
- improved_average_duration_sec_all: `0.5453`
- baseline_average_duration_sec_common: `0.553`
- improved_average_duration_sec_common: `0.5452`
- common_average_delta_sec: `-0.0078`
- baseline_total_duration_sec_common: `19.3548`
- improved_total_duration_sec_common: `19.0832`

## Top Regressions

- `task_016`: `0.5249` -> `0.5574` (delta: `0.0325`, tool_calls: `12` -> `12`)
- `task_065`: `0.5378` -> `0.5625` (delta: `0.0247`, tool_calls: `8` -> `8`)
- `task_054`: `0.5082` -> `0.5267` (delta: `0.0185`, tool_calls: `10` -> `10`)
- `task_024`: `0.5426` -> `0.5607` (delta: `0.0181`, tool_calls: `9` -> `9`)
- `task_038`: `0.5283` -> `0.5463` (delta: `0.018`, tool_calls: `8` -> `8`)
- `task_048`: `0.5295` -> `0.546` (delta: `0.0165`, tool_calls: `10` -> `10`)
- `task_067`: `0.5223` -> `0.5366` (delta: `0.0143`, tool_calls: `10` -> `10`)
- `task_019`: `0.5536` -> `0.567` (delta: `0.0134`, tool_calls: `10` -> `10`)
- `task_017`: `0.5311` -> `0.5423` (delta: `0.0112`, tool_calls: `10` -> `10`)
- `task_030`: `0.5365` -> `0.5474` (delta: `0.0109`, tool_calls: `8` -> `8`)

## Top Improvements

- `task_006`: `0.5882` -> `0.4969` (delta: `-0.0913`, tool_calls: `9` -> `9`)
- `task_042`: `0.5775` -> `0.5327` (delta: `-0.0448`, tool_calls: `10` -> `10`)
- `task_034`: `0.5525` -> `0.5103` (delta: `-0.0422`, tool_calls: `11` -> `11`)
- `task_022`: `0.5624` -> `0.5283` (delta: `-0.0341`, tool_calls: `9` -> `9`)
- `task_059`: `0.5493` -> `0.5153` (delta: `-0.034`, tool_calls: `8` -> `8`)
- `task_061`: `0.5613` -> `0.5333` (delta: `-0.028`, tool_calls: `8` -> `8`)
- `task_044`: `0.571` -> `0.5447` (delta: `-0.0263`, tool_calls: `8` -> `8`)
- `task_036`: `0.5581` -> `0.5333` (delta: `-0.0248`, tool_calls: `8` -> `8`)
- `task_046`: `0.5459` -> `0.5225` (delta: `-0.0234`, tool_calls: `8` -> `8`)
- `task_058`: `0.5615` -> `0.5414` (delta: `-0.0201`, tool_calls: `10` -> `10`)

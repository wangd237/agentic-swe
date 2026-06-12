# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev39_001`
- improved_batch_run_id: `batch_run_realissuev40_001`
- created_at: `2026-06-12T02:26:16.753551+00:00`

## Task Set

- baseline_task_count: `36`
- improved_task_count: `37`
- common_task_count: `36`
- added_task_ids: `['task_075']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5453`
- improved_average_duration_sec_all: `0.5717`
- baseline_average_duration_sec_common: `0.5453`
- improved_average_duration_sec_common: `0.5722`
- common_average_delta_sec: `0.0269`
- baseline_total_duration_sec_common: `19.632`
- improved_total_duration_sec_common: `20.6006`

## Top Regressions

- `task_059`: `0.5153` -> `0.5833` (delta: `0.068`, tool_calls: `8` -> `8`)
- `task_036`: `0.5333` -> `0.6004` (delta: `0.0671`, tool_calls: `8` -> `8`)
- `task_010`: `0.5354` -> `0.6` (delta: `0.0646`, tool_calls: `9` -> `9`)
- `task_046`: `0.5225` -> `0.5863` (delta: `0.0638`, tool_calls: `8` -> `8`)
- `task_034`: `0.5103` -> `0.5712` (delta: `0.0609`, tool_calls: `11` -> `11`)
- `task_042`: `0.5327` -> `0.5893` (delta: `0.0566`, tool_calls: `10` -> `10`)
- `task_071`: `0.5171` -> `0.5678` (delta: `0.0507`, tool_calls: `8` -> `8`)
- `task_022`: `0.5283` -> `0.5749` (delta: `0.0466`, tool_calls: `9` -> `9`)
- `task_073`: `0.5488` -> `0.5929` (delta: `0.0441`, tool_calls: `8` -> `8`)
- `task_069`: `0.5389` -> `0.5815` (delta: `0.0426`, tool_calls: `8` -> `8`)

## Top Improvements

- `task_065`: `0.5625` -> `0.534` (delta: `-0.0285`, tool_calls: `8` -> `8`)
- `task_028`: `0.5899` -> `0.5618` (delta: `-0.0281`, tool_calls: `8` -> `8`)
- `task_013`: `0.5742` -> `0.5573` (delta: `-0.0169`, tool_calls: `9` -> `9`)
- `task_016`: `0.5574` -> `0.5549` (delta: `-0.0025`, tool_calls: `12` -> `12`)
- `task_019`: `0.567` -> `0.5654` (delta: `-0.0016`, tool_calls: `10` -> `10`)
- `task_052`: `0.559` -> `0.5586` (delta: `-0.0004`, tool_calls: `12` -> `12`)

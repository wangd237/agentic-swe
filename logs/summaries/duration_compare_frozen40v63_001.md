# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen40v62r2_001`
- improved_batch_run_id: `batch_run_frozen40v63r2_001`
- created_at: `2026-06-12T12:33:32.865812+00:00`

## Task Set

- baseline_task_count: `40`
- improved_task_count: `40`
- common_task_count: `40`
- added_task_ids: `[]`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5554`
- improved_average_duration_sec_all: `0.5594`
- baseline_average_duration_sec_common: `0.5554`
- improved_average_duration_sec_common: `0.5594`
- common_average_delta_sec: `0.004`
- baseline_total_duration_sec_common: `22.2172`
- improved_total_duration_sec_common: `22.3745`

## Top Regressions

- `task_058`: `0.5432` -> `0.6101` (delta: `0.0669`, tool_calls: `10` -> `10`)
- `task_026`: `0.53` -> `0.5868` (delta: `0.0568`, tool_calls: `9` -> `9`)
- `task_024`: `0.5213` -> `0.5672` (delta: `0.0459`, tool_calls: `9` -> `9`)
- `task_050`: `0.5144` -> `0.5552` (delta: `0.0408`, tool_calls: `8` -> `8`)
- `task_008`: `0.5506` -> `0.586` (delta: `0.0354`, tool_calls: `9` -> `9`)
- `task_010`: `0.5614` -> `0.5959` (delta: `0.0345`, tool_calls: `9` -> `9`)
- `task_046`: `0.5481` -> `0.5796` (delta: `0.0315`, tool_calls: `8` -> `8`)
- `task_042`: `0.5605` -> `0.5845` (delta: `0.024`, tool_calls: `10` -> `10`)
- `task_019`: `0.5444` -> `0.567` (delta: `0.0226`, tool_calls: `10` -> `10`)
- `task_040`: `0.5626` -> `0.584` (delta: `0.0214`, tool_calls: `12` -> `12`)

## Top Improvements

- `task_063`: `0.6333` -> `0.5152` (delta: `-0.1181`, tool_calls: `8` -> `8`)
- `task_079`: `0.59` -> `0.5319` (delta: `-0.0581`, tool_calls: `9` -> `9`)
- `task_028`: `0.6006` -> `0.5594` (delta: `-0.0412`, tool_calls: `8` -> `8`)
- `task_081`: `0.5551` -> `0.5178` (delta: `-0.0373`, tool_calls: `9` -> `9`)
- `task_006`: `0.5691` -> `0.5434` (delta: `-0.0257`, tool_calls: `9` -> `9`)
- `task_056`: `0.7895` -> `0.7646` (delta: `-0.0249`, tool_calls: `10` -> `10`)
- `task_048`: `0.5517` -> `0.5277` (delta: `-0.024`, tool_calls: `10` -> `10`)
- `task_069`: `0.5262` -> `0.5102` (delta: `-0.016`, tool_calls: `8` -> `8`)
- `task_032`: `0.5624` -> `0.5473` (delta: `-0.0151`, tool_calls: `9` -> `9`)
- `task_038`: `0.5852` -> `0.5776` (delta: `-0.0076`, tool_calls: `8` -> `8`)

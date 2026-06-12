# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev42_001`
- improved_batch_run_id: `batch_run_realissuev43_001`
- created_at: `2026-06-12T03:24:29.429868+00:00`

## Task Set

- baseline_task_count: `39`
- improved_task_count: `40`
- common_task_count: `39`
- added_task_ids: `['task_081']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5157`
- improved_average_duration_sec_all: `0.5241`
- baseline_average_duration_sec_common: `0.5157`
- improved_average_duration_sec_common: `0.5252`
- common_average_delta_sec: `0.0095`
- baseline_total_duration_sec_common: `20.1113`
- improved_total_duration_sec_common: `20.4832`

## Top Regressions

- `task_056`: `0.6864` -> `0.7661` (delta: `0.0797`, tool_calls: `10` -> `10`)
- `task_013`: `0.5107` -> `0.5766` (delta: `0.0659`, tool_calls: `9` -> `9`)
- `task_008`: `0.5028` -> `0.5589` (delta: `0.0561`, tool_calls: `9` -> `9`)
- `task_038`: `0.5001` -> `0.5429` (delta: `0.0428`, tool_calls: `8` -> `8`)
- `task_016`: `0.4977` -> `0.5338` (delta: `0.0361`, tool_calls: `12` -> `12`)
- `task_048`: `0.5191` -> `0.552` (delta: `0.0329`, tool_calls: `10` -> `10`)
- `task_073`: `0.4828` -> `0.5108` (delta: `0.028`, tool_calls: `8` -> `8`)
- `task_075`: `0.4851` -> `0.513` (delta: `0.0279`, tool_calls: `10` -> `10`)
- `task_032`: `0.5088` -> `0.536` (delta: `0.0272`, tool_calls: `9` -> `9`)
- `task_026`: `0.5084` -> `0.5331` (delta: `0.0247`, tool_calls: `9` -> `9`)

## Top Improvements

- `task_077`: `0.5145` -> `0.4689` (delta: `-0.0456`, tool_calls: `9` -> `9`)
- `task_006`: `0.5571` -> `0.5257` (delta: `-0.0314`, tool_calls: `9` -> `9`)
- `task_057`: `0.5217` -> `0.4963` (delta: `-0.0254`, tool_calls: `10` -> `10`)
- `task_034`: `0.5249` -> `0.5068` (delta: `-0.0181`, tool_calls: `11` -> `11`)
- `task_022`: `0.5289` -> `0.5131` (delta: `-0.0158`, tool_calls: `9` -> `9`)
- `task_010`: `0.5316` -> `0.5197` (delta: `-0.0119`, tool_calls: `9` -> `9`)
- `task_071`: `0.5003` -> `0.4901` (delta: `-0.0102`, tool_calls: `8` -> `8`)
- `task_050`: `0.5018` -> `0.4918` (delta: `-0.01`, tool_calls: `8` -> `8`)
- `task_028`: `0.5257` -> `0.5172` (delta: `-0.0085`, tool_calls: `8` -> `8`)
- `task_067`: `0.5012` -> `0.493` (delta: `-0.0082`, tool_calls: `10` -> `10`)

# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev34_001`
- improved_batch_run_id: `batch_run_realissuev35_001`
- created_at: `2026-06-11T16:08:07.153462+00:00`

## Task Set

- baseline_task_count: `31`
- improved_task_count: `32`
- common_task_count: `31`
- added_task_ids: `['task_065']`
- removed_task_ids: `[]`

## Aggregate

- baseline_average_duration_sec_all: `0.5391`
- improved_average_duration_sec_all: `0.535`
- baseline_average_duration_sec_common: `0.5391`
- improved_average_duration_sec_common: `0.5361`
- common_average_delta_sec: `-0.003`
- baseline_total_duration_sec_common: `16.713`
- improved_total_duration_sec_common: `16.6196`

## Top Regressions

- `task_017`: `0.5353` -> `0.5854` (delta: `0.0501`, tool_calls: `10` -> `10`)
- `task_060`: `0.5027` -> `0.5333` (delta: `0.0306`, tool_calls: `8` -> `8`)
- `task_010`: `0.5154` -> `0.5423` (delta: `0.0269`, tool_calls: `9` -> `9`)
- `task_008`: `0.5199` -> `0.5425` (delta: `0.0226`, tool_calls: `9` -> `9`)
- `task_019`: `0.5538` -> `0.5742` (delta: `0.0204`, tool_calls: `10` -> `10`)
- `task_026`: `0.5305` -> `0.5488` (delta: `0.0183`, tool_calls: `9` -> `9`)
- `task_034`: `0.5354` -> `0.5456` (delta: `0.0102`, tool_calls: `11` -> `11`)
- `task_040`: `0.5268` -> `0.5368` (delta: `0.01`, tool_calls: `12` -> `12`)
- `task_048`: `0.5292` -> `0.5382` (delta: `0.009`, tool_calls: `10` -> `10`)
- `task_059`: `0.5099` -> `0.5173` (delta: `0.0074`, tool_calls: `8` -> `8`)

## Top Improvements

- `task_022`: `0.5574` -> `0.5108` (delta: `-0.0466`, tool_calls: `9` -> `9`)
- `task_024`: `0.5701` -> `0.5293` (delta: `-0.0408`, tool_calls: `9` -> `9`)
- `task_032`: `0.5488` -> `0.5116` (delta: `-0.0372`, tool_calls: `9` -> `9`)
- `task_057`: `0.5407` -> `0.5046` (delta: `-0.0361`, tool_calls: `10` -> `10`)
- `task_061`: `0.5181` -> `0.4859` (delta: `-0.0322`, tool_calls: `8` -> `8`)
- `task_052`: `0.5415` -> `0.5136` (delta: `-0.0279`, tool_calls: `12` -> `12`)
- `task_050`: `0.5212` -> `0.4969` (delta: `-0.0243`, tool_calls: `8` -> `8`)
- `task_036`: `0.5612` -> `0.5386` (delta: `-0.0226`, tool_calls: `8` -> `8`)
- `task_038`: `0.5513` -> `0.5392` (delta: `-0.0121`, tool_calls: `8` -> `8`)
- `task_030`: `0.5348` -> `0.525` (delta: `-0.0098`, tool_calls: `8` -> `8`)

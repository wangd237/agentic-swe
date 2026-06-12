# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen40v62r2_001`
- improved_batch_run_id: `batch_run_frozen40v63r2_001`
- common_task_count: `40`
- baseline_average_duration_sec: `0.5554`
- improved_average_duration_sec: `0.5594`
- average_duration_delta_sec: `0.004`

## Top Task Regressions

- `task_058`: `0.5432` -> `0.6101` (delta: `0.0669`, dominant_tool: `run_tests`, dominant_delta: `0.0416`)
- `task_026`: `0.53` -> `0.5868` (delta: `0.0568`, dominant_tool: `run_tests`, dominant_delta: `0.0591`)
- `task_024`: `0.5213` -> `0.5672` (delta: `0.0459`, dominant_tool: `run_tests`, dominant_delta: `0.0358`)
- `task_050`: `0.5144` -> `0.5552` (delta: `0.0408`, dominant_tool: `run_tests`, dominant_delta: `0.0471`)
- `task_008`: `0.5506` -> `0.586` (delta: `0.0354`, dominant_tool: `run_tests`, dominant_delta: `0.019`)
- `task_010`: `0.5614` -> `0.5959` (delta: `0.0345`, dominant_tool: `run_tests`, dominant_delta: `0.0244`)
- `task_046`: `0.5481` -> `0.5796` (delta: `0.0315`, dominant_tool: `run_tests`, dominant_delta: `0.0405`)
- `task_042`: `0.5605` -> `0.5845` (delta: `0.024`, dominant_tool: `run_tests`, dominant_delta: `0.0179`)
- `task_019`: `0.5444` -> `0.567` (delta: `0.0226`, dominant_tool: `run_tests`, dominant_delta: `0.0218`)
- `task_040`: `0.5626` -> `0.584` (delta: `0.0214`, dominant_tool: `search_code`, dominant_delta: `0.0101`)

## Top Tool Regressions

- `unattributed_overhead`: baseline avg `0.0099` -> improved avg `0.0114` (total delta: `0.0603`)
- `search_code`: baseline avg `0.0072` -> improved avg `0.0083` (total delta: `0.0448`)
- `copy_workspace`: baseline avg `0.0023` -> improved avg `0.003` (total delta: `0.0246`)
- `run_tests`: baseline avg `0.5303` -> improved avg `0.5308` (total delta: `0.019`)
- `read_file`: baseline avg `0.0011` -> improved avg `0.0013` (total delta: `0.0093`)
- `list_files`: baseline avg `0.0006` -> improved avg `0.0007` (total delta: `0.0037`)

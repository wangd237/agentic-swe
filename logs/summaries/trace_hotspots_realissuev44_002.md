# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev43_001`
- improved_batch_run_id: `batch_run_realissuev44_002`
- common_task_count: `40`
- baseline_average_duration_sec: `0.5241`
- improved_average_duration_sec: `0.5187`
- average_duration_delta_sec: `-0.0054`

## Top Task Regressions

- `task_046`: `0.5133` -> `0.5538` (delta: `0.0405`, dominant_tool: `run_tests`, dominant_delta: `0.0291`)
- `task_034`: `0.5068` -> `0.5258` (delta: `0.019`, dominant_tool: `copy_workspace`, dominant_delta: `0.016`)
- `task_028`: `0.5172` -> `0.5356` (delta: `0.0184`, dominant_tool: `run_tests`, dominant_delta: `0.0156`)
- `task_024`: `0.5171` -> `0.535` (delta: `0.0179`, dominant_tool: `run_tests`, dominant_delta: `0.0202`)
- `task_016`: `0.5338` -> `0.5485` (delta: `0.0147`, dominant_tool: `run_tests`, dominant_delta: `0.0148`)
- `task_026`: `0.5331` -> `0.5473` (delta: `0.0142`, dominant_tool: `run_tests`, dominant_delta: `0.011`)
- `task_065`: `0.5164` -> `0.526` (delta: `0.0096`, dominant_tool: `search_code`, dominant_delta: `0.0122`)
- `task_044`: `0.523` -> `0.5321` (delta: `0.0091`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0099`)
- `task_050`: `0.4918` -> `0.5009` (delta: `0.0091`, dominant_tool: `run_tests`, dominant_delta: `0.0077`)
- `task_057`: `0.4963` -> `0.5043` (delta: `0.008`, dominant_tool: `run_tests`, dominant_delta: `0.008`)

## Top Tool Regressions

- `unattributed_overhead`: baseline avg `0.011` -> improved avg `0.0128` (total delta: `0.0724`)
- `copy_workspace`: baseline avg `0.0029` -> improved avg `0.0029` (total delta: `0.0012`)
- `read_file`: baseline avg `0.0012` -> improved avg `0.0012` (total delta: `0.0003`)

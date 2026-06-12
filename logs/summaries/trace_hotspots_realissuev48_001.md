# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev47_001`
- improved_batch_run_id: `batch_run_realissuev48_001`
- common_task_count: `44`
- baseline_average_duration_sec: `0.5234`
- improved_average_duration_sec: `0.5241`
- average_duration_delta_sec: `0.0007`

## Top Task Regressions

- `task_038`: `0.5233` -> `0.5564` (delta: `0.0331`, dominant_tool: `run_tests`, dominant_delta: `0.0286`)
- `task_060`: `0.485` -> `0.5153` (delta: `0.0303`, dominant_tool: `run_tests`, dominant_delta: `0.0226`)
- `task_067`: `0.5044` -> `0.5346` (delta: `0.0302`, dominant_tool: `run_tests`, dominant_delta: `0.0273`)
- `task_046`: `0.5336` -> `0.5609` (delta: `0.0273`, dominant_tool: `run_tests`, dominant_delta: `0.0405`)
- `task_079`: `0.5011` -> `0.5277` (delta: `0.0266`, dominant_tool: `search_code`, dominant_delta: `0.0152`)
- `task_056`: `0.7477` -> `0.7733` (delta: `0.0256`, dominant_tool: `run_tests`, dominant_delta: `0.0271`)
- `task_061`: `0.4976` -> `0.5232` (delta: `0.0256`, dominant_tool: `run_tests`, dominant_delta: `0.026`)
- `task_069`: `0.4869` -> `0.5108` (delta: `0.0239`, dominant_tool: `run_tests`, dominant_delta: `0.025`)
- `task_087`: `0.4644` -> `0.4878` (delta: `0.0234`, dominant_tool: `run_tests`, dominant_delta: `0.0144`)
- `task_063`: `0.4817` -> `0.5013` (delta: `0.0196`, dominant_tool: `run_tests`, dominant_delta: `0.0151`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.4926` -> improved avg `0.4941` (total delta: `0.0694`)
- `copy_workspace`: baseline avg `0.0026` -> improved avg `0.0027` (total delta: `0.0073`)
- `search_code`: baseline avg `0.0089` -> improved avg `0.0089` (total delta: `0.0012`)

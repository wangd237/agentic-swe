# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v39_001`
- improved_batch_run_id: `batch_run_frozen20v40_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5443`
- improved_average_duration_sec: `0.5682`
- average_duration_delta_sec: `0.0239`

## Top Task Regressions

- `task_013`: `0.5363` -> `0.605` (delta: `0.0687`, dominant_tool: `run_tests`, dominant_delta: `0.0438`)
- `task_036`: `0.5208` -> `0.5795` (delta: `0.0587`, dominant_tool: `run_tests`, dominant_delta: `0.0758`)
- `task_032`: `0.5438` -> `0.5962` (delta: `0.0524`, dominant_tool: `run_tests`, dominant_delta: `0.0523`)
- `task_046`: `0.5466` -> `0.5913` (delta: `0.0447`, dominant_tool: `run_tests`, dominant_delta: `0.0465`)
- `task_042`: `0.5397` -> `0.582` (delta: `0.0423`, dominant_tool: `run_tests`, dominant_delta: `0.0494`)
- `task_030`: `0.5231` -> `0.5645` (delta: `0.0414`, dominant_tool: `run_tests`, dominant_delta: `0.0489`)
- `task_028`: `0.5173` -> `0.5568` (delta: `0.0395`, dominant_tool: `run_tests`, dominant_delta: `0.0365`)
- `task_022`: `0.5332` -> `0.5652` (delta: `0.032`, dominant_tool: `run_tests`, dominant_delta: `0.0349`)
- `task_006`: `0.5211` -> `0.5489` (delta: `0.0278`, dominant_tool: `run_tests`, dominant_delta: `0.029`)
- `task_038`: `0.5439` -> `0.5618` (delta: `0.0179`, dominant_tool: `run_tests`, dominant_delta: `0.0215`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.5163` -> improved avg `0.5442` (total delta: `0.558`)
- `search_code`: baseline avg `0.0071` -> improved avg `0.0074` (total delta: `0.0052`)

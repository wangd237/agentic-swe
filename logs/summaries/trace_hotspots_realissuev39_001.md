# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev38_001`
- improved_batch_run_id: `batch_run_realissuev39_001`
- common_task_count: `35`
- baseline_average_duration_sec: `0.553`
- improved_average_duration_sec: `0.5452`
- average_duration_delta_sec: `-0.0078`

## Top Task Regressions

- `task_016`: `0.5249` -> `0.5574` (delta: `0.0325`, dominant_tool: `run_tests`, dominant_delta: `0.0169`)
- `task_065`: `0.5378` -> `0.5625` (delta: `0.0247`, dominant_tool: `run_tests`, dominant_delta: `0.0269`)
- `task_054`: `0.5082` -> `0.5267` (delta: `0.0185`, dominant_tool: `run_tests`, dominant_delta: `0.026`)
- `task_024`: `0.5426` -> `0.5607` (delta: `0.0181`, dominant_tool: `run_tests`, dominant_delta: `0.0307`)
- `task_038`: `0.5283` -> `0.5463` (delta: `0.018`, dominant_tool: `run_tests`, dominant_delta: `0.0157`)
- `task_048`: `0.5295` -> `0.546` (delta: `0.0165`, dominant_tool: `run_tests`, dominant_delta: `0.019`)
- `task_067`: `0.5223` -> `0.5366` (delta: `0.0143`, dominant_tool: `search_code`, dominant_delta: `0.0092`)
- `task_019`: `0.5536` -> `0.567` (delta: `0.0134`, dominant_tool: `run_tests`, dominant_delta: `0.0354`)
- `task_017`: `0.5311` -> `0.5423` (delta: `0.0112`, dominant_tool: `run_tests`, dominant_delta: `0.0176`)
- `task_030`: `0.5365` -> `0.5474` (delta: `0.0109`, dominant_tool: `run_tests`, dominant_delta: `0.0079`)

## Top Tool Regressions

- `unattributed_overhead`: baseline avg `0.0116` -> improved avg `0.0129` (total delta: `0.0456`)

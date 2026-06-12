# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev39_001`
- improved_batch_run_id: `batch_run_realissuev40_001`
- common_task_count: `36`
- baseline_average_duration_sec: `0.5453`
- improved_average_duration_sec: `0.5722`
- average_duration_delta_sec: `0.0269`

## Top Task Regressions

- `task_059`: `0.5153` -> `0.5833` (delta: `0.068`, dominant_tool: `run_tests`, dominant_delta: `0.0565`)
- `task_036`: `0.5333` -> `0.6004` (delta: `0.0671`, dominant_tool: `run_tests`, dominant_delta: `0.0476`)
- `task_010`: `0.5354` -> `0.6` (delta: `0.0646`, dominant_tool: `run_tests`, dominant_delta: `0.0413`)
- `task_046`: `0.5225` -> `0.5863` (delta: `0.0638`, dominant_tool: `run_tests`, dominant_delta: `0.0809`)
- `task_034`: `0.5103` -> `0.5712` (delta: `0.0609`, dominant_tool: `run_tests`, dominant_delta: `0.049`)
- `task_042`: `0.5327` -> `0.5893` (delta: `0.0566`, dominant_tool: `search_code`, dominant_delta: `0.0355`)
- `task_071`: `0.5171` -> `0.5678` (delta: `0.0507`, dominant_tool: `run_tests`, dominant_delta: `0.0545`)
- `task_022`: `0.5283` -> `0.5749` (delta: `0.0466`, dominant_tool: `run_tests`, dominant_delta: `0.0465`)
- `task_073`: `0.5488` -> `0.5929` (delta: `0.0441`, dominant_tool: `run_tests`, dominant_delta: `0.0554`)
- `task_069`: `0.5389` -> `0.5815` (delta: `0.0426`, dominant_tool: `run_tests`, dominant_delta: `0.0266`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.515` -> improved avg `0.5426` (total delta: `0.9935`)
- `search_code`: baseline avg `0.0097` -> improved avg `0.0127` (total delta: `0.1087`)

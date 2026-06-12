# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v35_001`
- improved_batch_run_id: `batch_run_frozen20v36_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5402`
- improved_average_duration_sec: `0.5386`
- average_duration_delta_sec: `-0.0016`

## Top Task Regressions

- `task_040`: `0.5331` -> `0.5747` (delta: `0.0416`, dominant_tool: `run_tests`, dominant_delta: `0.0422`)
- `task_024`: `0.531` -> `0.5571` (delta: `0.0261`, dominant_tool: `run_tests`, dominant_delta: `0.0231`)
- `task_006`: `0.505` -> `0.53` (delta: `0.025`, dominant_tool: `run_tests`, dominant_delta: `0.0187`)
- `task_032`: `0.5186` -> `0.5422` (delta: `0.0236`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0202`)
- `task_030`: `0.5255` -> `0.5402` (delta: `0.0147`, dominant_tool: `run_tests`, dominant_delta: `0.0066`)
- `task_036`: `0.5381` -> `0.5517` (delta: `0.0136`, dominant_tool: `run_tests`, dominant_delta: `0.0073`)
- `task_022`: `0.5084` -> `0.5138` (delta: `0.0054`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0086`)
- `task_034`: `0.5423` -> `0.5453` (delta: `0.003`, dominant_tool: `run_tests`, dominant_delta: `0.011`)

## Top Tool Regressions

- `unattributed_overhead`: baseline avg `0.0111` -> improved avg `0.0119` (total delta: `0.0162`)
- `list_files`: baseline avg `0.0006` -> improved avg `0.0008` (total delta: `0.0038`)
- `copy_workspace`: baseline avg `0.0022` -> improved avg `0.0023` (total delta: `0.002`)

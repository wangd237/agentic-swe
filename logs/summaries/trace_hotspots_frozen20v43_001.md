# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v42_001`
- improved_batch_run_id: `batch_run_frozen20v43_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5186`
- improved_average_duration_sec: `0.5291`
- average_duration_delta_sec: `0.0105`

## Top Task Regressions

- `task_013`: `0.5152` -> `0.576` (delta: `0.0608`, dominant_tool: `run_tests`, dominant_delta: `0.0739`)
- `task_008`: `0.5031` -> `0.559` (delta: `0.0559`, dominant_tool: `run_tests`, dominant_delta: `0.0597`)
- `task_038`: `0.4983` -> `0.5411` (delta: `0.0428`, dominant_tool: `run_tests`, dominant_delta: `0.0441`)
- `task_016`: `0.4982` -> `0.5344` (delta: `0.0362`, dominant_tool: `run_tests`, dominant_delta: `0.0406`)
- `task_026`: `0.5087` -> `0.5344` (delta: `0.0257`, dominant_tool: `run_tests`, dominant_delta: `0.019`)
- `task_036`: `0.5135` -> `0.5342` (delta: `0.0207`, dominant_tool: `run_tests`, dominant_delta: `0.0292`)
- `task_032`: `0.5049` -> `0.5242` (delta: `0.0193`, dominant_tool: `run_tests`, dominant_delta: `0.0223`)
- `task_017`: `0.519` -> `0.5291` (delta: `0.0101`, dominant_tool: `run_tests`, dominant_delta: `0.0144`)
- `task_044`: `0.5115` -> `0.5207` (delta: `0.0092`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.008`)
- `task_040`: `0.5211` -> `0.5293` (delta: `0.0082`, dominant_tool: `run_tests`, dominant_delta: `0.0154`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.4866` -> improved avg `0.501` (total delta: `0.2873`)
- `show_diff`: baseline avg `0.0026` -> improved avg `0.0029` (total delta: `0.0058`)
- `read_file`: baseline avg `0.0011` -> improved avg `0.0013` (total delta: `0.0049`)
- `copy_workspace`: baseline avg `0.0023` -> improved avg `0.0025` (total delta: `0.0041`)

# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev46_001`
- improved_batch_run_id: `batch_run_realissuev47_001`
- common_task_count: `43`
- baseline_average_duration_sec: `0.5243`
- improved_average_duration_sec: `0.5245`
- average_duration_delta_sec: `0.0002`

## Top Task Regressions

- `task_044`: `0.5153` -> `0.5476` (delta: `0.0323`, dominant_tool: `run_tests`, dominant_delta: `0.0219`)
- `task_052`: `0.5025` -> `0.5345` (delta: `0.032`, dominant_tool: `run_tests`, dominant_delta: `0.0317`)
- `task_010`: `0.5094` -> `0.5368` (delta: `0.0274`, dominant_tool: `run_tests`, dominant_delta: `0.0173`)
- `task_067`: `0.478` -> `0.5044` (delta: `0.0264`, dominant_tool: `run_tests`, dominant_delta: `0.0169`)
- `task_008`: `0.5223` -> `0.5481` (delta: `0.0258`, dominant_tool: `run_tests`, dominant_delta: `0.0127`)
- `task_065`: `0.4957` -> `0.5209` (delta: `0.0252`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0104`)
- `task_026`: `0.5359` -> `0.5578` (delta: `0.0219`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0105`)
- `task_040`: `0.5139` -> `0.5323` (delta: `0.0184`, dominant_tool: `search_code`, dominant_delta: `0.0112`)
- `task_058`: `0.5109` -> `0.5281` (delta: `0.0172`, dominant_tool: `run_tests`, dominant_delta: `0.0114`)
- `task_034`: `0.5114` -> `0.5283` (delta: `0.0169`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0085`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.4922` -> improved avg `0.4936` (total delta: `0.0628`)
- `unattributed_overhead`: baseline avg `0.0122` -> improved avg `0.0128` (total delta: `0.0269`)
- `show_diff`: baseline avg `0.0028` -> improved avg `0.003` (total delta: `0.0045`)
- `copy_workspace`: baseline avg `0.0025` -> improved avg `0.0026` (total delta: `0.0042`)
- `list_files`: baseline avg `0.0007` -> improved avg `0.0008` (total delta: `0.0037`)

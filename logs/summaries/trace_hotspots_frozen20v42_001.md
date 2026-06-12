# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v41_001`
- improved_batch_run_id: `batch_run_frozen20v42_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5185`
- improved_average_duration_sec: `0.5186`
- average_duration_delta_sec: `0.0001`

## Top Task Regressions

- `task_006`: `0.5031` -> `0.5579` (delta: `0.0548`, dominant_tool: `run_tests`, dominant_delta: `0.0536`)
- `task_030`: `0.4824` -> `0.5158` (delta: `0.0334`, dominant_tool: `run_tests`, dominant_delta: `0.0299`)
- `task_010`: `0.4945` -> `0.5274` (delta: `0.0329`, dominant_tool: `run_tests`, dominant_delta: `0.0129`)
- `task_036`: `0.4882` -> `0.5135` (delta: `0.0253`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.011`)
- `task_034`: `0.5092` -> `0.5251` (delta: `0.0159`, dominant_tool: `search_code`, dominant_delta: `0.0087`)
- `task_017`: `0.5107` -> `0.519` (delta: `0.0083`, dominant_tool: `search_code`, dominant_delta: `0.0132`)
- `task_042`: `0.5187` -> `0.5259` (delta: `0.0072`, dominant_tool: `search_code`, dominant_delta: `0.006`)
- `task_013`: `0.5085` -> `0.5152` (delta: `0.0067`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0098`)
- `task_019`: `0.5319` -> `0.5371` (delta: `0.0052`, dominant_tool: `search_code`, dominant_delta: `0.0065`)
- `task_022`: `0.5231` -> `0.5246` (delta: `0.0015`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0104`)

## Top Tool Regressions

- `search_code`: baseline avg `0.0078` -> improved avg `0.0117` (total delta: `0.0781`)
- `unattributed_overhead`: baseline avg `0.0114` -> improved avg `0.0125` (total delta: `0.022`)
- `show_diff`: baseline avg `0.0022` -> improved avg `0.0026` (total delta: `0.0064`)
- `copy_workspace`: baseline avg `0.0021` -> improved avg `0.0023` (total delta: `0.0028`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0013` (total delta: `0.0016`)
- `list_files`: baseline avg `0.0006` -> improved avg `0.0007` (total delta: `0.0011`)

# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev50_001`
- improved_batch_run_id: `batch_run_realissuev51_002`
- common_task_count: `47`
- baseline_average_duration_sec: `0.5583`
- improved_average_duration_sec: `0.6995`
- average_duration_delta_sec: `0.1412`

## Top Task Regressions

- `task_038`: `0.581` -> `1.0054` (delta: `0.4244`, dominant_tool: `run_tests`, dominant_delta: `0.4299`)
- `task_040`: `0.5931` -> `0.8578` (delta: `0.2647`, dominant_tool: `run_tests`, dominant_delta: `0.2268`)
- `task_006`: `0.599` -> `0.8391` (delta: `0.2401`, dominant_tool: `run_tests`, dominant_delta: `0.2359`)
- `task_042`: `0.5322` -> `0.7492` (delta: `0.217`, dominant_tool: `run_tests`, dominant_delta: `0.189`)
- `task_044`: `0.5582` -> `0.7729` (delta: `0.2147`, dominant_tool: `run_tests`, dominant_delta: `0.2184`)
- `task_065`: `0.5368` -> `0.7177` (delta: `0.1809`, dominant_tool: `run_tests`, dominant_delta: `0.1811`)
- `task_083`: `0.5001` -> `0.6658` (delta: `0.1657`, dominant_tool: `run_tests`, dominant_delta: `0.1444`)
- `task_067`: `0.53` -> `0.6915` (delta: `0.1615`, dominant_tool: `run_tests`, dominant_delta: `0.1475`)
- `task_073`: `0.561` -> `0.7206` (delta: `0.1596`, dominant_tool: `run_tests`, dominant_delta: `0.1309`)
- `task_063`: `0.5434` -> `0.7021` (delta: `0.1587`, dominant_tool: `run_tests`, dominant_delta: `0.1534`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.525` -> improved avg `0.6537` (total delta: `6.0457`)
- `unattributed_overhead`: baseline avg `0.0115` -> improved avg `0.0163` (total delta: `0.2235`)
- `search_code`: baseline avg `0.013` -> improved avg `0.0159` (total delta: `0.1391`)
- `show_diff`: baseline avg `0.0027` -> improved avg `0.0044` (total delta: `0.0783`)
- `copy_workspace`: baseline avg `0.0026` -> improved avg `0.0041` (total delta: `0.0703`)
- `rule_based_patch`: baseline avg `0.0016` -> improved avg `0.0022` (total delta: `0.0323`)
- `read_file`: baseline avg `0.0013` -> improved avg `0.0019` (total delta: `0.0296`)
- `list_files`: baseline avg `0.0007` -> improved avg `0.0011` (total delta: `0.0177`)

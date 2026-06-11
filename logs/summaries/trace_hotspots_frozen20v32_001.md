# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v31_001`
- improved_batch_run_id: `batch_run_frozen20v32_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.6122`
- improved_average_duration_sec: `0.6774`
- average_duration_delta_sec: `0.0652`

## Top Task Regressions

- `task_040`: `0.6213` -> `0.9456` (delta: `0.3243`, dominant_tool: `run_tests`, dominant_delta: `0.3177`)
- `task_038`: `0.5846` -> `0.754` (delta: `0.1694`, dominant_tool: `run_tests`, dominant_delta: `0.1538`)
- `task_036`: `0.6084` -> `0.77` (delta: `0.1616`, dominant_tool: `run_tests`, dominant_delta: `0.1437`)
- `task_034`: `0.6275` -> `0.7888` (delta: `0.1613`, dominant_tool: `run_tests`, dominant_delta: `0.1535`)
- `task_032`: `0.5983` -> `0.7213` (delta: `0.123`, dominant_tool: `run_tests`, dominant_delta: `0.0863`)
- `task_026`: `0.5993` -> `0.7076` (delta: `0.1083`, dominant_tool: `run_tests`, dominant_delta: `0.0928`)
- `task_024`: `0.6149` -> `0.7012` (delta: `0.0863`, dominant_tool: `run_tests`, dominant_delta: `0.0922`)
- `task_008`: `0.6284` -> `0.7109` (delta: `0.0825`, dominant_tool: `run_tests`, dominant_delta: `0.0763`)
- `task_042`: `0.6392` -> `0.7014` (delta: `0.0622`, dominant_tool: `run_tests`, dominant_delta: `0.0409`)
- `task_022`: `0.5931` -> `0.6432` (delta: `0.0501`, dominant_tool: `run_tests`, dominant_delta: `0.0447`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.574` -> improved avg `0.6275` (total delta: `1.0696`)
- `search_code`: baseline avg `0.0226` -> improved avg `0.0261` (total delta: `0.07`)
- `show_diff`: baseline avg `0.0094` -> improved avg `0.0121` (total delta: `0.054`)
- `list_files`: baseline avg `0.0031` -> improved avg `0.0054` (total delta: `0.0463`)
- `rule_based_patch`: baseline avg `0.0015` -> improved avg `0.0031` (total delta: `0.0328`)
- `read_file`: baseline avg `0.0008` -> improved avg `0.0015` (total delta: `0.0155`)
- `unattributed_overhead`: baseline avg `0.0009` -> improved avg `0.0017` (total delta: `0.0147`)

# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev45_001`
- improved_batch_run_id: `batch_run_realissuev46_001`
- common_task_count: `42`
- baseline_average_duration_sec: `0.5175`
- improved_average_duration_sec: `0.5252`
- average_duration_delta_sec: `0.0077`

## Top Task Regressions

- `task_019`: `0.4977` -> `0.5549` (delta: `0.0572`, dominant_tool: `run_tests`, dominant_delta: `0.0449`)
- `task_016`: `0.4983` -> `0.5503` (delta: `0.052`, dominant_tool: `run_tests`, dominant_delta: `0.0467`)
- `task_036`: `0.5245` -> `0.5682` (delta: `0.0437`, dominant_tool: `run_tests`, dominant_delta: `0.037`)
- `task_013`: `0.507` -> `0.5443` (delta: `0.0373`, dominant_tool: `run_tests`, dominant_delta: `0.045`)
- `task_032`: `0.5069` -> `0.5418` (delta: `0.0349`, dominant_tool: `run_tests`, dominant_delta: `0.0232`)
- `task_022`: `0.5201` -> `0.5541` (delta: `0.034`, dominant_tool: `run_tests`, dominant_delta: `0.0252`)
- `task_060`: `0.4913` -> `0.5225` (delta: `0.0312`, dominant_tool: `search_code`, dominant_delta: `0.0109`)
- `task_042`: `0.5239` -> `0.5534` (delta: `0.0295`, dominant_tool: `run_tests`, dominant_delta: `0.0349`)
- `task_079`: `0.4907` -> `0.5161` (delta: `0.0254`, dominant_tool: `run_tests`, dominant_delta: `0.0163`)
- `task_017`: `0.5045` -> `0.5285` (delta: `0.024`, dominant_tool: `run_tests`, dominant_delta: `0.0096`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.4888` -> improved avg `0.4931` (total delta: `0.1838`)
- `search_code`: baseline avg `0.0087` -> improved avg `0.0113` (total delta: `0.1067`)
- `unattributed_overhead`: baseline avg `0.0116` -> improved avg `0.012` (total delta: `0.0141`)
- `show_diff`: baseline avg `0.0027` -> improved avg `0.0028` (total delta: `0.0077`)
- `copy_workspace`: baseline avg `0.0024` -> improved avg `0.0025` (total delta: `0.0041`)
- `rule_based_patch`: baseline avg `0.0014` -> improved avg `0.0014` (total delta: `0.0016`)
- `read_file`: baseline avg `0.0013` -> improved avg `0.0013` (total delta: `0.0012`)
- `list_files`: baseline avg `0.0007` -> improved avg `0.0007` (total delta: `0.0002`)

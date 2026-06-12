# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev44_002`
- improved_batch_run_id: `batch_run_realissuev45_001`
- common_task_count: `41`
- baseline_average_duration_sec: `0.5173`
- improved_average_duration_sec: `0.5181`
- average_duration_delta_sec: `0.0008`

## Top Task Regressions

- `task_056`: `0.7427` -> `0.7867` (delta: `0.044`, dominant_tool: `run_tests`, dominant_delta: `0.0338`)
- `task_071`: `0.4782` -> `0.514` (delta: `0.0358`, dominant_tool: `run_tests`, dominant_delta: `0.0371`)
- `task_073`: `0.493` -> `0.5265` (delta: `0.0335`, dominant_tool: `search_code`, dominant_delta: `0.015`)
- `task_077`: `0.4767` -> `0.5093` (delta: `0.0326`, dominant_tool: `run_tests`, dominant_delta: `0.0182`)
- `task_030`: `0.4966` -> `0.5287` (delta: `0.0321`, dominant_tool: `run_tests`, dominant_delta: `0.0223`)
- `task_083`: `0.4614` -> `0.4821` (delta: `0.0207`, dominant_tool: `run_tests`, dominant_delta: `0.0118`)
- `task_048`: `0.5042` -> `0.523` (delta: `0.0188`, dominant_tool: `run_tests`, dominant_delta: `0.0175`)
- `task_058`: `0.5153` -> `0.534` (delta: `0.0187`, dominant_tool: `run_tests`, dominant_delta: `0.0239`)
- `task_006`: `0.4995` -> `0.515` (delta: `0.0155`, dominant_tool: `search_code`, dominant_delta: `0.0133`)
- `task_040`: `0.5248` -> `0.5402` (delta: `0.0154`, dominant_tool: `search_code`, dominant_delta: `0.0104`)

## Top Tool Regressions

- `search_code`: baseline avg `0.0075` -> improved avg `0.0088` (total delta: `0.0541`)
- `run_tests`: baseline avg `0.4882` -> improved avg `0.4893` (total delta: `0.0421`)
- `read_file`: baseline avg `0.0012` -> improved avg `0.0013` (total delta: `0.0042`)

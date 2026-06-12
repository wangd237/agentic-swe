# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev41_001`
- improved_batch_run_id: `batch_run_realissuev42_001`
- common_task_count: `38`
- baseline_average_duration_sec: `0.5173`
- improved_average_duration_sec: `0.5165`
- average_duration_delta_sec: `-0.0008`

## Top Task Regressions

- `task_006`: `0.4834` -> `0.5571` (delta: `0.0737`, dominant_tool: `run_tests`, dominant_delta: `0.0629`)
- `task_010`: `0.499` -> `0.5316` (delta: `0.0326`, dominant_tool: `run_tests`, dominant_delta: `0.0305`)
- `task_034`: `0.4965` -> `0.5249` (delta: `0.0284`, dominant_tool: `run_tests`, dominant_delta: `0.0164`)
- `task_042`: `0.4985` -> `0.5257` (delta: `0.0272`, dominant_tool: `run_tests`, dominant_delta: `0.0106`)
- `task_017`: `0.4986` -> `0.52` (delta: `0.0214`, dominant_tool: `search_code`, dominant_delta: `0.012`)
- `task_019`: `0.5179` -> `0.5376` (delta: `0.0197`, dominant_tool: `run_tests`, dominant_delta: `0.0122`)
- `task_054`: `0.4896` -> `0.5073` (delta: `0.0177`, dominant_tool: `search_code`, dominant_delta: `0.0139`)
- `task_065`: `0.4868` -> `0.5035` (delta: `0.0167`, dominant_tool: `run_tests`, dominant_delta: `0.0148`)
- `task_048`: `0.5037` -> `0.5191` (delta: `0.0154`, dominant_tool: `search_code`, dominant_delta: `0.0219`)
- `task_077`: `0.5011` -> `0.5145` (delta: `0.0134`, dominant_tool: `search_code`, dominant_delta: `0.0145`)

## Top Tool Regressions

- `search_code`: baseline avg `0.0103` -> improved avg `0.0133` (total delta: `0.1131`)
- `show_diff`: baseline avg `0.0024` -> improved avg `0.0026` (total delta: `0.0092`)
- `copy_workspace`: baseline avg `0.0022` -> improved avg `0.0023` (total delta: `0.0054`)
- `read_file`: baseline avg `0.0011` -> improved avg `0.0011` (total delta: `0.0013`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0012` (total delta: `0.001`)
- `list_files`: baseline avg `0.0006` -> improved avg `0.0006` (total delta: `0.0004`)

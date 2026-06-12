# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev48_001`
- improved_batch_run_id: `batch_run_realissuev49_001`
- common_task_count: `45`
- baseline_average_duration_sec: `0.5234`
- improved_average_duration_sec: `0.5882`
- average_duration_delta_sec: `0.0648`

## Top Task Regressions

- `task_087`: `0.4878` -> `0.6227` (delta: `0.1349`, dominant_tool: `run_tests`, dominant_delta: `0.1093`)
- `task_089`: `0.459` -> `0.5853` (delta: `0.1263`, dominant_tool: `run_tests`, dominant_delta: `0.0863`)
- `task_056`: `0.7733` -> `0.8884` (delta: `0.1151`, dominant_tool: `run_tests`, dominant_delta: `0.103`)
- `task_010`: `0.5148` -> `0.628` (delta: `0.1132`, dominant_tool: `run_tests`, dominant_delta: `0.1022`)
- `task_058`: `0.5043` -> `0.6137` (delta: `0.1094`, dominant_tool: `run_tests`, dominant_delta: `0.0935`)
- `task_022`: `0.5316` -> `0.6399` (delta: `0.1083`, dominant_tool: `run_tests`, dominant_delta: `0.1047`)
- `task_052`: `0.5007` -> `0.6082` (delta: `0.1075`, dominant_tool: `run_tests`, dominant_delta: `0.0898`)
- `task_050`: `0.5008` -> `0.6023` (delta: `0.1015`, dominant_tool: `run_tests`, dominant_delta: `0.0897`)
- `task_006`: `0.523` -> `0.6236` (delta: `0.1006`, dominant_tool: `run_tests`, dominant_delta: `0.0896`)
- `task_042`: `0.5276` -> `0.627` (delta: `0.0994`, dominant_tool: `run_tests`, dominant_delta: `0.0766`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.4936` -> improved avg `0.5502` (total delta: `2.5483`)
- `search_code`: baseline avg `0.0088` -> improved avg `0.0167` (total delta: `0.3547`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0013` (total delta: `0.0056`)
- `read_file`: baseline avg `0.0012` -> improved avg `0.0013` (total delta: `0.0044`)
- `show_diff`: baseline avg `0.0028` -> improved avg `0.0029` (total delta: `0.003`)
- `unattributed_overhead`: baseline avg `0.0123` -> improved avg `0.0124` (total delta: `0.0027`)

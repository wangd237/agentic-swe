# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v34_001`
- improved_batch_run_id: `batch_run_frozen20v35_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5368`
- improved_average_duration_sec: `0.5402`
- average_duration_delta_sec: `0.0034`

## Top Task Regressions

- `task_017`: `0.4802` -> `0.5856` (delta: `0.1054`, dominant_tool: `run_tests`, dominant_delta: `0.0772`)
- `task_008`: `0.5112` -> `0.5423` (delta: `0.0311`, dominant_tool: `run_tests`, dominant_delta: `0.017`)
- `task_013`: `0.5143` -> `0.5417` (delta: `0.0274`, dominant_tool: `run_tests`, dominant_delta: `0.0124`)
- `task_010`: `0.5156` -> `0.5425` (delta: `0.0269`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0107`)
- `task_019`: `0.5538` -> `0.5741` (delta: `0.0203`, dominant_tool: `run_tests`, dominant_delta: `0.016`)
- `task_026`: `0.531` -> `0.5453` (delta: `0.0143`, dominant_tool: `run_tests`, dominant_delta: `0.025`)
- `task_016`: `0.5222` -> `0.5354` (delta: `0.0132`, dominant_tool: `run_tests`, dominant_delta: `0.0112`)
- `task_040`: `0.5275` -> `0.5331` (delta: `0.0056`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.01`)
- `task_042`: `0.5492` -> `0.5521` (delta: `0.0029`, dominant_tool: `run_tests`, dominant_delta: `0.0264`)
- `task_034`: `0.5402` -> `0.5423` (delta: `0.0021`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0083`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.5076` -> improved avg `0.5112` (total delta: `0.0731`)
- `read_file`: baseline avg `0.0011` -> improved avg `0.0012` (total delta: `0.0027`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0012` (total delta: `0.0006`)
- `list_files`: baseline avg `0.0006` -> improved avg `0.0006` (total delta: `0.0001`)

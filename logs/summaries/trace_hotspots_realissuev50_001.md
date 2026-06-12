# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev49_001`
- improved_batch_run_id: `batch_run_realissuev50_001`
- common_task_count: `46`
- baseline_average_duration_sec: `0.5869`
- improved_average_duration_sec: `0.5592`
- average_duration_delta_sec: `-0.0277`

## Top Task Regressions

- `task_091`: `0.5228` -> `0.5552` (delta: `0.0324`, dominant_tool: `search_code`, dominant_delta: `0.0227`)
- `task_028`: `0.5543` -> `0.5853` (delta: `0.031`, dominant_tool: `run_tests`, dominant_delta: `0.0367`)
- `task_093`: `0.5288` -> `0.5587` (delta: `0.0299`, dominant_tool: `run_tests`, dominant_delta: `0.0181`)
- `task_077`: `0.5189` -> `0.548` (delta: `0.0291`, dominant_tool: `run_tests`, dominant_delta: `0.031`)
- `task_034`: `0.5492` -> `0.578` (delta: `0.0288`, dominant_tool: `run_tests`, dominant_delta: `0.0162`)
- `task_032`: `0.5639` -> `0.5767` (delta: `0.0128`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0101`)
- `task_073`: `0.5511` -> `0.561` (delta: `0.0099`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0093`)
- `task_024`: `0.5852` -> `0.5945` (delta: `0.0093`, dominant_tool: `run_tests`, dominant_delta: `0.018`)

## Top Tool Regressions

- `rule_based_patch`: baseline avg `0.0013` -> improved avg `0.0016` (total delta: `0.0102`)
- `read_file`: baseline avg `0.0013` -> improved avg `0.0013` (total delta: `0.0001`)

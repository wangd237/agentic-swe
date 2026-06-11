# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev32_001`
- improved_batch_run_id: `batch_run_realissuev33_001`
- common_task_count: `30`
- baseline_average_duration_sec: `0.6778`
- improved_average_duration_sec: `0.5423`
- average_duration_delta_sec: `-0.1355`

## Top Task Regressions

- 当前没有检测到任务级时延回升

## Top Tool Regressions

- `unattributed_overhead`: baseline avg `0.0018` -> improved avg `0.0117` (total delta: `0.2978`)
- `copy_workspace`: baseline avg `0.0` -> improved avg `0.0022` (total delta: `0.0654`)

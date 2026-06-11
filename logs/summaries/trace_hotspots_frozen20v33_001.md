# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v32_001`
- improved_batch_run_id: `batch_run_frozen20v33_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.6774`
- improved_average_duration_sec: `0.5379`
- average_duration_delta_sec: `-0.1395`

## Top Task Regressions

- 当前没有检测到任务级时延回升

## Top Tool Regressions

- `unattributed_overhead`: baseline avg `0.0017` -> improved avg `0.0117` (total delta: `0.2008`)
- `copy_workspace`: baseline avg `0.0` -> improved avg `0.0021` (total delta: `0.0418`)

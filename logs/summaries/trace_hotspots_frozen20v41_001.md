# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_frozen20v40_001`
- improved_batch_run_id: `batch_run_frozen20v41_001`
- common_task_count: `20`
- baseline_average_duration_sec: `0.5682`
- improved_average_duration_sec: `0.5185`
- average_duration_delta_sec: `-0.0497`

## Top Task Regressions

- 当前没有检测到任务级时延回升

## Top Tool Regressions

- `read_file`: baseline avg `0.0007` -> improved avg `0.0015` (total delta: `0.0171`)
- `show_diff`: baseline avg `0.0016` -> improved avg `0.0022` (total delta: `0.0132`)
- `copy_workspace`: baseline avg `0.0017` -> improved avg `0.0021` (total delta: `0.0082`)
- `search_code`: baseline avg `0.0074` -> improved avg `0.0078` (total delta: `0.0081`)
- `rule_based_patch`: baseline avg `0.0009` -> improved avg `0.0012` (total delta: `0.0054`)
- `list_files`: baseline avg `0.0004` -> improved avg `0.0006` (total delta: `0.0042`)
- `unattributed_overhead`: baseline avg `0.0113` -> improved avg `0.0114` (total delta: `0.0019`)

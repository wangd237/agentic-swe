# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev33_001`
- improved_batch_run_id: `batch_run_realissuev34_001`
- common_task_count: `30`
- baseline_average_duration_sec: `0.5423`
- improved_average_duration_sec: `0.5409`
- average_duration_delta_sec: `-0.0014`

## Top Task Regressions

- `task_024`: `0.5107` -> `0.5701` (delta: `0.0594`, dominant_tool: `run_tests`, dominant_delta: `0.0529`)
- `task_028`: `0.5137` -> `0.567` (delta: `0.0533`, dominant_tool: `run_tests`, dominant_delta: `0.0323`)
- `task_022`: `0.5136` -> `0.5574` (delta: `0.0438`, dominant_tool: `run_tests`, dominant_delta: `0.0261`)
- `task_019`: `0.5118` -> `0.5538` (delta: `0.042`, dominant_tool: `run_tests`, dominant_delta: `0.0368`)
- `task_046`: `0.5207` -> `0.5493` (delta: `0.0286`, dominant_tool: `run_tests`, dominant_delta: `0.0205`)
- `task_032`: `0.5206` -> `0.5488` (delta: `0.0282`, dominant_tool: `run_tests`, dominant_delta: `0.0329`)
- `task_038`: `0.5241` -> `0.5513` (delta: `0.0272`, dominant_tool: `search_code`, dominant_delta: `0.0215`)
- `task_036`: `0.5351` -> `0.5612` (delta: `0.0261`, dominant_tool: `run_tests`, dominant_delta: `0.0285`)
- `task_017`: `0.5094` -> `0.5353` (delta: `0.0259`, dominant_tool: `run_tests`, dominant_delta: `0.0159`)
- `task_016`: `0.5138` -> `0.5375` (delta: `0.0237`, dominant_tool: `run_tests`, dominant_delta: `0.0221`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.5028` -> improved avg `0.5049` (total delta: `0.0637`)
- `unattributed_overhead`: baseline avg `0.0117` -> improved avg `0.0128` (total delta: `0.0335`)
- `copy_workspace`: baseline avg `0.0022` -> improved avg `0.0023` (total delta: `0.0039`)
- `read_file`: baseline avg `0.0011` -> improved avg `0.0012` (total delta: `0.0022`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0013` (total delta: `0.0019`)

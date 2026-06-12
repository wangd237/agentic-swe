# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev36_001`
- improved_batch_run_id: `batch_run_realissuev37_001`
- common_task_count: `33`
- baseline_average_duration_sec: `0.5312`
- improved_average_duration_sec: `0.6046`
- average_duration_delta_sec: `0.0734`

## Top Task Regressions

- `task_056`: `0.6763` -> `0.8408` (delta: `0.1645`, dominant_tool: `run_tests`, dominant_delta: `0.1498`)
- `task_022`: `0.5243` -> `0.6456` (delta: `0.1213`, dominant_tool: `run_tests`, dominant_delta: `0.1188`)
- `task_017`: `0.5314` -> `0.6378` (delta: `0.1064`, dominant_tool: `run_tests`, dominant_delta: `0.0778`)
- `task_050`: `0.4919` -> `0.5899` (delta: `0.098`, dominant_tool: `run_tests`, dominant_delta: `0.1105`)
- `task_059`: `0.4914` -> `0.5891` (delta: `0.0977`, dominant_tool: `run_tests`, dominant_delta: `0.0868`)
- `task_006`: `0.5154` -> `0.6043` (delta: `0.0889`, dominant_tool: `run_tests`, dominant_delta: `0.0862`)
- `task_067`: `0.4954` -> `0.584` (delta: `0.0886`, dominant_tool: `run_tests`, dominant_delta: `0.0805`)
- `task_052`: `0.5096` -> `0.594` (delta: `0.0844`, dominant_tool: `run_tests`, dominant_delta: `0.0829`)
- `task_016`: `0.5238` -> `0.6076` (delta: `0.0838`, dominant_tool: `run_tests`, dominant_delta: `0.076`)
- `task_028`: `0.5235` -> `0.6071` (delta: `0.0836`, dominant_tool: `run_tests`, dominant_delta: `0.0827`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.5015` -> improved avg `0.5759` (total delta: `2.4539`)
- `show_diff`: baseline avg `0.0025` -> improved avg `0.0028` (total delta: `0.0104`)
- `copy_workspace`: baseline avg `0.0024` -> improved avg `0.0025` (total delta: `0.0059`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0013` (total delta: `0.0033`)

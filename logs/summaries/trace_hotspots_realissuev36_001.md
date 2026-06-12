# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev35_001`
- improved_batch_run_id: `batch_run_realissuev36_001`
- common_task_count: `32`
- baseline_average_duration_sec: `0.535`
- improved_average_duration_sec: `0.5323`
- average_duration_delta_sec: `-0.0027`

## Top Task Regressions

- `task_040`: `0.5368` -> `0.5738` (delta: `0.037`, dominant_tool: `run_tests`, dominant_delta: `0.0386`)
- `task_032`: `0.5116` -> `0.5412` (delta: `0.0296`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.019`)
- `task_024`: `0.5293` -> `0.5549` (delta: `0.0256`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0086`)
- `task_063`: `0.4911` -> `0.5096` (delta: `0.0185`, dominant_tool: `search_code`, dominant_delta: `0.0113`)
- `task_065`: `0.5007` -> `0.517` (delta: `0.0163`, dominant_tool: `search_code`, dominant_delta: `0.0162`)
- `task_030`: `0.525` -> `0.5406` (delta: `0.0156`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0108`)
- `task_036`: `0.5386` -> `0.5526` (delta: `0.014`, dominant_tool: `run_tests`, dominant_delta: `0.0107`)
- `task_022`: `0.5108` -> `0.5243` (delta: `0.0135`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0085`)
- `task_056`: `0.6692` -> `0.6763` (delta: `0.0071`, dominant_tool: `run_tests`, dominant_delta: `0.0149`)
- `task_057`: `0.5046` -> `0.5112` (delta: `0.0066`, dominant_tool: `search_code`, dominant_delta: `0.0047`)

## Top Tool Regressions

- `unattributed_overhead`: baseline avg `0.0118` -> improved avg `0.0127` (total delta: `0.0294`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0013` (total delta: `0.0011`)
- `copy_workspace`: baseline avg `0.0023` -> improved avg `0.0024` (total delta: `0.001`)

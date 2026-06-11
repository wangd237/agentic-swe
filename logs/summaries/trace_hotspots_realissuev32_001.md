# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev31_001`
- improved_batch_run_id: `batch_run_realissuev32_001`
- common_task_count: `29`
- baseline_average_duration_sec: `0.6115`
- improved_average_duration_sec: `0.6767`
- average_duration_delta_sec: `0.0652`

## Top Task Regressions

- `task_040`: `0.6213` -> `0.9463` (delta: `0.325`, dominant_tool: `run_tests`, dominant_delta: `0.3265`)
- `task_034`: `0.6275` -> `0.8038` (delta: `0.1763`, dominant_tool: `run_tests`, dominant_delta: `0.1668`)
- `task_036`: `0.6087` -> `0.7715` (delta: `0.1628`, dominant_tool: `run_tests`, dominant_delta: `0.1557`)
- `task_038`: `0.5843` -> `0.747` (delta: `0.1627`, dominant_tool: `run_tests`, dominant_delta: `0.1516`)
- `task_050`: `0.5778` -> `0.7151` (delta: `0.1373`, dominant_tool: `run_tests`, dominant_delta: `0.1351`)
- `task_048`: `0.5912` -> `0.7246` (delta: `0.1334`, dominant_tool: `run_tests`, dominant_delta: `0.1209`)
- `task_032`: `0.5983` -> `0.7152` (delta: `0.1169`, dominant_tool: `run_tests`, dominant_delta: `0.0867`)
- `task_026`: `0.5993` -> `0.7075` (delta: `0.1082`, dominant_tool: `run_tests`, dominant_delta: `0.0773`)
- `task_052`: `0.6041` -> `0.7033` (delta: `0.0992`, dominant_tool: `run_tests`, dominant_delta: `0.1051`)
- `task_024`: `0.6149` -> `0.7012` (delta: `0.0863`, dominant_tool: `run_tests`, dominant_delta: `0.0906`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.5687` -> improved avg `0.621` (total delta: `1.5149`)
- `search_code`: baseline avg `0.0255` -> improved avg `0.0294` (total delta: `0.1131`)
- `list_files`: baseline avg `0.0031` -> improved avg `0.0061` (total delta: `0.0877`)
- `rule_based_patch`: baseline avg `0.0014` -> improved avg `0.0038` (total delta: `0.0694`)
- `show_diff`: baseline avg `0.0108` -> improved avg `0.0125` (total delta: `0.0496`)
- `read_file`: baseline avg `0.0008` -> improved avg `0.002` (total delta: `0.0348`)
- `unattributed_overhead`: baseline avg `0.0011` -> improved avg `0.0018` (total delta: `0.0203`)

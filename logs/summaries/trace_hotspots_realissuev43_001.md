# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev42_001`
- improved_batch_run_id: `batch_run_realissuev43_001`
- common_task_count: `39`
- baseline_average_duration_sec: `0.5157`
- improved_average_duration_sec: `0.5252`
- average_duration_delta_sec: `0.0095`

## Top Task Regressions

- `task_056`: `0.6864` -> `0.7661` (delta: `0.0797`, dominant_tool: `run_tests`, dominant_delta: `0.1022`)
- `task_013`: `0.5107` -> `0.5766` (delta: `0.0659`, dominant_tool: `run_tests`, dominant_delta: `0.0753`)
- `task_008`: `0.5028` -> `0.5589` (delta: `0.0561`, dominant_tool: `run_tests`, dominant_delta: `0.0543`)
- `task_038`: `0.5001` -> `0.5429` (delta: `0.0428`, dominant_tool: `run_tests`, dominant_delta: `0.0401`)
- `task_016`: `0.4977` -> `0.5338` (delta: `0.0361`, dominant_tool: `run_tests`, dominant_delta: `0.0408`)
- `task_048`: `0.5191` -> `0.552` (delta: `0.0329`, dominant_tool: `run_tests`, dominant_delta: `0.0383`)
- `task_073`: `0.4828` -> `0.5108` (delta: `0.028`, dominant_tool: `run_tests`, dominant_delta: `0.0221`)
- `task_075`: `0.4851` -> `0.513` (delta: `0.0279`, dominant_tool: `run_tests`, dominant_delta: `0.0145`)
- `task_032`: `0.5088` -> `0.536` (delta: `0.0272`, dominant_tool: `run_tests`, dominant_delta: `0.0385`)
- `task_026`: `0.5084` -> `0.5331` (delta: `0.0247`, dominant_tool: `run_tests`, dominant_delta: `0.019`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.4827` -> improved avg `0.4962` (total delta: `0.5265`)
- `copy_workspace`: baseline avg `0.0023` -> improved avg `0.0029` (total delta: `0.0227`)
- `show_diff`: baseline avg `0.0026` -> improved avg `0.0029` (total delta: `0.0118`)
- `rule_based_patch`: baseline avg `0.0012` -> improved avg `0.0014` (total delta: `0.0073`)
- `read_file`: baseline avg `0.0011` -> improved avg `0.0012` (total delta: `0.0036`)
- `list_files`: baseline avg `0.0006` -> improved avg `0.0007` (total delta: `0.0024`)

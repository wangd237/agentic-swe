# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `batch_run_realissuev34_001`
- improved_batch_run_id: `batch_run_realissuev35_001`
- common_task_count: `31`
- baseline_average_duration_sec: `0.5391`
- improved_average_duration_sec: `0.5361`
- average_duration_delta_sec: `-0.003`

## Top Task Regressions

- `task_017`: `0.5353` -> `0.5854` (delta: `0.0501`, dominant_tool: `search_code`, dominant_delta: `0.0306`)
- `task_060`: `0.5027` -> `0.5333` (delta: `0.0306`, dominant_tool: `run_tests`, dominant_delta: `0.0284`)
- `task_010`: `0.5154` -> `0.5423` (delta: `0.0269`, dominant_tool: `run_tests`, dominant_delta: `0.0198`)
- `task_008`: `0.5199` -> `0.5425` (delta: `0.0226`, dominant_tool: `run_tests`, dominant_delta: `0.0233`)
- `task_019`: `0.5538` -> `0.5742` (delta: `0.0204`, dominant_tool: `run_tests`, dominant_delta: `0.0115`)
- `task_026`: `0.5305` -> `0.5488` (delta: `0.0183`, dominant_tool: `run_tests`, dominant_delta: `0.0249`)
- `task_034`: `0.5354` -> `0.5456` (delta: `0.0102`, dominant_tool: `search_code`, dominant_delta: `0.0054`)
- `task_040`: `0.5268` -> `0.5368` (delta: `0.01`, dominant_tool: `unattributed_overhead`, dominant_delta: `0.0094`)
- `task_048`: `0.5292` -> `0.5382` (delta: `0.009`, dominant_tool: `run_tests`, dominant_delta: `0.0221`)
- `task_059`: `0.5099` -> `0.5173` (delta: `0.0074`, dominant_tool: `search_code`, dominant_delta: `0.0166`)

## Top Tool Regressions

- `run_tests`: baseline avg `0.5035` -> improved avg `0.5057` (total delta: `0.0674`)
- `show_diff`: baseline avg `0.0022` -> improved avg `0.0026` (total delta: `0.0117`)
- `read_file`: baseline avg `0.0012` -> improved avg `0.0013` (total delta: `0.0046`)
- `list_files`: baseline avg `0.0006` -> improved avg `0.0008` (total delta: `0.0034`)
- `copy_workspace`: baseline avg `0.0023` -> improved avg `0.0024` (total delta: `0.0016`)

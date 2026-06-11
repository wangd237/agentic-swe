# Run Tests Mode Cohort Analysis

## Cohort

- cohort_label: `run_tests_hotspots_v32`
- task_count: `4`
- task_ids: `['task_034', 'task_036', 'task_038', 'task_040']`

## Aggregate

- average_persistent_run_tests_delta_sec: `-0.0068`
- average_fresh_run_tests_delta_sec: `-0.0091`
- average_persistent_command_delta_sec: `-0.0068`
- average_fresh_command_delta_sec: `-0.009`
- average_persistent_combined_delta_sec: `-0.0059`
- average_fresh_combined_delta_sec: `-0.0068`
- average_fresh_copy_duration_sec: `0.0023`
- fresh_slower_than_source_task_count: `2`
- persistent_slower_than_source_task_count: `2`

## Task Snapshots

- `task_034`: persistent run_tests delta=`0.0005`, fresh run_tests delta=`0.0064`, fresh copy avg=`0.0023`, fresh combined delta=`0.0087`
- `task_040`: persistent run_tests delta=`0.0001`, fresh run_tests delta=`0.0057`, fresh copy avg=`0.0024`, fresh combined delta=`0.0081`
- `task_036`: persistent run_tests delta=`-0.0094`, fresh run_tests delta=`-0.0222`, fresh copy avg=`0.0023`, fresh combined delta=`-0.0199`
- `task_038`: persistent run_tests delta=`-0.0184`, fresh run_tests delta=`-0.0261`, fresh copy avg=`0.0022`, fresh combined delta=`-0.0239`

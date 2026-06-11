# Pytest Phase Cohort Analysis

## Cohort

- cohort_label: `run_tests_hotspots_v32`
- task_count: `4`
- task_ids: `['task_034', 'task_036', 'task_038', 'task_040']`

## Aggregate

- average_pytest_startup_over_python_sec: `0.1322`
- average_collect_over_pytest_startup_sec: `0.0797`
- average_full_over_collect_sec: `0.0159`
- average_collect_first_minus_repeated_sec: `0.0132`
- average_full_first_minus_repeated_sec: `-0.0065`
- full_slower_than_collect_task_count: `4`
- collect_slower_than_startup_task_count: `4`

## Task Snapshots

- `task_038`: startup over python=`0.1254`, collect over startup=`0.077`, full over collect=`0.0254`, full first minus repeated=`-0.0146`
- `task_040`: startup over python=`0.1286`, collect over startup=`0.0793`, full over collect=`0.02`, full first minus repeated=`-0.0142`
- `task_036`: startup over python=`0.1374`, collect over startup=`0.0854`, full over collect=`0.0091`, full first minus repeated=`0.0044`
- `task_034`: startup over python=`0.1375`, collect over startup=`0.077`, full over collect=`0.009`, full first minus repeated=`-0.0014`

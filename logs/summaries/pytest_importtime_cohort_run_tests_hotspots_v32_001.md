# Pytest Importtime Cohort Analysis

## Cohort

- cohort_label: `run_tests_hotspots_v32`
- task_count: `4`
- task_ids: `['task_034', 'task_036', 'task_038', 'task_040']`

## Aggregate

- average_collect_wall_delta_sec: `0.0815`
- average_collect_import_self_delta_us: `21773`
- average_collect_unique_module_delta: `37`
- average_collect_wall_first_minus_repeated_sec: `0.0119`
- average_collect_import_self_first_minus_repeated_us: `-165.5`
- collect_slower_than_version_task_count: `4`

## Top Extra Modules

- `_ctypes`: task_count=`4`
- `_elementtree`: task_count=`4`
- `_pytest._argcomplete`: task_count=`4`
- `_pytest.faulthandler`: task_count=`4`
- `_pytest.helpconfig`: task_count=`4`
- `_pytest.junitxml`: task_count=`4`
- `_pytest.pastebin`: task_count=`4`
- `_pytest.setuponly`: task_count=`4`
- `_pytest.setupplan`: task_count=`4`
- `_pytest.skipping`: task_count=`4`

## Task Snapshots

- `task_038`: collect wall delta=`0.0876`, collect import self delta(us)=`23550`, collect module delta=`37`
- `task_034`: collect wall delta=`0.0861`, collect import self delta(us)=`22719`, collect module delta=`37`
- `task_036`: collect wall delta=`0.0785`, collect import self delta(us)=`20715`, collect module delta=`37`
- `task_040`: collect wall delta=`0.074`, collect import self delta(us)=`20109`, collect module delta=`37`

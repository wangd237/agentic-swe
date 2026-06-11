# Pytest Importtime Cohort Analysis

## Cohort

- cohort_label: `run_tests_hotspots_v32`
- task_count: `4`
- task_ids: `['task_034', 'task_036', 'task_038', 'task_040']`

## Aggregate

- average_collect_wall_delta_sec: `0.0697`
- average_collect_import_self_delta_us: `20898`
- average_collect_unique_module_delta: `37`
- average_collect_wall_first_minus_repeated_sec: `0.0113`
- average_collect_import_self_first_minus_repeated_us: `1449.75`
- collect_slower_than_version_task_count: `4`

## Top Extra Modules

- `_ctypes`: task_count=`4`
- `pyexpat`: task_count=`4`
- `xml.etree.ElementTree`: task_count=`4`
- `_pytest.skipping`: task_count=`4`
- `ctypes.wintypes`: task_count=`4`
- `ctypes`: task_count=`4`
- `pdb`: task_count=`4`
- `_pytest.terminalprogress`: task_count=`4`
- `_elementtree`: task_count=`1`
- `ctypes._endian`: task_count=`1`
- `code`: task_count=`1`
- `_pytest.threadexception`: task_count=`1`

## Task Snapshots

- `task_040`: collect wall delta=`0.068`, collect import self delta(us)=`30108`, collect module delta=`37`
- `task_034`: collect wall delta=`0.0709`, collect import self delta(us)=`18859`, collect module delta=`37`
- `task_036`: collect wall delta=`0.0707`, collect import self delta(us)=`18363`, collect module delta=`37`
- `task_038`: collect wall delta=`0.0693`, collect import self delta(us)=`16262`, collect module delta=`37`

# Pytest Importtime Benchmark

## Task

- task_id: `task_036`
- test_command: `python -m pytest tests/test_hostname.py -q`
- repetitions: `3`

## Phases

- `pytest_version_importtime`: wall avg=`0.1691`, import self avg(us)=`124328`, module avg=`253`
- `pytest_collect_importtime`: wall avg=`0.2476`, import self avg(us)=`145043`, module avg=`290`

## Derived Metrics

- average_collect_wall_delta_sec: `0.0785`
- average_collect_import_self_delta_us: `20715`
- average_collect_unique_module_delta: `37`
- collect_wall_first_minus_repeated_sec: `0.004`
- collect_import_self_first_minus_repeated_us: `-1578`

## Latest Collect Extra Modules

- `_ctypes`: self_us=`2087`, cumulative_us=`2087`
- `_elementtree`: self_us=`0`, cumulative_us=`0`
- `_pytest._argcomplete`: self_us=`0`, cumulative_us=`0`
- `_pytest.faulthandler`: self_us=`0`, cumulative_us=`0`
- `_pytest.helpconfig`: self_us=`0`, cumulative_us=`0`
- `_pytest.junitxml`: self_us=`0`, cumulative_us=`0`
- `_pytest.pastebin`: self_us=`0`, cumulative_us=`0`
- `_pytest.setuponly`: self_us=`0`, cumulative_us=`0`
- `_pytest.setupplan`: self_us=`0`, cumulative_us=`0`
- `_pytest.skipping`: self_us=`0`, cumulative_us=`0`

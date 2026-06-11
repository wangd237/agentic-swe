# Pytest Importtime Benchmark

## Task

- task_id: `task_034`
- test_command: `python -m pytest tests/test_utils.py -q`
- repetitions: `3`

## Phases

- `pytest_version_importtime`: wall avg=`0.173`, import self avg(us)=`123626`, module avg=`253`
- `pytest_collect_importtime`: wall avg=`0.2591`, import self avg(us)=`146345`, module avg=`290`

## Derived Metrics

- average_collect_wall_delta_sec: `0.0861`
- average_collect_import_self_delta_us: `22719`
- average_collect_unique_module_delta: `37`
- collect_wall_first_minus_repeated_sec: `0.0213`
- collect_import_self_first_minus_repeated_us: `137`

## Latest Collect Extra Modules

- `_ctypes`: self_us=`2514`, cumulative_us=`2514`
- `_elementtree`: self_us=`0`, cumulative_us=`0`
- `_pytest._argcomplete`: self_us=`0`, cumulative_us=`0`
- `_pytest.faulthandler`: self_us=`0`, cumulative_us=`0`
- `_pytest.helpconfig`: self_us=`0`, cumulative_us=`0`
- `_pytest.junitxml`: self_us=`0`, cumulative_us=`0`
- `_pytest.pastebin`: self_us=`0`, cumulative_us=`0`
- `_pytest.setuponly`: self_us=`0`, cumulative_us=`0`
- `_pytest.setupplan`: self_us=`0`, cumulative_us=`0`
- `_pytest.skipping`: self_us=`0`, cumulative_us=`0`

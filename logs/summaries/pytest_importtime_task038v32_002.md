# Pytest Importtime Benchmark

## Task

- task_id: `task_038`
- test_command: `python -m pytest tests/test_validator.py -q`
- repetitions: `3`

## Phases

- `pytest_version_importtime`: wall avg=`0.1864`, import self avg(us)=`136705`, module avg=`253`
- `pytest_collect_importtime`: wall avg=`0.2557`, import self avg(us)=`152967`, module avg=`290`

## Derived Metrics

- average_collect_wall_delta_sec: `0.0693`
- average_collect_import_self_delta_us: `16262`
- average_collect_unique_module_delta: `37`
- collect_wall_first_minus_repeated_sec: `0.0094`
- collect_import_self_first_minus_repeated_us: `3335`

## Latest Collect Extra Modules

- `_ctypes`: self_us=`2354`, cumulative_us=`2354`
- `xml.etree.ElementTree`: self_us=`1174`, cumulative_us=`3553`
- `pdb`: self_us=`1159`, cumulative_us=`2843`
- `_pytest.skipping`: self_us=`1095`, cumulative_us=`1095`
- `_pytest.terminalprogress`: self_us=`849`, cumulative_us=`849`
- `pyexpat`: self_us=`845`, cumulative_us=`845`
- `ctypes.wintypes`: self_us=`841`, cumulative_us=`841`
- `ctypes`: self_us=`836`, cumulative_us=`3668`
- `_pytest.stepwise`: self_us=`819`, cumulative_us=`819`
- `cmd`: self_us=`798`, cumulative_us=`798`

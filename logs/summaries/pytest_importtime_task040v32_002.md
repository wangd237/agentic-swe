# Pytest Importtime Benchmark

## Task

- task_id: `task_040`
- test_command: `python -m pytest tests/test_requirements.py -q`
- repetitions: `3`

## Phases

- `pytest_version_importtime`: wall avg=`0.1869`, import self avg(us)=`135234`, module avg=`253`
- `pytest_collect_importtime`: wall avg=`0.2549`, import self avg(us)=`165342`, module avg=`290`

## Derived Metrics

- average_collect_wall_delta_sec: `0.068`
- average_collect_import_self_delta_us: `30108`
- average_collect_unique_module_delta: `37`
- collect_wall_first_minus_repeated_sec: `0.0008`
- collect_import_self_first_minus_repeated_us: `-5594`

## Latest Collect Extra Modules

- `_ctypes`: self_us=`3269`, cumulative_us=`3269`
- `xml.etree.ElementTree`: self_us=`1382`, cumulative_us=`4301`
- `_pytest.skipping`: self_us=`1158`, cumulative_us=`1158`
- `pyexpat`: self_us=`977`, cumulative_us=`977`
- `pdb`: self_us=`976`, cumulative_us=`2521`
- `ctypes.wintypes`: self_us=`976`, cumulative_us=`976`
- `ctypes`: self_us=`882`, cumulative_us=`4840`
- `_pytest.terminalprogress`: self_us=`781`, cumulative_us=`781`
- `_pytest.unittest`: self_us=`705`, cumulative_us=`705`
- `_pytest._argcomplete`: self_us=`702`, cumulative_us=`702`

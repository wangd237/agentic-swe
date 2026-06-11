# Pytest Importtime Benchmark

## Task

- task_id: `task_034`
- test_command: `python -m pytest tests/test_utils.py -q`
- repetitions: `3`

## Phases

- `pytest_version_importtime`: wall avg=`0.1886`, import self avg(us)=`135921`, module avg=`253`
- `pytest_collect_importtime`: wall avg=`0.2595`, import self avg(us)=`154780`, module avg=`290`

## Derived Metrics

- average_collect_wall_delta_sec: `0.0709`
- average_collect_import_self_delta_us: `18859`
- average_collect_unique_module_delta: `37`
- collect_wall_first_minus_repeated_sec: `0.0306`
- collect_import_self_first_minus_repeated_us: `6712`

## Latest Collect Extra Modules

- `_ctypes`: self_us=`2235`, cumulative_us=`2235`
- `pyexpat`: self_us=`1314`, cumulative_us=`1314`
- `xml.etree.ElementTree`: self_us=`1249`, cumulative_us=`4499`
- `_pytest.skipping`: self_us=`1112`, cumulative_us=`1112`
- `ctypes.wintypes`: self_us=`1080`, cumulative_us=`1080`
- `ctypes`: self_us=`1026`, cumulative_us=`3973`
- `pdb`: self_us=`1016`, cumulative_us=`2326`
- `_elementtree`: self_us=`852`, cumulative_us=`2165`
- `_pytest.terminalprogress`: self_us=`786`, cumulative_us=`786`
- `ctypes._endian`: self_us=`712`, cumulative_us=`712`

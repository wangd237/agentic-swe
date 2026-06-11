# Pytest Importtime Benchmark

## Task

- task_id: `task_036`
- test_command: `python -m pytest tests/test_hostname.py -q`
- repetitions: `3`

## Phases

- `pytest_version_importtime`: wall avg=`0.1868`, import self avg(us)=`136657`, module avg=`253`
- `pytest_collect_importtime`: wall avg=`0.2575`, import self avg(us)=`155020`, module avg=`290`

## Derived Metrics

- average_collect_wall_delta_sec: `0.0707`
- average_collect_import_self_delta_us: `18363`
- average_collect_unique_module_delta: `37`
- collect_wall_first_minus_repeated_sec: `0.0045`
- collect_import_self_first_minus_repeated_us: `1346`

## Latest Collect Extra Modules

- `_ctypes`: self_us=`2698`, cumulative_us=`2698`
- `xml.etree.ElementTree`: self_us=`1312`, cumulative_us=`3743`
- `_pytest.skipping`: self_us=`1137`, cumulative_us=`1137`
- `ctypes`: self_us=`999`, cumulative_us=`4221`
- `pdb`: self_us=`984`, cumulative_us=`2964`
- `_pytest.terminalprogress`: self_us=`940`, cumulative_us=`940`
- `code`: self_us=`855`, cumulative_us=`1399`
- `_pytest.threadexception`: self_us=`835`, cumulative_us=`835`
- `ctypes.wintypes`: self_us=`811`, cumulative_us=`811`
- `pyexpat`: self_us=`799`, cumulative_us=`799`

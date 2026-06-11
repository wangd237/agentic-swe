# Pytest Phase Benchmark

## Task

- task_id: `task_036`
- test_command: `python -m pytest tests/test_hostname.py -q`
- repetitions: `3`

## Phases

- `python_noop`: command avg=`0.0452`, first=`0.0534`, repeated avg=`0.0411`
- `pytest_version`: command avg=`0.1826`, first=`0.1826`, repeated avg=`0.1825`
- `pytest_collect_only`: command avg=`0.268`, first=`0.2746`, repeated avg=`0.2647`
- `pytest_full_run`: command avg=`0.2771`, first=`0.28`, repeated avg=`0.2756`

## Derived Metrics

- average_pytest_startup_over_python_sec: `0.1374`
- average_collect_over_pytest_startup_sec: `0.0854`
- average_full_over_collect_sec: `0.0091`
- collect_first_minus_repeated_sec: `0.0099`
- full_first_minus_repeated_sec: `0.0044`

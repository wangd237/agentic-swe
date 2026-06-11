# Pytest Phase Benchmark

## Task

- task_id: `task_034`
- test_command: `python -m pytest tests/test_utils.py -q`
- repetitions: `3`

## Phases

- `python_noop`: command avg=`0.0465`, first=`0.056`, repeated avg=`0.0417`
- `pytest_version`: command avg=`0.184`, first=`0.1851`, repeated avg=`0.1835`
- `pytest_collect_only`: command avg=`0.261`, first=`0.2824`, repeated avg=`0.2502`
- `pytest_full_run`: command avg=`0.27`, first=`0.2691`, repeated avg=`0.2705`

## Derived Metrics

- average_pytest_startup_over_python_sec: `0.1375`
- average_collect_over_pytest_startup_sec: `0.077`
- average_full_over_collect_sec: `0.009`
- collect_first_minus_repeated_sec: `0.0322`
- full_first_minus_repeated_sec: `-0.0014`

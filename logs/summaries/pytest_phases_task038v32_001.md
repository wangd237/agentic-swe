# Pytest Phase Benchmark

## Task

- task_id: `task_038`
- test_command: `python -m pytest tests/test_validator.py -q`
- repetitions: `3`

## Phases

- `python_noop`: command avg=`0.038`, first=`0.0401`, repeated avg=`0.0369`
- `pytest_version`: command avg=`0.1634`, first=`0.1662`, repeated avg=`0.162`
- `pytest_collect_only`: command avg=`0.2404`, first=`0.238`, repeated avg=`0.2415`
- `pytest_full_run`: command avg=`0.2658`, first=`0.2561`, repeated avg=`0.2707`

## Derived Metrics

- average_pytest_startup_over_python_sec: `0.1254`
- average_collect_over_pytest_startup_sec: `0.077`
- average_full_over_collect_sec: `0.0254`
- collect_first_minus_repeated_sec: `-0.0035`
- full_first_minus_repeated_sec: `-0.0146`

# Pytest Phase Benchmark

## Task

- task_id: `task_040`
- test_command: `python -m pytest tests/test_requirements.py -q`
- repetitions: `3`

## Phases

- `python_noop`: command avg=`0.0381`, first=`0.0409`, repeated avg=`0.0367`
- `pytest_version`: command avg=`0.1667`, first=`0.1721`, repeated avg=`0.1639`
- `pytest_collect_only`: command avg=`0.246`, first=`0.2554`, repeated avg=`0.2414`
- `pytest_full_run`: command avg=`0.266`, first=`0.2565`, repeated avg=`0.2707`

## Derived Metrics

- average_pytest_startup_over_python_sec: `0.1286`
- average_collect_over_pytest_startup_sec: `0.0793`
- average_full_over_collect_sec: `0.02`
- collect_first_minus_repeated_sec: `0.014`
- full_first_minus_repeated_sec: `-0.0142`

# Run Tests Mode Benchmark

## Task

- task_id: `task_038`
- test_command: `python -m pytest tests/test_validator.py -q`
- repetitions: `3`

## Modes

- `source_repo`: run_tests avg=`0.2645`, copy avg=`0.0`, command avg=`0.2642`, combined avg=`0.2645`
- `persistent_workspace`: run_tests avg=`0.2461`, copy avg=`0.0009`, command avg=`0.2459`, combined avg=`0.247`
- `fresh_workspace`: run_tests avg=`0.2384`, copy avg=`0.0022`, command avg=`0.2382`, combined avg=`0.2406`

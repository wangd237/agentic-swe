# Run Tests Mode Benchmark

## Task

- task_id: `task_034`
- test_command: `python -m pytest tests/test_utils.py -q`
- repetitions: `3`

## Modes

- `source_repo`: run_tests avg=`0.2647`, copy avg=`0.0`, command avg=`0.2645`, combined avg=`0.2647`
- `persistent_workspace`: run_tests avg=`0.2652`, copy avg=`0.0009`, command avg=`0.265`, combined avg=`0.2661`
- `fresh_workspace`: run_tests avg=`0.2711`, copy avg=`0.0023`, command avg=`0.2709`, combined avg=`0.2734`

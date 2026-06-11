# Run Tests Mode Benchmark

## Task

- task_id: `task_040`
- test_command: `python -m pytest tests/test_requirements.py -q`
- repetitions: `3`

## Modes

- `source_repo`: run_tests avg=`0.2653`, copy avg=`0.0`, command avg=`0.2651`, combined avg=`0.2653`
- `persistent_workspace`: run_tests avg=`0.2654`, copy avg=`0.001`, command avg=`0.2651`, combined avg=`0.2663`
- `fresh_workspace`: run_tests avg=`0.271`, copy avg=`0.0024`, command avg=`0.2708`, combined avg=`0.2734`

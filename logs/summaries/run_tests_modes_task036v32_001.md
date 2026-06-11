# Run Tests Mode Benchmark

## Task

- task_id: `task_036`
- test_command: `python -m pytest tests/test_hostname.py -q`
- repetitions: `3`

## Modes

- `source_repo`: run_tests avg=`0.2596`, copy avg=`0.0`, command avg=`0.2594`, combined avg=`0.2596`
- `persistent_workspace`: run_tests avg=`0.2502`, copy avg=`0.0009`, command avg=`0.25`, combined avg=`0.2511`
- `fresh_workspace`: run_tests avg=`0.2374`, copy avg=`0.0023`, command avg=`0.2372`, combined avg=`0.2397`

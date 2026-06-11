# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_038`
- test_command: `python -m pytest tests/test_validator.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.2483`, import self avg(us)=`145711`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2532`, import self avg(us)=`149040`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `minimal_safe_plugins`: wall avg=`0.2176`, import self avg(us)=`141389`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.0307`, import delta(us)=`-4322`, module delta=`-22`, removed modules count=`22`
- `light_terminal_plugins`: wall delta=`0.0049`, import delta(us)=`3329`, module delta=`-15`, removed modules count=`15`

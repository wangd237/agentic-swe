# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_040`
- test_command: `python -m pytest tests/test_requirements.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.0386`, import self avg(us)=`8386`, module avg=`33`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.0427`, import self avg(us)=`8773`, module avg=`33`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `minimal_safe_plugins`: wall avg=`0.0419`, import self avg(us)=`9210`, module avg=`33`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`0.0033`, import delta(us)=`824`, module delta=`0`, removed modules count=`0`
- `light_terminal_plugins`: wall delta=`0.0041`, import delta(us)=`387`, module delta=`0`, removed modules count=`0`

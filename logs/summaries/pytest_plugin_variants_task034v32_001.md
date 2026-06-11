# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_034`
- test_command: `python -m pytest tests/test_utils.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.0382`, import self avg(us)=`8243`, module avg=`33`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.0415`, import self avg(us)=`8650`, module avg=`33`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `minimal_safe_plugins`: wall avg=`0.0435`, import self avg(us)=`9210`, module avg=`33`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `light_terminal_plugins`: wall delta=`0.0033`, import delta(us)=`407`, module delta=`0`, removed modules count=`0`
- `minimal_safe_plugins`: wall delta=`0.0053`, import delta(us)=`967`, module delta=`0`, removed modules count=`0`

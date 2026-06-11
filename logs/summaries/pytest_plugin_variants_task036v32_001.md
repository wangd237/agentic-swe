# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_036`
- test_command: `python -m pytest tests/test_hostname.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.0429`, import self avg(us)=`9085`, module avg=`33`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.0427`, import self avg(us)=`8496`, module avg=`33`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `minimal_safe_plugins`: wall avg=`0.0437`, import self avg(us)=`9482`, module avg=`33`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `light_terminal_plugins`: wall delta=`-0.0002`, import delta(us)=`-589`, module delta=`0`, removed modules count=`0`
- `minimal_safe_plugins`: wall delta=`0.0008`, import delta(us)=`397`, module delta=`0`, removed modules count=`0`

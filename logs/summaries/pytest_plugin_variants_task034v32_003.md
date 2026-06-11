# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_034`
- test_command: `python -m pytest tests/test_utils.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.26`, import self avg(us)=`149754`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2468`, import self avg(us)=`147350`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `debug_exception_plugins`: wall avg=`0.2322`, import self avg(us)=`153705`, module avg=`284`, flags=`-p no:debugging -p no:unraisableexception -p no:threadexception`
- `minimal_safe_plugins`: wall avg=`0.225`, import self avg(us)=`146204`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.035`, import delta(us)=`-3550`, module delta=`-22`, removed modules count=`22`
- `debug_exception_plugins`: wall delta=`-0.0278`, import delta(us)=`3951`, module delta=`-6`, removed modules count=`6`
- `light_terminal_plugins`: wall delta=`-0.0132`, import delta(us)=`-2404`, module delta=`-15`, removed modules count=`15`

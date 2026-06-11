# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_034`
- test_command: `python -m pytest tests/test_utils.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.2642`, import self avg(us)=`159765`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2437`, import self avg(us)=`146288`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `debugging_only`: wall avg=`0.2493`, import self avg(us)=`149315`, module avg=`286`, flags=`-p no:debugging`
- `unraisableexception_only`: wall avg=`0.2272`, import self avg(us)=`146600`, module avg=`289`, flags=`-p no:unraisableexception`
- `threadexception_only`: wall avg=`0.2636`, import self avg(us)=`153350`, module avg=`289`, flags=`-p no:threadexception`
- `debug_exception_plugins`: wall avg=`0.2294`, import self avg(us)=`148007`, module avg=`284`, flags=`-p no:debugging -p no:unraisableexception -p no:threadexception`
- `minimal_safe_plugins`: wall avg=`0.2082`, import self avg(us)=`135119`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.056`, import delta(us)=`-24646`, module delta=`-22`, removed modules count=`22`
- `unraisableexception_only`: wall delta=`-0.037`, import delta(us)=`-13165`, module delta=`-1`, removed modules count=`1`
- `debug_exception_plugins`: wall delta=`-0.0348`, import delta(us)=`-11758`, module delta=`-6`, removed modules count=`6`
- `light_terminal_plugins`: wall delta=`-0.0205`, import delta(us)=`-13477`, module delta=`-15`, removed modules count=`15`
- `debugging_only`: wall delta=`-0.0149`, import delta(us)=`-10450`, module delta=`-4`, removed modules count=`4`
- `threadexception_only`: wall delta=`-0.0006`, import delta(us)=`-6415`, module delta=`-1`, removed modules count=`1`

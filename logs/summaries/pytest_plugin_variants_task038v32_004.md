# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_038`
- test_command: `python -m pytest tests/test_validator.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.258`, import self avg(us)=`154273`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2395`, import self avg(us)=`147524`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `debugging_only`: wall avg=`0.2475`, import self avg(us)=`155878`, module avg=`286`, flags=`-p no:debugging`
- `unraisableexception_only`: wall avg=`0.2324`, import self avg(us)=`154948`, module avg=`289`, flags=`-p no:unraisableexception`
- `threadexception_only`: wall avg=`0.2628`, import self avg(us)=`160528`, module avg=`289`, flags=`-p no:threadexception`
- `debug_exception_plugins`: wall avg=`0.223`, import self avg(us)=`148947`, module avg=`284`, flags=`-p no:debugging -p no:unraisableexception -p no:threadexception`
- `minimal_safe_plugins`: wall avg=`0.2116`, import self avg(us)=`140565`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.0464`, import delta(us)=`-13708`, module delta=`-22`, removed modules count=`22`
- `debug_exception_plugins`: wall delta=`-0.035`, import delta(us)=`-5326`, module delta=`-6`, removed modules count=`6`
- `unraisableexception_only`: wall delta=`-0.0256`, import delta(us)=`675`, module delta=`-1`, removed modules count=`1`
- `light_terminal_plugins`: wall delta=`-0.0185`, import delta(us)=`-6749`, module delta=`-15`, removed modules count=`15`
- `debugging_only`: wall delta=`-0.0105`, import delta(us)=`1605`, module delta=`-4`, removed modules count=`4`
- `threadexception_only`: wall delta=`0.0048`, import delta(us)=`6255`, module delta=`-1`, removed modules count=`1`

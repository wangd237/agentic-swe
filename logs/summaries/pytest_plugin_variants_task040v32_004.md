# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_040`
- test_command: `python -m pytest tests/test_requirements.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.2555`, import self avg(us)=`151207`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2382`, import self avg(us)=`142856`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `debugging_only`: wall avg=`0.2488`, import self avg(us)=`153297`, module avg=`286`, flags=`-p no:debugging`
- `unraisableexception_only`: wall avg=`0.2294`, import self avg(us)=`148426`, module avg=`289`, flags=`-p no:unraisableexception`
- `threadexception_only`: wall avg=`0.2693`, import self avg(us)=`156028`, module avg=`289`, flags=`-p no:threadexception`
- `debug_exception_plugins`: wall avg=`0.2214`, import self avg(us)=`143350`, module avg=`284`, flags=`-p no:debugging -p no:unraisableexception -p no:threadexception`
- `minimal_safe_plugins`: wall avg=`0.2076`, import self avg(us)=`135485`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.0479`, import delta(us)=`-15722`, module delta=`-22`, removed modules count=`22`
- `debug_exception_plugins`: wall delta=`-0.0341`, import delta(us)=`-7857`, module delta=`-6`, removed modules count=`6`
- `unraisableexception_only`: wall delta=`-0.0261`, import delta(us)=`-2781`, module delta=`-1`, removed modules count=`1`
- `light_terminal_plugins`: wall delta=`-0.0173`, import delta(us)=`-8351`, module delta=`-15`, removed modules count=`15`
- `debugging_only`: wall delta=`-0.0067`, import delta(us)=`2090`, module delta=`-4`, removed modules count=`4`
- `threadexception_only`: wall delta=`0.0138`, import delta(us)=`4821`, module delta=`-1`, removed modules count=`1`

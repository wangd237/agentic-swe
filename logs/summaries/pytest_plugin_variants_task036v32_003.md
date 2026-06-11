# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_036`
- test_command: `python -m pytest tests/test_hostname.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.2579`, import self avg(us)=`149916`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2463`, import self avg(us)=`146944`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `debug_exception_plugins`: wall avg=`0.2326`, import self avg(us)=`153907`, module avg=`284`, flags=`-p no:debugging -p no:unraisableexception -p no:threadexception`
- `minimal_safe_plugins`: wall avg=`0.225`, import self avg(us)=`147575`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.0329`, import delta(us)=`-2341`, module delta=`-22`, removed modules count=`22`
- `debug_exception_plugins`: wall delta=`-0.0253`, import delta(us)=`3991`, module delta=`-6`, removed modules count=`6`
- `light_terminal_plugins`: wall delta=`-0.0116`, import delta(us)=`-2972`, module delta=`-15`, removed modules count=`15`

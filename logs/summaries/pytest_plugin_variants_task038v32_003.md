# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_038`
- test_command: `python -m pytest tests/test_validator.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.2531`, import self avg(us)=`152733`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2389`, import self avg(us)=`146012`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `debug_exception_plugins`: wall avg=`0.2314`, import self avg(us)=`152584`, module avg=`284`, flags=`-p no:debugging -p no:unraisableexception -p no:threadexception`
- `minimal_safe_plugins`: wall avg=`0.2193`, import self avg(us)=`142030`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.0338`, import delta(us)=`-10703`, module delta=`-22`, removed modules count=`22`
- `debug_exception_plugins`: wall delta=`-0.0217`, import delta(us)=`-149`, module delta=`-6`, removed modules count=`6`
- `light_terminal_plugins`: wall delta=`-0.0142`, import delta(us)=`-6721`, module delta=`-15`, removed modules count=`15`

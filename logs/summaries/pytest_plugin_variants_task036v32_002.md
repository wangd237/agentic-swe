# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_036`
- test_command: `python -m pytest tests/test_hostname.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.2507`, import self avg(us)=`145883`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2531`, import self avg(us)=`150595`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `minimal_safe_plugins`: wall avg=`0.2166`, import self avg(us)=`140462`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.0341`, import delta(us)=`-5421`, module delta=`-22`, removed modules count=`22`
- `light_terminal_plugins`: wall delta=`0.0024`, import delta(us)=`4712`, module delta=`-15`, removed modules count=`15`

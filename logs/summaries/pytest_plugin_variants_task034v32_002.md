# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_034`
- test_command: `python -m pytest tests/test_utils.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.249`, import self avg(us)=`152111`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2432`, import self avg(us)=`152989`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `minimal_safe_plugins`: wall avg=`0.2152`, import self avg(us)=`143397`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.0338`, import delta(us)=`-8714`, module delta=`-22`, removed modules count=`22`
- `light_terminal_plugins`: wall delta=`-0.0058`, import delta(us)=`878`, module delta=`-15`, removed modules count=`15`

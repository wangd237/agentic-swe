# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_040`
- test_command: `python -m pytest tests/test_requirements.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.2448`, import self avg(us)=`146001`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2482`, import self avg(us)=`148296`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `minimal_safe_plugins`: wall avg=`0.2167`, import self avg(us)=`141047`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.0281`, import delta(us)=`-4954`, module delta=`-22`, removed modules count=`22`
- `light_terminal_plugins`: wall delta=`0.0034`, import delta(us)=`2295`, module delta=`-15`, removed modules count=`15`

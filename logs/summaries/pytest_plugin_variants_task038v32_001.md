# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_038`
- test_command: `python -m pytest tests/test_validator.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.0431`, import self avg(us)=`9104`, module avg=`33`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.0439`, import self avg(us)=`8491`, module avg=`33`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `minimal_safe_plugins`: wall avg=`0.0436`, import self avg(us)=`9290`, module avg=`33`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`0.0005`, import delta(us)=`186`, module delta=`0`, removed modules count=`0`
- `light_terminal_plugins`: wall delta=`0.0008`, import delta(us)=`-613`, module delta=`0`, removed modules count=`0`

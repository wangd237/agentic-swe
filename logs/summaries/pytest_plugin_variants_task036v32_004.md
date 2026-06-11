# Pytest Plugin Variant Benchmark

## Task

- task_id: `task_036`
- test_command: `python -m pytest tests/test_hostname.py -q`
- repetitions: `3`

## Variants

- `default_plugins`: wall avg=`0.257`, import self avg(us)=`153539`, module avg=`290`, flags=`(none)`
- `light_terminal_plugins`: wall avg=`0.2352`, import self avg(us)=`145348`, module avg=`275`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress`
- `debugging_only`: wall avg=`0.2475`, import self avg(us)=`152737`, module avg=`286`, flags=`-p no:debugging`
- `unraisableexception_only`: wall avg=`0.2328`, import self avg(us)=`150079`, module avg=`289`, flags=`-p no:unraisableexception`
- `threadexception_only`: wall avg=`0.2628`, import self avg(us)=`154288`, module avg=`289`, flags=`-p no:threadexception`
- `debug_exception_plugins`: wall avg=`0.2225`, import self avg(us)=`145581`, module avg=`284`, flags=`-p no:debugging -p no:unraisableexception -p no:threadexception`
- `minimal_safe_plugins`: wall avg=`0.2088`, import self avg(us)=`135895`, module avg=`268`, flags=`-p no:junitxml -p no:pastebin -p no:setuponly -p no:setupplan -p no:stepwise -p no:warnings -p no:faulthandler -p no:terminalprogress -p no:debugging -p no:unraisableexception -p no:threadexception`

## Deltas vs Default

- `minimal_safe_plugins`: wall delta=`-0.0482`, import delta(us)=`-17644`, module delta=`-22`, removed modules count=`22`
- `debug_exception_plugins`: wall delta=`-0.0345`, import delta(us)=`-7958`, module delta=`-6`, removed modules count=`6`
- `unraisableexception_only`: wall delta=`-0.0242`, import delta(us)=`-3460`, module delta=`-1`, removed modules count=`1`
- `light_terminal_plugins`: wall delta=`-0.0218`, import delta(us)=`-8191`, module delta=`-15`, removed modules count=`15`
- `debugging_only`: wall delta=`-0.0095`, import delta(us)=`-802`, module delta=`-4`, removed modules count=`4`
- `threadexception_only`: wall delta=`0.0058`, import delta(us)=`749`, module delta=`-1`, removed modules count=`1`

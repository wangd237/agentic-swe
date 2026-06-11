# Pytest Plugin Variant Cohort Analysis

## Cohort

- cohort_label: `run_tests_hotspots_v32`
- task_count: `4`
- task_ids: `['task_034', 'task_036', 'task_038', 'task_040']`

## Ranked Variants

- `minimal_safe_plugins`: avg wall delta=`-0.0496`, avg import delta(us)=`-17930`, avg module delta=`-22`
- `debug_exception_plugins`: avg wall delta=`-0.0346`, avg import delta(us)=`-8225`, avg module delta=`-6`
- `unraisableexception_only`: avg wall delta=`-0.0282`, avg import delta(us)=`-4683`, avg module delta=`-1`
- `light_terminal_plugins`: avg wall delta=`-0.0195`, avg import delta(us)=`-9192`, avg module delta=`-15`
- `debugging_only`: avg wall delta=`-0.0104`, avg import delta(us)=`-1889`, avg module delta=`-4`
- `threadexception_only`: avg wall delta=`0.0059`, avg import delta(us)=`1352`, avg module delta=`-1`

## Removed Modules

- `minimal_safe_plugins`: `_elementtree` x4, `_pytest.faulthandler` x4, `_pytest.junitxml` x4, `_pytest.pastebin` x4, `_pytest.setuponly` x4, `_pytest.setupplan` x4
- `debug_exception_plugins`: `_pytest.threadexception` x4, `_pytest.unraisableexception` x4, `cmd` x4, `code` x4, `codeop` x4, `pdb` x4
- `unraisableexception_only`: `_pytest.unraisableexception` x4
- `light_terminal_plugins`: `_elementtree` x4, `_pytest.faulthandler` x4, `_pytest.junitxml` x4, `_pytest.pastebin` x4, `_pytest.setuponly` x4, `_pytest.setupplan` x4
- `debugging_only`: `cmd` x4, `code` x4, `codeop` x4, `pdb` x4
- `threadexception_only`: `_pytest.threadexception` x4

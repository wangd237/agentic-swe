# Pytest Plugin Variant Cohort Analysis

## Cohort

- cohort_label: `run_tests_hotspots_v32`
- task_count: `4`
- task_ids: `['task_034', 'task_036', 'task_038', 'task_040']`

## Ranked Variants

- `minimal_safe_plugins`: avg wall delta=`-0.0331`, avg import delta(us)=`-6415`, avg module delta=`-22`
- `debug_exception_plugins`: avg wall delta=`-0.0235`, avg import delta(us)=`2073`, avg module delta=`-6`
- `light_terminal_plugins`: avg wall delta=`-0.0123`, avg import delta(us)=`-4433`, avg module delta=`-15`

## Removed Modules

- `minimal_safe_plugins`: `_elementtree` x4, `_pytest.faulthandler` x4, `_pytest.junitxml` x4, `_pytest.pastebin` x4, `_pytest.setuponly` x4, `_pytest.setupplan` x4
- `debug_exception_plugins`: `_pytest.threadexception` x4, `_pytest.unraisableexception` x4, `cmd` x4, `code` x4, `codeop` x4, `pdb` x4
- `light_terminal_plugins`: `_elementtree` x4, `_pytest.faulthandler` x4, `_pytest.junitxml` x4, `_pytest.pastebin` x4, `_pytest.setuponly` x4, `_pytest.setupplan` x4

# Pytest Import Group Analysis

## Cohort

- cohort_label: `run_tests_hotspots_v32`
- task_count: `4`
- task_ids: `['task_034', 'task_036', 'task_038', 'task_040']`

## Ranked Groups

- `pytest_optional_plugins`: avg self(us)=`6181`, avg modules=`14`, present tasks=`4`
- `windows_ctypes`: avg self(us)=`5103`, avg modules=`4`, present tasks=`4`
- `xml_stack`: avg self(us)=`4026`, avg modules=`6`, present tasks=`4`
- `terminal_chain`: avg self(us)=`3653`, avg modules=`7`, present tasks=`4`
- `debugging_chain`: avg self(us)=`2094`, avg modules=`3`, present tasks=`4`
- `pytest_collection_core`: avg self(us)=`1126`, avg modules=`1`, present tasks=`4`
- `python_shell_chain`: avg self(us)=`722`, avg modules=`2`, present tasks=`4`
- `other`: avg self(us)=`0`, avg modules=`0`, present tasks=`0`

## Dominant Tasks

- `task_040`: import delta(us)=`30108`, dominant group=`pytest_optional_plugins`, dominant self(us)=`6641`
- `task_034`: import delta(us)=`18859`, dominant group=`pytest_optional_plugins`, dominant self(us)=`5682`
- `task_036`: import delta(us)=`18363`, dominant group=`pytest_optional_plugins`, dominant self(us)=`6495`
- `task_038`: import delta(us)=`16262`, dominant group=`pytest_optional_plugins`, dominant self(us)=`5907`

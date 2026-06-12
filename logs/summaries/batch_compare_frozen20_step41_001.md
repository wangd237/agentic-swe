# Batch Eval Compare Report

## Compare

- compare_id: `batch_compare_frozen20_step41_001`
- baseline_eval_id: `batch_eval_frozen20v60r2_001`
- improved_eval_id: `batch_eval_frozen20v61r1_001`
- baseline_policy_id: `improved_v60`
- improved_policy_id: `improved_v61`
- created_at: `2026-06-12T11:30:07.476463+00:00`

## Headline

- `success_rate`: `1.0` -> `0.0` (delta: `-1.0`, outcome: `regressed`)
- `test_pass_rate`: `1.0` -> `0.0` (delta: `-1.0`, outcome: `regressed`)
- `partial_fix_rate`: `0.0` -> `0.0` (delta: `0.0`, outcome: `unchanged`)
- `average_duration_sec`: `0.5471` -> `0.5663` (delta: `0.0192`, outcome: `regressed`)

## Metric Deltas

- `average_duration_sec`: baseline `0.5471` -> improved `0.5663` (delta: `0.0192`, outcome: `regressed`)
- `average_modified_files`: baseline `1.0` -> improved `0.0` (delta: `-1.0`, outcome: `improved`)
- `average_steps`: baseline `10.25` -> improved `10.25` (delta: `0.0`, outcome: `unchanged`)
- `average_tool_calls`: baseline `9.25` -> improved `8.25` (delta: `-1.0`, outcome: `improved`)
- `key_file_read_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_count`: baseline `0` -> improved `0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `reasonable_finish_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `repeated_search_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `success_count`: baseline `20` -> improved `0` (delta: `-20.0`, outcome: `regressed`)
- `success_rate`: baseline `1.0` -> improved `0.0` (delta: `-1.0`, outcome: `regressed`)
- `task_count`: baseline `20` -> improved `20` (delta: `0.0`, outcome: `neutral`)
- `test_execution_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `test_pass_count`: baseline `20` -> improved `0` (delta: `-20.0`, outcome: `regressed`)
- `test_pass_rate`: baseline `1.0` -> improved `0.0` (delta: `-1.0`, outcome: `regressed`)

## Taxonomy Deltas

- `Premature Finish`: baseline `0` -> improved `20` (delta: `20`)

## Per-Task Label Changes

- `task_006`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_008`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_010`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_013`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_016`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_017`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_019`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_022`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_024`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_026`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_028`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_030`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_032`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_034`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_036`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_038`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_040`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_042`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_044`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_046`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)

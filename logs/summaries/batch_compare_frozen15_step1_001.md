# Batch Eval Compare Report

## Compare

- compare_id: `batch_compare_frozen15_step1_001`
- baseline_eval_id: `batch_eval_frozen15v16_001`
- improved_eval_id: `batch_eval_frozen15v17_001`
- baseline_policy_id: `improved_v16`
- improved_policy_id: `improved_v17`
- created_at: `2026-06-10T06:57:59.594860+00:00`

## Headline

- `success_rate`: `0.9333` -> `1.0` (delta: `0.0667`, outcome: `improved`)
- `test_pass_rate`: `0.9333` -> `1.0` (delta: `0.0667`, outcome: `improved`)
- `partial_fix_rate`: `0.0` -> `0.0` (delta: `0.0`, outcome: `unchanged`)
- `average_duration_sec`: `0.5926` -> `0.5906` (delta: `-0.002`, outcome: `improved`)

## Metric Deltas

- `average_duration_sec`: baseline `0.5926` -> improved `0.5906` (delta: `-0.002`, outcome: `improved`)
- `average_modified_files`: baseline `0.9333` -> improved `1.0` (delta: `0.0667`, outcome: `regressed`)
- `average_steps`: baseline `9.2667` -> improved `9.2667` (delta: `0.0`, outcome: `unchanged`)
- `average_tool_calls`: baseline `9.2` -> improved `9.2667` (delta: `0.0667`, outcome: `regressed`)
- `key_file_read_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_count`: baseline `0` -> improved `0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `reasonable_finish_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `repeated_search_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `success_count`: baseline `14` -> improved `15` (delta: `1.0`, outcome: `improved`)
- `success_rate`: baseline `0.9333` -> improved `1.0` (delta: `0.0667`, outcome: `improved`)
- `task_count`: baseline `15` -> improved `15` (delta: `0.0`, outcome: `neutral`)
- `test_execution_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `test_pass_count`: baseline `14` -> improved `15` (delta: `1.0`, outcome: `improved`)
- `test_pass_rate`: baseline `0.9333` -> improved `1.0` (delta: `0.0667`, outcome: `improved`)

## Taxonomy Deltas

- `Premature Finish`: baseline `1` -> improved `0` (delta: `-1`)

## Per-Task Label Changes

- `task_006`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_008`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_010`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_013`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_016`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_017`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_019`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_022`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_024`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_026`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_028`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_030`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_032`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_034`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_036`: baseline `Premature Finish` -> improved `无错误标签` (changed: `True`)

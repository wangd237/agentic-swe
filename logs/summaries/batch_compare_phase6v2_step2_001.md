# Batch Eval Compare Report

## Compare

- compare_id: `batch_compare_phase6v2_step2_001`
- baseline_eval_id: `batch_eval_improvedv1r2_001`
- improved_eval_id: `batch_eval_improvedv2_001`
- baseline_policy_id: `improved_v1`
- improved_policy_id: `improved_v2`
- created_at: `2026-06-06T06:34:42.389817+00:00`

## Headline

- `success_rate`: `0.6667` -> `1.0` (delta: `0.3333`, outcome: `improved`)
- `test_pass_rate`: `0.6667` -> `1.0` (delta: `0.3333`, outcome: `improved`)
- `partial_fix_rate`: `0.3333` -> `0.0` (delta: `-0.3333`, outcome: `improved`)
- `average_duration_sec`: `0.4835` -> `0.5025` (delta: `0.019`, outcome: `regressed`)

## Metric Deltas

- `average_duration_sec`: baseline `0.4835` -> improved `0.5025` (delta: `0.019`, outcome: `regressed`)
- `average_modified_files`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `average_steps`: baseline `9.0` -> improved `9.0` (delta: `0.0`, outcome: `unchanged`)
- `average_tool_calls`: baseline `9.0` -> improved `9.0` (delta: `0.0`, outcome: `unchanged`)
- `key_file_read_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_count`: baseline `1` -> improved `0` (delta: `-1.0`, outcome: `improved`)
- `partial_fix_rate`: baseline `0.3333` -> improved `0.0` (delta: `-0.3333`, outcome: `improved`)
- `reasonable_finish_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `repeated_search_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `success_count`: baseline `2` -> improved `3` (delta: `1.0`, outcome: `improved`)
- `success_rate`: baseline `0.6667` -> improved `1.0` (delta: `0.3333`, outcome: `improved`)
- `task_count`: baseline `3` -> improved `3` (delta: `0.0`, outcome: `neutral`)
- `test_execution_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `test_pass_count`: baseline `2` -> improved `3` (delta: `1.0`, outcome: `improved`)
- `test_pass_rate`: baseline `0.6667` -> improved `1.0` (delta: `0.3333`, outcome: `improved`)

## Taxonomy Deltas

- `Patch Incorrect`: baseline `1` -> improved `0` (delta: `-1`)

## Per-Task Label Changes

- `task_001`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_003`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_004`: baseline `Patch Incorrect` -> improved `无错误标签` (changed: `True`)

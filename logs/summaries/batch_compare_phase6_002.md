# Batch Eval Compare Report

## Compare

- compare_id: `batch_compare_phase6_002`
- baseline_eval_id: `batch_eval_baseline_001`
- improved_eval_id: `batch_eval_improved_001`
- baseline_policy_id: `baseline_v1`
- improved_policy_id: `improved_v1`
- created_at: `2026-06-05T13:55:07.688013+00:00`

## Headline

- `success_rate`: `0.5` -> `1.0` (delta: `0.5`, outcome: `improved`)
- `test_pass_rate`: `0.5` -> `1.0` (delta: `0.5`, outcome: `improved`)
- `partial_fix_rate`: `0.5` -> `0.0` (delta: `-0.5`, outcome: `improved`)
- `average_duration_sec`: `0.4734` -> `0.4574` (delta: `-0.016`, outcome: `improved`)

## Metric Deltas

- `average_duration_sec`: baseline `0.4734` -> improved `0.4574` (delta: `-0.016`, outcome: `improved`)
- `average_modified_files`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `average_steps`: baseline `9.0` -> improved `9.0` (delta: `0.0`, outcome: `unchanged`)
- `average_tool_calls`: baseline `9.0` -> improved `9.0` (delta: `0.0`, outcome: `unchanged`)
- `key_file_read_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_count`: baseline `1` -> improved `0` (delta: `-1.0`, outcome: `improved`)
- `partial_fix_rate`: baseline `0.5` -> improved `0.0` (delta: `-0.5`, outcome: `improved`)
- `reasonable_finish_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `repeated_search_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `success_count`: baseline `1` -> improved `2` (delta: `1.0`, outcome: `improved`)
- `success_rate`: baseline `0.5` -> improved `1.0` (delta: `0.5`, outcome: `improved`)
- `task_count`: baseline `2` -> improved `2` (delta: `0.0`, outcome: `neutral`)
- `test_execution_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `test_pass_count`: baseline `1` -> improved `2` (delta: `1.0`, outcome: `improved`)
- `test_pass_rate`: baseline `0.5` -> improved `1.0` (delta: `0.5`, outcome: `improved`)

## Taxonomy Deltas

- `Patch Incorrect`: baseline `1` -> improved `0` (delta: `-1`)

## Per-Task Label Changes

- `task_001`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_003`: baseline `Patch Incorrect` -> improved `无错误标签` (changed: `True`)

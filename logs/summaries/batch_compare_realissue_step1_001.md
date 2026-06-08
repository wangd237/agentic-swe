# Batch Eval Compare Report

## Compare

- compare_id: `batch_compare_realissue_step1_001`
- baseline_eval_id: `batch_eval_realissuev2_001`
- improved_eval_id: `batch_eval_realissuev3_001`
- baseline_policy_id: `improved_v2`
- improved_policy_id: `improved_v3`
- created_at: `2026-06-08T06:56:02.693553+00:00`

## Headline

- `success_rate`: `0.0` -> `1.0` (delta: `1.0`, outcome: `improved`)
- `test_pass_rate`: `0.0` -> `1.0` (delta: `1.0`, outcome: `improved`)
- `partial_fix_rate`: `0.0` -> `0.0` (delta: `0.0`, outcome: `unchanged`)
- `average_duration_sec`: `0.5436` -> `0.5563` (delta: `0.0127`, outcome: `regressed`)

## Metric Deltas

- `average_duration_sec`: baseline `0.5436` -> improved `0.5563` (delta: `0.0127`, outcome: `regressed`)
- `average_modified_files`: baseline `0.0` -> improved `1.0` (delta: `1.0`, outcome: `regressed`)
- `average_steps`: baseline `9.0` -> improved `9.0` (delta: `0.0`, outcome: `unchanged`)
- `average_tool_calls`: baseline `8.0` -> improved `9.0` (delta: `1.0`, outcome: `regressed`)
- `key_file_read_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_count`: baseline `0` -> improved `0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `reasonable_finish_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `repeated_search_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `success_count`: baseline `0` -> improved `1` (delta: `1.0`, outcome: `improved`)
- `success_rate`: baseline `0.0` -> improved `1.0` (delta: `1.0`, outcome: `improved`)
- `task_count`: baseline `1` -> improved `1` (delta: `0.0`, outcome: `neutral`)
- `test_execution_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `test_pass_count`: baseline `0` -> improved `1` (delta: `1.0`, outcome: `improved`)
- `test_pass_rate`: baseline `0.0` -> improved `1.0` (delta: `1.0`, outcome: `improved`)

## Taxonomy Deltas

- `Premature Finish`: baseline `1` -> improved `0` (delta: `-1`)

## Per-Task Label Changes

- `task_006`: baseline `Premature Finish` -> improved `无错误标签` (changed: `True`)

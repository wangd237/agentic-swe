# Batch Eval Compare Report

## Compare

- compare_id: `batch_compare_realissue_step3_001`
- baseline_eval_id: `batch_eval_realissuev4r2_001`
- improved_eval_id: `batch_eval_realissuev5_001`
- baseline_policy_id: `improved_v4`
- improved_policy_id: `improved_v5`
- created_at: `2026-06-08T08:27:35.757216+00:00`

## Headline

- `success_rate`: `0.6667` -> `1.0` (delta: `0.3333`, outcome: `improved`)
- `test_pass_rate`: `0.6667` -> `1.0` (delta: `0.3333`, outcome: `improved`)
- `partial_fix_rate`: `0.0` -> `0.0` (delta: `0.0`, outcome: `unchanged`)
- `average_duration_sec`: `0.5592` -> `0.5503` (delta: `-0.0089`, outcome: `improved`)

## Metric Deltas

- `average_duration_sec`: baseline `0.5592` -> improved `0.5503` (delta: `-0.0089`, outcome: `improved`)
- `average_modified_files`: baseline `0.6667` -> improved `1.0` (delta: `0.3333`, outcome: `regressed`)
- `average_steps`: baseline `9.0` -> improved `9.0` (delta: `0.0`, outcome: `unchanged`)
- `average_tool_calls`: baseline `8.6667` -> improved `9.0` (delta: `0.3333`, outcome: `regressed`)
- `key_file_read_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_count`: baseline `0` -> improved `0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `reasonable_finish_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `repeated_search_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `success_count`: baseline `2` -> improved `3` (delta: `1.0`, outcome: `improved`)
- `success_rate`: baseline `0.6667` -> improved `1.0` (delta: `0.3333`, outcome: `improved`)
- `task_count`: baseline `3` -> improved `3` (delta: `0.0`, outcome: `neutral`)
- `test_execution_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `test_pass_count`: baseline `2` -> improved `3` (delta: `1.0`, outcome: `improved`)
- `test_pass_rate`: baseline `0.6667` -> improved `1.0` (delta: `0.3333`, outcome: `improved`)

## Taxonomy Deltas

- `Premature Finish`: baseline `1` -> improved `0` (delta: `-1`)

## Per-Task Label Changes

- `task_006`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_008`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_010`: baseline `Premature Finish` -> improved `无错误标签` (changed: `True`)

# Batch Eval Compare Report

## Compare

- compare_id: `batch_compare_realissue_step8_001`
- baseline_eval_id: `batch_eval_realissuev9r2_001`
- improved_eval_id: `batch_eval_realissuev10_001`
- baseline_policy_id: `improved_v9`
- improved_policy_id: `improved_v10`
- created_at: `2026-06-09T03:16:54.460969+00:00`

## Headline

- `success_rate`: `0.875` -> `1.0` (delta: `0.125`, outcome: `improved`)
- `test_pass_rate`: `0.875` -> `1.0` (delta: `0.125`, outcome: `improved`)
- `partial_fix_rate`: `0.0` -> `0.0` (delta: `0.0`, outcome: `unchanged`)
- `average_duration_sec`: `0.5334` -> `0.5302` (delta: `-0.0032`, outcome: `improved`)

## Metric Deltas

- `average_duration_sec`: baseline `0.5334` -> improved `0.5302` (delta: `-0.0032`, outcome: `improved`)
- `average_modified_files`: baseline `0.875` -> improved `1.0` (delta: `0.125`, outcome: `regressed`)
- `average_steps`: baseline `9.625` -> improved `9.625` (delta: `0.0`, outcome: `unchanged`)
- `average_tool_calls`: baseline `9.5` -> improved `9.625` (delta: `0.125`, outcome: `regressed`)
- `key_file_read_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_count`: baseline `0` -> improved `0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `reasonable_finish_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `repeated_search_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `success_count`: baseline `7` -> improved `8` (delta: `1.0`, outcome: `improved`)
- `success_rate`: baseline `0.875` -> improved `1.0` (delta: `0.125`, outcome: `improved`)
- `task_count`: baseline `8` -> improved `8` (delta: `0.0`, outcome: `neutral`)
- `test_execution_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `test_pass_count`: baseline `7` -> improved `8` (delta: `1.0`, outcome: `improved`)
- `test_pass_rate`: baseline `0.875` -> improved `1.0` (delta: `0.125`, outcome: `improved`)

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
- `task_022`: baseline `Premature Finish` -> improved `无错误标签` (changed: `True`)

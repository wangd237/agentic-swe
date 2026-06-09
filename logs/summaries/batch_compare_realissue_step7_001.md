# Batch Eval Compare Report

## Compare

- compare_id: `batch_compare_realissue_step7_001`
- baseline_eval_id: `batch_eval_realissuev8r2_001`
- improved_eval_id: `batch_eval_realissuev9_001`
- baseline_policy_id: `improved_v8`
- improved_policy_id: `improved_v9`
- created_at: `2026-06-09T02:46:55.773352+00:00`

## Headline

- `success_rate`: `0.8571` -> `1.0` (delta: `0.1429`, outcome: `improved`)
- `test_pass_rate`: `0.8571` -> `1.0` (delta: `0.1429`, outcome: `improved`)
- `partial_fix_rate`: `0.0` -> `0.0` (delta: `0.0`, outcome: `unchanged`)
- `average_duration_sec`: `0.5962` -> `0.5928` (delta: `-0.0034`, outcome: `improved`)

## Metric Deltas

- `average_duration_sec`: baseline `0.5962` -> improved `0.5928` (delta: `-0.0034`, outcome: `improved`)
- `average_modified_files`: baseline `0.8571` -> improved `1.0` (delta: `0.1429`, outcome: `regressed`)
- `average_steps`: baseline `9.7143` -> improved `9.7143` (delta: `0.0`, outcome: `unchanged`)
- `average_tool_calls`: baseline `9.5714` -> improved `9.7143` (delta: `0.1429`, outcome: `regressed`)
- `key_file_read_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_count`: baseline `0` -> improved `0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `reasonable_finish_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `repeated_search_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `success_count`: baseline `6` -> improved `7` (delta: `1.0`, outcome: `improved`)
- `success_rate`: baseline `0.8571` -> improved `1.0` (delta: `0.1429`, outcome: `improved`)
- `task_count`: baseline `7` -> improved `7` (delta: `0.0`, outcome: `neutral`)
- `test_execution_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `test_pass_count`: baseline `6` -> improved `7` (delta: `1.0`, outcome: `improved`)
- `test_pass_rate`: baseline `0.8571` -> improved `1.0` (delta: `0.1429`, outcome: `improved`)

## Taxonomy Deltas

- `Premature Finish`: baseline `1` -> improved `0` (delta: `-1`)

## Per-Task Label Changes

- `task_006`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_008`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_010`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_013`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_016`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_017`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_019`: baseline `Premature Finish` -> improved `无错误标签` (changed: `True`)

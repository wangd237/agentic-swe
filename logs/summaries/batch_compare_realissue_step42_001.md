# Batch Eval Compare Report

## Compare

- compare_id: `batch_compare_realissue_step42_001`
- baseline_eval_id: `batch_eval_realissuev60r2_001`
- improved_eval_id: `batch_eval_realissuev61r1_001`
- baseline_policy_id: `improved_v60`
- improved_policy_id: `improved_v61`
- created_at: `2026-06-12T11:29:29.477033+00:00`

## Headline

- `success_rate`: `1.0` -> `0.2069` (delta: `-0.7931`, outcome: `regressed`)
- `test_pass_rate`: `1.0` -> `0.2069` (delta: `-0.7931`, outcome: `regressed`)
- `partial_fix_rate`: `0.0` -> `0.0` (delta: `0.0`, outcome: `unchanged`)
- `average_duration_sec`: `0.5262` -> `0.5317` (delta: `0.0055`, outcome: `regressed`)

## Metric Deltas

- `average_duration_sec`: baseline `0.5262` -> improved `0.5317` (delta: `0.0055`, outcome: `regressed`)
- `average_modified_files`: baseline `1.0` -> improved `0.2069` (delta: `-0.7931`, outcome: `improved`)
- `average_steps`: baseline `10.2982` -> improved `10.3276` (delta: `0.0294`, outcome: `regressed`)
- `average_tool_calls`: baseline `9.2982` -> improved `8.5345` (delta: `-0.7637`, outcome: `improved`)
- `key_file_read_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_count`: baseline `0` -> improved `0` (delta: `0.0`, outcome: `unchanged`)
- `partial_fix_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `reasonable_finish_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `repeated_search_rate`: baseline `0.0` -> improved `0.0` (delta: `0.0`, outcome: `unchanged`)
- `success_count`: baseline `57` -> improved `12` (delta: `-45.0`, outcome: `regressed`)
- `success_rate`: baseline `1.0` -> improved `0.2069` (delta: `-0.7931`, outcome: `regressed`)
- `task_count`: baseline `57` -> improved `58` (delta: `1.0`, outcome: `neutral`)
- `test_execution_rate`: baseline `1.0` -> improved `1.0` (delta: `0.0`, outcome: `unchanged`)
- `test_pass_count`: baseline `57` -> improved `12` (delta: `-45.0`, outcome: `regressed`)
- `test_pass_rate`: baseline `1.0` -> improved `0.2069` (delta: `-0.7931`, outcome: `regressed`)

## Taxonomy Deltas

- `Premature Finish`: baseline `0` -> improved `46` (delta: `46`)

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
- `task_048`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_050`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_052`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_054`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_056`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_057`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_058`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_059`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_060`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_061`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_063`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_065`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_067`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_069`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_071`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_073`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_075`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_077`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_079`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_081`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_083`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_085`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_087`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_089`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_091`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_093`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_095`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_097`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_099`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_101`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_103`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_105`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_107`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_109`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_111`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_113`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)
- `task_115`: baseline `无错误标签` -> improved `Premature Finish` (changed: `True`)
- `task_117`: baseline `无错误标签` -> improved `无错误标签` (changed: `False`)

# Eval 设计说明

## 当前阶段

当前处于 `Phase 5`，最小 baseline 评测链路已经实现。

## 当前输入协议

评测当前读取：

- `logs/summaries/batch_run_001.json` 这类 batch summary
- 其中每条任务指向的：
  - `task.json`
  - `result.json`
  - `trace.json`
  - `patch.diff`

## 当前指标定义

### 结果指标

- `Success Rate`
  - 定义：`final_status == "success"` 的比例
- `Test Pass Rate`
  - 定义：`test_exit_code == 0` 的比例
- `Partial Fix Rate`
  - 定义：非 success，但 `patch_applied == true` 且 `post_test_exit_code != 0` 的比例

### 工具使用指标

- `key_file_read_rate`
  - 定义：`trace.read_files` 与 `task.target_files_hint` 有交集的比例
- `test_execution_rate`
  - 定义：trace 中存在 `run_tests` 步骤的比例
- `repeated_search_rate`
  - 定义：同一任务中出现重复 `search_code` query 的比例
- `reasonable_finish_rate`
  - 定义：存在 `post_test_exit_code` 的比例

### Patch 与效率指标

- `average_modified_files`
- `average_steps`
- `average_tool_calls`
- `average_duration_sec`

## 当前错误分类规则

当前 taxonomy 由 `evals/error_taxonomy.py` 提供，采用纯规则法。

支持的标签：

- `Wrong File Selection`
- `Wrong Root Cause`
- `Patch Incorrect`
- `No Test Execution`
- `Over-editing`
- `Premature Finish`
- `Looping / Repeated Search`

## 当前限制

- 当前 dev set 太小，而且全部成功
- 因此 taxonomy 链路已经打通，但还没有真实失败样本来验证分类价值
- 进入后续 phase 时，需要补充更难、更真实、更多样的正式任务集

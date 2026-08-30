# ADR-0003: 工具大输出落盘

**日期**: 2026-08-30
**状态**: 已采纳

## Problem

`ToolExecutor.summarize_for_model` 中，超大工具结果被硬截断：
- `_json_for_model` 超过 `max_chars` 直接砍尾加 `...<truncated>`，无回取路径
- search 类工具 `matches[:50]` + `truncated_matches` 计数，超出 50 条后永久丢失
- `trace.json` 只存 600 字符摘要，**工具原始完整输出不落盘**，审计链断裂
- run_tests 的完整 stdout/stderr 虽然在 tool_result 的 data 里，但 LLM agent 路径
  没有任何落盘渠道（`task_runner` 的 pre/post_test_stdout.txt 只在 rule-based 路径写入）

## Decision

1. 在主循环的工具结果处理点增加落盘判断：单次输出超过 **12K 字符** 时，
   完整 JSON 写入 `logs/trajectories/<task_id>/<run_id>/tool_outputs/<step_XXX>_<tool_name>.json`
2. **落盘是附加行为，不改变回喂内容**：模型仍然收到 `summarize_for_model` 的
   4000 字符摘要，外加一段提示（"完整输出已落盘至 <路径>，如需更多匹配行请用
   grep 重新搜索并缩小范围"）。这样落盘纯粹服务审计，不引入行为变化，
   无需重新验证任务成功率
3. **阈值设 12K 字符**（而非 6K~8K），原因：
   - `max_tool_chars=4000` 是回喂上限，6K~8K 阈值会让仅略超上限的输出触发落盘
   - 先观察 12K 阈值下的触发频率，再调
4. 落盘文件计入 `TraceStep.evidence_ids`（`spill:<相对路径>`），保证可审计
5. **run_tests 不跳过**：LLM agent 路径下它没有其他落盘渠道，恰恰最需要 spill

## Alternatives Considered

1. **阈值 6K~8K（原建议）**: 过于激进。拒绝。
2. **落盘 + 回喂改为 800 字符预览（原方案）**: 改变模型输入，需要重新验证
   全部任务成功率，成本高。当前阶段选择"落盘不换预览"——审计价值先拿到，
   行为变化留到有需要时再做。**已知代价：4K~12K 区间的输出被截断喂给模型
   但不落盘，信息既丢又不可回取**。接受此缝隙，因为该区间内容通常已被
   summarize 的结构化摘要覆盖。
3. **落盘到 workspace 内**: read_file 可直接读，但会污染 git status/diff。拒绝。
3. **放宽 read_file 白名单允许读 run 目录**: 引入安全边界问题。暂不采纳，
   用"提示模型重新 grep"替代"read 回取"。

## Risks

- 模型可能忽略"重新 grep"的提示，反复 read 大文件。缓解：提示语写清楚
  "用 grep 重新搜索窄范围"
- 落盘文件数量在长任务中累积。缓解：16 轮上限，最多 ~16 个文件，可接受。
- 4K~12K 区间的信息缝隙（见 Alternatives 2）。缓解：观察实际触发频率后
  决定是否收紧阈值。

## Files Changed

- `app/agent/llm_agent.py`: 主循环增加 `_spill_large_tool_result`，trace evidence 引用
- `app/runtime/harness.py`: `RunPaths` 增加 `tool_outputs_dir`
- `tests/test_llm_agent.py`: 3 个回归测试（大结果落盘 / 小结果不落盘 /
  run_tests 小输出不落盘）

## 验证

pytest: 377 passed（374 + 3）。

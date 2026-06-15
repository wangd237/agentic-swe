# Target 2 Failure Deep Dive

状态：interim。Target 2 要求至少 `5` 条失败 case 的 trace 级根因分析。当前 DeepSeek scratch-guard 后 frozen_40 只有 `1` 条仍失败，因此本文件先沉淀已有 `3` 条有价值 case：`1` 条当前未解边界 + `2` 条由 trace-driven 改进或重跑转成功的历史失败。Kimi/GLM frozen_40 完成后，需要补齐至少 `2` 条跨模型失败或不一致 case。

## Summary

| Case | Run | Status | Type | Root cause |
| --- | --- | --- | --- | --- |
| `task_048` | `run_20260615T064450000602Z_7854` | incomplete | current failure | packaging `Version.base_version` 语义理解边界 |
| `task_032` before guard | `run_20260615T062851496288Z_7250` | incomplete | harness failure | 模型反复写 `debug.py`，但工具面不支持执行任意脚本 |
| `task_032` after guard | `run_20260615T064258972478Z_5407` | success | fixed by harness | scratch-file guard 迫使模型回到目标文件 |
| `task_030` before | `run_20260615T053708905100Z_0543` | incomplete | repair precision | 已定位逗号问题，但返回格式多出换行 |
| `task_030` after | `run_20260615T064231984612Z_4621` | success | stochastic / evidence sensitive | 新 run 同样 13 tool calls，但修正了 inline table 返回格式 |

## Case 1：`task_048` 当前未解边界

- latest run: [result](E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_048/run_20260615T064450000602Z_7854/result.json), [trace](E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_048/run_20260615T064450000602Z_7854/trace.json)
- final_status: `incomplete`
- incomplete_reason: `max_iterations`
- modified_files: none
- post_test_exit_code: `1`
- failed test: `tests/test_specifiers.py::SpecifierContainsTests::test_larger_dev_with_local_is_greater`

Trace signal:

- Agent 读取了 `packaging_specifier_repo/specifiers.py`，看到了 local version 分支中 `Version(prospective_version.base_version) == Version(self.spec_version.base_version)`。
- Agent 也读取了 `README.md`，其中明确写着当前缺陷是“错误地只比较了 `base_version`”。
- 但后续 reasoning 反复围绕 `base_version` 的语义打转：一会儿认为它保留 dev，一会儿怀疑 `Version.__gt__` 对 local 有特殊行为，最后没有形成 patch。
- 这次 run 没有留下 `debug.py`，也没有写错文件；失败更纯粹地暴露为领域语义边界。

Root cause:

模型没有把“local 版本比较的业务规则”转化成代码修改策略。它试图在脑内模拟 installed `packaging` 的 `Version` 行为，但当前工具面不能执行任意 probes，且仓库内没有 packaging 源码可读，导致分析停在循环里。

Harness implication:

- 这不是 scratch-file 污染问题，scratch guard 已经把 patch surface 清干净。
- 可考虑后续加一个受控诊断工具，例如只允许执行任务测试命令或只允许 `python -c` 的白名单表达式，但这会扩大工具面，需要谨慎。
- 更保守的 prompt 优化方向：当 README/测试/目标注释都直接指出缺陷时，不要继续证明第三方库内部行为；先修改本仓库分支条件，再用 `run_tests` 验证。

## Case 2：`task_032` scratch-file failure → success

Before:

- run: [result](E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_032/run_20260615T062851496288Z_7250/result.json), [trace](E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_032/run_20260615T062851496288Z_7250/trace.json)
- final_status: `incomplete`
- incomplete_reason: `max_iterations`
- modified_files: `debug.py`
- total_tool_calls: `13`

After:

- run: [result](E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_032/run_20260615T064258972478Z_5407/result.json), [trace](E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_032/run_20260615T064258972478Z_5407/trace.json)
- final_status: `success`
- modified_files: `packaging_wheel_repo/utils.py`
- total_tool_calls: `9`
- post_test_exit_code: `0`

Trace signal:

- Before run 中，模型已经读取了 `packaging_wheel_repo/utils.py` 和测试，也用 grep 找到了 normalized 相关线索。
- 但它随后写入 `debug.py`，收到 `scratch_file_warning` 后仍继续写 `debug.py`，甚至在文本里说“让我直接运行它”，而工具面没有任意命令执行能力。
- After run 中，模型没有再写 scratch 文件，而是直接 `edit_file` 修改 `packaging_wheel_repo/utils.py`，加入 `_normalize_version()` 并在解析时拒绝非 normalized 版本。

Root cause:

仅靠 prompt/warning 不足以约束模型行为。模型会把“写一个 probe 脚本”当成自然调试路径，但当前 agent 工具面并不支持执行它，于是产生无效 patch 和迭代浪费。

Harness change:

- `ToolExecutor.execute("write_file")` 对 `debug.py/tmp.py/scratch.py/probe.py` 直接返回 `scratch_file_not_allowed`。
- system prompt 和 tool schema 同步为“不要创建临时调试文件”。

Result:

DeepSeek frozen_40 从 `37/40` 提升到 `39/40`，其中 `task_032` 从稳定失败转为成功。这是 Target 2 的第一条明确 trace-driven harness optimization。

## Case 3：`task_030` inline table formatting failure → success

Before:

- run: [result](E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_030/run_20260615T053708905100Z_0543/result.json), [trace](E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_030/run_20260615T053708905100Z_0543/trace.json)
- final_status: `incomplete`
- incomplete_reason: `max_iterations`
- modified_files: `tomlkit_inline_table_repo/formatter.py`
- total_tool_calls: `13`

After:

- run: [result](E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_030/run_20260615T064231984612Z_4621/result.json), [trace](E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_030/run_20260615T064231984612Z_4621/trace.json)
- final_status: `success`
- modified_files: `tomlkit_inline_table_repo/formatter.py`
- total_tool_calls: `13`
- post_test_exit_code: `0`

Trace signal:

- Before run 定位方向正确：原实现把 `new_key` 直接黏到 inline table body 后，缺少 `, `。
- 失败点在修复细节：它一度把结果写成跨行格式，破坏 inline table 单行输出。
- After run 同样用了 `13` tool calls，但最终同时修了两个细节：插入 `, ` 分隔符，并把返回值收口为 `return f"{prefix}{fixed_body}}}\n"`。

Root cause:

这是格式精度边界，而不是定位失败。模型知道“要加逗号”，但第一次没有保持 TOML inline table 的单行格式不变量。

Harness implication:

- `run_tests` failure summary 的 `output_excerpt` 对这类任务很重要，因为断言 diff 中的换行、括号位置就是关键证据。
- 该任务不应被记录为稳定能力边界；它在新 run 中转成功，说明边界受输出细节、失败摘要和采样路径影响。

## Pending Deep Dives

Kimi/GLM frozen_40 跑完后，至少补齐：

1. 一条三模型全失败 case：说明 agent 框架共同边界。
2. 一条跨模型不一致 case：说明同一 harness 下模型能力差异。

每条必须包含：

- result / trace 链接
- failed stage：定位 / 修复 / 验证
- root cause：模型语义、工具限制、prompt 误导、测试摘要不足、或任务本身边界
- 是否触发 harness/prompt 改进
- 改进后是否复测

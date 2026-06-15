# Week Target：Agent 工具链升级

**主题：参照 Claude Code harness 设计，把 agent 从「能修」升级到「修得好、修得快、修错了能回退」。不做展示层。**

预期时间：2026-06-15 → 2026-06-22

## 背景

当前 agent 的工具链：`list_files / search_code / read_file / run_tests / write_file / show_diff`。6 个工具，能跑通闭环（33 runs / 87.9% 成功率），但有三个硬伤：

1. **只能全量覆写文件** — `write_file` 要求模型输出完整文件。修一行代码要重新生成整个模块，浪费 token 且容易引入错误
2. **破坏性写入无保护** — 写错了回不去，只能从头重来。Claude Code 每次 Edit 前自动 snapshot
3. **测试失败信息是 raw dump** — 模型收到几百行 pytest traceback，真正有用的只有最后几行，被 `summarize_for_model` 截断后往往看不到关键断言

这些不是展示层问题，是直接限制修复成功率的问题。本周参照 Claude Code 的 harness 设计逐一解决。

## 5 个交付物

### 交付物 1：`edit_file` — 精确部分编辑

当前 `write_file`：模型输出 300 行文件修 1 行 → 浪费 token 且容易出错。Claude Code 用 `Edit(old_string, new_string)` 做精确替换。

新增 `edit_file` 工具：
- 参数：`relative_path`, `old_string`, `new_string`
- 语义：在文件中找到 `old_string` 的**精确匹配**（含缩进），替换为 `new_string`
- 如果 `old_string` 不唯一 → 返回 error + 列出匹配行号 + 上下文，让模型提供更精确的 `old_string`
- 如果 `old_string` 不存在 → 返回 error
- 复用现有 `write_file` 的路径安全校验
- 替换成功时返回结构化信息：`replacement_count=1`、目标行号、`old_length/new_length`，方便 trace 和模型复盘

涉及文件：
- `app/tools/edit_file.py` — 新文件
- `app/agent/tool_definitions.py` — 注册 `edit_file` 工具 schema
- `app/agent/tool_executor.py` — 分发 `edit_file`

### 交付物 2：Checkpoint + Undo

Claude Code harness：每次 Edit 前记录文件状态，出问题可以回退。当前 agent：`write_file` 直接覆写，不可逆。

实现方案：
- `write_file` 和 `edit_file` 执行前，自动把目标文件复制到 `.agent_checkpoints/step_N/<relative_path>`，保留目录结构
- `ToolExecutor` 中维护写操作 step 计数，每次写操作前保存“写入前状态”
- 新增 `undo` 工具：回滚最近一次写操作影响的文件，恢复到该写操作前的 checkpoint，返回回退了哪些文件
- `.agent_checkpoints/` 是 agent 内部状态，不应污染 `show_diff`、最终 `patch.diff` 或对外评测产物
- Agent 循环里 `run_tests` 失败后，模型可以选择 `undo` + 重新尝试，而不是在错误基础上叠错误

涉及文件：
- `app/agent/tool_executor.py` — checkpoint 逻辑 + `undo` 分发
- `app/agent/tool_definitions.py` — 注册 `undo` 工具 schema
- `app/tools/show_diff.py` — 过滤 `.agent_checkpoints/`
- agent 循环无改动（模型自己决定何时 undo）

### 交付物 3：结构化测试失败信息

当前 `run_tests` 失败时，`summarize_for_model` 把整个 pytest 输出截断到 4000 字符。模型通常只能看到前几十行 import 错误或 fixture setup，实际的 `AssertionError` 被截掉了。

改造 `run_tests` 工具返回结构：
- 成功路径：返回现有 summary，不改
- 失败路径：解析 pytest 输出（`=== short test summary ===` 和 `FAILURES` 段的 `AssertionError`），提取：
  - 失败的测试名
  - 断言内容（expected vs actual 或 assert 行）
  - 所在文件和行号
  - 构造 `data.failure_summary`，包含 `failed_tests`、`assertion_lines`、`locations`、`short_summary`
- `summarize_for_model` 优先用 `failure_summary`，不够才用完整输出

涉及文件：
- `app/tools/run_tests.py` — 解析 pytest 输出，构造 `failure_summary`
- `app/agent/tool_executor.py` 的 `summarize_for_model` — 优先用 `failure_summary`

### 交付物 4：并行只读工具调用

当前 agent 一次一个工具。`list_files` → 等结果 → `read_file` → 等结果，5 个只读 tool call 要 5 个 API round trip。Claude Code 允许同一轮并发多个只读工具。

实现方案：
- 在 ReAct 循环中，同一轮 LLM 返回的多个 `tool_use` block：
  - 如果全是只读工具（`list_files / search_code / read_file / show_diff`）→ 并发执行（`concurrent.futures.ThreadPoolExecutor`）
  - 如果包含写入工具（`write_file / edit_file / undo`）→ 写操作前的只读工具仍可并发，写入保持顺序
- Trace 里记录并发关系（`parallel_group_id`），但回传给 LLM 的 tool result 顺序必须保持原始 `tool_use` 顺序，避免消息链错位
- 只改执行层，不改 LLM 端——模型不知道并发，它只是同一轮返回了多个 tool_use

涉及文件：
- `app/agent/llm_agent.py` — ReAct 循环中工具执行段

### 交付物 5：重跑失败 case，验证提升

工具链升级完成后，重跑之前 4 条 incomplete 的任务。对比：

- 如果有 case 因为新工具（`edit_file` 减少 token 浪费、checkpoint 允许回退重试、结构化错误帮助定位）而转为 `success` → 记入 `docs/agent_eval_summary.md` 作为升级证据
- 如果仍然失败 → 分析根因，确认是能力边界而非工具链缺陷
- 产出：升级前 vs 升级后的对比数据（成功率、平均 tool calls、平均 duration）
- 外部 LLM API 调用需要人工审批；本周允许在审批后使用真实 API 做 rerun 验证

## 不做

- 不做多模型对比（Kimi/GLM）
- 不加新 benchmark 任务
- 不做文档/展示层工作（README、case study、one-pager 等暂缓）
- 不做 Reflection / multi-agent
- 不做 prompt 优化（除非跑失败 case 时发现明显问题）

## 验收标准

| 检查项 | 达标线 |
|--------|--------|
| `edit_file` 可用 | 模型能通过 old/new string 精确编辑文件，唯一/非唯一/不存在三种路径均正确处理 |
| checkpoint + undo 闭环 | `write_file`/`edit_file` 自动 checkpoint，`undo` 可回退，workspace 不变 |
| 结构化测试失败信息 | 失败时 `failure_summary` 包含测试名、断言内容、文件行号 |
| 并行只读 | 同轮多个只读 tool_use 并发执行，trace 有并发标记 |
| 测试通过 | `python -m pytest tests/test_llm_agent.py -q` 新增 + 已有测试全部通过 |
| 升级验证 | 重跑 4 条 incomplete case，记录对比数据 |
| `git status` | 干净 |

## 当前追踪状态

| 交付物 | 当前状态 | 证据 / 下一步 |
|--------|----------|---------------|
| `edit_file` 精确部分编辑 | 已完成首版 | 已新增工具实现、LLM tool schema、executor 分发、prompt 引导；测试覆盖唯一匹配、不唯一、不存在、路径越界，以及 agent loop 自动验证 |
| Checkpoint + Undo | 已完成首版 | `write_file` / `edit_file` 写入前自动 checkpoint，`undo` 可回滚最近一次成功写操作；`.agent_checkpoints/` 已从 diff / patch 过滤 |
| 结构化测试失败信息 | 已完成首版 | `run_tests` 已返回 `data.failure_summary`（失败测试、断言行、文件行号、短摘要），`summarize_for_model` 已优先回传结构化失败摘要 |
| 并行只读工具调用 | 已完成首版 | 同轮连续只读工具会并发执行，trace 记录 `parallel_group_id`，回传给 LLM 的 tool result 顺序保持原始 `tool_use` 顺序 |
| 重跑 4 条 incomplete case | 已完成首版 | 已审批真实 API rerun：`task_132` 保持 `incomplete/no_patch` 但 tool calls `14 -> 5` 且 trace 出现并行只读；`task_054` 用正常 minimal policy 从旧受限 incomplete 转为 `success` |
| focused tests | 当前通过 | `python -m pytest tests/test_runtime_diagnostics.py tests/test_tool_executor.py tests/test_edit_file.py tests/test_llm_agent.py tests/test_write_file.py -q --basetemp .pytest_tmp_week_target` 当前为 `29 passed` |

## 推荐执行顺序

1. 先实现 `edit_file`，用单元测试覆盖唯一匹配、不唯一、不存在、路径越界。
2. 再实现 checkpoint + undo，并确认 `.agent_checkpoints/` 不进入 diff / patch。
3. 改造 `run_tests` 的结构化失败摘要，让模型优先看到关键断言。
4. 在前三项稳定后，再做并行只读工具调用；保持 trace 可审计、tool result 回传顺序稳定。
5. 最后审批外部 API 调用，重跑 4 条 incomplete case，记录升级前后对比。

## 参考

Claude Code 的 harness 设计核心原则（来自源码分析）：
- 每次写入前自动 snapshot → checkpoint
- `Edit` 工具用 `old_string` 精确匹配，不唯一时报错而非盲替
- 工具返回对模型友好的结构化信息，而非 raw dump
- 只读工具独立于写入工具，可安全并发

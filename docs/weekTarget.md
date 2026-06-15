# Week Target：Harness 深水区 — 对齐 Claude Code 执行架构

**主题：把我们 agent 的 harness 从「能工作」升级到 Claude Code 级别的工程化执行架构。6 个交付物，按对修复能力的影响从大到小排列。**

预期时间：2026-06-15 → 2026-06-22

## 背景

过去两周，agent 从 0 到 1（ReAct 循环），再从 1 到 2（edit_file / checkpoint / 并行 / 结构化失败）。当前 harness 状态：

| 能力 | 我们 | Claude Code | 差距 |
|------|------|-------------|------|
| 工作区隔离 | ✅ copy to workspace | ✅ git worktree | 路径安全够了 |
| 写入回退 | ⚠️ 手动文件复制 checkpoint | ✅ git commit + reset | 脆弱，多文件回退不可靠 |
| 行动前规划 | ❌ 直接调工具 | ✅ thinking block 先行 | 复杂 bug 容易盲改 |
| 上下文管理 | ❌ 无感知 | ✅ 接近上限时压缩旧消息 | 长任务可能丢上下文 |
| 子任务分解 | ❌ 无 | ✅ TodoWrite 拆任务 | 多文件修复一步到底 |
| 搜索能力 | ⚠️ 字面搜索 | ✅ Grep 正则 + 文件:行号:内容 | 复杂模式搜不到 |
| 工具反馈 | ⚠️ 统一截断 max_chars | ✅ 按工具类型智能截断 | 关键信息被噪音挤掉 |
| Prompt 缓存 | ❌ | ✅ 系统提示词缓存 | 纯成本优化 |

本周补齐全部 7 项差距。

## 6 个交付物（按影响从大到小）

### 交付物 1：Git 原生工作区 — 原子 checkpoint + 多文件回退

当前 checkpoint 实现：写入前 shutil.copy2 到 `.agent_checkpoints/step_N/`，undo 时 copy 回来。问题：
- 大文件每次完整复制，浪费磁盘和 IO
- 一次写入多个文件时 checkpoint 是逐个的，回退不一致
- `.agent_checkpoints/` 目录需要处处过滤（list_files / show_diff）

Claude Code 的做法：workspace 初始化时 `git init && git add -A && git commit -m "initial"`。每次写入 = `git add <file> && git commit -m "<tool_name>: <relative_path>"`。Undo = `git reset --hard HEAD~1`。Show diff = `git diff initial..HEAD`。

改造内容：
- `copy_repo_to_workspace` 后自动 `git init && git add -A && git commit --no-gpg-sign -m "initial"`
- `write_file` / `edit_file` 成功后自动 `git add <relative_path> && git commit --no-gpg-sign -m "<tool_name>: <relative_path>"`
- `undo` → `git reset --hard HEAD~1`，可连续 undo 多次
- `show_diff` → `git diff initial..HEAD`（天然排除 `.agent_checkpoints/` 因为它不在 git track 里）
- 删除现有 `.agent_checkpoints/` 目录逻辑（`_checkpoint_before_write` / `_finalize_checkpoint` / `_undo_last_write` / `_checkpoint_stack`）
- 删除 `common.py` 中 `.agent_checkpoints` 的 ignore 条目

收益：
- Checkpoint 存储从完整文件复制变成 git object delta，几乎零空间开销
- 多文件回退自然原子（git 的 commit 粒度包含当次写入的所有文件）
- show_diff 天然干净，不需要过滤忽略目录
- 免费获得完整版本历史（`git log` 可审计 agent 的所有写入）

涉及文件：
- `app/runtime/harness.py` — `copy_repo_to_workspace` 后 git init
- `app/agent/tool_executor.py` — 删除 checkpoint 逻辑，改为 git 操作（或抽到 harness）
- `app/tools/show_diff.py` — 改为 `git diff initial..HEAD`
- `app/agent/tool_definitions.py` — `undo` schema 不变（接口兼容）
- `app/tools/common.py` — 删除 `.agent_checkpoints` ignore

### 交付物 2：规划先行 — 模型行动前输出推理

当前：模型在收到任务后直接输出 `tool_use`。对于简单任务（task_019 加一个 None guard）够了。但对于复杂任务（task_024 jinja2 静态分析），模型经常先读了一堆无关文件才开始理解问题——因为它没有先停下来想。

Claude Code：模型在调用工具前先输出 thinking block（`type: "text"`），描述当前理解、计划做什么、为什么。这是模型自己生成的，不是系统注入的。

实现方案（最小改造）：
- 改 `build_system_prompt()`：明确要求模型「在调用任何工具之前，先简短分析当前情况和下一步计划。不要跳过这个步骤。」
- Agent 循环中：当 assistant response 包含 text block 时，优先把 text 作为「思考」记录到 trace，然后再处理 tool_use
- Trace 中新增 `action_type: "planning"` 的 step 类型
- **不引入额外 LLM 调用** — 规划和行动在同一轮 response 中，token 开销只增加几十个字的推理文本

验证方式：对比加 planning 前后的 agent 行为——平均 tool calls 是否降低（规划更精确）、复杂任务成功率是否提升。

涉及文件：
- `app/agent/llm_prompts.py` — system prompt 加 planning 指令
- `app/agent/llm_agent.py` — trace 记录 text block 为 planning step

### 交付物 3：上下文窗口感知 + 压缩

当前：agent 无感知上下文上限。OpenAI-compatible API 的 context window 通常 128K tokens，12 iterations × 每轮 4000 字符 tool result = ~50K 字符，一般够用。但复杂任务（读大文件 + 多次搜索 + 长 traceback）可能逼近。一旦超出，API 返回 error，agent 崩溃。

Claude Code：追踪每条消息的 token 估算，接近上限时将旧消息压缩为摘要。

实现方案（实用主义，不引入 tokenizer 依赖）：
- 在 agent 循环中维护 `context_char_estimate`：每次 append message 时累加字符数
- 设定安全阈值 `max_context_chars`（默认 80000，保守估计约 20K tokens）
- 当 `context_char_estimate > max_context_chars` 时触发压缩：
  - 保留：system prompt + 最近 3 轮对话 + 当前 user message
  - 压缩中间轮次：仅保留每轮 tool call 的 name + summary（丢弃完整 tool result）
  - 插入一条 system 注入消息：「Earlier context has been summarized. Key findings so far: ...」
- `max_context_chars` 放入 `LLMConfig`，可配置

涉及文件：
- `app/agent/llm_agent.py` — 上下文追踪 + 压缩逻辑
- `app/agent/llm_config.py` — 新增 `max_context_chars` 字段

### 交付物 4：子任务分解 — 复杂任务先拆再修

当前：agent 对多文件 bug 的典型失败模式——先修了文件 A，跑测试仍失败，再修文件 B，又失败，步步摸黑直到 iteration 耗尽。

Claude Code：用 TodoWrite 把复杂任务拆成子任务，每完成一个勾掉一个，agent 始终知道自己在哪一步、还剩什么。

实现方案（轻量版）：
- 在 system prompt 中指导模型：「遇到多步骤或跨文件修复时，先列出步骤清单，然后逐项完成。」
- 模型通过 text response 自行输出清单（如 "1. 定位根因 → 2. 修复文件A → 3. 修复文件B → 4. 验证"），后续每轮更新进度
- **不引入 TodoWrite 工具** — 避免工具膨胀。用 prompt 引导模型自主管理步骤
- 在 `_classify_final_state` 中新增 incomplete_reason：`"task_incomplete"` — 当模型明确表示任务未全部完成但主动停止时使用（区别于 `no_patch` / `max_iterations`）

涉及文件：
- `app/agent/llm_prompts.py` — system prompt 加子任务分解指导
- `app/agent/llm_agent.py` — `_classify_final_state` 新增 reason

### 交付物 5：Grep 工具 — 正则代码搜索

当前 `search_code`：传入字面字符串，`grep -F`（固定字符串匹配）。这意味着搜 `def test_\w+` 不行，搜 `import\s+os` 不行，搜 `return\s+False` 不行。

Claude Code 最常用的工具是 Grep（正则搜索），返回 `file:line:content` 格式。这对模型定位代码是质变——一次正则搜出所有匹配，模型可以批量读取相关文件，而不是逐个猜测函数名然后字面搜索。

新增 `grep` 工具：
- 参数：`pattern`（正则表达式）、`glob`（可选文件过滤，如 `*.py`）、`max_results`（默认 20）
- 实现：`grep -rnP`（或 Python `re` 遍历文件，跨平台更可靠）
- 返回：`matches: [{file, line, content}]`，带截断控制
- `search_code` 保留不删（字面搜索对新手模型更友好，两个工具互补）

涉及文件：
- `app/tools/grep.py` — 新文件
- `app/agent/tool_definitions.py` — 注册 grep 工具 schema
- `app/agent/tool_executor.py` — 分发 grep
- `app/agent/llm_prompts.py` — system prompt 提示 grep 可用于正则搜索

### 交付物 6：上下文感知的 tool result 截断

当前 `summarize_for_model`：所有工具统一截断到 `max_chars` 字符。问题：
- `read_file` 的文件内容被截断 → 模型看不到完整代码
- `run_tests` 成功的 stdout（几百行 `test_xxx PASSED`）占满空间，关键的 diff 或错误被挤掉
- `list_files` 的文件列表被截断 → 模型不知道有哪些文件

Claude Code：按工具类型智能保留/丢弃字段。

改造 `summarize_for_model`：
- `run_tests`：成功 → 仅保留 summary（"N tests passed"）；失败 → 优先保留 `failure_summary`（已在交付物 3 中实现）
- `read_file`：**不截断** — 模型需要看到完整源码才能正确编辑。如果文件超过某个上限（20000 字符），返回摘要 + 提示模型用 offset/limit 分段读取
- `list_files`：保留完整文件列表（一般不超 2000 字符），仅在不匹配的 huge repo 时截断
- `search_code` / `grep`：保留匹配行 + 文件路径，截断到 `max_matches`
- `show_diff`：不截断（diff 本身紧凑）
- `write_file` / `edit_file`：保留 summary + changed_files + checkpoint 信息，丢弃完整 old/new content 回显

涉及文件：
- `app/agent/tool_executor.py` — `summarize_for_model` 改造为按工具类型分发

---

## 不做

- 不做 Prompt caching（OpenAI-compatible 服务端自己处理，客户端不做）
- 不做 Streaming 响应
- 不做 Sub-agent 生成（多 agent 不在当前架构范围内）
- 不做 Permission system（自动化 agent 不需要）
- 不加新 benchmark 任务
- 不做文档/展示层工作
- 不做多模型对比（上周计划，本周先搁置）

## 验收标准

| 检查项 | 达标线 |
|--------|--------|
| Git 原生工作区 | `write_file`/`edit_file` 后 git log 有对应 commit，`undo` = git reset，`show_diff` = git diff，删除旧 checkpoint 代码 |
| 规划先行 | agent 在调工具前输出推理文本，trace 有 planning step 记录 |
| 上下文压缩 | 超过阈值时自动压缩旧消息，不丢失关键信息 |
| 子任务分解 | 复杂任务模型自动列出步骤并按步骤推进 |
| Grep 工具 | 正则搜索返回 file:line:content，与 search_code 共存 |
| 智能截断 | 按工具类型差异化截断，read_file 不截断，成功测试只保留摘要 |
| 已有测试 | `python -m pytest tests/test_llm_agent.py tests/test_edit_file.py tests/test_tool_executor.py -q` 全部通过 |
| 升级验证 | 在 10 条任务（含 2 条之前失败的）上跑升级版 agent，对比升级前后 |
| `git status` | 干净 |

## 推荐执行顺序

1. **Git 原生工作区** — 先做，因为会删旧 checkpoint 代码，影响面最大
2. **智能截断** — 在 git 改动后的工具层上改，依赖最少
3. **Grep 工具** — 独立新文件，不碰现有逻辑
4. **规划先行** — prompt 改动 + trace 改动，代码量小但需配合前面的工具变更
5. **子任务分解** — 依赖规划先行，也是 prompt 改动为主
6. **上下文压缩** — 最后做，依赖全部工具就位后才知道哪些消息需要优先保留
7. **升级验证** — 最后跑 10 条，记录对比

# Agent Case Studies

本文档只记录 LLM agent 的真实运行案例。规则版 baseline 的历史案例仍保留在 [docs/case_studies.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/case_studies.md)。

## Case 1：DeepSeek Agent 修复 CRLF ANSI 行解析

**任务**：`task_010`  
**来源**：`Textualize/rich#4090`  
**模型**：`deepseek-chat`  
**policy**：`llm_deepseek_minimal`  
**run_id**：`run_20260614T080459321811Z_6319`  
**结果**：`success`

### 问题

任务要求修复 CRLF 行尾解析问题。旧实现会把 `\r\n` 中的 `\r` 当作终端回车覆盖符处理，导致 CRLF 文本被解析成空白行。

### Agent 行为

这次 run 的关键步骤是：

1. `list_files` 查看仓库结构。
2. `read_file` 读取 `rich_ansi_repo/ansi.py`。
3. `read_file` 读取 `tests/test_ansi.py`。
4. `write_file` 修改 `rich_ansi_repo/ansi.py`。
5. `run_tests` 执行 `python -m pytest tests/test_ansi.py -q`。
6. `show_diff` 查看最终 patch。

完整 trace 见：

- [trace.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_010/run_20260614T080459321811Z_6319/trace.json)

### Patch

核心改动是在 `AnsiDecoder.decode_text()` 里先把 CRLF 归一化：

```python
terminal_text = terminal_text.replace("\r\n", "\n")
```

对应 diff：

- [patch.diff](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_010/run_20260614T080459321811Z_6319/patch.diff)

### 验证结果

`run_tests` 返回：

```text
测试命令执行成功，目标测试已通过。
```

运行摘要：

- final_status：`success`
- total_tool_calls：`6`
- modified_files：`rich_ansi_repo/ansi.py`
- duration_sec：`19.2406`

### 价值

这个案例是项目方向矫正后的第一条真实 LLM agent 成功 run。它说明当前项目已经不只是 rule-based benchmark solver，而是具备了可复盘的 LLM tool-use 修复闭环。

同时，这个案例也展示了验证层的价值：agent 不靠自然语言自称完成，而是通过 `run_tests` 和 `show_diff` 给出可审计证据。

## Case 2：Jinja 静态分析控制流修复

**任务**：`task_024`  
**来源**：`pallets/jinja#2069`  
**模型**：`deepseek-chat`  
**policy**：`llm_deepseek_minimal`  
**run_id**：`run_20260614T113402398598Z_5993`  
**结果**：`success`

### 问题

任务要求修复模板变量静态分析误报。旧实现先收集所有分支中被赋值的变量，却又把已经赋值的变量重新加入 `undeclared`，导致变量在所有分支都被 `set` 后仍被误判为未声明。

### Agent 行为

这次 run 的关键步骤是：

1. `list_files` 查看仓库结构。
2. `read_file` 读取 `jinja_meta_repo/meta.py`。
3. `read_file` 读取 `tests/test_meta.py`。
4. `run_tests` 先观察失败测试。
5. `write_file` 修改 `jinja_meta_repo/meta.py`。
6. `run_tests` 验证修复后的测试结果。

完整 trace 见：

- [trace.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_024/run_20260614T113402398598Z_5993/trace.json)

### Agent 决策关键点

Agent 没有尝试改测试，也没有加特殊 case，而是先读实现再读测试，把问题定位到 `find_undeclared_variables()` 中的反向循环。这个循环和前面 `assigned_variables.update()` 的语义冲突：前者已经把分支赋值变量视为声明，后者又把这些变量塞回 `undeclared`。

### Patch

核心改动是删除把已赋值变量重新加入 `undeclared` 的循环：

```python
undeclared = {name for name in used_variables if name not in assigned_variables}
return undeclared
```

对应 diff：

- [patch.diff](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_024/run_20260614T113402398598Z_5993/patch.diff)

### 验证结果

- final_status：`success`
- total_tool_calls：`6`
- modified_files：`jinja_meta_repo/meta.py`
- post_test_summary：`测试命令执行成功，目标测试已通过。`

### 价值

这个案例比简单边界值修复更像真实 coding agent 能力展示：agent 需要理解“被所有分支赋值”与“未声明变量”之间的静态分析关系，而不是只做字符串替换。

## Case 3：Click 负向 Boolean Flag 默认值修复

**任务**：`task_016`  
**来源**：`pallets/click#3111`  
**模型**：`deepseek-chat`  
**policy**：`llm_deepseek_minimal`  
**run_id**：`run_20260614T113438108363Z_4434`  
**结果**：`success`

### 问题

任务要求修复负向 boolean flag 在未显式提供时错误覆盖默认值的问题。旧实现里存在一个特殊分支：当 `default=True` 且 `flag_value=False` 时，即使用户没有提供 flag，也会返回 `False`，导致默认值失效。

### Agent 行为

这次 run 的关键步骤是：

1. `list_files` 查看仓库结构。
2. `read_file` 读取 `click_flag_repo/core.py`。
3. `read_file` 读取 `tests/test_flags.py`。
4. `read_file` 读取 `click_flag_repo/__init__.py`，确认导出路径。
5. `write_file` 修改 `click_flag_repo/core.py`。
6. `run_tests` 执行 `python -m pytest tests/test_flags.py -q`。
7. `show_diff` 查看最终 patch。

完整 trace 见：

- [trace.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_016/run_20260614T113438108363Z_4434/trace.json)

### Agent 决策关键点

Agent 的关键判断是区分“用户显式提供 flag”和“flag 的默认值”。负向 flag 的 `flag_value=False` 只有在 `provided=True` 时才应该生效；未提供时必须返回 `default`。因此修复不是新增复杂条件，而是删除错误的特殊分支，让函数回到清晰的两段逻辑。

### Patch

核心改动如下：

```python
if provided:
    return flag_value
return default
```

对应 diff：

- [patch.diff](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_016/run_20260614T113438108363Z_4434/patch.diff)

### 验证结果

- final_status：`success`
- total_tool_calls：`7`
- modified_files：`click_flag_repo/core.py`
- post_test_summary：`测试命令执行成功，目标测试已通过。`

### 价值

这个案例体现的是 API 行为语义修复，而不是崩溃修复。它适合展示 agent 能否读懂 CLI flag 的默认值、显式输入和负向选项之间的关系。

## Case 4：Click Confirm 输出 ANSI 清理

**任务**：`task_093`  
**来源**：`pallets/click#3572`  
**模型**：`deepseek-chat`  
**policy**：`llm_deepseek_minimal`  
**run_id**：`run_20260614T113509337696Z_0010`  
**结果**：`success`

### 问题

任务要求修复 `confirm(color=False)` 时仍然输出 ANSI 控制序列的问题。旧实现中 `render_echo_output()` 已经在 `color=False` 时调用 `strip_ansi()`，但 `render_confirm_output()` 直接使用原始 message，导致两个输出路径行为不一致。

### Agent 行为

这次 run 的关键步骤是：

1. `list_files` 查看仓库结构。
2. `read_file` 读取 `click_confirm_repo/prompts.py`。
3. `read_file` 读取 `tests/test_prompts.py`。
4. `run_tests` 先确认目标测试失败。
5. `write_file` 修改 `click_confirm_repo/prompts.py`。
6. `run_tests` 验证 3 个回归测试全部通过。

完整 trace 见：

- [trace.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_093/run_20260614T113509337696Z_0010/trace.json)

### Agent 决策关键点

Agent 没有重新实现 ANSI parser，而是复用同文件里已有的 `strip_ansi()` 和 `render_echo_output()` 语义。这是一个很重要的工程判断：同类输出路径应该共享同一条颜色禁用规则，避免 confirm 和 echo 行为分叉。

### Patch

核心改动是让 confirm 在 `color=False` 时和 echo 一样清理 ANSI：

```python
rendered = message if color else strip_ansi(message)
return f"{rendered} [y/N]: {user_input}\n"
```

对应 diff：

- [patch.diff](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_093/run_20260614T113509337696Z_0010/patch.diff)

### 验证结果

- final_status：`success`
- total_tool_calls：`6`
- modified_files：`click_confirm_repo/prompts.py`
- post_test_summary：`测试命令执行成功，目标测试已通过。`

### 价值

这个案例展示了 agent 对“相邻已有实现”的利用能力：不是硬编码测试期望，而是把 confirm 路径对齐到 echo 路径已经存在的颜色处理语义。

## 其他成功记录

除上述 4 条详细案例外，当前还记录了 1 条真实 LLM agent 成功 run：

| Task | 来源 | 核心修复 | Run |
| --- | --- | --- | --- |
| `task_019` | `dateutil/dateutil#1432` | `UTC/GMT` 无 offset 时回落为零偏移，避免对 `None` 做符号变换 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_019/run_20260614T113332817562Z_3323/result.json) |

完整汇总见 [docs/agent_eval_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_eval_summary.md)。

## 边界案例：测试已绿但无 patch，不误报成功

**任务**：`task_132`  
**来源**：`Textualize/rich#2411`  
**结果**：`incomplete`  
**run_id**：`run_20260614T115513496398Z_8231`

这条 challenge 任务的测试在 agent 修改前已经通过。Agent 读取了代码、测试和 README，多次运行测试并确认当前实现已经满足回归测试，但没有生成任何 patch。

关键产物：

- [trace.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_132/run_20260614T115513496398Z_8231/trace.json)
- [result.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_132/run_20260614T115513496398Z_8231/result.json)

这个案例的价值不在于修复成功，而在于暴露了一个重要边界：如果任务 repo 已经处于测试通过状态，agent 不应仅凭测试绿就宣称修复成功。当前运行结果保持 `incomplete`，`patch_applied = false`，说明验证逻辑避免了“无实际 patch 的成功误报”。

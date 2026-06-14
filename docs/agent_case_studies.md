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

## 小样本成功记录

除 Case 1 外，本轮又补了 4 条真实 LLM agent 成功 run：

| Task | 来源 | 核心修复 | Run |
| --- | --- | --- | --- |
| `task_019` | `dateutil/dateutil#1432` | `UTC/GMT` 无 offset 时回落为零偏移，避免对 `None` 做符号变换 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_019/run_20260614T113332817562Z_3323/result.json) |
| `task_024` | `pallets/jinja#2069` | 删除把已赋值变量重新加入 `undeclared` 的错误循环 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_024/run_20260614T113402398598Z_5993/result.json) |
| `task_016` | `pallets/click#3111` | 修复负向 boolean flag 在未显式提供时错误覆盖默认值的问题 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_016/run_20260614T113438108363Z_4434/result.json) |
| `task_093` | `pallets/click#3572` | `confirm(color=False)` 时复用 ANSI 清理逻辑，避免颜色码残留 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_093/run_20260614T113509337696Z_0010/result.json) |

这 5 条 run 的共同点是：

- 都由 `scripts/run_issue_agent.py` 触发；
- 都使用 `llm_deepseek_minimal`；
- 都产生了 `trace.json / result.json / patch.diff`；
- 都修改了目标源文件；
- 都通过了任务自带测试命令。

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

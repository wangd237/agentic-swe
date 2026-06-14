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


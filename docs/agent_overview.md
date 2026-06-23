# Agent Overview

本文档描述当前项目里的 LLM coding agent 主体。Benchmark、frozen set、stability recheck 都是验证层；本页只回答一个问题：这个 agent 本身如何工作。

## 1. 定位

当前 agent 面向真实 GitHub issue 派生的本地任务。给定一条 task，它会在隔离 workspace 中完成：

```text
读 issue -> 观察仓库 -> 读取相关文件 -> 写入 patch -> 跑测试验证 -> 查看 diff -> 输出总结
```

当前主入口是：

- `scripts/run_issue_agent.py`
- `app/agent/llm_agent.py`
- `optimization/policy_versions/llm_deepseek_minimal.json`

provider 抽象是 OpenAI-compatible Chat Completions。DeepSeek 只是当前 policy 示例；后续切换 Kimi、GLM 或其他兼容服务时，只需要换 policy 中的 `llm_api_key_env / llm_base_url_env / llm_model` 等字段。

## 2. 双轨结构

项目现在有两类 agent：

| Agent | 角色 | 入口 |
| --- | --- | --- |
| LLM coding agent | 当前主角，负责展示真实工具调用与修复闭环 | `scripts/run_issue_agent.py` |
| Rule-based baseline | 稳定下限与对比对象 | `scripts/run_single_task.py` |

这不是两套互相竞争的系统。Rule-based baseline 继续保留，因为它提供了稳定、可复现的对照；LLM agent 是现在要展示的主体。

## 3. 工具集合

LLM agent 当前有 11 项工具层能力：10 个模型可调用工具，加上 git 原生 checkpoint 作为写入/回滚底座。

| 工具 | 作用 |
| --- | --- |
| `list_files` | 查看仓库文件结构 |
| `search_code` | 搜索关键代码或错误文本 |
| `grep` | 用正则搜索代码并返回匹配行 |
| `read_file` | 读取代码、测试或配置 |
| `run_tests` | 执行任务测试命令 |
| `write_file` | 写入完整文件内容 |
| `edit_file` | 用 `old_string` / `new_string` 做精确局部替换 |
| `show_diff` | 查看 workspace 相对原始 repo 的变更 |
| `undo` | 回滚最近一次写入或编辑 |
| `python_repl` | 受控执行单表达式，查询第三方库对象行为 |
| git checkpoint | 每次成功写入后自动提交 workspace，`show_diff` 基于 `initial..HEAD`，`undo` 通过原生 git reset 回到上一 checkpoint |

工具返回统一结构，便于 trace 落盘和模型继续决策。

## 4. 验证策略

LLM agent 不只看模型最后一句话。它会跟踪每次 `write_file` 后的 workspace generation：

- 每次成功 `write_file`，generation 增加。
- 只有当前 generation 被 `run_tests` 验证通过，最终状态才允许是 `success`。
- 如果模型写完文件后直接停止，系统会自动执行 `show_diff` 和 `run_tests`，并把结果回喂给模型继续修正或确认。

这避免了一个常见误判：模型先跑过一次测试，之后又改了文件，但没有重新验证，却被标成成功。

## 5. 运行产物

每次运行都会落盘：

- `task.json`
- `trace.json`
- `result.json`
- `patch.diff`
- `summary.md`

这些产物让一次 agent run 可以被复盘、比较和收录为 case study。

## 6. 首次真实 LLM Run

当前第一条真实 DeepSeek run：

- task：`task_010`
- run：`run_20260614T080459321811Z_6319`
- policy：`llm_deepseek_minimal`
- model：`deepseek-chat`
- final_status：`success`
- total_tool_calls：`6`
- modified_files：`rich_ansi_repo/ansi.py`
- trace：[trace.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_010/run_20260614T080459321811Z_6319/trace.json)
- result：[result.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_010/run_20260614T080459321811Z_6319/result.json)
- patch：[patch.diff](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_010/run_20260614T080459321811Z_6319/patch.diff)

这次 run 已经跑通完整链路：读取文件、写入 patch、运行测试、查看 diff、输出原因分析。

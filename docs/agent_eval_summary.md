# Agent Eval Summary

本文档记录当前 LLM coding agent 的小样本真实运行结果。目标不是替代完整 benchmark，而是为求职展示提供一个清晰、可审计的 agent 能力快照。

## 1. Run 设置

- agent：OpenAI-compatible LLM coding agent
- policy：`llm_deepseek_minimal`
- model：`deepseek-chat`
- runner：`scripts/run_issue_agent.py`
- 样本数：`5`
- 样本选择原则：文件少、测试明确、覆盖不同库和缺陷类型

运行命令形态：

```bash
python scripts/run_issue_agent.py --task benchmarks/tasks/<task_id>.json --policy optimization/policy_versions/llm_deepseek_minimal.json
```

## 2. 结果表

| Task | Repo / Issue | 缺陷类型 | Status | Tool calls | Modified file | Run |
| --- | --- | --- | --- | ---: | --- | --- |
| `task_010` | `Textualize/rich#4090` | CRLF ANSI 行解析 | `success` | 6 | `rich_ansi_repo/ansi.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_010/run_20260614T080459321811Z_6319/result.json) |
| `task_019` | `dateutil/dateutil#1432` | UTC/GMT 零偏移回落 | `success` | 5 | `dateutil_tz_repo/tz.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_019/run_20260614T113332817562Z_3323/result.json) |
| `task_024` | `pallets/jinja#2069` | 分支赋值静态分析 | `success` | 6 | `jinja_meta_repo/meta.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_024/run_20260614T113402398598Z_5993/result.json) |
| `task_016` | `pallets/click#3111` | 负向 boolean flag 默认值 | `success` | 7 | `click_flag_repo/core.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_016/run_20260614T113438108363Z_4434/result.json) |
| `task_093` | `pallets/click#3572` | confirm 输出 ANSI 清理 | `success` | 6 | `click_confirm_repo/prompts.py` | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_093/run_20260614T113509337696Z_0010/result.json) |

## 3. 汇总指标

| 指标 | 当前结果 |
| --- | --- |
| 主样本任务数 | `5` |
| 主样本成功数 | `5` |
| 主样本成功率 | `100%` |
| 覆盖库数 | `4` (`rich`, `dateutil`, `jinja`, `click`) |
| 平均工具调用数 | `6.0` |
| 所有成功是否有 patch | `yes` |
| 所有成功是否通过测试验证 | `yes` |

## 4. LLM Agent vs Rule-based Baseline

| Task | LLM status | LLM tool calls | Baseline status | Baseline tool calls | 观察 |
| --- | --- | ---: | --- | ---: | --- |
| `task_010` | `success` | 6 | `success` | 9 | LLM 独立定位 CRLF 根因，工具调用更少 |
| `task_019` | `success` | 5 | `success` | 10 | LLM 直接修复 UTC/GMT 无 offset 语义 |
| `task_024` | `success` | 6 | `success` | 9 | LLM 能处理轻量静态分析误判 |
| `task_016` | `success` | 7 | `success` | 12 | LLM 能解释负向 flag 与 default 的交互 |
| `task_093` | `success` | 6 | `success` | 10 | LLM 复用 echo 路径的 ANSI 清理语义 |

这组对比的重点不是证明 LLM 一定优于规则版 baseline，而是说明项目已经具备清晰双轨结构：LLM agent 是展示主角，rule-based solver 是稳定参照。

## 5. 扩展样本

| Task | Repo / Issue | 缺陷类型 | Status | Tool calls | Run |
| --- | --- | --- | --- | ---: | --- |
| `task_036` | `python-jsonschema/jsonschema#1121` | hostname 格式检查异常回落 | `success` | 5 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_036/run_20260614T115358297399Z_9685/result.json) |
| `task_099` | `pallets/jinja#2108` | macro include generator repr | `success` | 6 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_099/run_20260614T115439071151Z_9032/result.json) |
| `task_132` | `Textualize/rich#2411` | Windows-like legacy console 编码边界 | `incomplete` | 14 | [result](/E:/My_Projects/agentic-software-engineering-roadmap/logs/trajectories/task_132/run_20260614T115513496398Z_8231/result.json) |

`task_132` 是当前最有价值的边界案例：测试一开始就已经通过，agent 没有生成 patch，最终状态保持 `incomplete`。这说明当前成功判定不会因为“测试通过”就误报修复成功，而是还要求有实际 patch 和当前 generation 的验证证据。

后续新 run 会在 `result.json` 中写入 `incomplete_reason`，用于区分 `no_patch`、`failed_tests`、`max_iterations`、`no_tests_run`、`unverified_patch` 等失败或边界类型。

## 6. 观察

这 5 条任务覆盖了不同类型的修复：

- 文本解析边界：`task_010`
- 时区偏移语义：`task_019`
- 静态分析控制流：`task_024`
- CLI flag 默认值：`task_016`
- CLI 输出 ANSI 清理：`task_093`

当前最重要的结论是：LLM agent 已经不只是跑通单个 demo，而是在多个库、多类缺陷上完成了可审计的工具调用、patch 写入和测试验证闭环。

## 7. 当前边界

这仍然是小样本结果，不应夸大成完整 benchmark 通过率。下一步应该补：

- 1 条更复杂的跨文件或更长上下文任务；
- 把失败分类汇总进 README / case study，使 `incomplete_reason` 能直接服务求职展示。

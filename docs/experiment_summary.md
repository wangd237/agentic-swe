# 实验摘要

本文档是当前项目的实验导读层。完整历史流水账仍保留在 [docs/results.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/results.md) 和 [docs/optimization_log.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/optimization_log.md)，但当前对外叙事以 LLM coding agent 为主。

## 1. 实验目标

当前目标是验证一个面向真实 GitHub issue 的 coding agent 是否能完成端到端修复闭环：

```text
读 issue -> 搜代码 -> 定位根因 -> 写 patch -> 跑测试 -> 记录 trace/result/diff
```

benchmark、frozen set、规则版 baseline 和 stability recheck 都是验证底座。它们的作用是证明 agent 不是孤立 demo，而不是替代 agent 成为项目主角。

## 2. 核心结论

- LLM agent 已经在 `5` 条主样本真实 issue 派生任务上完成 `5 / 5` success。
- 每条成功样本都有可审计产物：`trace.json / result.json / patch.diff`。
- 扩展样本中还有 `2` 条 success 和 `1` 条有价值的 `incomplete` 边界案例。
- 当前成功判定要求有实际 patch，并且当前 workspace generation 已通过测试验证。
- `incomplete_reason` 已进入结果 schema，可区分无 patch、测试失败、达到迭代上限等边界类型。
- 规则版 baseline 继续保留为稳定参照，而不是求职展示主角。

## 3. LLM Agent 小样本快照

| 维度 | 当前值 |
| --- | --- |
| 主样本任务数 | `5` |
| 主样本成功数 | `5` |
| 覆盖库 | `rich`, `dateutil`, `jinja`, `click` |
| 平均工具调用数 | `6.0` |
| 当前 policy | `llm_deepseek_minimal` |
| provider 抽象 | OpenAI-compatible |
| 关键产物 | `trace.json / result.json / patch.diff` |

完整表格见 [docs/agent_eval_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_eval_summary.md)。

## 4. 代表性观察

### 成功不是模型自称

Agent 的最终状态不依赖模型最后一句自然语言，而是依赖：

- 是否有实际 diff；
- `run_tests` 是否通过；
- 测试结果是否对应当前 workspace generation。

这避免了“先跑过测试，后改文件却没复测”的假成功。

### 边界案例有展示价值

`task_132` 的测试在修改前已经通过，agent 没有生成 patch，因此结果保持 `incomplete`。这类案例很适合面试时说明：系统不会把“无实际修复”包装成成功。

### Baseline 是参照，不是主角

规则版 baseline 在正式任务集上很稳定，说明验证底座扎实。但当前求职目标需要展示的是 LLM agent 的工具调用、决策轨迹和失败恢复能力。

## 5. 验证底座快照

| 维度 | 当前值 |
| --- | --- |
| 正式真实任务数 | `66` |
| challenge 任务数 | `6` |
| 来源生态数 | `16` |
| 规则版 baseline 策略 | `improved_v71` |
| frozen_40 连续无回归版本数 | `8` |

这些数字继续作为可信度证据保留，但不再作为下一阶段主要增长目标。

## 6. 当前缺口

- 需要 1 条更复杂的 LLM agent 案例，最好是跨文件或更长上下文任务。
- 需要把 `incomplete_reason` 汇总进 case study，让失败分类成为展示资产。
- README 首屏还可以继续压缩，让 agent 能力比验证底座更醒目。

## 7. 推荐阅读路径

1. [README.md](/E:/My_Projects/agentic-software-engineering-roadmap/README.md)
2. [docs/agent_overview.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_overview.md)
3. [docs/agent_eval_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_eval_summary.md)
4. [docs/agent_case_studies.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_case_studies.md)
5. [docs/architecture.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/architecture.md)

## 8. 一句话总结

当前实验已经从“benchmark 是否成熟”切换到“LLM coding agent 是否能被可信展示”：主角是 agent，验证底座是证据。

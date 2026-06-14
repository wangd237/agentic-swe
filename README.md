# Agentic SWE

一个面向真实 GitHub issue 的 OpenAI-compatible coding agent 项目，当前正在从“规则版 benchmark solver”收口成“LLM agent + 验证底座”的结构。

它不只是在本地跑一个“会改代码的 agent”，而是把真实 issue 任务构造、隔离执行、轨迹落盘、批量评测、策略优化、冻结集回归和稳定性复跑串成了一条完整闭环。

## 核心结果

### Agent 能力

| 指标 | 当前结果 |
| --- | --- |
| 已记录 LLM agent run | `33` |
| 成功任务完成数 | `29 / 33` |
| 可审计成功案例数 | `29` 条 trace / result / patch |
| Challenge / 边界样本 | `7` 条，另有受限策略 failure-taxonomy run |
| 已覆盖生态 | `9` 个（`rich`, `dateutil`, `jinja`, `click`, `jsonschema`, `packaging`, `tomlkit`, `watchfiles`, `anyio`） |
| 平均工具调用数 | `6.7` |
| 当前 LLM agent 策略 | `llm_deepseek_minimal` |
| 当前结论 | `Agent 已在 33 条真实 issue 派生任务上完成可审计运行，其中 29 条成功，并覆盖 no_patch / max_iterations 两类 incomplete reason` |

### 验证底座

> | 指标 | 当前结果 |
> | --- | --- |
> | 正式真实任务数 | `66` |
> | challenge 任务数 | `6` |
> | 来源生态数 | `16` |
> | 规则版 baseline 正式集成功率 | `100%` |
> | 规则版 baseline 正式集测试通过率 | `100%` |
> | 当前规则版 baseline 策略 | `improved_v71` |
> | `frozen_40` 连续无回归版本数 | `8` |
> | `frozen_40` 当前最小验证均值耗时 | `0.5794s` |

基于 [docs/agent_eval_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_eval_summary.md) 和 [docs/agent_case_studies.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_case_studies.md)，当前 agent 已完成从真实任务定义、代码定位、补丁生成、测试验证到结果落盘的完整闭环；验证底座继续作为 baseline、回归保护和规模化评测证据。

## Agent Run Loop

```text
GitHub issue / semi-real task
          |
          v
   manifest 选题与任务定义
          |
          v
   repo workspace 隔离复制
          |
          v
   agent loop
   (读文件 / 搜索 / 测试 / patch / diff)
          |
          v
   轨迹与结果落盘
   (task.json / trace.json / result.json / patch.diff)
```

## 项目特点

- LLM agent 通过 OpenAI-compatible tool calling 调用现有工具；当前策略示例使用 DeepSeek，后续可切换到 Kimi、GLM 等兼容服务。
- Agent 修复过程不是只看最终 diff，而是落盘 `trace.json` / `result.json` / `patch.diff`，可复盘每次读文件、搜索、测试、写入和 diff 检查。
- Agent 的成功判定依赖 `run_tests` 和最终 `final_status`，不是让模型自称完成。
- harness 是一等公民：强调工作区隔离、路径边界、产物契约和批量复现能力。
- 任务不是纯 synthetic demo，而是 `66` 条来自真实开源 issue 的 `semi_real` benchmark。
- 规则版 baseline 不是废弃资产，而是用于和 LLM agent 对比的稳定下限。
- 优化不是“凭感觉调 prompt”，规则版 baseline 已版本化到 `improved_v71`，并且有冻结集无回归验证与稳定性复跑。
- 评测不是只有成功率，还包括 taxonomy、耗时、步数、稳定性复跑和 maturity 审计。
- 性能治理现在还支持环境基线快照，能先把“环境变慢”和“策略变慢”做一层拆分。
- challenge 集独立管理：系统边界题可以单独运行和展示，而不污染正式 benchmark 口径。

## 快速开始

安装依赖：

```bash
python -m pip install -r requirements.txt
```

配置 LLM provider：

```bash
cp .env.example .env
```

然后在 `.env` 中填入一个 OpenAI-compatible provider 的 API key / base URL / model。当前仓库提供 DeepSeek、Kimi、GLM 和通用 OpenAI-compatible policy 示例；真实 key 不应提交。

运行最小 LLM agent 入口：

```bash
python scripts/run_issue_agent.py --task benchmarks/tasks/task_010.json --policy optimization/policy_versions/llm_deepseek_minimal.json
```

说明：

- 当前 `scripts/run_issue_agent.py` 已经接入最小 LLM tool-use 闭环
- 工具层直接复用现有 `list_files / search_code / read_file / run_tests / write_file / show_diff`
- LLM 输出预算默认 `8000` tokens，避免 `write_file` 写完整文件时被过早截断
- Agent 对 `write_file` 后的 workspace generation 做验证跟踪，未验证的新改动不会被标记为 success
- 当前 DeepSeek 策略从 `.env` 或当前进程环境读取 `DEEPSEEK_API_KEY / DEEPSEEK_BASE_URL / DEEPSEEK_MODEL`，变量示例见 `.env.example`
- Kimi / GLM 等兼容服务可复制 `optimization/policy_versions/llm_openai_compatible_template.json`，或直接使用 `llm_kimi_minimal.json` / `llm_glm_minimal.json` 并配置对应环境变量
- 规则版入口仍然保留，用作 baseline 对比

规则版 baseline 单任务运行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_128.json --policy optimization/policy_versions/improved_v71.json
```

批量评测并自动附带稳定性检查与 maturity 审计：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v71.json --run-label frozen20_v71_pipeline --stability-check --stability-repetitions 3 --stability-manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json
```

运行 challenge 任务集：

```bash
python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v71.json --run-label challengev71
```

单独做同策略稳定性复跑：

```bash
python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v71.json --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --repetitions 3 --run-label frozen40_v71_stability
```

采集当前机器的环境基线快照：

```bash
python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines
```

## LLM Agent 小样本结果

| 指标 | 当前结果 |
| --- | --- |
| 已记录 LLM run | `33` |
| success | `29` |
| incomplete | `4` |
| 当前成功率 | `87.9%` |
| challenge / boundary run | `7` |
| incomplete reason | `no_patch`, `max_iterations` |
| 平均工具调用数 | `6.7` |

完整小样本结果见 [docs/agent_eval_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_eval_summary.md)。

当前样本里，`task_132` 是一个有价值的边界案例：测试初始即通过、agent 没有生成 patch，最终保持 `incomplete/no_patch`，避免把“无实际修复”误报为成功。新增受限策略 run `task_054` 产生 `incomplete/max_iterations`，用于验证失败分类不是只有一种。

## 验证底座代表性案例

- `task_024` `pallets/jinja#2069`
  - 不是简单 if 修补，而是模板变量在分支赋值场景下的控制流语义分析。
- `task_036` `python-jsonschema/jsonschema#1121`
  - 体现了从“测试失败”到“异常回落语义修复”的典型优化路径，首个通过版本是 `improved_v17`。
- `task_122` `fsspec/filesystem_spec#979`
  - 当前第 `61` 条正式任务，补齐了 `unstrip_protocol()` 在前缀保护场景下错误返回原路径的问题。
- `task_123` `agronholm/anyio#1109`
  - 当前第 `62` 条正式任务，把重复进入同一个 `TaskGroup` 时泄漏内部 `AttributeError` 的问题收口为受控 `RuntimeError`。
- `task_124` `agronholm/anyio#1111`
  - 当前第 `63` 条正式任务，补齐了 `_deliver_cancellation` 对已完成 task 的清理逻辑，避免 cancellation spin。
- `task_125` `agronholm/anyio#1113`
  - 当前第 `64` 条正式任务，补齐了 `from_thread.check_cancelled()` 在已取消上下文中的取消语义。
- `task_128` `agronholm/anyio#82`
  - 当前第 `65` 条正式任务，补齐了 asyncio / curio backend 在嵌套 task group 场景下泄漏取消异常的问题。
- `task_129` `agronholm/anyio#88`
  - 当前第 `66` 条正式任务，补齐了 asyncio backend 下父任务在子任务失败后被额外取消的问题。
- `task_126` `samuelcolvin/watchfiles#266`
  - 当前首条 challenge 任务，用来展示 `ignore_permission_denied` 相关边界题的独立承载方式。
- `task_127` `samuelcolvin/watchfiles#110`
  - 当前第 `2` 条 challenge 任务，用来承载 Windows `Ctrl+C` / watcher 停止语义这类 hard case 边界题。
- `task_130` `samuelcolvin/watchfiles#169`
  - 当前第 `3` 条 challenge 任务，用来承载 WSL / Docker / Linux-like 环境下 `metadata-write` 事件被错误过滤、从而不触发 reload 的边界题。
- `task_131` `samuelcolvin/watchfiles#215`
  - 当前第 `4` 条 challenge 任务，用来承载编辑器保存行为下 watch event 语义的边界题。
- `task_132` `Textualize/rich#2411`
  - 当前第 `5` 条 challenge 任务，用来承载 Windows-like legacy 编码流上的字符降级边界题。
- `task_133` `Textualize/rich#2457`
  - 当前第 `6` 条 challenge 任务，用来承载 Windows-like legacy console 下 `no_color` 被忽略的颜色禁用边界题。

完整任务索引见 [docs/benchmark_registry.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/benchmark_registry.md)。

challenge 集说明见 [docs/challenge_set.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/challenge_set.md)。

challenge 候选短名单见 [docs/challenge_shortlist.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/challenge_shortlist.md)。

## 项目结构

```text
app/
  agent/        # agent loop、policy、patch strategy
  runtime/      # harness、workspace 隔离、批量运行
  schemas/      # Task / Trace / Result 的 pydantic schema
  tools/        # 文件、搜索、测试、写入、diff 工具
benchmarks/
  manifests/    # 正式集、challenge 集、冻结集
  repos/        # semi-real benchmark 仓库
  tasks/        # 任务定义
docs/           # 架构、实验摘要、指南、案例
evals/          # metrics、taxonomy、compare
logs/           # 运行轨迹与评测产物
optimization/   # policy 版本与优化记录
scripts/        # 单任务、批量评测、稳定性复跑等脚本
```

## 技术栈

- Python
- Pydantic
- pytest
- OpenAI-compatible Chat Completions
- subprocess 驱动的测试执行
- 文件级 patch / diff
- manifest 驱动的 benchmark 管理

OpenTelemetry 当前没有默认接入。项目现阶段优先把本地 JSON trace、评测报告和稳定性复跑做扎实，再考虑更重的观测栈。

## 文档导航

- Agent 概览：[docs/agent_overview.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_overview.md)
- Agent 小样本评测：[docs/agent_eval_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_eval_summary.md)
- Agent 案例：[docs/agent_case_studies.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_case_studies.md)
- 架构说明：[docs/architecture.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/architecture.md)
- 实验摘要：[docs/experiment_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/experiment_summary.md)
- 完整结果日志：[docs/results.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/results.md)
- Harness 设计：[docs/harness.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/harness.md)
- 基准任务注册表：[docs/benchmark_registry.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/benchmark_registry.md)
- Challenge 说明：[docs/challenge_set.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/challenge_set.md)
- Challenge 候选短名单：[docs/challenge_shortlist.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/challenge_shortlist.md)
- 项目实施指南：[GUIDE.md](/E:/My_Projects/agentic-software-engineering-roadmap/GUIDE.md)
- V2 路线图：[docs/v2_roadmap.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/v2_roadmap.md)

## 当前阶段判断

这已经不是一个“先让 agent 存在”的阶段了。

当前项目的主角已经切到 LLM coding agent：它能在隔离 workspace 里读 issue、搜代码、改文件、跑测试、落盘 trace，并已有 `29 / 33` 条可审计成功 run。现有 benchmark / frozen / stability 体系的角色，是给 agent 提供可信验证层和 baseline 参照：

- 有 LLM tool-use agent
- 有 case study trace / result / patch 证据
- 有正式集
- 有冻结集
- 有策略版本化
- 有批量评测
- 有稳定性复跑
- 有 maturity 审计

接下来的重点不是继续堆规则版任务数量，而是继续补齐 agent 求职展示最需要的证据：更复杂的跨文件任务、失败类型分类，以及更精简的 README 首屏叙事。

# Agentic SWE

一个面向 GitHub issue 自动修复的 mini agentic software engineering benchmark 项目。

它不只是在本地跑一个“会改代码的 agent”，而是把真实 issue 任务构造、隔离执行、轨迹落盘、批量评测、策略优化、冻结集回归和稳定性复跑串成了一条完整闭环。

## 核心结果

| 指标 | 当前结果 |
| --- | --- |
| 正式真实任务数 | `66` |
| challenge 任务数 | `3` |
| 来源生态数 | `16` |
| 当前正式集成功率 | `100%` |
| 当前正式集测试通过率 | `100%` |
| 当前策略版本 | `improved_v71` |
| `frozen_40` 连续无回归版本数 | `8` |
| `frozen_40` 当前最小验证均值耗时 | `0.5794s` |
| 当前结论 | `v71 已把正式任务扩到 66 条，并完成正式集、frozen_20、frozen_40 三线功能全绿；相对 v70，正式集平均耗时回落，但两条冻结集平均耗时回升，当前应继续补稳定性复跑与性能复核` |

基于 [benchmark_maturity_maturity_087.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/benchmark_maturity_maturity_087.json)、[batch_eval_realissuev71r2_001.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/batch_eval_realissuev71r2_001.json)、[batch_compare_frozen20_step71_r2_001.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/batch_compare_frozen20_step71_r2_001.json) 和 [batch_compare_frozen40_step71_r2_001.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/batch_compare_frozen40_step71_r2_001.json)，当前项目已经达到“真实 issue benchmark v1 可用”阶段，并继续向更成熟的 benchmark 基础设施推进。

## 系统闭环

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
          |
          v
   batch run / batch eval / taxonomy
          |
          v
   compare / frozen 回归 / maturity audit / stability recheck
          |
          v
   policy 迭代与下一轮 benchmark 扩容
```

## 项目特点

- 任务不是纯 synthetic demo，而是 `66` 条来自真实开源 issue 的 `semi_real` benchmark。
- 优化不是“凭感觉调 prompt”，而是版本化到 `improved_v71`，并且有冻结集无回归验证与稳定性复跑。
- 评测不是只有成功率，还包括 taxonomy、耗时、步数、稳定性复跑和 maturity 审计。
- 性能治理现在还支持环境基线快照，能先把“环境变慢”和“策略变慢”做一层拆分。
- harness 是一等公民：强调工作区隔离、路径边界、产物契约和批量复现能力。
- challenge 集独立管理：系统边界题可以单独运行和展示，而不污染正式 benchmark 口径。

## 快速开始

安装依赖：

```bash
python -m pip install -r requirements.txt
```

单任务运行：

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

## 代表性案例

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
- subprocess 驱动的测试执行
- 文件级 patch / diff
- manifest 驱动的 benchmark 管理

OpenTelemetry 当前没有默认接入。项目现阶段优先把本地 JSON trace、评测报告和稳定性复跑做扎实，再考虑更重的观测栈。

## 文档导航

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

这已经不是一个“做出最小 demo”的阶段了。

当前项目更接近一个可持续迭代的 benchmark 基础设施：

- 有正式集
- 有冻结集
- 有策略版本化
- 有批量评测
- 有稳定性复跑
- 有 maturity 审计

接下来的重点不再是单纯追求任务数量，而是继续提升展示层、稳定性门控、生态均衡度和真实 issue 导入效率。

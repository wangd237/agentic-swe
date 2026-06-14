# 实验摘要

本文档是 [docs/results.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/results.md) 的导读层。

如果 `results.md` 负责保存完整实验审计轨迹，那么本文档负责回答三个更直接的问题：

1. 这个项目到底做成了什么
2. 哪些策略迭代最关键
3. 现在离下一阶段还差什么

## 1. 实验目标

这个项目的目标不是做一个“看起来像 agent 的 demo”，而是建设一套可持续迭代的 agentic software engineering benchmark 基础设施。

这里的“基础设施”至少包含五个部分：

- 持续扩容的真实 issue 任务集
- 可复现的 harness 执行环境
- 面向 batch 的评测系统
- 可比较的策略版本化机制
- 可用于无回归验证的冻结集与稳定性复跑

截至 `2026-06-13`，第一阶段目标已经收口到一个明确状态：项目进入“真实 issue benchmark v1 可用”阶段。

## 2. 核心结论

- 正式任务集已经扩充到 `64` 条，全部来自真实 GitHub issue 语义重构的 `semi_real` 任务。
- 来源生态已经达到 `16` 个，显著超过最初 maturity 目标要求的 `6` 个。
- 当前 `improved_v69` 在正式任务集上达到 `100% success_rate` 和 `100% test_pass_rate`。
- `frozen_40` 已建立完成，并且实现了连续 `8` 个版本的无回归 streak。
- `improved_v69` 已在正式集、`frozen_20`、`frozen_40` 三条线上完成最小验证，并补齐两条冻结集的 stability recheck，当前结论为 `stable`。
- `improved_v68` 仍是上一轮性能更优的参考版本；`v69` 在成功扩入 `task_125` 后出现平均耗时回升，当前已经进入专项性能复核阶段。
- 评测流水线已经不只是“跑一遍 batch eval”，而是能自动附带 stability check 和 maturity audit。

## 3. 当前量化快照

| 维度 | 当前值 |
| --- | --- |
| 正式任务数 | `64` |
| 来源生态数 | `16` |
| 当前策略版本 | `improved_v69` |
| 正式集成功率 | `100%` |
| 正式集测试通过率 | `100%` |
| `frozen_40` 规模 | `40` |
| `frozen_40` 连续无回归版本数 | `8` |
| `realissue v69 average_duration_sec` | `0.5656` |
| `frozen20 v69 average_duration_sec` | `0.5975` |
| `frozen40 v69 average_duration_sec` | `0.5861` |
| `frozen20 v69 stability mean duration` | `0.5665` |
| `frozen20 v69 stability conclusion` | `stable` |
| `frozen40 v69 stability mean duration` | `0.5555` |
| `frozen40 v69 stability conclusion` | `stable` |
| 当前三线结论 | `realissue / frozen20 / frozen40 全绿` |

数据来源：

- [benchmark_maturity_maturity_075.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/benchmark_maturity_maturity_075.json)
- [batch_eval_realissuev69r1_001.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/batch_eval_realissuev69r1_001.json)
- [batch_eval_frozen20v69r1_001.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/batch_eval_frozen20v69r1_001.json)
- [batch_eval_frozen40v69r1_001.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/batch_eval_frozen40v69r1_001.json)
- [stability_recheck_frozen20_v69_stability_001.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/stability_recheck_frozen20_v69_stability_001.json)
- [stability_recheck_frozen40_v69_stability_001.json](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/stability_recheck_frozen40_v69_stability_001.json)

## 4. Baseline 到当前版本的演进

这个项目的策略演进不是一次性跳跃，而是逐步扩任务、逐步修 patch strategy、逐步补回归体系的过程。

### 关键阶段对比

| 阶段 | 代表版本 | 主要意义 |
| --- | --- | --- |
| 真实 issue 起点 | `improved_v3` | 第一个 requests 真实 issue 任务打通 |
| 早期泛化增强 | `improved_v17` | 在 hostname 异常回落类问题上形成代表性改进 |
| 性能拐点 | `improved_v33` | `-p no:unraisableexception` 优化让冻结集耗时出现明显改善 |
| 稳定基线 | `improved_v50` | 冻结集 streak 收口，成为后续性能对比的重要基线段 |
| 扩容完成阶段 | `improved_v63` | 第 `60` 条正式任务纳入，正式集达到 `60/60` |
| 继续扩容阶段 | `improved_v64` | 第 `61` 条正式任务纳入，并补齐 `fsspec` 新生态 |
| 并发生态扩容 | `improved_v66` | 第 `63` 条正式任务纳入，并补齐 `anyio` 第二条并发语义任务 |
| 保守性能回收 | `improved_v68` | 在保持三线全绿的前提下，相对 `v66` 回收正式集与冻结集平均耗时 |
| 最新扩容版本 | `improved_v69` | 第 `64` 条正式任务纳入，并补齐 `from_thread.check_cancelled()` 的取消语义问题 |

## 5. 最关键的里程碑版本

### `improved_v3`

这是项目真正进入“真实 issue benchmark”方向的起点。它标志着系统不再只围绕 synthetic 样例工作，而开始在 requests 语义上验证端到端闭环。

### `improved_v17`

这是一个很有代表性的优化节点。`jsonschema hostname` 相关任务从失败到通过，不只是简单让测试过，而是把异常回落与正常验证语义分开处理，说明 patch strategy 已经开始覆盖更细的行为边界。

### `improved_v33`

这是性能视角的重要拐点。通过在 pytest 调用参数上增加 `-p no:unraisableexception`，冻结集平均耗时出现改善，说明该项目的优化不仅在追成功率，也已经进入执行成本调优阶段。

### `improved_v50`

这一阶段的意义在于稳定性。它对应的是“冻结集能否长期无回归”的方法论逐渐成形，为后续 maturity 目标的 streak 统计提供了稳定支点。

### `improved_v63`

当前正式任务集的第 `60` 条任务在这一版本纳入，标志着规模目标达成。它不是单纯多加一题，而是把项目从“在做扩容”推进到了“扩容目标已收口，开始强调成熟度”。

### `improved_v64`

这一版本的意义在于两点同时成立：一是把 `fsspec/filesystem_spec#979` 推进成正式任务 `task_122`，让正式集达到 `61` 条并扩到第 `15` 个生态；二是在新增任务后继续保持正式集、`frozen_20`、`frozen_40` 功能全绿，并把两条稳定性复跑都收口为 `stable`。

### `improved_v65`

这一版本把 `agronholm/anyio#1109` 推进成正式任务 `task_123`，让正式集达到 `62` 条并扩到第 `16` 个生态。更关键的是，它先经历了单任务层面的“旧策略失败 / 新策略成功”，随后补齐了正式集、`frozen_20`、`frozen_40` 三线最小验证，并进一步补齐两条冻结集的稳定性复跑，最终确认这次扩容没有带来功能回归，而且冻结集结论已经回到 `stable`。

### `improved_v66`

这一版本把 `agronholm/anyio#1111` 推进成正式任务 `task_124`，让正式集达到 `63` 条。它的主要价值不只是再多一条并发题，而是补上了 `_deliver_cancellation` 在已完成 task 上的 spin 语义缺陷，说明当前 benchmark 已经开始覆盖更真实的协程生命周期问题。

### `improved_v68`

`v66` 三线全绿后，项目没有停在“功能正确”这一层，而是继续对性能回升做了拆解。`improved_v67` 试图通过更激进的 pytest plugin 裁剪进一步压时延，但因为 `-p no:debugging` 破坏了 unittest 路径对 `_pytest.debugging` 中 `trace` 选项的访问，导致多条任务失败，因而被明确否证。`improved_v68` 则转向更保守的 runtime 优化，只保留 `-p no:unraisableexception` 与 `-p no:threadexception`，最终在正式集、`frozen_20`、`frozen_40` 三线继续保持全绿，并把三条线平均耗时都从 `v66` 水平回落。

### `improved_v69`

这一版本把 `agronholm/anyio#1113` 推进成正式任务 `task_125`，让正式集达到 `64` 条。它的直接修复点是 `from_thread.check_cancelled()` 在已取消上下文中的取消语义缺陷，说明 benchmark 已经继续深入到并发取消边界。但和 `v68` 不同，`v69` 虽然在正式集、`frozen_20`、`frozen_40` 上仍然三线全绿，平均耗时却相对 `v68` 出现了回升，因此它同时开启了下一阶段“功能继续扩容、性能单独复核”的工作模式。

## 6. 冻结集演进

冻结集不是一开始就有 `40` 条，而是随着项目成熟逐步扩展：

| 阶段 | 冻结集规模 | 作用 |
| --- | --- | --- |
| 初版 | `15` | 建立最小同集合回归能力 |
| 扩展一 | `18` | 扩大早期代表任务覆盖 |
| 扩展二 | `20` | 形成较稳定的小型冻结集 |
| 当前阶段 | `40` | 作为 benchmark maturity v1 的正式稳定性基线 |

这个演进过程的意义在于：

- 项目不只是在“加题”
- 也在同步建设“如何证明后续没退化”

## 7. 性能优化关键节点

### `v32 -> v33`

代表性动作是增加 pytest 额外参数 `-p no:unraisableexception`。这类优化看起来很小，但对批量跑 benchmark 的总时长有持续影响，是典型的 harness / runtime 层收益。

### `v66 -> v68`

这一段是当前最有代表性的性能治理案例。`v66` 在扩入 `task_124` 后仍然三线全绿，但平均耗时有所回升；后续通过 pytest phase / importtime / plugin 变体下钻，确认主因集中在 `run_tests` 的 subprocess 与 pytest collection 链路。`v67` 的激进关闭 debugging 插件方案失败后，`v68` 采用更保守的 `-p no:threadexception` 裁剪，最终在不牺牲成功率的前提下，把正式集、`frozen_20`、`frozen_40` 的平均耗时都从 `v66` 拉回。

### `v68 -> v69`

这一段代表项目已经进入更成熟的治理节奏。`v69` 功能上成功把正式集从 `63` 条扩到 `64` 条，并在正式集、`frozen_20`、`frozen_40` 三条线上保持 `100%` 通过；但公共任务时延对比显示平均耗时仍然分别回升了 `+0.0241s`、`+0.0366s`、`+0.0272s`。进一步的 trace 热点分析把线索收敛到 `run_tests` 与 `search_code`，随后又通过 `search_code` 查询签名对照、冷启动 / 热启动基准，确认搜索本体暂时不像稳定退化主因。这说明项目现在不再是“加题成功就结束”，而是会继续对新增版本做性能复核和证据分层。

## 8. 新增的成熟度基础设施

最近这轮工作最重要的，不只是多跑了一次结果，而是给评测流水线补上了两个过去缺失的能力：

### stability recheck

新增脚本 [scripts/stability_recheck.py](/E:/My_Projects/agentic-software-engineering-roadmap/scripts/stability_recheck.py)，用于：

- 同策略同 manifest 复跑多次
- 统计均值、标准差、最小值、最大值
- 检测 outlier
- 判断功能一致性
- 输出 `stable / borderline / unstable` 结论

### maturity audit in pipeline

[scripts/run_real_issue_eval.py](/E:/My_Projects/agentic-software-engineering-roadmap/scripts/run_real_issue_eval.py) 现在已经可以在 batch eval 结束后自动：

- 触发 stability check
- 输出 maturity 摘要
- 生成 maturity 报告产物

这意味着 benchmark 的“规模、稳定性、性能、无回归能力”已经被同一条流水线同时观察。

## 9. 当前还存在的边界

虽然第一阶段已经可用，但仍有几个现实边界：

- 正式任务仍全部是 `semi_real`，尚未进入直接操作真实上游仓库的大规模阶段
- patch strategy 当前仍主要依赖规则型能力积累
- 稳定性复跑机制已经补上，而且 `v69` 已完成 `frozen_20 / frozen_40` 的 stability recheck，但未来继续扩并发家族后，仍要持续观察长尾波动是否重新放大
- 展示层正在持续收口，部分案例文档仍需要从“流水账”升级为“可讲故事的工程材料”

## 10. 推荐阅读路径

如果你想继续深入，建议按下面顺序看：

1. [README.md](/E:/My_Projects/agentic-software-engineering-roadmap/README.md)
2. [docs/architecture.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/architecture.md)
3. [docs/benchmark_registry.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/benchmark_registry.md)
4. [docs/results.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/results.md)
5. [docs/optimization_log.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/optimization_log.md)

## 11. 一句话总结

当前项目已经从“能不能做出一个会改代码的 agent”升级到了“能不能做出一套可持续评测、可稳定复跑、可长期扩容的真实 issue benchmark 基础设施”，而答案已经基本是可以。

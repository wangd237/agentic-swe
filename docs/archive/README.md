# 文档归档

本目录存放历史过程文档。它们记录了项目各阶段的决策与数据，
但不再是当前主线——当前文档入口见 [README 文档导航](../../README.md#文档导航)。

## 归档原因分类

| 类别 | 文件 | 说明 |
|---|---|---|
| **历史流水账** | `optimization_log.md`（17k 行） | rule-based 时代 v1-v63 全量迭代记录 |
| | `results.md` | rule-based 时代结果流水账 |
| | `project_memory.md` | 冷启动记忆卡（内容已过时） |
| **sourcing 过程文档** | `candidate_shortlist.md`、`challenge_shortlist.md`、`challenge_set.md`、`challenge_sourcing_brief_a3.md`、`issue_sourcing_brief_a2.md`、`issue_sourcing_spec.md` | benchmark 任务筛选的中间产物 |
| **已完成的阶段性报告** | `stress_test_report.md`（Target 1）、`failure_deep_dive.md`、`model_comparison.md`（Target 2 interim）、`experiment_summary.md` | 结论已并入 agent_eval_summary / war_stories |
| **已被取代的设计文档** | `eval_design.md`、`optimization.md`、`benchmark.md` | 现行版本见 architecture.md / agent_eval_summary.md |
| **已过时的行动清单** | `next_actions.md` | Target 2 时代的 TODO，Kimi/GLM key 永远没来 |

## 为什么保留而不删除

这些文档包含可追溯的实验数据（frozen set 对比、duration 回归分析等），
是"度量驱动迭代"的证据。归档而非删除，需要追溯实验数据时可查。

注意：部分文档引用的 `logs/summaries/` 过程产物已在仓库瘦身时清理，
链接失效属预期；关键结论性数据已摘录进现行文档。

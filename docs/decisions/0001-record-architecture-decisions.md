# ADR-0001: 采用架构决策记录

**日期**: 2026-08-30
**状态**: 已采纳

## Problem

项目从 rule-based solver 演进为 LLM coding agent，经历了 27 天 159 个 commit 的密集迭代。大量设计决策散落在代码注释、commit message、war_stories 和调研报告中，缺乏统一索引。面试准备阶段需要能快速回溯"为什么做/不做某个决策"。

## Decision

采用轻量 ADR（Architecture Decision Record）格式，在 `docs/decisions/` 目录下维护。每个决策一个文件，模板：

- **Problem**: 触发决策的问题
- **Decision**: 做了什么选择
- **Alternatives**: 被拒绝的方案及原因
- **Risks**: 已知风险
- **Files changed**: 受影响文件

## Alternatives Considered

1. **扩展现有 war_stories.md / failure_analysis.md**: 这两份文档侧重点在"出了什么问题"和"怎么归因"，不是"为什么做了这个选择"。拒绝原因是语义不吻合。
2. **新建独立 docs/ 子目录 vs 合并到现有文档**: 选择独立子目录，因为 ADR 是另一种时间线（按决策而非按事故），交叉引用即可，不破坏已收敛的 9 文档体系。

## Risks

- 文档体系从 9 个扩展到 10+ 个，可能稀释"收敛"效果。缓解：ADR 只记真决策，不做过程笔记。
- 与 war_stories 的边界模糊。缓解：war_stories 是"事故→归因→教训"，ADR 是"选择→备选→风险"，两者互补不重叠。

## Files Changed

- `docs/decisions/` (新建目录)
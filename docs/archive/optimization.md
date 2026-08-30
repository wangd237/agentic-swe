# 优化说明

> 这是规则版 baseline 和早期 policy 对比的历史说明。当前优化主线已经切到 LLM coding agent 的真实运行、失败分类和 case study 展示。

当前处于 `Phase 6`，优化系统已经开始首轮对比实验。

## 当前状态

当前已经完成：

- 单任务 patch 闭环
- batch run
- baseline eval
- baseline vs improved 首轮 policy 对比
- `improved_v2` 第二轮 policy 对比

这意味着下一阶段可以正式开始：

- 冻结 baseline
- 创建 improved 版本
- 比较优化前后指标

## 优化过程记录

从现在开始，具体每一轮优化动作与指标对比，统一记录在：

- `docs/optimization_log.md`

记录原则：

- 只追加，不覆盖旧迭代
- baseline 与 improved 的历史结果都保留
- compare 报告也必须保留历史版本
- 每一轮都要能回溯到对应的配置文件和结果文件

## 当前推荐的优化闭环

现在建议每一轮优化都按下面顺序执行：

1. 运行 baseline batch run
2. 运行 improved batch run
3. 分别生成 baseline / improved batch eval
4. 运行 `python -m evals.compare_evals` 生成自动 compare 报告
5. 追加记录到 `docs/optimization_log.md`

这样做的价值是：

- 每轮优化都有独立产物
- 指标变化不是手工整理，而是自动沉淀
- 后续接入更多 benchmark 或 GitHub 真实 issue 时，流程不用重写

后续将按规格书顺序推进：

1. Prompt Optimization
2. Policy Optimization
3. Grader / Rule Optimization
4. Optional Light Post-Training

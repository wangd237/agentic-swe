# A3 Challenge Sourcing Brief

> 这是前一阶段用于 challenge 题 sourcing 的 brief。当前 challenge 线应服务 agent 边界展示和 `incomplete_reason` 分类，而不是为了继续堆题。

本文件用于指导“下一条 challenge 题应该怎么找”。

如果：

- `docs/issue_sourcing_brief_a2.md` 负责正式主集扩容
- `docs/challenge_set.md` 负责说明 challenge 集当前是什么

那么本文件负责定义：

- 什么样的 GitHub issue 更适合进入 challenge 线
- 什么样的 issue 虽然看起来难，但不适合进入 challenge 线
- 返回候选时应该怎样组织，才能直接进入下一步筛选

适用阶段：

- `v2 roadmap` 的 `A3`
- 当前 challenge 集已有 `3` 条任务：
  - `task_126 / samuelcolvin/watchfiles#266`
  - `task_127 / samuelcolvin/watchfiles#110`
  - `task_130 / samuelcolvin/watchfiles#169`
- 当前本地 challenge shortlist 为空，需要重新 sourcing 第 `4` 条 challenge 候选

## 当前背景

当前 challenge 线已经具备：

- 独立 manifest：
  - `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- 独立评测入口：
  - `scripts/run_challenge_eval.py`
- 独立说明文档：
  - `docs/challenge_set.md`

但当前更准确的状态不是“已经有下一条明确 challenge 候选”，而是：

- 前 `3` 条 challenge 已落地
- 第 `4` 条 challenge 候选需要重新 sourcing

同时要特别避免一个已经发生过的错误：

- 不能把已经进入正式主集的题，再写成 challenge 候选

当前已经明确不应再进入 challenge shortlist 的例子：

- `dateutil/dateutil#1191`，已在正式主集，对应 `task_050`
- `PyCQA/isort#1815`，已在正式主集，对应 `task_061`
- `pallets/click#2402`，已在正式主集，对应 `task_042`

## challenge 题的核心定位

challenge 题不是“更难的正式题”，而是：

- 适合展示系统边界
- 可以独立承载
- 但暂时不适合直接并入正式主集

更直白地说，challenge 题优先承载的是：

- 边界代表性强
- 但 benchmark 主口径证据还不够保守的题

## 当前最高优先级

### 1. 平台 / 环境语境较重，但仍可稳定本地化的题

理想形态：

- 原 issue 带有明显平台、环境或运行上下文
- 例如：
  - Windows / Linux 行为差异
  - WSL / Docker / 挂载目录
  - 文件系统事件、路径规范化、编码边界
- 但可以压成：
  - 单仓库
  - 单模块
  - 1 到 3 条稳定回归测试

为什么适合 challenge：

- 这类题很能展示“真实世界问题的脏边界”
- 但如果直接并入正式主集，容易把主口径拉向环境依赖

### 2. parser / formatter / control-flow 内部语义很复杂的题

理想形态：

- 问题边界仍然清楚
- 但修复需要理解较复杂的内部语义路径
- 或者 issue 很像“高风险回归题”

优先示例类型：

- parser token 边界
- formatter profile / wrapping / layout 分支
- dispatch / control-flow / fallback 语义链

为什么适合 challenge：

- 这类题能体现系统边界和复杂性
- 但短期内未必适合作为正式主集的稳定扩容证据

### 3. 更像“展示题”而不是“规模扩容题”的 issue

理想形态：

- 题目本身很有讲述价值
- 可以清楚说明：
  - 为什么真实 issue 难
  - 为什么本地缩题需要保守处理
  - 为什么它值得单独展示

## 更适合 challenge、而不是正式主集的信号

如果一个 issue 满足下面任意一条，应优先考虑 challenge 而不是正式主集：

- 原 issue 的平台 / 环境语境很重
- 当前缩题后虽然稳定，但与原 issue 的代表性仍有距离
- 更适合作为系统边界展示，而不是成功率统计样本
- 修复语义复杂，短期内回归风险较高

## 不适合 challenge 的 issue

下面这些题，即便质量不错，也不应优先进入 challenge：

- 单函数、单模块、边界清楚、很容易形成“旧版失败 / 新版成功”的题
- 更适合作为正式主集继续扩容的题
- 已经进入正式主集的题
- 只是“难”，但没有清晰系统边界意义的题

## 必须排除的 issue

即便很像 challenge，也不要推荐以下 issue：

- 需要真实网络、数据库、浏览器、守护进程才能稳定复现
- 明显依赖特定机器环境才能触发，无法压成本地稳定回归
- 修复需要跨多个子系统大范围改动
- 需要概率型并发竞争、长时间压力测试才能偶发出现
- 更像性能优化，而不是正确性 bug
- 行为规范本身有明显争议

## 最理想的 challenge issue 形态

请优先寻找这类 issue：

- 标题直接描述错误行为
- 有最小复现代码或明确现象
- 能推断 1 个核心模块
- 能压成 1 到 3 条稳定本地测试
- issue 自带明显“系统边界”叙事价值

## 返回结果时的排序规则

请按下面顺序排序候选：

1. 平台 / 环境语境重，但可稳定本地化的题
2. parser / formatter / control-flow 的复杂边界题
3. 其它明显更适合 challenge 而不是正式主集的高质量题

## 返回格式

请严格按下面格式返回，每个候选单独一段：

```text
1. repo: owner/name
   challenge_fit: platform-heavy / environment-heavy / parser-complexity / formatter-complexity / control-flow-boundary / other
   issue: #1234
   title: ...
   url: ...
   why_it_fits_challenge:
   why_not_formal_yet:
   expected_target_files:
   expected_test_shape:
   estimated_difficulty: medium / hard
   risk_notes:
   recommendation: high / medium / low
```

## 补充要求

- 如果 issue 已经被正式主集吸收，不要返回
- 如果 issue 同时适合正式主集和 challenge，默认优先归入正式主集，不要强行放 challenge
- 如果 issue 很像 challenge，但环境依赖仍然太重，请在 `risk_notes` 里明确说明
- 如果同一个仓库给出多个候选，默认只保留最好的 `1` 条

## 一句话总结

当前 A3 的关键不是“找更难的题”，而是**找更适合展示系统边界、但暂时不适合直接并入正式主集的题**。

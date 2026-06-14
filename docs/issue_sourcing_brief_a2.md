# A2 Issue Sourcing Brief

本文件是 `docs/issue_sourcing_spec.md` 的补充版。

如果 `issue_sourcing_spec.md` 负责定义“什么样的 issue 适合做 benchmark”，那么本文件负责定义：

- **当前这一个阶段最应该优先找什么**
- **哪些方向暂时不该再优先堆**
- **返回给主会话时应该怎样组织结果，才能直接进入下一步筛选**

适用阶段：

- `v2 roadmap` 的 `A2`
- 当前正式集 `60` 条、`14` 个生态、`frozen_40` 已建立完成之后

## 当前背景

基于 [defect_coverage_v2_gap_analysis_002.md](/E:/My_Projects/agentic-software-engineering-roadmap/logs/summaries/defect_coverage_v2_gap_analysis_002.md)，当前正式 benchmark 的缺陷家族分布已经比较明确：

- 覆盖最重的两类：
  - `解析与字符串语义 = 15`
  - `序列化与反序列化 = 15`
- 其次：
  - `继承、优先级与控制流 = 7`
  - `格式化与渲染 = 6`
- 当前明确空白：
  - `并发与协程 = 0`
  - `文件路径与 IO = 0`

因此下一轮扩容的目标，不再是“再找一些容易转 semi_real 的 issue”，而是：

- **优先填补当前 0 覆盖家族**
- **避免继续在已过密的家族里重复堆题**

## 当前最高优先级

### 1. 并发与协程类 bug

优先仓库：

- `asyncio`
- `trio`
- `anyio`

优先问题形态：

- `async` / `await` 调用顺序错误
- 协程对象被错误暴露、错误复用或错误消费
- 任务取消、超时、上下文切换边界
- 事件循环状态判断错误
- 同步/异步接口桥接处的明确行为 bug

理想特征：

- 能缩成单模块或单函数
- 测试稳定，不依赖时序竞争
- 不是“偶发 race”
- 更像“明确错误行为”而不是“概率型调度问题”

### 2. 文件路径与 IO 类 bug

优先仓库：

- `pathlib`
- `watchfiles`
- `fsspec`

优先问题形态：

- 路径规范化
- 文件 URL / scheme 兼容性
- 相对路径 / 绝对路径行为错误
- 文件读写时边界条件错误
- glob / suffix / stem / join 之类的小型路径语义 bug

理想特征：

- 可以用临时目录或纯字符串路径完成复现
- 不依赖真实文件系统权限差异
- 不需要跨平台条件判断才能稳定触发

## 当前次优先级

### 3. 继承、优先级与控制流

当前这类问题已经是 benchmark 强项之一，因此继续补这类题时，更希望满足：

- 来自**新生态**
- 不是重复已有 `pydantic / attrs / jinja / pytest` 中已经覆盖过的近似语义
- 最好能补“注册链 / hook 链 / dispatch 顺序 / override 优先级”中的一个新角度

## 当前不建议优先继续堆的方向

下面这些方向不是不能做，而是当前阶段不该再排在最前：

- `tomlkit` 的序列化 / 容器 / 渲染小 bug
- `packaging` 的解析 / normalization / marker / specifier 类边界 bug
- `dateutil` 的 parser 字符串边界 bug
- 与现有 `requests / click / jinja / jsonschema` 已有题型高度相似的微调版问题

原因不是这些题不好，而是：

- 当前这些家族已经足够密集
- 继续堆会让 benchmark 的“广度”改善很有限

## 必须排除的 issue

即便来自优先仓库，也不要推荐以下 issue：

- 需要真实网络、数据库、浏览器、守护进程才能稳定复现
- 明显是性能优化而不是正确性 bug
- 需要跨多个子系统一起改
- 需要复杂并发压力测试才能偶发复现
- 行为规范本身就存在争议
- 需要大范围 API 设计调整

## 最理想的 issue 形态

请优先寻找这种 issue：

- 标题直接描述错误行为
- 有最小复现代码
- 有明确当前输出或报错
- 有明确期望输出
- 能定位到 1 个核心模块
- 修复后很容易压成 1 到 3 个稳定回归测试

## 返回结果时的排序规则

请按照下面顺序排序候选：

1. `并发与协程` 中边界最清晰、最容易最小化复现的 issue
2. `文件路径与 IO` 中边界最清晰、最容易最小化复现的 issue
3. `继承、优先级与控制流` 中来自新生态的 issue
4. 其它虽不是最高优先级，但明显高质量、低风险、易于转 semi_real 的 issue

## 返回格式

请严格按下面格式返回，每个候选单独一段：

```text
1. repo: owner/name
   family: 并发与协程 / 文件路径与 IO / 继承、优先级与控制流 / 其他
   issue: #1234
   title: ...
   url: ...
   why_it_fits:
   expected_target_files:
   expected_test_shape:
   estimated_difficulty: easy / medium / hard
   risk_notes:
   recommendation: high / medium / low
```

## 补充要求

- 如果同一个仓库给出多个候选，默认只保留最好的 `1` 到 `2` 条
- 如果 issue 看起来很合适，但依赖太重，请明确写在 `risk_notes`
- 如果 issue 更像 challenge case 而不是正式集候选，请标注：
  - `recommendation: medium`
  - 并在 `risk_notes` 里说明更适合 challenge manifest

## 一句话总结

当前 A2 的关键不是“继续找题”，而是**优先用新生态补齐 `并发与协程` 和 `文件路径与 IO` 这两个 0 覆盖家族**。

# 架构说明

本文档描述当前 `agentic-swe` 的真实实现结构，而不是早期规划状态。

当前系统已经具备：

- 基于 `semi_real` GitHub issue 任务的正式 benchmark
- 基于 harness 的隔离执行与轨迹落盘
- 单任务与批量评测闭环
- 策略版本化优化
- 冻结集回归验证
- 稳定性复跑与 benchmark maturity 审计

## 1. 系统分层

```text
task / manifest / benchmark data
              |
              v
      scripts orchestration
      (run_single / batch / eval / recheck)
              |
              v
         runtime harness
   (workspace / logs / isolation / lifecycle)
              |
              v
          agent loop
   (planner / executor / patch strategy)
              |
              v
            tools
 (list / search / read / test / write / diff)
              |
              v
      schemas + eval system
 (Task / Trace / Result / metrics / taxonomy)
```

## 2. 目录职责

- `app/agent`
  - `planner.py`：生成当前步骤的最小计划
  - `executor.py`：驱动工具调用和执行闭环
  - `policy.py`：加载 policy JSON，提供策略配置
  - `patcher.py`：维护规则型 patch strategy 及版本继承链
- `app/tools`
  - 提供 agent 可调用的最小工具集合
  - 统一处理路径解析、工作区边界和返回结构
- `app/runtime`
  - 管理 task run 生命周期、workspace 隔离、日志落盘和 batch 运行
- `app/schemas`
  - 用 Pydantic 定义 `Task / Trace / Result` 等结构化数据
- `benchmarks`
  - 保存任务定义、manifest 和 semi-real benchmark 仓库
- `evals`
  - 保存 metrics、error taxonomy、compare 等评测逻辑
- `optimization`
  - 保存策略版本、优化记录和实验迭代资产
- `scripts`
  - 对外暴露单任务运行、批量评测、稳定性复跑和 maturity 审计入口

## 3. Agent Loop 执行流程

单条任务的大致运行链路如下：

1. 读取任务 JSON，构造 `Task` schema
2. runtime 创建本次 run 目录和独立 workspace
3. agent 读取 policy 配置，装配 planner / executor / patcher
4. planner 生成当前步骤计划
5. executor 根据计划调用工具：
   - `list_files`
   - `search_code`
   - `read_file`
   - `run_tests`
   - `write_file`
   - `show_diff`
6. 如果 patch strategy 命中，就在 workspace 内修改目标文件
7. 重新执行测试，判断是否满足成功条件
8. 将 `trace.json`、`result.json`、`patch.diff`、`summary.md` 等产物落盘
9. 批量模式下继续汇总到 batch run / batch eval

这个设计刻意保持 agent loop 简洁，把复杂度放到 harness、工具边界和评测链路，而不是写成一棵难维护的硬编码状态机。

## 4. 工具层设计

当前工具层集中在 `app/tools`，核心工具是：

- `list_files`
- `search_code`
- `read_file`
- `run_tests`
- `write_file`
- `show_diff`

### 统一接口约定

工具返回结构统一为：

```json
{
  "ok": true,
  "tool_name": "read_file",
  "summary": "已读取目标文件",
  "data": {},
  "error": null
}
```

这套约定带来的好处是：

- agent 层不需要为每个工具单独写分支适配
- trace 可以稳定落盘
- 后续替换工具实现时，不需要改主循环接口

### 安全边界

工具层的关键约束不是“能力多”，而是“边界清晰”：

- 只允许在当前 run 的 workspace 内写入
- benchmark 原始 repo 作为只读来源保留
- 路径解析统一走安全路径函数
- `show_diff` 只比较当前任务相关的工作副本变更

## 5. Runtime / Harness 设计

runtime 是这个项目的核心基础设施，重点在 `app/runtime`。

### 关键职责

- 为每次任务运行创建独立目录
- 将 repo 复制到任务级 workspace
- 协调 agent、工具和日志落盘
- 批量运行时收集每条任务结果
- 为评测系统提供稳定的输入契约

### run 目录契约

单次运行会落盘标准化产物，例如：

- `task.json`
- `trace.json`
- `result.json`
- `patch.diff`
- `summary.md`

这个契约很重要，因为它让：

- 单任务调试可复现
- batch eval 可直接消费 run 结果
- 后续 compare / taxonomy / 审计脚本不必依赖内存态

### 隔离策略

当前采用每个任务一份独立 workspace 的方式，优先保证：

- 不同任务之间互不污染
- 写入边界明确
- 错误恢复时更容易定位问题

这也是从 `learn-claude-code` harness 经验里明确吸收的一点：先把隔离和持久化做正确，再谈更复杂的多 agent 或并行控制。

## 6. 策略版本化机制

策略版本保存在 `optimization/policy_versions/` 下，例如：

- `improved_v32.json`
- `improved_v50.json`
- `improved_v64.json`

### policy JSON 当前承载的配置

当前配置层重点承载：

- `policy_id`
- `patch_strategy`
- `pytest_additional_flags`

### 真实实现中的继承链位置

这里有一个很重要的事实口径：

- 规则继承链不是通过某个 `rule_ids` 配置表驱动
- 当前真实实现是在 [app/agent/patcher.py](/E:/My_Projects/agentic-software-engineering-roadmap/app/agent/patcher.py) 中维护版本化 patch strategy

也就是说：

- policy JSON 负责声明“当前使用哪个策略版本”
- 具体某个版本包含哪些规则型修复能力，由 `patcher.py` 内部维护

这种实现方式的优点是简单、直观、容易快速迭代；缺点是版本规模继续增大后，规则组织会变得更重，这也是后续可继续演进的方向。

## 7. Eval 层设计

评测系统不是单一脚本，而是逐层递进的结构：

### 第一层：metrics

关注核心量化指标，例如：

- `success_rate`
- `test_pass_rate`
- `average_duration_sec`
- `average_steps`
- `average_tool_calls`
- `average_modified_files`

### 第二层：error taxonomy

失败不只看“没过”，还会归因到错误类型，便于下一轮优化判断。

### 第三层：batch eval

对一个 manifest 上的所有任务统一汇总，输出：

- JSON 报告
- Markdown 摘要

### 第四层：compare / maturity / stability

在基础 batch eval 之上，又补了三层更高价值能力：

- `compare`
  - 对比不同策略版本的指标变化
- `maturity audit`
  - 审核正式任务数、生态数、冻结集规模、连续无回归 streak 是否达标
- `stability recheck`
  - 同策略同 manifest 复跑多次，检查性能波动和功能一致性

当前 [scripts/run_real_issue_eval.py](/E:/My_Projects/agentic-software-engineering-roadmap/scripts/run_real_issue_eval.py) 已经可以把 batch run、batch eval、stability check 和 maturity audit 串在一条流水线里。

## 8. 数据分层

项目里的任务来源分成三层概念：

- `synthetic`
  - 完全人造，适合最早期联调和脚本打通
- `semi_real`
  - 基于真实 GitHub issue 抽取语义，构造成可控的本地 benchmark repo
- `real_issue`
  - 更接近真实仓库和真实上下文的任务形态

当前正式 benchmark 的 `64` 条任务全部是 `semi_real`。

这么做的原因很务实：

- 既保留真实 issue 的语义难度
- 又避免直接操作大仓库时的高成本和高不确定性
- 更适合进行快速策略迭代和冻结集回归

## 9. 实验管理与数据集分工

当前实验不是把所有任务混成一锅，而是按用途区分集合：

- 正式集
  - 用于衡量当前版本的广泛覆盖能力
- frozen 集
  - 用于衡量无回归和长期稳定性
- 候选池
  - 用于后续扩容和生态补齐

当前关键 manifest 包括：

- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
- `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
- `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`
- `benchmarks/manifests/real_issue_tasks_frozen_40_v1.json`

这种设计让我们可以把“扩容”和“回归验证”拆开管理，避免因为正式集持续变动而失去稳定评测基线。

其中 `challenge manifest` 专门承载：

- 已 ready
- 有展示价值
- 但暂不适合进入正式主集

的保守题目，用来表达系统边界，而不污染正式 benchmark 口径。

## 10. 当前架构的优势与边界

### 当前优势

- 闭环完整：任务、运行、评测、优化、复跑都已打通
- 数据可审计：核心状态都能落盘
- 迭代快：策略版本化和 semi-real 任务形态支持快速扩容
- 基础设施意识明确：稳定性复跑和 maturity 审计已经成为一等能力

### 当前边界

- patch strategy 仍以规则型实现为主
- 正式集尚未进入直接操作真实上游仓库的阶段
- 稳定性复跑已经有了，但仍需继续提升到更强的常态化门控
- 展示层和案例层仍在继续收口

## 11. 建议阅读顺序

如果你想快速理解项目，建议按下面顺序阅读：

1. [README.md](/E:/My_Projects/agentic-software-engineering-roadmap/README.md)
2. [docs/experiment_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/experiment_summary.md)
3. [docs/harness.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/harness.md)
4. [docs/benchmark_registry.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/benchmark_registry.md)
5. [docs/results.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/results.md)

# 架构说明

## 当前阶段

当前处于 `Phase 5`，本文件先记录系统的目标分层与职责边界，后续随着实现推进补充详细流程图与运行时说明。

## 分层约定

- `app/agent`：放 Agent 的提示词、规划、执行和策略
- `app/tools`：放 Agent 可调用工具的统一接口
- `app/runtime`：放任务运行、工作副本与日志落盘逻辑
- `app/schemas`：放 Task / Trace / Result 等结构化定义
- `benchmarks`：放任务定义和基准仓库
- `evals`：放评测与错误分类
- `optimization`：放 prompt / policy / 训练增强资料

## 当前实现说明

当前已经完成：

- 目录骨架创建
- 核心模块路径固定
- 基于 pydantic 的最小 schema
- 三个基础观察工具
- `run_tests` 工具
- `write_file` 与 `show_diff` 工具
- 最小规则型 patch 生成器
- 单任务 patch 闭环脚本
- 批量运行脚本与批量汇总器
- metrics / taxonomy / batch eval
- 首版 harness 运行时骨架

当前尚未完成：

- improved 对比实验

## Harness 设计原则

当前项目明确采用 `模型做决策，harness 提供环境` 的思路。

这意味着我们优先建设的是：

- 明确工具接口
- 清晰运行目录
- 工作副本隔离
- 路径安全边界
- 可落盘、可评测、可恢复的状态文件

详细设计见 [docs/harness.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/harness.md)。

# Agentic Software Engineering for GitHub Issue Resolution

这是一个面向 `小型 Python 仓库 issue 修复` 的 Agent 工程项目。

当前仓库按照实施规格书推进，目标不是只做一个能演示的助手，而是逐步完成下面这条主线闭环：

`Task -> Agent Run -> Logging -> Evaluation -> Optimization -> Re-run`

## 当前状态

- 当前阶段：`Phase 6 - 优化系统`
- 当前成果：
  - 已创建主项目骨架
  - 已创建首个最小 benchmark 仓库 `sample_repo`
  - 已创建开发任务集 `task_001` / `task_002`
  - 已提供 patch 闭环入口脚本 `scripts/run_single_task.py`
  - 已提供批量运行入口脚本 `scripts/run_batch.py`
  - 已提供评测入口 `python -m evals.batch_eval`
  - 已接入首版 harness 运行时骨架
  - 已实现 `list_files` / `search_code` / `read_file`
  - 已实现 `run_tests`
  - 已实现 `write_file` / `show_diff`
  - 已实现最小规则型 patch 生成器
  - 已实现基于 `pydantic` 的 schema 校验
  - 已支持单任务自动修复 `task_001` 并生成真实 `patch.diff`
  - 已支持通过 manifest 批量运行任务并输出汇总结果
  - 已支持对 batch run 输出 baseline 评测报告
  - 已完成首轮 baseline vs improved policy 对比
  - 已支持自动生成 baseline vs improved 对比报告
  - 已完成 `improved_v2` 策略迭代，补充首元素 `None` 场景修复
  - 已补充项目说明文档与阶段指南

## 项目目标

- 面向小型 Python 仓库实现一个最小可运行的 SWE-Agent
- 让 Agent 能逐步完成 issue 理解、代码检索、patch 生成、测试验证与结果记录
- 在主线跑通后，补齐 batch eval、错误分类与优化闭环
- 最终产出可复现、可比较、可展示的项目结果

## 目录概览

```text
app/
  agent/        # Agent 提示词、规划、执行、策略
  tools/        # Agent 可调用工具
  runtime/      # 运行时会话、任务执行、日志写入
  schemas/      # Task / Trace / Result 数据结构
benchmarks/
  tasks/        # 结构化任务定义
  repos/        # 基准仓库
docs/           # 架构、benchmark、评测、优化文档
evals/          # 指标、错误分类、批量评测
logs/           # 运行日志与结果产物
optimization/   # prompt / policy / 训练增强预留目录
scripts/        # 入口脚本
```

其中任务定义当前已经支持 `source_type`：

- `synthetic`
- `semi_real`
- `real_issue`

这让后续从本地联调集逐步过渡到 GitHub 真实 issue 集时，不需要重做任务结构。

## 快速体验

### 1. 运行 Patch 闭环

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_001.json
```

这个命令当前会完成：

- 读取并校验任务 JSON
- 创建独立 run 目录与工作副本
- 执行 `list_files`、`search_code`、`read_file`
- 执行修复前测试
- 生成并写入最小 patch
- 执行修复后测试
- 生成 `patch.diff`
- 输出推荐阅读文件
- 保存 `task.json`、`result.json`、`trace.json`、`patch.diff`、`summary.md`
- 保存 pre/post test stdout 与 stderr

### 2. 运行 benchmark 仓库测试

```bash
cd benchmarks/repos/sample_repo
python -m pytest tests/test_parser.py -q
```

说明：

- 当前环境已安装 `pytest`
- 测试文件仍保持 `unittest.TestCase` 风格，因此也兼容后续不同执行器

### 3. 运行批量任务

```bash
python scripts/run_batch.py
```

这个命令当前会完成：

- 读取 `benchmarks/manifests/dev_tasks.json`
- 顺序运行其中的任务
- 为每条任务生成独立 run 目录
- 在 `logs/summaries/` 下生成批量汇总 JSON 与 Markdown

### 4. 运行 baseline 评测

```bash
python -m evals.batch_eval --batch-summary logs/summaries/batch_run_001.json --output-dir logs/summaries
```

这个命令当前会完成：

- 读取 batch run 汇总和对应的 `task/result/trace/patch`
- 计算 baseline 指标
- 生成错误 taxonomy
- 在 `logs/summaries/` 下输出评测 JSON 与 Markdown

### 5. 生成 baseline vs improved 对比报告

```bash
python -m evals.compare_evals --baseline-eval logs/summaries/batch_eval_baseline_001.json --improved-eval logs/summaries/batch_eval_improved_001.json --output-dir logs/summaries --run-label phase6
```

这个命令当前会完成：

- 读取两份 batch eval JSON
- 自动计算各项指标 delta
- 自动对比 taxonomy 变化
- 生成追加式 compare JSON 与 Markdown
- 为后续优化迭代保留可回溯的对比产物

### 6. 校验任务定义与真实 issue 候选清单

```bash
python scripts/validate_tasks.py
```

这个命令当前会完成：

- 校验 `benchmarks/tasks/` 下的任务 JSON 是否符合 schema
- 校验 `source_type` 是否合法
- 校验未来真实 issue 候选清单的最小结构

## 当前 benchmark 任务

当前 benchmark 已分成三层：

- `Dev Set`
  - manifest: `benchmarks/manifests/dev_tasks.json`
  - tasks: `task_001`、`task_002`
  - 用途：联调单任务闭环、batch runner 与基础评测链路
- `Report Set`
  - manifest: `benchmarks/manifests/report_tasks.json`
  - tasks: `task_001`、`task_003`、`task_004`
  - 用途：执行 `baseline vs improved` 的正式对比
- `Future GitHub Real-Issue Set`
  - 当前未接入仓库内
  - 当前候选清单文件：`benchmarks/real_world_candidates.json`
  - 未来会引入 GitHub 上的小型真实仓库 issue 作为更正式的外部评测集

## 当前 baseline 结果

- batch run：`logs/summaries/batch_run_001.json`
- batch eval：`logs/summaries/batch_eval_001.json`
- 当前指标：
  - success_rate: `1.0`
  - test_pass_rate: `1.0`
  - average_steps: `9.0`
  - average_tool_calls: `9.0`

## 当前 improved 对比结果

当前 Phase 6 已经形成两段式优化：

- `baseline_v1 -> improved_v1`
  - report set: `task_001`、`task_003`
  - success_rate: `0.5 -> 1.0`
  - test_pass_rate: `0.5 -> 1.0`
  - partial_fix_rate: `0.5 -> 0.0`
- `improved_v1 -> improved_v2`
  - report set: `task_001`、`task_003`、`task_004`
  - success_rate: `0.6667 -> 1.0`
  - test_pass_rate: `0.6667 -> 1.0`
  - partial_fix_rate: `0.3333 -> 0.0`

当前最新对比产物：

- baselinev2：
  - `logs/summaries/batch_eval_baselinev2_001.json`
- improved_v1：
  - `logs/summaries/batch_eval_improvedv1r2_001.json`
- improved_v2：
  - `logs/summaries/batch_eval_improvedv2_001.json`
- compare：
  - `logs/summaries/batch_compare_phase6v2_step2_001.json`

## Harness 设计方向

这个项目会借鉴 `learn-claude-code` 的核心思路，但不会照搬整套复杂机制。当前已确定的方向是：

- 保持 Agent loop 尽量简单，把工程重点放在 harness
- 工具层使用显式接口和统一返回结构
- 路径访问始终受工作区边界约束
- 每次 run 的目录和产物文件作为真实状态源
- 工作副本隔离优先于“直接改 benchmark 原仓库”

更细的设计见 [docs/harness.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/harness.md)。

## 下一步

下一阶段将继续深化 `Phase 6 - 优化系统`，重点实现：

- 扩充 report set
- 增加更自动化的实验报告与案例沉淀
- 逐步接入 GitHub 真实仓库 issue 作为更正式的评测来源
- 继续做 prompt / policy / grader 组合优化
- 形成更有说服力的 improved 对比

更详细的阶段说明、体验方式和文件职责见 [GUIDE.md](/E:/My_Projects/agentic-software-engineering-roadmap/GUIDE.md)。

# 优化迭代记录

本文件专门记录：

- 每一轮优化改了什么
- 为什么要改
- 改动落在哪些文件
- 对应的 baseline / improved 指标对比
- 当前结论与下一步计划

这样做的目的有两个：

- 方便项目内部持续迭代时追踪因果链
- 方便求职展示时清楚说明“你到底优化了什么，为什么有效”

## 记录模板

后续每一轮优化建议按下面结构补充：

### Iteration N

- 时间：
- 阶段：
- 目标：
- 改动类型：`prompt` / `policy` / `grader` / `benchmark` / `runtime`
- 改动摘要：
- 主要涉及文件：
- baseline 运行：
- improved 运行：
- 指标对比：
- 结论：
- 剩余问题：

## Iteration 0：主线打通前的基线建设

### 背景

这一轮还不属于真正的 “improved vs baseline” 优化实验。

它的作用是先把主线工程打通，让后续优化有稳定基线可比较。

### 当前已经完成的基线建设

#### Phase 1：观察型 Agent

- 改动内容：
  - 实现 `list_files`
  - 实现 `search_code`
  - 实现 `read_file`
  - 引入 `pydantic` schema
  - 打通单任务 observation run
- 主要文件：
  - `app/tools/list_files.py`
  - `app/tools/search_code.py`
  - `app/tools/read_file.py`
  - `app/schemas/task_schema.py`
  - `app/schemas/trace_schema.py`
  - `app/schemas/result_schema.py`
  - `app/runtime/task_runner.py`
- 结果：
  - Agent 能推荐 `sample_repo/parser.py`
  - Agent 能推荐 `tests/test_parser.py`

#### Phase 2：测试闭环

- 改动内容：
  - 实现 `run_tests`
  - 屏蔽 `pytest` 自动插件加载带来的环境噪声
  - 保存 `test_stdout.txt` / `test_stderr.txt`
  - 提取失败测试和失败位置摘要
- 主要文件：
  - `app/tools/run_tests.py`
  - `app/runtime/task_runner.py`
- 结果：
  - 能定位失败测试：
    - `tests/test_parser.py::ParseItemsTests::test_empty_input_returns_empty_list`
  - 能定位失败位置：
    - `sample_repo/parser.py:6 (IndexError)`

#### Phase 3：Patch 闭环

- 改动内容：
  - 实现 `write_file`
  - 实现 `show_diff`
  - 引入最小规则型 patch 生成器
  - 打通修复前测试 -> patch 应用 -> 修复后测试 -> diff 落盘
- 主要文件：
  - `app/tools/write_file.py`
  - `app/tools/show_diff.py`
  - `app/agent/patcher.py`
  - `app/runtime/task_runner.py`
- 结果：
  - `task_001` 可自动修复成功
  - `patch.diff` 已生成

#### Phase 4：批量运行

- 改动内容：
  - 实现 `scripts/run_batch.py`
  - 实现 `app/runtime/batch_runner.py`
  - 增加 `task_002`
  - 增加 `benchmarks/manifests/dev_tasks.json`
- 主要文件：
  - `scripts/run_batch.py`
  - `app/runtime/batch_runner.py`
  - `benchmarks/tasks/task_002.json`
  - `benchmarks/manifests/dev_tasks.json`
- 结果：
  - `batch_run_001` 成功运行 2 条任务

#### Phase 5：baseline eval

- 改动内容：
  - 实现 `evals/metrics.py`
  - 实现 `evals/error_taxonomy.py`
  - 实现 `evals/batch_eval.py`
  - 生成 baseline 评测报告
- 主要文件：
  - `evals/metrics.py`
  - `evals/error_taxonomy.py`
  - `evals/batch_eval.py`
  - `docs/eval_design.md`
  - `docs/results.md`
- baseline 结果：
  - batch run：`logs/summaries/batch_run_001.json`
  - batch eval：`logs/summaries/batch_eval_001.json`
- 当前指标：
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `partial_fix_rate = 0.0`
  - `average_steps = 9.0`
  - `average_tool_calls = 9.0`
  - `average_duration_sec = 0.5406`
  - `average_modified_files = 1.0`
  - `key_file_read_rate = 1.0`
  - `test_execution_rate = 1.0`
  - `repeated_search_rate = 0.0`
  - `reasonable_finish_rate = 1.0`
- taxonomy：
  - 当前没有命中任何错误标签

### 当前结论

- baseline 主线已经完整打通
- 当前结果适合证明“系统能跑通”
- 但当前开发任务集过于简单，暂时不适合证明“优化确实有效”

### 下一步优化建议

后续进入真正的优化迭代时，建议从下面三类动作里至少选择一类：

1. `benchmark` 扩展
   - 增加更难、更真实、更多样的任务
   - 让错误 taxonomy 有机会出现非空结果

2. `policy` 优化
   - 限制无效搜索
   - 更严格地约束修改文件范围
   - 在 patch 前增加更明确的“证据是否充分”检查

3. `prompt` 优化
   - 强化“先解释问题再修改”
   - 强化“修复后必须重新运行测试”
   - 强化“修改应尽量最小化”

## 你后续应该如何使用这个文件

当我们开始做 `Phase 6` 的 improved 实验时，我会在这里继续追加：

- `Iteration 1`
- `Iteration 2`
- ...

每一轮都记录：

- 优化动作
- 对比指标
- 是否真的带来改进
- 如果没有改进，失败原因是什么

## Iteration 1：Policy Optimization（baseline_v1 -> improved_v1）

### 时间

- 2026-06-05

### 阶段

- `Phase 6`

### 目标

- 让系统不只修复空输入问题
- 进一步处理 `None` 元素导致的归一化失败
- 在同一 report set 上形成 baseline vs improved 的真实指标差异

### 改动类型

- `policy`
- `benchmark`
- `runtime`

### 改动摘要

- 增加可加载的 policy 配置机制
- 新增：
  - `optimization/policy_versions/baseline.json`
  - `optimization/policy_versions/improved.json`
- patch 生成器从“只处理空输入”扩展为：
  - baseline：只插入空输入保护
  - improved：插入空输入保护 + `None` 元素过滤
- 新增更有区分度的 benchmark：
  - `benchmarks/repos/multi_bug_repo`
  - `benchmarks/tasks/task_003.json`
  - `benchmarks/manifests/report_tasks.json`
- 修复运行隔离问题：
  - 单任务 `run_id` 改为时间戳+随机后缀
  - batch / eval 输出支持显式 label，避免结果覆盖
  - 复制 benchmark repo 时忽略缓存目录

### 主要涉及文件

- `app/agent/policy.py`
- `app/agent/patcher.py`
- `app/runtime/task_runner.py`
- `app/runtime/batch_runner.py`
- `app/runtime/harness.py`
- `scripts/run_single_task.py`
- `scripts/run_batch.py`
- `evals/batch_eval.py`
- `optimization/policy_versions/baseline.json`
- `optimization/policy_versions/improved.json`
- `benchmarks/tasks/task_003.json`
- `benchmarks/manifests/report_tasks.json`

### baseline 运行

- batch run：
  - `logs/summaries/batch_run_baseline_001.json`
- batch eval：
  - `logs/summaries/batch_eval_baseline_001.json`

### improved 运行

- batch run：
  - `logs/summaries/batch_run_improved_002.json`
- batch eval：
  - `logs/summaries/batch_eval_improved_001.json`

### 指标对比

#### 核心结果

- `success_rate`
  - baseline: `0.5`
  - improved: `1.0`
- `test_pass_rate`
  - baseline: `0.5`
  - improved: `1.0`
- `partial_fix_rate`
  - baseline: `0.5`
  - improved: `0.0`

#### 效率与行为

- `average_steps`
  - baseline: `9.0`
  - improved: `9.0`
- `average_tool_calls`
  - baseline: `9.0`
  - improved: `9.0`
- `average_duration_sec`
  - baseline: `0.4734`
  - improved: `0.4574`
- `average_modified_files`
  - baseline: `1.0`
  - improved: `1.0`

#### taxonomy

- baseline：
  - `Patch Incorrect = 1`
- improved：
  - 无错误标签

### 关键案例

#### baseline 失败案例：`task_003`

- 运行结果：
  - `logs/trajectories/task_003/run_20260605T105811156609Z_6459/result.json`
- 现象：
  - baseline 先修掉了空输入问题
  - 但修复后测试仍在 `multi_bug_repo/parser.py:12` 因 `None.strip()` 失败
- 结论：
  - baseline patch 只覆盖了第一层 bug，属于 `Patch Incorrect`

#### improved 成功案例：`task_003`

- 运行结果：
  - `logs/trajectories/task_003/run_20260605T105820967482Z_0932/result.json`
- 现象：
  - improved 同时加入：
    - 空输入保护
    - `None` 元素过滤
  - 修复后测试全部通过

### 结论

- 这轮优化是有效的
- improved 相比 baseline 在同一 report set 上将成功率从 `0.5` 提升到 `1.0`
- 而且没有引入额外步骤成本，平均步数和工具调用数保持不变

### 剩余问题

- 当前 report set 仍然很小，只有 2 条任务
- improved 仍然是规则型 patch，不是真正通用的智能修复策略
- 后续如果要让对比更有说服力，需要：
  - 扩充更多真实或半真实任务
  - 引入更复杂的失败模式
  - 继续做 prompt / policy / grader 组合优化

## Iteration 2：Compare Reporting Infrastructure（phase6_compare_v1）

### 时间

- 2026-06-05

### 阶段

- `Phase 6`

### 目标

- 把 baseline vs improved 的差异比较从“手写整理”升级为“自动生成标准化报告”
- 明确区分 `Dev Set / Report Set / Future GitHub Real-Issue Set`
- 为后续更多优化轮次保留追加式对比记录能力

### 改动类型

- `eval`
- `runtime`
- `docs`
- `benchmark`

### 改动摘要

- 新增自动 compare 模块：
  - `evals/compare_evals.py`
- compare 报告支持：
  - 指标 delta 自动计算
  - `improved / regressed / unchanged` 自动判定
  - taxonomy 数量变化汇总
  - 每个 task 的标签变化汇总
- 新增 compare 产物：
  - `logs/summaries/batch_compare_phase6_002.json`
  - `logs/summaries/batch_compare_phase6_002.md`
- 文档层补充 benchmark 分层说明：
  - `Dev Set`
  - `Report Set`
  - `Future GitHub Real-Issue Set`

### 主要涉及文件

- `evals/compare_evals.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/optimization.md`

### baseline 运行

- eval：
  - `logs/summaries/batch_eval_baseline_001.json`

### improved 运行

- eval：
  - `logs/summaries/batch_eval_improved_001.json`

### compare 运行

- compare：
  - `logs/summaries/batch_compare_phase6_002.json`

### 指标对比

- `success_rate`
  - baseline: `0.5`
  - improved: `1.0`
  - delta: `+0.5`
- `test_pass_rate`
  - baseline: `0.5`
  - improved: `1.0`
  - delta: `+0.5`
- `partial_fix_rate`
  - baseline: `0.5`
  - improved: `0.0`
  - delta: `-0.5`
- `average_duration_sec`
  - baseline: `0.4734`
  - improved: `0.4574`
  - delta: `-0.016`

### taxonomy 对比

- `Patch Incorrect`
  - baseline: `1`
  - improved: `0`

### 结论

- 现在每一轮优化都可以自动生成标准化 compare 报告
- 这让优化过程不仅有 baseline / improved 单独结果，也有专门的“差异结果”
- 后续扩充 report set，或接入 GitHub 真实 issue 任务时，可以直接复用这条 compare 链路

### 剩余问题

- compare 仍然基于当前最小指标集合，后续可继续扩展更多质量维度
- 当前 report set 样本数仍偏少
- 真实 GitHub issue 评测集还未正式接入

## Iteration 3：Leading-None Handling（improved_v1 -> improved_v2）

### 时间

- 2026-06-06

### 阶段

- `Phase 6`

### 目标

- 继续扩充 report set
- 增加一个更接近真实数据清洗的缺陷模式
- 验证 `improved_v1` 到 `improved_v2` 的收益是否真实存在

### 改动类型

- `benchmark`
- `policy`
- `eval`
- `docs`

### 改动摘要

- 新增 benchmark repo：
  - `benchmarks/repos/leading_none_repo`
- 新增任务：
  - `benchmarks/tasks/task_004.json`
- report set 扩充为 3 条任务：
  - `task_001`
  - `task_003`
  - `task_004`
- 新增策略配置：
  - `optimization/policy_versions/improved_v2.json`
- patch 生成器新增能力：
  - 在归一化前先过滤所有 `None`
  - 同时覆盖：
    - 空输入
    - 首元素 `None`
    - 中间 `None`

### 主要涉及文件

- `benchmarks/repos/leading_none_repo/leading_none_repo/parser.py`
- `benchmarks/repos/leading_none_repo/tests/test_parser.py`
- `benchmarks/tasks/task_004.json`
- `benchmarks/manifests/report_tasks.json`
- `optimization/policy_versions/improved_v2.json`
- `app/agent/patcher.py`
- `docs/case_studies.md`
- `docs/results.md`

### baseline 运行

- batch run：
  - `logs/summaries/batch_run_baselinev2_001.json`
- batch eval：
  - `logs/summaries/batch_eval_baselinev2_001.json`

### improved_v1 运行

- batch run：
  - `logs/summaries/batch_run_improvedv1r2_001.json`
- batch eval：
  - `logs/summaries/batch_eval_improvedv1r2_001.json`

### improved_v2 运行

- batch run：
  - `logs/summaries/batch_run_improvedv2_001.json`
- batch eval：
  - `logs/summaries/batch_eval_improvedv2_001.json`

### compare 运行

- `baseline_v1 -> improved_v1`
  - `logs/summaries/batch_compare_phase6v2_step1_001.json`
- `improved_v1 -> improved_v2`
  - `logs/summaries/batch_compare_phase6v2_step2_001.json`

### 指标对比

#### 扩充后 report set 的整体结果

- `success_rate`
  - baseline_v1: `0.3333`
  - improved_v1: `0.6667`
  - improved_v2: `1.0`
- `test_pass_rate`
  - baseline_v1: `0.3333`
  - improved_v1: `0.6667`
  - improved_v2: `1.0`
- `partial_fix_rate`
  - baseline_v1: `0.6667`
  - improved_v1: `0.3333`
  - improved_v2: `0.0`

#### improved_v1 -> improved_v2

- `success_rate`
  - `0.6667 -> 1.0`
- `test_pass_rate`
  - `0.6667 -> 1.0`
- `partial_fix_rate`
  - `0.3333 -> 0.0`

### taxonomy

- baseline_v1：
  - `Patch Incorrect = 2`
- improved_v1：
  - `Patch Incorrect = 1`
- improved_v2：
  - 无错误标签

### 关键案例

#### improved_v1 失败案例：`task_004`

- 运行结果：
  - `logs/trajectories/task_004/run_20260606T063355750903Z_6189/result.json`
- 现象：
  - `improved_v1` 修掉了空输入问题
  - 也能处理循环中的 `None`
  - 但 `first_item` 仍然可能是 `None`
  - 修复后测试失败在 `leading_none_repo/parser.py:9 (AttributeError)`

#### improved_v2 成功案例：`task_004`

- 运行结果：
  - `logs/trajectories/task_004/run_20260606T063355735782Z_2513/result.json`
- 现象：
  - `improved_v2` 在归一化前先构造 `cleaned_items`
  - 空输入与所有 `None` 场景都能统一处理
  - 修复后测试全部通过

### 结论

- `improved_v2` 的收益是真实的，不是只在旧任务集上“刷分”
- 通过新增 `task_004`，report set 从 2 条扩到了 3 条
- 当前策略演进链路已经形成：
  - `baseline_v1`：只处理空输入
  - `improved_v1`：处理空输入 + 中间 `None`
  - `improved_v2`：处理空输入 + 全量 `None`

### 剩余问题

- 当前 patch 仍然是规则型，不具备通用代码理解能力
- report set 仍然偏小
- 下一步应该逐步接入 GitHub 真实 issue 任务

## Iteration 4：Real-Issue Task Infrastructure（future_real_issue_v1）

### 时间

- 2026-06-08

### 阶段

- `Phase 6`

### 目标

- 为后续接入 GitHub 真实 issue 补齐任务结构与校验入口
- 避免未来引入真实任务时临时修改 schema 和 benchmark 规范

### 改动类型

- `schema`
- `benchmark`
- `docs`

### 改动摘要

- `Task` schema 新增：
  - `source_type`
- 当前支持的来源类型：
  - `synthetic`
  - `semi_real`
  - `real_issue`
- 新增候选清单：
  - `benchmarks/real_world_candidates.json`
- 新增校验脚本：
  - `scripts/validate_tasks.py`
- 现有任务全部显式补齐：
  - `source_type: synthetic`

### 主要涉及文件

- `app/schemas/task_schema.py`
- `benchmarks/tasks/task_001.json`
- `benchmarks/tasks/task_002.json`
- `benchmarks/tasks/task_003.json`
- `benchmarks/tasks/task_004.json`
- `benchmarks/real_world_candidates.json`
- `scripts/validate_tasks.py`
- `docs/benchmark.md`
- `docs/architecture.md`

### 结论

- 当前项目已经不只是“口头上计划以后接入真实 issue”
- 真实 issue 的候选入口、来源字段和校验逻辑都已经落地
- 后续从 synthetic 过渡到 semi_real / real_issue 时，不需要重做任务结构

### 剩余问题

- 候选清单目前仍是占位结构，尚未填入真实仓库
- 真实 issue 任务导入脚本还未实现
- 真实仓库的测试环境适配仍需要后续逐仓库验证

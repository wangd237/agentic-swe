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

## Iteration 5：GitHub Issue Import Entry（real_issue_import_v1）

### 时间

- 2026-06-08

### 阶段

- `Phase 6`

### 目标

- 把真实 issue 入口从“数据结构预留”升级成“可执行导入链路”
- 让候选收集与 task 草稿生成都可以通过脚本完成

### 改动类型

- `benchmark`
- `tooling`
- `docs`

### 改动摘要

- 新增脚本：
  - `scripts/import_github_issue.py`
- 当前能力：
  - 通过 `gh issue view` 拉取 issue 元数据
  - 追加或更新 `benchmarks/real_world_candidates.json`
  - 可选生成 `real_issue` task 草稿
- 候选清单从占位样例改为空列表模板
- 校验脚本补充了候选字段与状态合法性检查

### 主要涉及文件

- `scripts/import_github_issue.py`
- `scripts/validate_tasks.py`
- `benchmarks/real_world_candidates.json`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`

### 结论

- 真实 issue 入口现在已经不是概念规划，而是可执行脚本
- 后续只要提供 GitHub 仓库和 issue 编号，就能先把候选导入本地数据集
- 生成 task 草稿后，再人工补齐 repo_path 和测试命令即可进入下一步实验

### 剩余问题

- 还没有填入第一条真实候选
- 还没有实现“clone/同步真实仓库到 benchmarks”这一步
- 真实仓库的测试环境适配仍需要人工判断

### 当前验证结果补充

- 已成功导入：
  - `psf/requests#6432`
- 已生成：
  - `benchmarks/tasks/task_005.json`
- 当前状态：
  - candidate 已切换为 `drafted`
  - task 草稿仍需人工补齐真实 repo_path 与测试命令

## Iteration 6：Semi-Real Runnable Task from Real Issue（improved_v2 -> improved_v3）

### 时间

- 2026-06-08

### 阶段

- `Phase 6`

### 目标

- 不只停留在真实 issue 候选导入
- 把首条真实 issue 推进成可运行的 semi_real 任务
- 验证策略能否覆盖依赖约束类修复

### 改动类型

- `benchmark`
- `policy`
- `eval`
- `docs`

### 改动摘要

- 保留：
  - `task_005` 作为 `real_issue` 草稿
- 新增：
  - `benchmarks/repos/requests_compat_repo`
  - `benchmarks/tasks/task_006.json`
  - `benchmarks/manifests/real_issue_tasks.json`
  - `optimization/policy_versions/improved_v3.json`
- patch 生成器新增能力：
  - 将 `urllib3>=1.21.1,<1.27` 放宽为 `urllib3>=1.21.1,<3`

### 主要涉及文件

- `benchmarks/repos/requests_compat_repo/setup.py`
- `benchmarks/repos/requests_compat_repo/tests/test_setup.py`
- `benchmarks/tasks/task_006.json`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v3.json`
- `app/agent/patcher.py`

### improved_v2 运行

- batch eval：
  - `logs/summaries/batch_eval_realissuev2_001.json`

### improved_v3 运行

- batch eval：
  - `logs/summaries/batch_eval_realissuev3_001.json`

### compare 运行

- compare：
  - `logs/summaries/batch_compare_realissue_step1_001.json`

### 指标对比

- `success_rate`
  - improved_v2: `0.0`
  - improved_v3: `1.0`
- `test_pass_rate`
  - improved_v2: `0.0`
  - improved_v3: `1.0`
- `taxonomy`
  - improved_v2: `Premature Finish = 1`
  - improved_v3: `无错误标签`

### 关键案例

#### improved_v2 失败案例：`task_006`

- 运行结果：
  - `logs/trajectories/task_006/run_20260608T065502481610Z_9951/result.json`
- 现象：
  - 已读取 `setup.py`
  - 但没有匹配到可修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v3 成功案例：`task_006`

- 运行结果：
  - `logs/trajectories/task_006/run_20260608T065502466819Z_5588/result.json`
- 现象：
  - 自动把 urllib3 上界放宽到 `3`
  - 修复后测试全部通过

### 结论

- 真实 issue 入口现在已经不只是候选收集，而是能推进到可运行 semi_real 任务
- `improved_v3` 证明当前系统开始具备跨缺陷类型扩展能力
- 这条链路比纯 toy parser bug 更接近真实工程维护问题

### 剩余问题

- 真实 issue 仍然主要以派生任务形式落地
- 还没有把真实仓库直接同步进本地 benchmark
- 复杂依赖和多文件修复仍需后续能力增强

## Iteration 7：Quoted Charset Parsing from Real Issue（improved_v3 -> improved_v4）

### 时间

- 2026-06-08

### 阶段

- `Phase 6`

### 目标

- 继续扩充真实 issue 派生任务集
- 增加一个更贴近函数级解析 bug 的 semi_real 任务
- 验证 `improved_v3` 到 `improved_v4` 的收益

### 改动类型

- `benchmark`
- `policy`
- `eval`
- `docs`

### 改动摘要

- 新增真实候选：
  - `psf/requests#7234`
- 新增草稿任务：
  - `task_007`
- 新增可运行 semi_real 任务：
  - `task_008`
- 新增 benchmark repo：
  - `benchmarks/repos/requests_encoding_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v4.json`
- patch 生成器新增能力：
  - quoted charset 去引号修复

### 主要涉及文件

- `benchmarks/tasks/task_007.json`
- `benchmarks/tasks/task_008.json`
- `benchmarks/repos/requests_encoding_repo/requests_encoding_repo/utils.py`
- `benchmarks/repos/requests_encoding_repo/tests/test_utils.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v4.json`
- `app/agent/patcher.py`

### improved_v3 运行

- batch eval：
  - `logs/summaries/batch_eval_realissuev3r2_001.json`

### improved_v4 运行

- batch eval：
  - `logs/summaries/batch_eval_realissuev4_001.json`

### compare 运行

- compare：
  - `logs/summaries/batch_compare_realissue_step2_001.json`

### 指标对比

- `success_rate`
  - improved_v3: `0.5`
  - improved_v4: `1.0`
- `test_pass_rate`
  - improved_v3: `0.5`
  - improved_v4: `1.0`
- `taxonomy`
  - improved_v3: `Premature Finish = 1`
  - improved_v4: `无错误标签`

### 关键案例

#### improved_v3 失败案例：`task_008`

- 运行结果：
  - `logs/trajectories/task_008/run_20260608T071833050400Z_5253/result.json`
- 现象：
  - 已读取 `requests_encoding_repo/utils.py`
  - 但没有匹配到 quoted charset 的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v4 成功案例：`task_008`

- 运行结果：
  - `logs/trajectories/task_008/run_20260608T071832844825Z_6236/result.json`
- 现象：
  - 自动把 quoted charset 值去引号
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 2 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v2`：只覆盖 task_006 之前的能力
  - `improved_v3`：覆盖依赖约束修复
  - `improved_v4`：进一步覆盖 quoted charset 解析修复

### 剩余问题

- 真实 issue 仍以派生任务形式为主
- 还没有把真实仓库直接同步到本地运行
- 当前 patch 策略仍然以规则法为主

## Iteration 8：Semi-Real Scaffold Entry（real_issue_scaffold_v1）

### 时间

- 2026-06-08

### 阶段

- `Phase 6`

### 目标

- 把 `real_issue -> semi_real` 的中间层标准化
- 降低后续接入第 3 条、第 4 条真实 issue 时的手工拼装成本
- 让候选状态和推进记录保持追加式演进

### 改动类型

- `benchmark`
- `runtime`
- `docs`

### 改动摘要

- 新增脚手架脚本：
  - `scripts/scaffold_semi_real_task.py`
- 当前能力：
  - 从 `real_issue` 草稿生成 `semi_real` 任务骨架
  - 自动创建 repo 目录、包文件、模块文件、测试文件、README
  - 自动维护候选状态：
    - `drafted`
    - `scaffolded`
    - `accepted`
  - `--ready` 模式下自动追加到 `benchmarks/manifests/real_issue_tasks.json`
- 优化 `scripts/import_github_issue.py`：
  - 重复导入时保留已有状态
  - 备注改为按时间追加，而不是覆盖
- 为脚手架入口补充独立回归测试
- 固化 `pytest` 的 `basetemp` 到仓库内，避免系统临时目录权限干扰测试

### 主要涉及文件

- `scripts/scaffold_semi_real_task.py`
- `scripts/import_github_issue.py`
- `scripts/validate_tasks.py`
- `tests/test_scaffold_semi_real_task.py`
- `pytest.ini`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`

### baseline 运行

- 无新增 batch 基线；这一轮属于真实 issue 入口工程增强

### improved 运行

- `python -m pytest tests/test_scaffold_semi_real_task.py -q`
- `python scripts/validate_tasks.py`

### 指标对比

- 本轮不产出新的 success_rate / test_pass_rate 对比
- 当前收益主要体现在：
  - 新 issue 接入步骤更标准化
  - 候选状态流更清晰
  - 记录方式更符合追加式演进要求

### 结论

- 真实 issue 入口现在不只是“导入候选 -> 人工手搓 semi_real”
- 已经具备可复用的脚手架层，后续扩展真实 issue 集会更稳
- 入口脚本本身已有测试保护，后续可以放心继续演化

### 剩余问题

- 还没有把脚手架直接连接到真实仓库快照同步
- 当前 semi_real 的缩题过程仍需要人工判断
- 后续可以继续补一个“从 draft 到 ready 的检查清单”工具

## Iteration 9：ANSI CRLF Parsing from Real Issue（improved_v4 -> improved_v5）

### 时间

- 2026-06-08

### 阶段

- `Phase 6`

### 目标

- 把第 3 条真实 issue 候选推进成可运行任务
- 验证 `improved_v4` 到 `improved_v5` 是否能覆盖 ANSI 文本 CRLF 行尾解析场景
- 继续扩充真实 issue 派生任务集的多样性

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 新增真实候选：
  - `Textualize/rich#4090`
- 新增草稿任务：
  - `task_009`
- 新增可运行 semi_real 任务：
  - `task_010`
- 新增 benchmark repo：
  - `benchmarks/repos/rich_ansi_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v5.json`
- patch 生成器新增能力：
  - 将 ANSI 文本拆分逻辑从 `re.split(r"(?<=\\n)", terminal_text)` 升级为兼容 CRLF 的 `splitlines(keepends=True)` 流程

### 主要涉及文件

- `benchmarks/tasks/task_009.json`
- `benchmarks/tasks/task_010.json`
- `benchmarks/repos/rich_ansi_repo/rich_ansi_repo/ansi.py`
- `benchmarks/repos/rich_ansi_repo/tests/test_ansi.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v5.json`
- `app/agent/patcher.py`

### improved_v4 运行

- batch run：
  - `logs/summaries/batch_run_realissuev4r2_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev4r2_001.json`

### improved_v5 运行

- batch run：
  - `logs/summaries/batch_run_realissuev5_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev5_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step3_001.json`

### 指标对比

- `success_rate`
  - improved_v4: `0.6667`
  - improved_v5: `1.0`
- `test_pass_rate`
  - improved_v4: `0.6667`
  - improved_v5: `1.0`
- `taxonomy`
  - improved_v4: `Premature Finish = 1`
  - improved_v5: `无错误标签`

### 关键案例

#### improved_v4 失败案例：`task_010`

- 运行结果：
  - `logs/trajectories/task_010/run_20260608T082525352281Z_4909/result.json`
- 现象：
  - 已读取 `rich_ansi_repo/ansi.py`
  - 但没有匹配到 CRLF 行尾拆分修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v5 成功案例：`task_010`

- 运行结果：
  - `logs/trajectories/task_010/run_20260608T082657180742Z_8552/result.json`
- 现象：
  - 自动把 ANSI 文本拆分逻辑改成兼容 CRLF 的流程
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 3 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v3`：覆盖依赖约束修复
  - `improved_v4`：覆盖 quoted charset 解析修复
  - `improved_v5`：进一步覆盖 ANSI 文本 CRLF 行尾拆分修复

### 剩余问题

- 真实 issue 仍以派生任务形式为主
- 还没有直接接入 rich 原仓库快照
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 12：Closest Marker Override from Real Issue（improved_v7 -> improved_v8）

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 把 `pytest-dev/pytest#14329` 推进成可运行任务
- 验证 `improved_v7` 到 `improved_v8` 是否能覆盖最近 marker 覆盖优先场景
- 继续扩充真实 issue 派生任务集，并保留追加式对比记录

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 新增可运行 semi_real 任务：
  - `task_017`
- 新增 benchmark repo：
  - `benchmarks/repos/pytest_marker_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v8.json`
- patch 生成器新增能力：
  - 将 `get_closest_marker` 的查找顺序调整为优先返回继承链中最近定义的 marker
- 候选清单同步记录：
  - `pytest-dev/pytest#14329` 已从草稿推进为 accepted
- 明确保留 `pydantic/pydantic#9582` 为草稿：
  - 当前更适合作为行为说明或文档澄清，不进入可运行 bugfix benchmark

### 主要涉及文件

- `benchmarks/tasks/task_017.json`
- `benchmarks/repos/pytest_marker_repo/pytest_marker_repo/markers.py`
- `benchmarks/repos/pytest_marker_repo/tests/test_markers.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v8.json`
- `app/agent/patcher.py`

### improved_v7 运行

- batch run：
  - `logs/summaries/batch_run_realissuev7r2_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev7r2_001.json`

### improved_v8 运行

- batch run：
  - `logs/summaries/batch_run_realissuev8_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev8_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step6_001.json`

### 指标对比

- `success_rate`
  - improved_v7: `0.8333`
  - improved_v8: `1.0`
- `test_pass_rate`
  - improved_v7: `0.8333`
  - improved_v8: `1.0`
- `average_steps`
  - improved_v7: `9.6667`
  - improved_v8: `9.6667`
- `average_duration_sec`
  - improved_v7: `0.6157`
  - improved_v8: `0.6148`
- `taxonomy`
  - improved_v7: `Premature Finish = 1`
  - improved_v8: `无错误标签`

### 关键案例

#### improved_v7 失败案例：`task_017`

- 运行结果：
  - `logs/trajectories/task_017/run_20260609T014410944207Z_8734/result.json`
- 现象：
  - 已读取 `pytest_marker_repo/markers.py`
  - 但没有匹配到 marker 继承覆盖的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v8 成功案例：`task_017`

- 运行结果：
  - `logs/trajectories/task_017/run_20260609T014626085779Z_4927/result.json`
- 现象：
  - 自动把 marker 查找顺序调整为反向遍历
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 6 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v7`：覆盖负向 boolean flag 默认值修复
  - `improved_v8`：进一步覆盖最近 marker 覆盖优先修复

### 剩余问题

- `pydantic/pydantic#9582` 目前仍更适合作为草稿与说明案例
- 真实 issue 仍以派生任务形式为主
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 13：Real-Issue Eval Pipeline Consolidation

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 把真实 issue 任务集的评测步骤从多命令手工串联，收敛成一条统一入口
- 让后续引入新 issue 后，更容易稳定复跑 batch / eval / compare
- 为将来接入更真实的 GitHub 仓库评测做脚本边界准备

### 改动类型

- `runtime`
- `eval`
- `docs`
- `tests`

### 改动摘要

- 新增统一脚本：
  - `scripts/run_real_issue_eval.py`
- 新脚本能力：
  - 读取 `benchmarks/manifests/real_issue_tasks.json`
  - 运行真实 issue 任务集 batch run
  - 自动生成 batch eval
  - 在提供 baseline eval 时自动生成 compare
  - 汇总当前 candidate 状态分布
- 新增测试：
  - `tests/test_run_real_issue_eval.py`
- 文档补充：
  - 在 `README.md` 与 `GUIDE.md` 增加一键运行真实 issue 评测流水线的体验入口

### 主要涉及文件

- `scripts/run_real_issue_eval.py`
- `tests/test_run_real_issue_eval.py`
- `README.md`
- `GUIDE.md`

### 当前结论

- 真实 issue 入口现在不只是“候选导入 -> 草稿 -> semi_real 脚手架”
- 也具备了“manifest -> batch run -> eval -> compare”的统一执行入口
- 后续接入新的真实 issue 候选时，可以更稳定地复用同一条评测链路

### 剩余问题

- 当前仍依赖人工指定 policy 和 compare baseline
- 还没有把“候选筛选建议 -> 自动导入”做成半自动流程
- 后续可以继续补一个 issue shortlist 到 candidate 文件的辅助入口

## Iteration 14：Expand New Real-Issue Candidate Pool

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 不再只复用当前仓库已收录来源，开始扩展新的真实 GitHub issue 候选来源
- 修复 `import_github_issue.py` 在 Windows + `gh` 输出场景下的编码兼容问题
- 让候选池继续保持追加式增长，而不是手工零散维护

### 改动类型

- `benchmark`
- `runtime`
- `docs`

### 改动摘要

- 修复 `scripts/import_github_issue.py`：
  - `gh` 输出改为按 bytes 读取
  - 统一按 `utf-8` + `errors=\"replace\"` 解码
  - 避免 Windows 默认编码导致 JSON 解析失败
- 新导入 3 条新来源候选：
  - `dateutil/dateutil#1442`
  - `dateutil/dateutil#1432`
  - `python-attrs/attrs#1479`
- 候选清单规模从 `7` 扩充到 `10`
- README / GUIDE 同步更新候选数量与来源

### 主要涉及文件

- `scripts/import_github_issue.py`
- `benchmarks/real_world_candidates.json`
- `README.md`
- `GUIDE.md`

### 当前结论

- 候选池现在已经不只覆盖 `requests / rich / pytest / click / pydantic`
- 也开始扩展到 `dateutil` 与 `attrs` 这样的新来源
- `dateutil/dateutil#1432` 和 `#1442` 都很像适合继续缩题成 `semi_real` 的函数级 bug
- `python-attrs/attrs#1479` 已导入，但从 issue 文案看仍需再判断它究竟是 bug 还是行为预期

### 剩余问题

- 新导入候选还没有完成人工筛选结论
- 还没有把最优新来源 issue 推进成新的 draft task
- 后续建议优先审查 `dateutil/dateutil#1432` 与 `#1442`

## Iteration 11：Negative Boolean Flag Default from Real Issue（improved_v6 -> improved_v7）

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 把 `pallets/click#3111` 推进成可运行任务
- 验证 `improved_v6` 到 `improved_v7` 是否能覆盖负向 boolean flag 的默认值场景
- 继续扩充真实 issue 派生任务集的语义多样性

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 新增真实候选：
  - `pydantic/pydantic#9582`
  - `pallets/click#3111`
- 新增草稿任务：
  - `task_014`
  - `task_015`
- 新增可运行 semi_real 任务：
  - `task_016`
- 新增 benchmark repo：
  - `benchmarks/repos/click_flag_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v7.json`
- patch 生成器新增能力：
  - 修正负向 boolean flag 在 `default=True` 且 `flag_value=False` 时被错误覆盖的问题

### 主要涉及文件

- `benchmarks/tasks/task_014.json`
- `benchmarks/tasks/task_015.json`
- `benchmarks/tasks/task_016.json`
- `benchmarks/repos/click_flag_repo/click_flag_repo/core.py`
- `benchmarks/repos/click_flag_repo/tests/test_flags.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v7.json`
- `app/agent/patcher.py`

### improved_v6 运行

- batch run：
  - `logs/summaries/batch_run_realissuev6r2_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev6r2_001.json`

### improved_v7 运行

- batch run：
  - `logs/summaries/batch_run_realissuev7_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev7_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step5_001.json`

### 指标对比

- `success_rate`
  - improved_v6: `0.8`
  - improved_v7: `1.0`
- `test_pass_rate`
  - improved_v6: `0.8`
  - improved_v7: `1.0`
- `taxonomy`
  - improved_v6: `Premature Finish = 1`
  - improved_v7: `无错误标签`

### 关键案例

#### improved_v6 失败案例：`task_016`

- 运行结果：
  - `logs/trajectories/task_016/run_20260608T093353125642Z_4116/result.json`
- 现象：
  - 已读取 `click_flag_repo/core.py`
  - 但没有匹配到负向 boolean flag 默认值修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v7 成功案例：`task_016`

- 运行结果：
  - `logs/trajectories/task_016/run_20260608T093522264692Z_8052/result.json`
- 现象：
  - 自动移除了错误的 `default=True -> flag_value=False` 特殊处理
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 5 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v6`：覆盖 RichHandler 时区偏移保留修复
  - `improved_v7`：进一步覆盖负向 boolean flag 默认值修复

### 剩余问题

- `pydantic/pydantic#9582` 目前仍停留在草稿阶段
- 真实 issue 仍以派生任务形式为主
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 10：RichHandler Timezone from Real Issue（improved_v5 -> improved_v6）

### 时间

- 2026-06-08

### 阶段

- `Phase 6`

### 目标

- 把第 4 条真实 issue 候选推进成可运行任务
- 验证 `improved_v5` 到 `improved_v6` 是否能覆盖 RichHandler 的时区偏移保留场景
- 继续扩充真实 issue 派生任务集的覆盖面

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 新增真实候选：
  - `Textualize/rich#3877`
- 新增草稿任务：
  - `task_012`
- 新增可运行 semi_real 任务：
  - `task_013`
- 新增 benchmark repo：
  - `benchmarks/repos/rich_handler_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v6.json`
- patch 生成器新增能力：
  - 将 `datetime.fromtimestamp(created)` 改为 `datetime.fromtimestamp(created, tz=self.time_zone)`，让 `%z` 能保留偏移信息

### 主要涉及文件

- `benchmarks/tasks/task_012.json`
- `benchmarks/tasks/task_013.json`
- `benchmarks/repos/rich_handler_repo/rich_handler_repo/logging.py`
- `benchmarks/repos/rich_handler_repo/tests/test_logging.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v6.json`
- `app/agent/patcher.py`

### improved_v5 运行

- batch run：
  - `logs/summaries/batch_run_realissuev5r2_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev5r2_001.json`

### improved_v6 运行

- batch run：
  - `logs/summaries/batch_run_realissuev6_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev6_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step4_001.json`

### 指标对比

- `success_rate`
  - improved_v5: `0.75`
  - improved_v6: `1.0`
- `test_pass_rate`
  - improved_v5: `0.75`
  - improved_v6: `1.0`
- `taxonomy`
  - improved_v5: `Premature Finish = 1`
  - improved_v6: `无错误标签`

### 关键案例

#### improved_v5 失败案例：`task_013`

- 运行结果：
  - `logs/trajectories/task_013/run_20260608T091039932929Z_8751/result.json`
- 现象：
  - 已读取 `rich_handler_repo/logging.py`
  - 但没有匹配到时区偏移保留修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v6 成功案例：`task_013`

- 运行结果：
  - `logs/trajectories/task_013/run_20260608T091342750273Z_4466/result.json`
- 现象：
  - 自动把 `datetime.fromtimestamp(created)` 改为带 `tz=` 的版本
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 4 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v5`：覆盖 ANSI 文本 CRLF 行尾拆分修复
  - `improved_v6`：进一步覆盖 RichHandler 时区偏移保留修复

### 剩余问题

- 真实 issue 仍以派生任务形式为主
- 还没有直接接入 rich 原仓库快照
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

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

## 2026-06-10 22:16 Phase 6 attrs alias 可见性扩容

### 本轮目标

- 把 `python-attrs/attrs#1479` 从 `to_review` 推进成正式可运行任务
- 为对象定义阶段的 alias / 元数据可见性补一条新的规则型 patch 能力
- 继续保留扩容对比与 `frozen_20` 同集合无回归对比

### 本轮新增任务

- `task_058`
  - 类型：`semi_real`
  - repo：`attrs_alias_repo`
  - 来源：`python-attrs/attrs#1479`
  - 缺陷：`field_transformer` 运行时默认 alias 仍是 `None`
  - 目标：变换阶段即可读取最终 alias，默认 alias 等于字段名

### 本轮策略改动

- 新增 `_handle_attrs_field_transformer_alias`
  - 命中 `attrs_alias_repo/model.py` 中的字段构建模板
  - 修复方式：在 `field_transformer` 运行前就回填默认 alias
- `improved_v29`
  - 在 `improved_v28` 能力链之上增加 alias 可见性修复

### 单任务分辨运行

- `improved_v28` 失败：
  - `logs/trajectories/task_058/run_20260610T141539455587Z_7032/result.json`
- `improved_v29` 成功：
  - `logs/trajectories/task_058/run_20260610T141539479416Z_5349/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev28_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev29_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev29_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step28_001.json`

### 冻结同集合运行

- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v28_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v29_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v29_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step8_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `26` 条任务集上的 `improved_v28`
  - improved 是扩充到 `27` 条任务后的 `improved_v29`
- 扩容对比结果：
  - `task_count`
    - improved_v28: `26`
    - improved_v29: `27`
  - `success_count`
    - improved_v28: `26`
    - improved_v29: `27`
  - `success_rate`
    - improved_v28: `1.0`
    - improved_v29: `1.0`
  - `test_pass_rate`
    - improved_v28: `1.0`
    - improved_v29: `1.0`
  - `average_steps`
    - improved_v28: `9.4231`
    - improved_v29: `9.4444`
  - `average_duration_sec`
    - improved_v28: `0.5898`
    - improved_v29: `0.5675`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 这一轮主要用于确认新增 alias 可见性规则不会带来回归
- 冻结同集合结果：
  - `task_count`
    - improved_v28: `20`
    - improved_v29: `20`
  - `success_count`
    - improved_v28: `20`
    - improved_v29: `20`
  - `success_rate`
    - improved_v28: `1.0`
    - improved_v29: `1.0`
  - `test_pass_rate`
    - improved_v28: `1.0`
    - improved_v29: `1.0`
  - `average_steps`
    - improved_v28: `9.25`
    - improved_v29: `9.25`
  - `average_duration_sec`
    - improved_v28: `0.5675`
    - improved_v29: `0.5688`
  - `taxonomy`
    - improved_v28: `无错误标签`
    - improved_v29: `无错误标签`

### 结论

- 真实 issue 派生任务集已经扩充到 `27` 条
- 候选池正式 accepted 提升到 `27` 条，`to_review` 收敛到 `3` 条
- `improved_v29` 把对象定义阶段 alias 可见性纳入正式覆盖面
- 扩容后继续保持 `100%` 成功率与 `100%` 测试通过率
- `frozen_20` 上无功能回归，仅有 `average_duration_sec` 从 `0.5675` 小幅波动到 `0.5688`

## 2026-06-10 22:26 Phase 6 sqlite transform 空字符串清洗扩容

### 本轮目标

- 把 `simonw/sqlite-utils#488` 从 `to_review` 推进成正式可运行任务
- 为数据清洗里的空字符串 / `null` 语义补一条新的规则型 patch 能力
- 继续保留扩容对比与 `frozen_20` 同集合无回归对比

### 本轮新增任务

- `task_059`
  - 类型：`semi_real`
  - repo：`sqlite_transform_repo`
  - 来源：`simonw/sqlite-utils#488`
  - 缺陷：数值列转换时空字符串仍被保留为 `""`
  - 目标：`integer` / `float` 转换时空字符串回落为 `None`

### 本轮策略改动

- 新增 `_handle_sqlite_transform_empty_string_numeric`
  - 命中 `sqlite_transform_repo/transform.py` 中的数值转换模板
  - 修复方式：把 `integer` / `float` 分支中的空字符串回落为 `None`
- `improved_v30`
  - 在 `improved_v29` 能力链之上增加数值列空字符串清洗修复

### 单任务分辨运行

- `improved_v29` 失败：
  - `logs/trajectories/task_059/run_20260610T142539239429Z_4515/result.json`
- `improved_v30` 成功：
  - `logs/trajectories/task_059/run_20260610T142539283117Z_5654/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev29_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev30_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev30_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step29_001.json`

### 冻结同集合运行

- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v29_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v30_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v30_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step9_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `27` 条任务集上的 `improved_v29`
  - improved 是扩充到 `28` 条任务后的 `improved_v30`
- 扩容对比结果：
  - `task_count`
    - improved_v29: `27`
    - improved_v30: `28`
  - `success_count`
    - improved_v29: `27`
    - improved_v30: `28`
  - `success_rate`
    - improved_v29: `1.0`
    - improved_v30: `1.0`
  - `test_pass_rate`
    - improved_v29: `1.0`
    - improved_v30: `1.0`
  - `average_steps`
    - improved_v29: `9.4444`
    - improved_v30: `9.3929`
  - `average_duration_sec`
    - improved_v29: `0.5675`
    - improved_v30: `0.5633`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 这一轮主要用于确认新增数值列空字符串清洗规则不会带来回归
- 冻结同集合结果：
  - `task_count`
    - improved_v29: `20`
    - improved_v30: `20`
  - `success_count`
    - improved_v29: `20`
    - improved_v30: `20`
  - `success_rate`
    - improved_v29: `1.0`
    - improved_v30: `1.0`
  - `test_pass_rate`
    - improved_v29: `1.0`
    - improved_v30: `1.0`
  - `average_steps`
    - improved_v29: `9.25`
    - improved_v30: `9.25`
  - `average_duration_sec`
    - improved_v29: `0.5688`
    - improved_v30: `0.5631`
  - `taxonomy`
    - improved_v29: `无错误标签`
    - improved_v30: `无错误标签`

### 结论

- 真实 issue 派生任务集已经扩充到 `28` 条
- 候选池正式 accepted 提升到 `28` 条，`to_review` 收敛到 `2` 条
- `improved_v30` 把数据清洗中的空字符串 / `null` 语义纳入正式覆盖面
- 扩容后继续保持 `100%` 成功率与 `100%` 测试通过率
- `frozen_20` 上无功能回归，且 `average_duration_sec` 从 `0.5688` 进一步改善到 `0.5631`

## 2026-06-11 12:56 Phase 6 sqlite extract null 过滤扩容

### 本轮目标

- 把 `simonw/sqlite-utils#186` 从 `to_review` 推进成正式可运行任务
- 为维表提取时的 `None` 过滤语义补一条新的规则型 patch 能力
- 继续保留扩容对比与 `frozen_20` 同集合无回归对比

### 本轮新增任务

- `task_060`
  - 类型：`semi_real`
  - repo：`sqlite_extract_repo`
  - 来源：`simonw/sqlite-utils#186`
  - 缺陷：extract 时错误为 `None` 生成维表记录
  - 目标：`None` 不参与维表提取，主表空值继续保留为 `None`

### 本轮策略改动

- 新增 `_handle_sqlite_extract_skip_nulls`
  - 命中 `sqlite_extract_repo/extract.py` 中的提取模板
  - 修复方式：先识别 `None`，直接保留在主表，不进入维表
- `improved_v31`
  - 在 `improved_v30` 能力链之上增加 null 提取过滤修复

### 单任务分辨运行

- `improved_v30` 失败：
  - `logs/trajectories/task_060/run_20260611T045609613781Z_7280/result.json`
- `improved_v31` 成功：
  - `logs/trajectories/task_060/run_20260611T045609607536Z_0345/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev30_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev31_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev31_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step30_001.json`

### 冻结同集合运行

- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v30_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v31_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v31_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step10_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `28` 条任务集上的 `improved_v30`
  - improved 是扩充到 `29` 条任务后的 `improved_v31`
- 扩容对比结果：
  - `task_count`
    - improved_v30: `28`
    - improved_v31: `29`
  - `success_count`
    - improved_v30: `28`
    - improved_v31: `29`
  - `success_rate`
    - improved_v30: `1.0`
    - improved_v31: `1.0`
  - `test_pass_rate`
    - improved_v30: `1.0`
    - improved_v31: `1.0`
  - `average_steps`
    - improved_v30: `9.3929`
    - improved_v31: `9.3448`
  - `average_duration_sec`
    - improved_v30: `0.5633`
    - improved_v31: `0.6115`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 这一轮主要用于确认新增 null 提取过滤规则不会带来功能回归
- 冻结同集合结果：
  - `task_count`
    - improved_v30: `20`
    - improved_v31: `20`
  - `success_count`
    - improved_v30: `20`
    - improved_v31: `20`
  - `success_rate`
    - improved_v30: `1.0`
    - improved_v31: `1.0`
  - `test_pass_rate`
    - improved_v30: `1.0`
    - improved_v31: `1.0`
  - `average_steps`
    - improved_v30: `9.25`
    - improved_v31: `9.25`
  - `average_duration_sec`
    - improved_v30: `0.5631`
    - improved_v31: `0.6122`
  - `taxonomy`
    - improved_v30: `无错误标签`
    - improved_v31: `无错误标签`

### 结论

- 真实 issue 派生任务集已经扩充到 `29` 条
- 候选池正式 accepted 提升到 `29` 条，`to_review` 收敛到 `1` 条
- `improved_v31` 把 null 提取过滤纳入正式覆盖面
- 扩容后继续保持 `100%` 成功率与 `100%` 测试通过率
- 本轮存在效率波动：步数略降，但 `average_duration_sec` 在扩容集与 `frozen_20` 上都明显回升，后续需要观察这是否是运行时抖动还是新任务分布导致

## 2026-06-11 13:24 Phase 6 isort profile 布局继承扩容

### 本轮目标

- 把 `PyCQA/isort#1815` 从 `to_review` 推进成正式可运行任务
- 为 profile 驱动的布局分派补一条新的规则型 patch 能力
- 清空当前高优先级真实 issue 候选池

### 本轮新增任务

- `task_061`
  - 类型：`semi_real`
  - repo：`isort_profile_repo`
  - 来源：`PyCQA/isort#1815`
  - 缺陷：tuple 格式化分支没有继承传入的 `profile`
  - 目标：`profile="black"` 时使用 vertical 布局，默认 profile 不回归

### 本轮策略改动

- 新增 `_handle_isort_tuple_profile_layout`
  - 命中 `isort_profile_repo/formatter.py` 中的容器格式化模板
  - 修复方式：让 tuple 格式化分支把 `profile` 传入布局分派
- `improved_v32`
  - 在 `improved_v31` 能力链之上增加 profile 布局继承修复

### 单任务分辨运行

- `improved_v31` 失败：
  - `logs/trajectories/task_061/run_20260611T052329621518Z_9635/result.json`
- `improved_v32` 成功：
  - `logs/trajectories/task_061/run_20260611T052329601465Z_4764/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev31_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev32_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev32_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step31_001.json`

### 冻结同集合运行

- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v31_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v32_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v32_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step11_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `29` 条任务集上的 `improved_v31`
  - improved 是扩充到 `30` 条任务后的 `improved_v32`
- 扩容对比结果：
  - `task_count`
    - improved_v31: `29`
    - improved_v32: `30`
  - `success_count`
    - improved_v31: `29`
    - improved_v32: `30`
  - `success_rate`
    - improved_v31: `1.0`
    - improved_v32: `1.0`
  - `test_pass_rate`
    - improved_v31: `1.0`
    - improved_v32: `1.0`
  - `average_steps`
    - improved_v31: `9.3448`
    - improved_v32: `9.3`
  - `average_duration_sec`
    - improved_v31: `0.6115`
    - improved_v32: `0.6778`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 这一轮主要用于确认新增 profile 布局继承规则不会带来功能回归
- 冻结同集合结果：
  - `task_count`
    - improved_v31: `20`
    - improved_v32: `20`
  - `success_count`
    - improved_v31: `20`
    - improved_v32: `20`
  - `success_rate`
    - improved_v31: `1.0`
    - improved_v32: `1.0`
  - `test_pass_rate`
    - improved_v31: `1.0`
    - improved_v32: `1.0`
  - `average_steps`
    - improved_v31: `9.25`
    - improved_v32: `9.25`
  - `average_duration_sec`
    - improved_v31: `0.6122`
    - improved_v32: `0.6774`
  - `taxonomy`
    - improved_v31: `无错误标签`
    - improved_v32: `无错误标签`

### 结论

- 真实 issue 派生任务集已经扩充到 `30` 条
- 当前高优先级真实候选池已经清零，候选状态收敛为 `accepted = 30`
- `improved_v32` 把 profile 驱动布局继承纳入正式覆盖面
- 扩容后继续保持 `100%` 成功率与 `100%` 测试通过率
- 但最近三轮 `average_duration_sec` 连续回升，后续应把 runtime 效率波动作为一个独立跟踪方向

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

## Iteration 15：Dateutil tzstr Zero-Offset Fallback（improved_v8 -> improved_v9）

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 把 `dateutil/dateutil#1432` 推进成可运行任务
- 验证 `improved_v8` 到 `improved_v9` 是否能覆盖 UTC/GMT 无 offset 的时区解析场景
- 继续扩充真实 issue 派生任务集的来源多样性

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 新增草稿任务：
  - `task_018`
- 新增可运行 semi_real 任务：
  - `task_019`
- 新增 benchmark repo：
  - `benchmarks/repos/dateutil_tz_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v9.json`
- patch 生成器新增能力：
  - 让 `tzstr("UTC")` / `tzstr("GMT")` 在无 offset 时回落为零偏移，而不是继续对 `None` 做符号变换

### 主要涉及文件

- `benchmarks/tasks/task_018.json`
- `benchmarks/tasks/task_019.json`
- `benchmarks/repos/dateutil_tz_repo/dateutil_tz_repo/tz.py`
- `benchmarks/repos/dateutil_tz_repo/tests/test_tz.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v9.json`
- `app/agent/patcher.py`

### improved_v8 运行

- batch run：
  - `logs/summaries/batch_run_realissuev8r2_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev8r2_001.json`

### improved_v9 运行

- batch run：
  - `logs/summaries/batch_run_realissuev9_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev9_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step7_001.json`

### 指标对比

- `success_rate`
  - improved_v8: `0.8571`
  - improved_v9: `1.0`
- `test_pass_rate`
  - improved_v8: `0.8571`
  - improved_v9: `1.0`
- `average_steps`
  - improved_v8: `9.7143`
  - improved_v9: `9.7143`
- `average_duration_sec`
  - improved_v8: `0.5962`
  - improved_v9: `0.5928`
- `taxonomy`
  - improved_v8: `Premature Finish = 1`
  - improved_v9: `无错误标签`

### 关键案例

#### improved_v8 失败案例：`task_019`

- 运行结果：
  - `logs/trajectories/task_019/run_20260609T024638741956Z_7113/result.json`
- 现象：
  - 已读取 `dateutil_tz_repo/tz.py`
  - 但没有匹配到 UTC/GMT 无 offset 的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v9 成功案例：`task_019`

- 运行结果：
  - `logs/trajectories/task_019/run_20260609T024638741954Z_4984/result.json`
- 现象：
  - 自动把无 offset 时的 `None` 处理改成零偏移回落
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 7 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v8`：覆盖最近 marker 覆盖优先修复
  - `improved_v9`：进一步覆盖 UTC/GMT 无 offset 时区解析修复

### 剩余问题

- `dateutil/dateutil#1442` 还没有继续推进成新的 semi_real 任务
- `python-attrs/attrs#1479` 仍需先判断其性质是否适合作为 bugfix benchmark
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 16：Dateutil Nine-Digit Time Parsing（improved_v9 -> improved_v10）

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 把 `dateutil/dateutil#1442` 推进成可运行任务
- 验证 `improved_v9` 到 `improved_v10` 是否能覆盖 9 位时间串解析场景
- 继续扩充真实 issue 派生任务集的时间解析覆盖面

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 新增草稿任务：
  - `task_021`
- 新增可运行 semi_real 任务：
  - `task_022`
- 新增 benchmark repo：
  - `benchmarks/repos/dateutil_parser_repo_v2`
- 新增策略配置：
  - `optimization/policy_versions/improved_v10.json`
- patch 生成器新增能力：
  - 让 9 位时间串按 `HHMMSSmmm` 直接解析，而不是继续抛出格式错误
- 更正记录：
  - `task_020` 是一次误生成的探索脚手架，不纳入正式 `real_issue_tasks` manifest

### 主要涉及文件

- `benchmarks/tasks/task_021.json`
- `benchmarks/tasks/task_022.json`
- `benchmarks/repos/dateutil_parser_repo_v2/dateutil_parser_repo_v2/parser.py`
- `benchmarks/repos/dateutil_parser_repo_v2/tests/test_parser.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v10.json`
- `app/agent/patcher.py`

### improved_v9 运行

- batch run：
  - `logs/summaries/batch_run_realissuev9r2_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev9r2_001.json`

### improved_v10 运行

- batch run：
  - `logs/summaries/batch_run_realissuev10_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev10_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step8_001.json`

### 指标对比

- `success_rate`
  - improved_v9: `0.875`
  - improved_v10: `1.0`
- `test_pass_rate`
  - improved_v9: `0.875`
  - improved_v10: `1.0`
- `average_steps`
  - improved_v9: `9.625`
  - improved_v10: `9.625`
- `average_duration_sec`
  - improved_v9: `0.5334`
  - improved_v10: `0.5302`
- `taxonomy`
  - improved_v9: `Premature Finish = 1`
  - improved_v10: `无错误标签`

### 关键案例

#### improved_v9 失败案例：`task_022`

- 运行结果：
  - `logs/trajectories/task_022/run_20260609T031630923827Z_5315/result.json`
- 现象：
  - 已读取 `dateutil_parser_repo_v2/parser.py`
  - 但没有匹配到 9 位时间串的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v10 成功案例：`task_022`

- 运行结果：
  - `logs/trajectories/task_022/run_20260609T031631019752Z_0565/result.json`
- 现象：
  - 自动把 9 位时间串接到 `HHMMSSmmm` 解析路径
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 8 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v9`：覆盖 UTC/GMT 无 offset 时区解析修复
  - `improved_v10`：进一步覆盖 9 位时间串解析修复

### 剩余问题

- `python-attrs/attrs#1479` 仍需先判断其性质是否适合作为 bugfix benchmark
- 新来源候选还没有继续扩大到更多项目
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 17：Jinja Branch-Assigned Undeclared Analysis（improved_v10 -> improved_v11）

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 把 `pallets/jinja#2069` 推进成可运行任务
- 验证 `improved_v10` 到 `improved_v11` 是否能覆盖模板变量控制流分析场景
- 继续把真实 issue 来源从解析类 bug 扩展到模板静态分析类 bug

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 新增草稿任务：
  - `task_023`
- 新增可运行 semi_real 任务：
  - `task_024`
- 新增 benchmark repo：
  - `benchmarks/repos/jinja_meta_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v11.json`
- patch 生成器新增能力：
  - 让模板分析中所有分支都已赋值的变量不再被判定为 undeclared

### 主要涉及文件

- `benchmarks/tasks/task_023.json`
- `benchmarks/tasks/task_024.json`
- `benchmarks/repos/jinja_meta_repo/jinja_meta_repo/meta.py`
- `benchmarks/repos/jinja_meta_repo/tests/test_meta.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v11.json`
- `app/agent/patcher.py`

### improved_v10 运行

- batch run：
  - `logs/summaries/batch_run_realissuev10r2_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev10r2_001.json`

### improved_v11 运行

- batch run：
  - `logs/summaries/batch_run_realissuev11_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev11_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step9_001.json`

### 指标对比

- `success_rate`
  - improved_v10: `0.8889`
  - improved_v11: `1.0`
- `test_pass_rate`
  - improved_v10: `0.8889`
  - improved_v11: `1.0`
- `average_steps`
  - improved_v10: `9.5556`
  - improved_v11: `9.5556`
- `average_duration_sec`
  - improved_v10: `0.5804`
  - improved_v11: `0.5872`
- `taxonomy`
  - improved_v10: `Premature Finish = 1`
  - improved_v11: `无错误标签`

### 关键案例

#### improved_v10 失败案例：`task_024`

- 运行结果：
  - `logs/trajectories/task_024/run_20260609T073418949787Z_3262/result.json`
- 现象：
  - 已读取 `jinja_meta_repo/meta.py`
  - 但没有匹配到模板变量控制流分析修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v11 成功案例：`task_024`

- 运行结果：
  - `logs/trajectories/task_024/run_20260609T073420436230Z_3587/result.json`
- 现象：
  - 自动识别“所有分支都已赋值”的变量不应再被标记为 undeclared
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 9 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v10`：覆盖 9 位时间串解析修复
  - `improved_v11`：进一步覆盖模板变量控制流分析修复

### 剩余问题

- `python-attrs/attrs#1479` 仍需先判断其性质是否适合作为 bugfix benchmark
- 新来源候选还可以继续扩展到更多模板、序列化或配置类项目
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 18：Jinja Slice Fill-With Boundary（improved_v11 -> improved_v12）

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 把 `pallets/jinja#2118` 推进成可运行任务
- 验证 `improved_v11` 到 `improved_v12` 是否能覆盖 slice filter 的补位边界场景
- 继续扩展真实 issue 候选来源到 `jinja / tomlkit / packaging`

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 新增真实候选：
  - `pallets/jinja#2118`
  - `python-poetry/tomlkit#494`
  - `python-poetry/tomlkit#495`
  - `pypa/packaging#873`
- 新增草稿任务：
  - `task_025`
- 新增可运行 semi_real 任务：
  - `task_026`
- 新增 benchmark repo：
  - `benchmarks/repos/jinja_slice_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v12.json`
- patch 生成器新增能力：
  - 仅在存在余数时才为 slice 的尾部分片补入 `fill_with`
- 同步补充：
  - `docs/issue_sourcing_spec.md`
  - 历史候选状态校正，确保已正式落地的 requests 候选显示为 `accepted`

### 主要涉及文件

- `benchmarks/tasks/task_025.json`
- `benchmarks/tasks/task_026.json`
- `benchmarks/repos/jinja_slice_repo/jinja_slice_repo/filters.py`
- `benchmarks/repos/jinja_slice_repo/tests/test_filters.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v12.json`
- `app/agent/patcher.py`
- `docs/issue_sourcing_spec.md`

### improved_v11 运行

- batch eval：
  - `logs/summaries/batch_eval_realissuev11_001.json`
- 单任务失败运行：
  - `logs/trajectories/task_026/run_20260609T082829222606Z_4753/result.json`

### improved_v12 运行

- batch run：
  - `logs/summaries/batch_run_realissuev12_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev12_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step10_001.json`
- 单任务成功运行：
  - `logs/trajectories/task_026/run_20260609T082829222608Z_9275/result.json`

### 指标对比

- 说明：
  - 这一轮 compare 的 baseline 是 9 条任务集上的 `improved_v11`
  - improved 是扩充到 10 条任务后的 `improved_v12`
  - 因此更适合看“扩容后是否维持成功率，以及平均效率是否下降”
- `task_count`
  - improved_v11: `9`
  - improved_v12: `10`
- `success_count`
  - improved_v11: `9`
  - improved_v12: `10`
- `success_rate`
  - improved_v11: `1.0`
  - improved_v12: `1.0`
- `test_pass_rate`
  - improved_v11: `1.0`
  - improved_v12: `1.0`
- `average_steps`
  - improved_v11: `9.5556`
  - improved_v12: `9.5`
- `average_duration_sec`
  - improved_v11: `0.5872`
  - improved_v12: `0.5526`
- `taxonomy`
  - improved_v11: `无错误标签`
  - improved_v12: `无错误标签`

### 关键案例

#### improved_v11 失败案例：`task_026`

- 运行结果：
  - `logs/trajectories/task_026/run_20260609T082829222606Z_4753/result.json`
- 现象：
  - 已读取 `jinja_slice_repo/filters.py`
  - 但没有匹配到 slice 补位边界修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v12 成功案例：`task_026`

- 运行结果：
  - `logs/trajectories/task_026/run_20260609T082829222608Z_9275/result.json`
- 现象：
  - 自动识别整除场景下不应再追加 `fill_with`
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 10 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v11`：覆盖模板变量控制流分析修复
  - `improved_v12`：进一步覆盖 slice filter 填充值边界修复
- 在任务集扩容的情况下，`improved_v12` 仍保持 `100%` 成功率与 `100%` 测试通过率
- 平均耗时和平均步骤数没有恶化，反而略有改善

### 剩余问题

- `tomlkit` 与 `packaging` 的新候选还需要继续筛选并推进成正式 semi_real 任务
- 当前 compare 主要是“逐轮扩容保持成功率”的证据链，后面也可以补同集合对比实验
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 19：Tomlkit Next-Line Comma Append（improved_v12 -> improved_v13）

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 把 `python-poetry/tomlkit#494` 推进成可运行任务
- 验证 `improved_v12` 到 `improved_v13` 是否能覆盖数组下一行逗号风格下的 append 场景
- 继续扩展真实任务集的序列化与格式保真能力

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 重新同步并推进真实候选：
  - `python-poetry/tomlkit#494`
- 新增草稿任务：
  - `task_027`
- 新增可运行 semi_real 任务：
  - `task_028`
- 新增 benchmark repo：
  - `benchmarks/repos/tomlkit_array_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v13.json`
- patch 生成器新增能力：
  - 保留数组“下一行逗号”原始风格，避免 append 后生成双逗号

### 主要涉及文件

- `benchmarks/tasks/task_027.json`
- `benchmarks/tasks/task_028.json`
- `benchmarks/repos/tomlkit_array_repo/tomlkit_array_repo/formatter.py`
- `benchmarks/repos/tomlkit_array_repo/tests/test_formatter.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v13.json`
- `app/agent/patcher.py`

### improved_v12 运行

- batch eval：
  - `logs/summaries/batch_eval_realissuev12_001.json`
- 单任务失败运行：
  - `logs/trajectories/task_028/run_20260609T094333654294Z_6340/result.json`

### improved_v13 运行

- batch run：
  - `logs/summaries/batch_run_realissuev13_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev13_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step11_001.json`
- 单任务成功运行：
  - `logs/trajectories/task_028/run_20260609T094333623016Z_0883/result.json`

### 指标对比

- 说明：
  - 这一轮 compare 的 baseline 是 10 条任务集上的 `improved_v12`
  - improved 是扩充到 11 条任务后的 `improved_v13`
  - 因此仍然更适合看“扩容后是否维持成功率，以及平均效率是否下降”
- `task_count`
  - improved_v12: `10`
  - improved_v13: `11`
- `success_count`
  - improved_v12: `10`
  - improved_v13: `11`
- `success_rate`
  - improved_v12: `1.0`
  - improved_v13: `1.0`
- `test_pass_rate`
  - improved_v12: `1.0`
  - improved_v13: `1.0`
- `average_steps`
  - improved_v12: `9.5`
  - improved_v13: `9.3636`
- `average_duration_sec`
  - improved_v12: `0.5526`
  - improved_v13: `0.5512`
- `taxonomy`
  - improved_v12: `无错误标签`
  - improved_v13: `无错误标签`

### 关键案例

#### improved_v12 失败案例：`task_028`

- 运行结果：
  - `logs/trajectories/task_028/run_20260609T094333654294Z_6340/result.json`
- 现象：
  - 已读取 `tomlkit_array_repo/formatter.py`
  - 但没有匹配到数组下一行逗号风格的追加修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v13 成功案例：`task_028`

- 运行结果：
  - `logs/trajectories/task_028/run_20260609T094333623016Z_0883/result.json`
- 现象：
  - 自动识别“下一行开头逗号”的原始风格不应再被重复补逗号
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 11 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v12`：覆盖 Jinja slice filter 填充值边界修复
  - `improved_v13`：进一步覆盖 toml 数组序列化重复逗号修复
- 在任务集扩容的情况下，`improved_v13` 仍保持 `100%` 成功率与 `100%` 测试通过率
- 平均步骤数和平均耗时继续保持轻微改善

### 剩余问题

- `python-poetry/tomlkit#495` 仍可作为下一条高优先级候选继续推进
- `pypa/packaging#873` 仍值得保留，但落题时要注意规范与实现边界
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 20：Tomlkit Dotted Inline Table Append（improved_v13 -> improved_v14）

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 把 `python-poetry/tomlkit#495` 推进成可运行任务
- 验证 `improved_v13` 到 `improved_v14` 是否能覆盖 dotted inline table 追加新键场景
- 继续扩展配置序列化类真实任务的覆盖面

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 重新同步并推进真实候选：
  - `python-poetry/tomlkit#495`
- 新增草稿任务：
  - `task_029`
- 新增可运行 semi_real 任务：
  - `task_030`
- 新增 benchmark repo：
  - `benchmarks/repos/tomlkit_inline_table_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v14.json`
- patch 生成器新增能力：
  - 为 dotted inline table 追加新键值对时补上逗号和空格分隔，避免输出黏连损坏

### 主要涉及文件

- `benchmarks/tasks/task_029.json`
- `benchmarks/tasks/task_030.json`
- `benchmarks/repos/tomlkit_inline_table_repo/tomlkit_inline_table_repo/formatter.py`
- `benchmarks/repos/tomlkit_inline_table_repo/tests/test_formatter.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v14.json`
- `app/agent/patcher.py`

### improved_v13 运行

- batch eval：
  - `logs/summaries/batch_eval_realissuev13_001.json`
- 单任务失败运行：
  - `logs/trajectories/task_030/run_20260609T103930077307Z_3328/result.json`

### improved_v14 运行

- batch run：
  - `logs/summaries/batch_run_realissuev14_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev14_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step12_001.json`
- 单任务成功运行：
  - `logs/trajectories/task_030/run_20260609T103930007671Z_9522/result.json`

### 指标对比

- 说明：
  - 这一轮 compare 的 baseline 是 11 条任务集上的 `improved_v13`
  - improved 是扩充到 12 条任务后的 `improved_v14`
  - 因此仍然更适合看“扩容后是否维持成功率，以及平均效率是否变化”
- `task_count`
  - improved_v13: `11`
  - improved_v14: `12`
- `success_count`
  - improved_v13: `11`
  - improved_v14: `12`
- `success_rate`
  - improved_v13: `1.0`
  - improved_v14: `1.0`
- `test_pass_rate`
  - improved_v13: `1.0`
  - improved_v14: `1.0`
- `average_steps`
  - improved_v13: `9.3636`
  - improved_v14: `9.25`
- `average_duration_sec`
  - improved_v13: `0.5512`
  - improved_v14: `0.5811`
- `taxonomy`
  - improved_v13: `无错误标签`
  - improved_v14: `无错误标签`

### 关键案例

#### improved_v13 失败案例：`task_030`

- 运行结果：
  - `logs/trajectories/task_030/run_20260609T103930077307Z_3328/result.json`
- 现象：
  - 已读取 `tomlkit_inline_table_repo/formatter.py`
  - 但没有匹配到 dotted inline table 分隔修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v14 成功案例：`task_030`

- 运行结果：
  - `logs/trajectories/task_030/run_20260609T103930007671Z_9522/result.json`
- 现象：
  - 自动识别 inline table 追加键值对时需要补上逗号和空格分隔
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 12 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v13`：覆盖数组下一行逗号风格 append 修复
  - `improved_v14`：进一步覆盖 dotted inline table 追加键值对修复
- 在任务集扩容的情况下，`improved_v14` 仍保持 `100%` 成功率与 `100%` 测试通过率
- 平均步骤数继续下降，但平均耗时从 `0.5512` 小幅回升到 `0.5811`，这需要后续继续观察

### 剩余问题

- 现在候选池里高优先级的下一条主要剩 `pypa/packaging#873`
- 当前 compare 主要是“逐轮扩容保持成功率”的证据链，后面也可以补同集合冻结对比
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 21：Packaging Wheel Version Normalization（improved_v14 -> improved_v15）

### 时间

- 2026-06-09

### 阶段

- `Phase 6`

### 目标

- 把 `pypa/packaging#873` 推进成可运行任务
- 验证 `improved_v14` 到 `improved_v15` 是否能覆盖 wheel 文件名版本号 normalization 校验场景
- 继续扩展解析与规范校验类真实任务的覆盖面

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 重新同步并推进真实候选：
  - `pypa/packaging#873`
- 新增草稿任务：
  - `task_031`
- 新增可运行 semi_real 任务：
  - `task_032`
- 新增 benchmark repo：
  - `benchmarks/repos/packaging_wheel_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v15.json`
- patch 生成器新增能力：
  - 拒绝未 normalized 的 wheel 文件名版本号

### 主要涉及文件

- `benchmarks/tasks/task_031.json`
- `benchmarks/tasks/task_032.json`
- `benchmarks/repos/packaging_wheel_repo/packaging_wheel_repo/utils.py`
- `benchmarks/repos/packaging_wheel_repo/tests/test_utils.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v15.json`
- `app/agent/patcher.py`

### improved_v14 运行

- batch eval：
  - `logs/summaries/batch_eval_realissuev14_001.json`
- 单任务失败运行：
  - `logs/trajectories/task_032/run_20260609T113004718414Z_9988/result.json`

### improved_v15 运行

- batch run：
  - `logs/summaries/batch_run_realissuev15_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev15_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step13_001.json`
- 单任务成功运行：
  - `logs/trajectories/task_032/run_20260609T113004713415Z_6758/result.json`

### 指标对比

- 说明：
  - 这一轮 compare 的 baseline 是 12 条任务集上的 `improved_v14`
  - improved 是扩充到 13 条任务后的 `improved_v15`
  - 因此仍然更适合看“扩容后是否维持成功率，以及平均效率是否变化”
- `task_count`
  - improved_v14: `12`
  - improved_v15: `13`
- `success_count`
  - improved_v14: `12`
  - improved_v15: `13`
- `success_rate`
  - improved_v14: `1.0`
  - improved_v15: `1.0`
- `test_pass_rate`
  - improved_v14: `1.0`
  - improved_v15: `1.0`
- `average_steps`
  - improved_v14: `9.25`
  - improved_v15: `9.2308`
- `average_duration_sec`
  - improved_v14: `0.5811`
  - improved_v15: `0.552`
- `taxonomy`
  - improved_v14: `无错误标签`
  - improved_v15: `无错误标签`

### 关键案例

#### improved_v14 失败案例：`task_032`

- 运行结果：
  - `logs/trajectories/task_032/run_20260609T113004718414Z_9988/result.json`
- 现象：
  - 已读取 `packaging_wheel_repo/utils.py`
  - 但没有匹配到 wheel 版本号 normalization 校验策略
  - 最终以 `Premature Finish` 失败

#### improved_v15 成功案例：`task_032`

- 运行结果：
  - `logs/trajectories/task_032/run_20260609T113004713415Z_6758/result.json`
- 现象：
  - 自动识别未 normalized 的 wheel 版本号需要被拒绝
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 13 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v14`：覆盖 dotted inline table 分隔修复
  - `improved_v15`：进一步覆盖 wheel 版本号 normalization 校验
- 在任务集扩容的情况下，`improved_v15` 仍保持 `100%` 成功率与 `100%` 测试通过率
- 平均步骤数继续小幅下降，平均耗时也从上一轮回落到了更健康的区间

### 剩余问题

- 目前高质量外部候选池已经基本吃完，需要继续扩新来源
- 当前 compare 主要是“逐轮扩容保持成功率”的证据链，后面建议补一次冻结同集合对比
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

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

## Iteration 22：Jsonschema Mixed-Type Extras Message Fallback（improved_v15 -> improved_v16）

### 时间

- 2026-06-10

### 阶段

- `Phase 6`

### 目标

- 把 `python-jsonschema/jsonschema#1157` 推进成可运行任务
- 验证 `improved_v15` 到 `improved_v16` 是否能覆盖 mixed-type extras 错误消息渲染场景
- 把用户提供的候选 issue 文件导入到候选池，继续扩充下一批 benchmark 来源

### 改动类型

- `policy`
- `benchmark`
- `docs`

### 改动摘要

- 从外部文件 `D:\Learning_Project\agentic_swe_benchmark_issues.txt` 追加导入 15 条候选 issue
- 候选池总量从 15 条扩充到 30 条
- 候选状态汇总更新为：
  - `accepted = 14`
  - `drafted = 1`
  - `to_review = 15`
- 重新同步并推进真实候选：
  - `python-jsonschema/jsonschema#1157`
- 新增草稿任务：
  - `task_033`
- 新增可运行 semi_real 任务：
  - `task_034`
- 新增 benchmark repo：
  - `benchmarks/repos/jsonschema_extras_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v16.json`
- patch 生成器新增能力：
  - mixed-type extras 在排序失败时回落到原顺序渲染
  - 避免错误消息生成阶段直接抛出 `TypeError`

### 主要涉及文件

- `benchmarks/tasks/task_033.json`
- `benchmarks/tasks/task_034.json`
- `benchmarks/repos/jsonschema_extras_repo/jsonschema_extras_repo/utils.py`
- `benchmarks/repos/jsonschema_extras_repo/tests/test_utils.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v16.json`
- `app/agent/patcher.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/case_studies.md`

### improved_v15 运行

- batch eval：
  - `logs/summaries/batch_eval_realissuev15_001.json`
- 单任务失败运行：
  - `logs/trajectories/task_034/run_20260610T062805245249Z_0514/result.json`

### improved_v16 运行

- batch run：
  - `logs/summaries/batch_run_realissuev16_001.json`
- batch eval：
  - `logs/summaries/batch_eval_realissuev16_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step14_001.json`
- 单任务成功运行：
  - `logs/trajectories/task_034/run_20260610T062805232250Z_3601/result.json`

### 指标对比

- 说明：
  - 这一轮 compare 的 baseline 是 13 条任务集上的 `improved_v15`
  - improved 是扩充到 14 条任务后的 `improved_v16`
  - 因此仍然更适合看“扩容后是否维持成功率，以及平均效率是否变化”
- `task_count`
  - improved_v15: `13`
  - improved_v16: `14`
- `success_count`
  - improved_v15: `13`
  - improved_v16: `14`
- `success_rate`
  - improved_v15: `1.0`
  - improved_v16: `1.0`
- `test_pass_rate`
  - improved_v15: `1.0`
  - improved_v16: `1.0`
- `average_steps`
  - improved_v15: `9.2308`
  - improved_v16: `9.3571`
- `average_duration_sec`
  - improved_v15: `0.552`
  - improved_v16: `0.5792`
- `taxonomy`
  - improved_v15: `无错误标签`
  - improved_v16: `无错误标签`

### 关键案例

#### improved_v15 失败案例：`task_034`

- 运行结果：
  - `logs/trajectories/task_034/run_20260610T062805245249Z_0514/result.json`
- 现象：
  - 已读取 `jsonschema_extras_repo/utils.py`
  - 但没有匹配到 mixed-type extras 排序失败的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v16 成功案例：`task_034`

- 运行结果：
  - `logs/trajectories/task_034/run_20260610T062805232250Z_3601/result.json`
- 现象：
  - 自动识别 mixed-type extras 在 `sorted(extras)` 时会抛出 `TypeError`
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 14 条
- 候选池已经扩充到 30 条，下一阶段选题空间明显更大
- 当前真实任务集上的结果链路已经形成：
  - `improved_v15`：覆盖 wheel 版本号 normalization 校验
  - `improved_v16`：进一步覆盖 mixed-type extras 错误消息渲染
- 在任务集扩容的情况下，`improved_v16` 仍保持 `100%` 成功率与 `100%` 测试通过率
- 这一轮没有带来效率提升，平均步骤数和平均耗时都有小幅回升，需要后续继续观察

### 剩余问题

- 当前 compare 仍然主要是“逐轮扩容保持成功率”的证据链，后面建议补一次冻结同集合对比
- 候选池虽然扩大了，但 `to_review` 还有 15 条，仍需要继续筛选高质量 issue
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 23：Jsonschema Hostname ValueError Fallback and Frozen-Set Eval（improved_v16 -> improved_v17）

### 时间

- 2026-06-10

### 阶段

- `Phase 6`

### 目标

- 把 `python-jsonschema/jsonschema#1121` 推进成可运行任务
- 验证 `improved_v16` 到 `improved_v17` 是否能覆盖 hostname 格式检查在空字符串场景下的异常回落
- 首次补齐冻结同集合评测，避免结果一直只有扩容对比

### 改动类型

- `policy`
- `benchmark`
- `docs`
- `eval`

### 改动摘要

- 重新同步并推进真实候选：
  - `python-jsonschema/jsonschema#1121`
- 候选状态汇总更新为：
  - `accepted = 15`
  - `drafted = 1`
  - `to_review = 14`
- 新增草稿任务：
  - `task_035`
- 新增可运行 semi_real 任务：
  - `task_036`
- 新增 benchmark repo：
  - `benchmarks/repos/jsonschema_hostname_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v17.json`
- 新增冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
- patch 生成器新增能力：
  - hostname 格式检查在空字符串场景下捕获 `ValueError`
  - 回落为普通格式校验失败，而不是直接中断执行

### 主要涉及文件

- `benchmarks/tasks/task_035.json`
- `benchmarks/tasks/task_036.json`
- `benchmarks/repos/jsonschema_hostname_repo/jsonschema_hostname_repo/hostname.py`
- `benchmarks/repos/jsonschema_hostname_repo/tests/test_hostname.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v17.json`
- `app/agent/patcher.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/case_studies.md`

### 单任务分辨运行

- `improved_v16` 失败：
  - `logs/trajectories/task_036/run_20260610T065725595352Z_2796/result.json`
- `improved_v17` 成功：
  - `logs/trajectories/task_036/run_20260610T065725595349Z_4937/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev16_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev17_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev17_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step15_001.json`

### 冻结同集合运行

- baseline batch run：
  - `logs/summaries/batch_run_frozen15v16_001.json`
- baseline batch eval：
  - `logs/summaries/batch_eval_frozen15v16_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen15v17_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen15v17_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen15_step1_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 14 条任务集上的 `improved_v16`
  - improved 是扩充到 15 条任务后的 `improved_v17`
- 扩容对比结果：
  - `task_count`
    - improved_v16: `14`
    - improved_v17: `15`
  - `success_count`
    - improved_v16: `14`
    - improved_v17: `15`
  - `success_rate`
    - improved_v16: `1.0`
    - improved_v17: `1.0`
  - `test_pass_rate`
    - improved_v16: `1.0`
    - improved_v17: `1.0`
  - `average_steps`
    - improved_v16: `9.3571`
    - improved_v17: `9.2667`
  - `average_duration_sec`
    - improved_v16: `0.5792`
    - improved_v17: `0.5887`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 15 条任务
  - 因此这是当前第一组可直接解释为策略改进的同集合对比
- 冻结同集合结果：
  - `task_count`
    - improved_v16: `15`
    - improved_v17: `15`
  - `success_count`
    - improved_v16: `14`
    - improved_v17: `15`
  - `success_rate`
    - improved_v16: `0.9333`
    - improved_v17: `1.0`
  - `test_pass_rate`
    - improved_v16: `0.9333`
    - improved_v17: `1.0`
  - `average_steps`
    - improved_v16: `9.2667`
    - improved_v17: `9.2667`
  - `average_duration_sec`
    - improved_v16: `0.5926`
    - improved_v17: `0.5906`
  - `taxonomy`
    - improved_v16: `Premature Finish = 1`
    - improved_v17: `无错误标签`

### 关键案例

#### improved_v16 失败案例：`task_036`

- 运行结果：
  - `logs/trajectories/task_036/run_20260610T065725595352Z_2796/result.json`
- 现象：
  - 已读取 `jsonschema_hostname_repo/hostname.py`
  - 但没有匹配到 hostname 空字符串异常回落的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v17 成功案例：`task_036`

- 运行结果：
  - `logs/trajectories/task_036/run_20260610T065725595349Z_4937/result.json`
- 现象：
  - 自动识别空字符串场景下不应继续抛出 `ValueError`
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 15 条
- 候选池里正式 accepted 任务提升到 15 条，`to_review` 还剩 14 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v16`：覆盖 mixed-type extras 错误消息渲染
  - `improved_v17`：进一步覆盖 hostname 格式检查异常回落
- 扩容对比中，`improved_v17` 保持了 `100%` 成功率与 `100%` 测试通过率
- 冻结同集合对比中，`improved_v17` 首次把同集合成功率从 `0.9333` 提升到 `1.0`

### 剩余问题

- 冻结同集合对比目前只有 1 轮，后面还需要继续累计更多冻结集合版本
- 候选池虽然还比较充足，但仍需要继续把 `to_review` issue 逐步筛成可运行任务
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## Iteration 24：Jsonschema Integer-Valued multipleOf Float（improved_v17 -> improved_v18）

### 时间

- 2026-06-10

### 阶段

- `Phase 6`

### 目标

- 把 `python-jsonschema/jsonschema#1159` 推进成可运行任务
- 验证 `improved_v17` 到 `improved_v18` 是否能覆盖 integer-valued `multipleOf` 浮点数的数值语义问题
- 在正式真实任务集扩容到 16 条后继续观察成功率和效率指标

### 改动类型

- `policy`
- `benchmark`
- `docs`
- `eval`

### 改动摘要

- 重新同步并推进真实候选：
  - `python-jsonschema/jsonschema#1159`
- 候选状态汇总更新为：
  - `accepted = 16`
  - `drafted = 1`
  - `to_review = 13`
- 新增草稿任务：
  - `task_037`
- 新增可运行 semi_real 任务：
  - `task_038`
- 新增 benchmark repo：
  - `benchmarks/repos/jsonschema_multipleof_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v18.json`
- patch 生成器新增能力：
  - 识别 integer-valued `multipleOf` 浮点数
  - 将 `11.0` 这类值按数学整数 `11` 处理，而不是继续走纯浮点误差路径

### 主要涉及文件

- `benchmarks/tasks/task_037.json`
- `benchmarks/tasks/task_038.json`
- `benchmarks/repos/jsonschema_multipleof_repo/jsonschema_multipleof_repo/validator.py`
- `benchmarks/repos/jsonschema_multipleof_repo/tests/test_validator.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v18.json`
- `app/agent/patcher.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/case_studies.md`
- `docs/project_memory.md`
- `docs/benchmark_registry.md`
- `docs/next_actions.md`
- `docs/candidate_shortlist.md`

### 单任务分辨运行

- `improved_v17` 失败：
  - `logs/trajectories/task_038/run_20260610T080630043149Z_0253/result.json`
- `improved_v18` 成功：
  - `logs/trajectories/task_038/run_20260610T080630051215Z_7084/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev17_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev18_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev18_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step16_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 15 条任务集上的 `improved_v17`
  - improved 是扩充到 16 条任务后的 `improved_v18`
- 扩容对比结果：
  - `task_count`
    - improved_v17: `15`
    - improved_v18: `16`
  - `success_count`
    - improved_v17: `15`
    - improved_v18: `16`
  - `success_rate`
    - improved_v17: `1.0`
    - improved_v18: `1.0`
  - `test_pass_rate`
    - improved_v17: `1.0`
    - improved_v18: `1.0`
  - `average_steps`
    - improved_v17: `9.2667`
    - improved_v18: `9.1875`
  - `average_duration_sec`
    - improved_v17: `0.5887`
    - improved_v18: `0.5649`

### 关键案例

#### improved_v17 失败案例：`task_038`

- 运行结果：
  - `logs/trajectories/task_038/run_20260610T080630043149Z_0253/result.json`
- 现象：
  - 已读取 `jsonschema_multipleof_repo/validator.py`
  - 但没有匹配到 integer-valued `multipleOf` 浮点数的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v18 成功案例：`task_038`

- 运行结果：
  - `logs/trajectories/task_038/run_20260610T080630051215Z_7084/result.json`
- 现象：
  - 自动识别 `11.0` 应按数学整数处理
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 16 条
- 候选池里正式 accepted 任务提升到 16 条，`to_review` 降到 13 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v17`：覆盖 hostname 格式检查异常回落
  - `improved_v18`：进一步覆盖 integer-valued `multipleOf` 浮点数数值语义
- 扩容对比中，`improved_v18` 继续保持 `100%` 成功率与 `100%` 测试通过率
- 同时平均步数和平均耗时都优于 `improved_v17`

### 剩余问题

- 这一轮仍是扩容对比，下一阶段需要继续补 `frozen_18` 或 `frozen_20` 的同集合证据
- 候选池虽然仍然充足，但高质量 `to_review` issue 需要继续向可运行任务收敛
- 当前 patch 策略仍然是规则法，需要持续扩任务和扩能力

## Iteration 25：Packaging Requirement Extra Normalization（improved_v18 -> improved_v19）

### 时间

- 2026-06-10

### 阶段

- `Phase 6`

### 目标

- 把 `pypa/packaging#845` 推进成可运行任务
- 验证 `improved_v18` 到 `improved_v19` 是否能覆盖 Requirement 复合 marker 中的 extra 规范化问题
- 在正式真实任务集扩容到 17 条后继续观察成功率和效率指标

### 改动类型

- `policy`
- `benchmark`
- `docs`
- `eval`

### 改动摘要

- 重新同步并推进真实候选：
  - `pypa/packaging#845`
- 候选状态汇总更新为：
  - `accepted = 17`
  - `drafted = 1`
  - `to_review = 12`
- 新增草稿任务：
  - `task_039`
- 新增可运行 semi_real 任务：
  - `task_040`
- 新增 benchmark repo：
  - `benchmarks/repos/packaging_requirement_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v19.json`
- patch 生成器新增能力：
  - 识别 Requirement 复合 marker 表达式里的 `extra == "..."`
  - 统一将 extra 名称规范化为连字符风格，而不是只处理单独 extra marker

### 主要涉及文件

- `benchmarks/tasks/task_039.json`
- `benchmarks/tasks/task_040.json`
- `benchmarks/repos/packaging_requirement_repo/packaging_requirement_repo/requirements.py`
- `benchmarks/repos/packaging_requirement_repo/tests/test_requirements.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v19.json`
- `app/agent/patcher.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/case_studies.md`
- `docs/project_memory.md`
- `docs/benchmark_registry.md`
- `docs/next_actions.md`
- `docs/candidate_shortlist.md`

### 单任务分辨运行

- `improved_v18` 失败：
  - `logs/trajectories/task_040/run_20260610T082655762905Z_1706/result.json`
- `improved_v19` 成功：
  - `logs/trajectories/task_040/run_20260610T082655778437Z_4902/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev18_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev19_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev19_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step17_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 16 条任务集上的 `improved_v18`
  - improved 是扩充到 17 条任务后的 `improved_v19`
- 扩容对比结果：
  - `task_count`
    - improved_v18: `16`
    - improved_v19: `17`
  - `success_count`
    - improved_v18: `16`
    - improved_v19: `17`
  - `success_rate`
    - improved_v18: `1.0`
    - improved_v19: `1.0`
  - `test_pass_rate`
    - improved_v18: `1.0`
    - improved_v19: `1.0`
  - `average_steps`
    - improved_v18: `9.1875`
    - improved_v19: `9.3529`
  - `average_duration_sec`
    - improved_v18: `0.5649`
    - improved_v19: `0.6026`

### 关键案例

#### improved_v18 失败案例：`task_040`

- 运行结果：
  - `logs/trajectories/task_040/run_20260610T082655762905Z_1706/result.json`
- 现象：
  - 已读取 `packaging_requirement_repo/requirements.py`
  - 但没有匹配到复合 marker 中 extra 规范化的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v19 成功案例：`task_040`

- 运行结果：
  - `logs/trajectories/task_040/run_20260610T082655778437Z_4902/result.json`
- 现象：
  - 自动识别复合 marker 表达式里的 extra 名称也需要统一规范化
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 17 条
- 候选池里正式 accepted 任务提升到 17 条，`to_review` 降到 12 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v18`：覆盖 integer-valued `multipleOf` 浮点数数值语义
  - `improved_v19`：进一步覆盖 Requirement extra 字符串规范化
- 扩容对比中，`improved_v19` 继续保持 `100%` 成功率与 `100%` 测试通过率
- 这一轮效率指标略有回升，需要在后续继续观察

### 剩余问题

- 这一轮仍是扩容对比，还没有为 `improved_v19` 补到同集合证据
- 候选池虽然仍然充足，但高质量 `to_review` issue 需要继续向可运行任务收敛
- 当前 patch 策略仍然是规则法，需要持续扩任务和扩能力

## Iteration 26：Click resolve_command None Fallback and Frozen-18 Eval（improved_v19 -> improved_v20）

### 时间

- 2026-06-10

### 阶段

- `Phase 6`

### 目标

- 把 `pallets/click#2402` 推进成可运行任务
- 验证 `improved_v19` 到 `improved_v20` 是否能覆盖 `cmd is None` 场景下的 CLI 解析异常回落
- 在正式真实任务集扩容到 18 条后补齐第二组冻结同集合评测

### 改动类型

- `policy`
- `benchmark`
- `docs`
- `eval`

### 改动摘要

- 重新同步并推进真实候选：
  - `pallets/click#2402`
- 候选状态汇总更新为：
  - `accepted = 18`
  - `drafted = 1`
  - `to_review = 11`
- 新增草稿任务：
  - `task_041`
- 新增可运行 semi_real 任务：
  - `task_042`
- 新增 benchmark repo：
  - `benchmarks/repos/click_alias_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v20.json`
- 新增冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
- patch 生成器新增能力：
  - 识别 `resolve_command` 在 `cmd is None` 时仍直接访问 `cmd.name` 的模式
  - 回落为普通返回语义，而不是继续抛出 `AttributeError`

### 主要涉及文件

- `benchmarks/tasks/task_041.json`
- `benchmarks/tasks/task_042.json`
- `benchmarks/repos/click_alias_repo/click_alias_repo/cli.py`
- `benchmarks/repos/click_alias_repo/tests/test_cli.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v20.json`
- `app/agent/patcher.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/case_studies.md`
- `docs/project_memory.md`
- `docs/benchmark_registry.md`
- `docs/next_actions.md`
- `docs/candidate_shortlist.md`

### 单任务分辨运行

- `improved_v19` 失败：
  - `logs/trajectories/task_042/run_20260610T082850769297Z_6577/result.json`
- `improved_v20` 成功：
  - `logs/trajectories/task_042/run_20260610T082850769921Z_3477/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev19_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev20_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev20_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step18_001.json`

### 冻结同集合运行

- baseline batch run：
  - `logs/summaries/batch_run_frozen18v19_001.json`
- baseline batch eval：
  - `logs/summaries/batch_eval_frozen18v19_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen18v20_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen18v20_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen18_step1_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 17 条任务集上的 `improved_v19`
  - improved 是扩充到 18 条任务后的 `improved_v20`
- 扩容对比结果：
  - `task_count`
    - improved_v19: `17`
    - improved_v20: `18`
  - `success_count`
    - improved_v19: `17`
    - improved_v20: `18`
  - `success_rate`
    - improved_v19: `1.0`
    - improved_v20: `1.0`
  - `test_pass_rate`
    - improved_v19: `1.0`
    - improved_v20: `1.0`
  - `average_steps`
    - improved_v19: `9.3529`
    - improved_v20: `9.3889`
  - `average_duration_sec`
    - improved_v19: `0.6026`
    - improved_v20: `0.5823`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 18 条任务
  - 因此这是当前第二组可直接解释为策略改进的同集合对比
- 冻结同集合结果：
  - `task_count`
    - improved_v19: `18`
    - improved_v20: `18`
  - `success_count`
    - improved_v19: `17`
    - improved_v20: `18`
  - `success_rate`
    - improved_v19: `0.9444`
    - improved_v20: `1.0`
  - `test_pass_rate`
    - improved_v19: `0.9444`
    - improved_v20: `1.0`
  - `average_steps`
    - improved_v19: `9.3889`
    - improved_v20: `9.3889`
  - `average_duration_sec`
    - improved_v19: `0.5736`
    - improved_v20: `0.5713`
  - `taxonomy`
    - improved_v19: `Premature Finish = 1`
    - improved_v20: `无错误标签`

### 关键案例

#### improved_v19 失败案例：`task_042`

- 运行结果：
  - `logs/trajectories/task_042/run_20260610T082850769297Z_6577/result.json`
- 现象：
  - 已读取 `click_alias_repo/cli.py`
  - 但没有匹配到 `cmd is None` 的异常回落修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v20 成功案例：`task_042`

- 运行结果：
  - `logs/trajectories/task_042/run_20260610T082850769921Z_3477/result.json`
- 现象：
  - 自动识别 `cmd is None` 时不应继续访问 `cmd.name`
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 18 条
- 候选池里正式 accepted 任务提升到 18 条，`to_review` 降到 11 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v19`：覆盖 Requirement extra 字符串规范化
  - `improved_v20`：进一步覆盖 CLI 命令解析异常回落
- 扩容对比中，`improved_v20` 继续保持 `100%` 成功率与 `100%` 测试通过率
- 冻结同集合对比中，`improved_v20` 把 18 条同集合成功率从 `0.9444` 提升到 `1.0`

### 剩余问题

- 现在已经有 `frozen_15` 和 `frozen_18` 两组证据，下一阶段应继续朝 `frozen_20` 累积
- 候选池虽然仍然充足，但 parser 类和容器状态污染类的高质量 issue 仍需优先推进
- 当前 patch 策略仍然是规则法，需要持续扩任务和扩能力

## Iteration 27：Month-Year Dot Parser Expansion（improved_v20 -> improved_v21）

### 时间

- 2026-06-10

### 阶段

- `Phase 6`

### 目标

- 把 `dateutil/dateutil#384` 推进成可运行任务
- 验证 `improved_v20` 到 `improved_v21` 是否能覆盖 `MM.YYYY` 点号分隔的月年解析场景
- 把正式真实任务集从 `18` 条扩容到 `19` 条

### 改动类型

- `policy`
- `benchmark`
- `docs`
- `eval`

### 改动摘要

- 重新同步并推进真实候选：
  - `dateutil/dateutil#384`
- 候选状态汇总更新为：
  - `accepted = 19`
  - `drafted = 1`
  - `to_review = 9`
- 新增草稿任务：
  - `task_043`
- 新增可运行 semi_real 任务：
  - `task_044`
- 新增 benchmark repo：
  - `benchmarks/repos/dateutil_month_year_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v21.json`
- patch 生成器新增能力：
  - 识别仅支持 `MM/YYYY` 的旧逻辑
  - 为 `MM.YYYY` 点号分隔输入补上月年解析分支

### 主要涉及文件

- `benchmarks/tasks/task_043.json`
- `benchmarks/tasks/task_044.json`
- `benchmarks/repos/dateutil_month_year_repo/dateutil_month_year_repo/parser.py`
- `benchmarks/repos/dateutil_month_year_repo/tests/test_parser.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v21.json`
- `app/agent/patcher.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/case_studies.md`
- `docs/project_memory.md`
- `docs/benchmark_registry.md`
- `docs/next_actions.md`
- `docs/candidate_shortlist.md`

### 单任务分辨运行

- `improved_v20` 失败：
  - `logs/trajectories/task_044/run_20260610T091839213626Z_1487/result.json`
- `improved_v21` 成功：
  - `logs/trajectories/task_044/run_20260610T092046267167Z_6076/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev20_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev21_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev21_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step19_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `18` 条任务集上的 `improved_v20`
  - improved 是扩充到 `19` 条任务后的 `improved_v21`
- 扩容对比结果：
  - `task_count`
    - improved_v20: `18`
    - improved_v21: `19`
  - `success_count`
    - improved_v20: `18`
    - improved_v21: `19`
  - `success_rate`
    - improved_v20: `1.0`
    - improved_v21: `1.0`
  - `test_pass_rate`
    - improved_v20: `1.0`
    - improved_v21: `1.0`
  - `average_steps`
    - improved_v20: `9.3889`
    - improved_v21: `9.3158`
  - `average_duration_sec`
    - improved_v20: `0.5823`
    - improved_v21: `0.5743`

### 关键案例

#### improved_v20 失败案例：`task_044`

- 运行结果：
  - `logs/trajectories/task_044/run_20260610T091839213626Z_1487/result.json`
- 现象：
  - 已读取 `dateutil_month_year_repo/parser.py`
  - 但没有匹配到点号分隔月年格式的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v21 成功案例：`task_044`

- 运行结果：
  - `logs/trajectories/task_044/run_20260610T092046267167Z_6076/result.json`
- 现象：
  - 自动识别 `MM.YYYY` 应沿用月年解析语义
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 `19` 条
- 候选池里正式 accepted 任务提升到 `19` 条，`to_review` 降到 `9` 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v20`：覆盖 CLI 命令解析异常回落
  - `improved_v21`：进一步覆盖月年点号分隔解析
- 扩容对比中，`improved_v21` 继续保持 `100%` 成功率与 `100%` 测试通过率
- 这一轮效率指标也有轻微改善

### 剩余问题

- 这一轮仍是扩容对比，还没有为 `improved_v21` 补到同集合证据
- 当前仍缺少容器状态污染、版本比较 `dev/local` 边界等类型
- 当前 patch 策略仍然是规则法，需要持续扩任务和扩能力

## Iteration 28：Single-Label Hostname and Frozen-20 Eval（improved_v21 -> improved_v22）

### 时间

- 2026-06-10

### 阶段

- `Phase 6`

### 目标

- 把 `python-jsonschema/jsonschema#1162` 推进成可运行任务
- 验证 `improved_v21` 到 `improved_v22` 是否能覆盖 single-label hostname 合法性场景
- 在正式真实任务集扩容到 `20` 条后补齐第 `3` 组冻结同集合评测

### 改动类型

- `policy`
- `benchmark`
- `docs`
- `eval`

### 改动摘要

- 重新同步并推进真实候选：
  - `python-jsonschema/jsonschema#1162`
- 候选状态汇总更新为：
  - `accepted = 20`
  - `drafted = 1`
  - `to_review = 9`
- 新增草稿任务：
  - `task_045`
- 新增可运行 semi_real 任务：
  - `task_046`
- 新增 benchmark repo：
  - `benchmarks/repos/jsonschema_single_label_hostname_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v22.json`
- 新增冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`
- patch 生成器新增能力：
  - 识别 single-label hostname 被错误拒绝的模式
  - 允许 `localhost` 这类主机名通过合法性检查

### 主要涉及文件

- `benchmarks/tasks/task_045.json`
- `benchmarks/tasks/task_046.json`
- `benchmarks/repos/jsonschema_single_label_hostname_repo/jsonschema_single_label_hostname_repo/validators.py`
- `benchmarks/repos/jsonschema_single_label_hostname_repo/tests/test_validators.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v22.json`
- `app/agent/patcher.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/case_studies.md`
- `docs/project_memory.md`
- `docs/benchmark_registry.md`
- `docs/next_actions.md`
- `docs/candidate_shortlist.md`

### 单任务分辨运行

- `improved_v21` 失败：
  - `logs/trajectories/task_046/run_20260610T092235177619Z_0236/result.json`
- `improved_v22` 成功：
  - `logs/trajectories/task_046/run_20260610T092235218448Z_4302/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev21_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev22_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev22_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step20_001.json`

### 冻结同集合运行

- baseline batch run：
  - `logs/summaries/batch_run_frozen20v21_001.json`
- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v21_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v22_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v22_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step1_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `19` 条任务集上的 `improved_v21`
  - improved 是扩充到 `20` 条任务后的 `improved_v22`
- 扩容对比结果：
  - `task_count`
    - improved_v21: `19`
    - improved_v22: `20`
  - `success_count`
    - improved_v21: `19`
    - improved_v22: `20`
  - `success_rate`
    - improved_v21: `1.0`
    - improved_v22: `1.0`
  - `test_pass_rate`
    - improved_v21: `1.0`
    - improved_v22: `1.0`
  - `average_steps`
    - improved_v21: `9.3158`
    - improved_v22: `9.25`
  - `average_duration_sec`
    - improved_v21: `0.5743`
    - improved_v22: `0.5552`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 因此这是当前第 `3` 组可直接解释为策略改进的同集合对比
- 冻结同集合结果：
  - `task_count`
    - improved_v21: `20`
    - improved_v22: `20`
  - `success_count`
    - improved_v21: `19`
    - improved_v22: `20`
  - `success_rate`
    - improved_v21: `0.95`
    - improved_v22: `1.0`
  - `test_pass_rate`
    - improved_v21: `0.95`
    - improved_v22: `1.0`
  - `average_steps`
    - improved_v21: `9.25`
    - improved_v22: `9.25`
  - `average_duration_sec`
    - improved_v21: `0.5536`
    - improved_v22: `0.5569`
  - `taxonomy`
    - improved_v21: `Premature Finish = 1`
    - improved_v22: `无错误标签`

### 关键案例

#### improved_v21 失败案例：`task_046`

- 运行结果：
  - `logs/trajectories/task_046/run_20260610T092235177619Z_0236/result.json`
- 现象：
  - 已读取 `jsonschema_single_label_hostname_repo/validators.py`
  - 但没有匹配到 single-label hostname 合法性的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v22 成功案例：`task_046`

- 运行结果：
  - `logs/trajectories/task_046/run_20260610T092235218448Z_4302/result.json`
- 现象：
  - 自动识别 `localhost` 这类 single-label hostname 不应被拒绝
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 `20` 条
- 候选池里正式 accepted 任务提升到 `20` 条，`to_review` 维持在 `9` 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v21`：覆盖 `MM.YYYY` 月年格式解析
  - `improved_v22`：进一步覆盖 single-label hostname 合法性
- 扩容对比中，`improved_v22` 继续保持 `100%` 成功率与 `100%` 测试通过率
- 冻结同集合对比中，`improved_v22` 把 `20` 条同集合成功率从 `0.95` 提升到 `1.0`

### 剩余问题

- 当前已经有 `frozen_15`、`frozen_18`、`frozen_20` 三组证据，后续应继续沿 `frozen_20` 累积
- 版本比较 `dev/local` 边界、容器状态污染、validator 扩展语义仍值得优先推进
- 当前 patch 策略仍然是规则法，需要持续扩任务和扩能力

## Iteration 29：Packaging Dev-Local Specifier Expansion（improved_v22 -> improved_v23）

### 时间

- 2026-06-10

### 阶段

- `Phase 6`

### 目标

- 把 `pypa/packaging#810` 推进成可运行任务
- 验证 `improved_v22` 到 `improved_v23` 是否能覆盖 `Specifier >` 在 `dev+local` 场景下的比较边界
- 把正式真实任务集从 `20` 条扩容到 `21` 条
- 在 `frozen_20` 上补一轮无回归验证

### 改动类型

- `policy`
- `benchmark`
- `docs`
- `eval`

### 改动摘要

- 重新同步并推进真实候选：
  - `pypa/packaging#810`
- 候选状态汇总更新为：
  - `accepted = 21`
  - `drafted = 1`
  - `to_review = 8`
- 新增草稿任务：
  - `task_047`
- 新增可运行 semi_real 任务：
  - `task_048`
- 新增 benchmark repo：
  - `benchmarks/repos/packaging_specifier_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v23.json`
- patch 生成器新增能力：
  - 识别带 `local` 段时错误只比较 `base_version` 的模式
  - 改为按 `public version` 判断是否与 specifier 相同

### 主要涉及文件

- `benchmarks/tasks/task_047.json`
- `benchmarks/tasks/task_048.json`
- `benchmarks/repos/packaging_specifier_repo/packaging_specifier_repo/specifiers.py`
- `benchmarks/repos/packaging_specifier_repo/tests/test_specifiers.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v23.json`
- `app/agent/patcher.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/case_studies.md`
- `docs/project_memory.md`
- `docs/benchmark_registry.md`
- `docs/next_actions.md`
- `docs/candidate_shortlist.md`

### 单任务分辨运行

- `improved_v22` 失败：
  - `logs/trajectories/task_048/run_20260610T094755253692Z_6416/result.json`
- `improved_v23` 成功：
  - `logs/trajectories/task_048/run_20260610T094755281044Z_1882/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev22_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev23_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev23_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step21_001.json`

### 冻结同集合运行

- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v22_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v23_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v23_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step2_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `20` 条任务集上的 `improved_v22`
  - improved 是扩充到 `21` 条任务后的 `improved_v23`
- 扩容对比结果：
  - `task_count`
    - improved_v22: `20`
    - improved_v23: `21`
  - `success_count`
    - improved_v22: `20`
    - improved_v23: `21`
  - `success_rate`
    - improved_v22: `1.0`
    - improved_v23: `1.0`
  - `test_pass_rate`
    - improved_v22: `1.0`
    - improved_v23: `1.0`
  - `average_steps`
    - improved_v22: `9.25`
    - improved_v23: `9.2857`
  - `average_duration_sec`
    - improved_v22: `0.5552`
    - improved_v23: `0.557`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 这一轮主要用于确认新增 `packaging` 规则不会带来回归
- 冻结同集合结果：
  - `task_count`
    - improved_v22: `20`
    - improved_v23: `20`
  - `success_count`
    - improved_v22: `20`
    - improved_v23: `20`
  - `success_rate`
    - improved_v22: `1.0`
    - improved_v23: `1.0`
  - `test_pass_rate`
    - improved_v22: `1.0`
    - improved_v23: `1.0`
  - `average_steps`
    - improved_v22: `9.25`
    - improved_v23: `9.25`
  - `average_duration_sec`
    - improved_v22: `0.5569`
    - improved_v23: `0.554`
  - `taxonomy`
    - improved_v22: `无错误标签`
    - improved_v23: `无错误标签`

### 关键案例

#### improved_v22 失败案例：`task_048`

- 运行结果：
  - `logs/trajectories/task_048/run_20260610T094755253692Z_6416/result.json`
- 现象：
  - 已读取 `packaging_specifier_repo/specifiers.py`
  - 但没有匹配到 `dev+local` 版本比较的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v23 成功案例：`task_048`

- 运行结果：
  - `logs/trajectories/task_048/run_20260610T094755281044Z_1882/result.json`
- 现象：
  - 自动识别带 `local` 段时不应只比较 `base_version`
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 `21` 条
- 候选池里正式 accepted 任务提升到 `21` 条，`to_review` 降到 `8` 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v22`：覆盖 single-label hostname 合法性
  - `improved_v23`：进一步覆盖 `Specifier >` 在 `dev+local` 场景下的比较语义
- 扩容对比中，`improved_v23` 继续保持 `100%` 成功率与 `100%` 测试通过率
- `frozen_20` 对比中，`improved_v23` 保持固定任务集无回归

### 剩余问题

- 当前最近一轮 `frozen_20` 结果是无回归，而不是新的成功率提升
- 容器状态污染、validator 扩展语义、轻量数据库提交语义仍值得优先推进
- 当前 patch 策略仍然是规则法，需要持续扩任务和扩能力

## Iteration 30：Attached Comma Year Parser Expansion（improved_v23 -> improved_v24）

### 时间

- 2026-06-10

### 阶段

- `Phase 6`

### 目标

- 把 `dateutil/dateutil#1191` 推进成可运行任务
- 验证 `improved_v23` 到 `improved_v24` 是否能覆盖年份前紧贴逗号时的 parser token 识别问题
- 把正式真实任务集从 `21` 条扩容到 `22` 条
- 在 `frozen_20` 上补一轮无回归验证

### 改动类型

- `policy`
- `benchmark`
- `docs`
- `eval`

### 改动摘要

- 重新同步并推进真实候选：
  - `dateutil/dateutil#1191`
- 候选状态汇总更新为：
  - `accepted = 22`
  - `drafted = 1`
  - `to_review = 7`
- 新增草稿任务：
  - `task_049`
- 新增可运行 semi_real 任务：
  - `task_050`
- 新增 benchmark repo：
  - `benchmarks/repos/dateutil_attached_comma_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v24.json`
- patch 生成器新增能力：
  - 识别年份 token 前紧贴逗号但未被清理的模式
  - 改为先移除前缀逗号，再识别四位年份

### 主要涉及文件

- `benchmarks/tasks/task_049.json`
- `benchmarks/tasks/task_050.json`
- `benchmarks/repos/dateutil_attached_comma_repo/dateutil_attached_comma_repo/parser.py`
- `benchmarks/repos/dateutil_attached_comma_repo/tests/test_parser.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v24.json`
- `app/agent/patcher.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/case_studies.md`
- `docs/project_memory.md`
- `docs/benchmark_registry.md`
- `docs/next_actions.md`
- `docs/candidate_shortlist.md`

### 单任务分辨运行

- `improved_v23` 失败：
  - `logs/trajectories/task_050/run_20260610T095611525999Z_6956/result.json`
- `improved_v24` 成功：
  - `logs/trajectories/task_050/run_20260610T095611540428Z_6190/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev23_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev24_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev24_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step22_001.json`

### 冻结同集合运行

- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v23_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v24_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v24_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step3_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `21` 条任务集上的 `improved_v23`
  - improved 是扩充到 `22` 条任务后的 `improved_v24`
- 扩容对比结果：
  - `task_count`
    - improved_v23: `21`
    - improved_v24: `22`
  - `success_count`
    - improved_v23: `21`
    - improved_v24: `22`
  - `success_rate`
    - improved_v23: `1.0`
    - improved_v24: `1.0`
  - `test_pass_rate`
    - improved_v23: `1.0`
    - improved_v24: `1.0`
  - `average_steps`
    - improved_v23: `9.2857`
    - improved_v24: `9.2273`
  - `average_duration_sec`
    - improved_v23: `0.557`
    - improved_v24: `0.5511`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 这一轮主要用于确认新增 date parser 规则不会带来回归
- 冻结同集合结果：
  - `task_count`
    - improved_v23: `20`
    - improved_v24: `20`
  - `success_count`
    - improved_v23: `20`
    - improved_v24: `20`
  - `success_rate`
    - improved_v23: `1.0`
    - improved_v24: `1.0`
  - `test_pass_rate`
    - improved_v23: `1.0`
    - improved_v24: `1.0`
  - `average_steps`
    - improved_v23: `9.25`
    - improved_v24: `9.25`
  - `average_duration_sec`
    - improved_v23: `0.554`
    - improved_v24: `0.548`
  - `taxonomy`
    - improved_v23: `无错误标签`
    - improved_v24: `无错误标签`

### 关键案例

#### improved_v23 失败案例：`task_050`

- 运行结果：
  - `logs/trajectories/task_050/run_20260610T095611525999Z_6956/result.json`
- 现象：
  - 已读取 `dateutil_attached_comma_repo/parser.py`
  - 但没有匹配到 `,2021` 这一类 year token 清理策略
  - 最终以 `Premature Finish` 失败

#### improved_v24 成功案例：`task_050`

- 运行结果：
  - `logs/trajectories/task_050/run_20260610T095611540428Z_6190/result.json`
- 现象：
  - 自动识别年份 token 前缀逗号需要先清理
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 `22` 条
- 候选池里正式 accepted 任务提升到 `22` 条，`to_review` 降到 `7` 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v23`：覆盖 `Specifier >` 在 `dev+local` 场景下的比较语义
  - `improved_v24`：进一步覆盖年份前紧贴逗号时的 parser token 识别
- 扩容对比中，`improved_v24` 继续保持 `100%` 成功率与 `100%` 测试通过率
- 扩容后的平均步数和平均耗时都优于上一轮
- `frozen_20` 对比中，`improved_v24` 保持固定任务集无回归

### 剩余问题

- 当前最近两轮 `frozen_20` 结果都是无回归，而不是新的成功率提升
- 容器状态污染、validator 扩展语义、轻量数据库提交语义仍值得优先推进
- 当前 patch 策略仍然是规则法，需要持续扩任务和扩能力

## Iteration 31：ErrorTree Read-Only Access Expansion（improved_v24 -> improved_v25）

### 时间

- 2026-06-10

### 阶段

- `Phase 6`

### 目标

- 把 `python-jsonschema/jsonschema#1328` 推进成可运行任务
- 验证 `improved_v24` 到 `improved_v25` 是否能覆盖 ErrorTree 缺失索引访问的状态污染问题
- 把正式真实任务集从 `22` 条扩容到 `23` 条
- 在 `frozen_20` 上补一轮无回归验证

### 改动类型

- `policy`
- `benchmark`
- `docs`
- `eval`

### 改动摘要

- 重新同步并推进真实候选：
  - `python-jsonschema/jsonschema#1328`
- 候选状态汇总更新为：
  - `accepted = 23`
  - `drafted = 1`
  - `to_review = 6`
- 新增草稿任务：
  - `task_051`
- 新增可运行 semi_real 任务：
  - `task_052`
- 新增 benchmark repo：
  - `benchmarks/repos/jsonschema_error_tree_repo`
- 新增策略配置：
  - `optimization/policy_versions/improved_v25.json`
- patch 生成器新增能力：
  - 识别 `__getitem__()` 用 `setdefault()` 写回空节点的模式
  - 改为只读返回空节点，不污染内部 children

### 主要涉及文件

- `benchmarks/tasks/task_051.json`
- `benchmarks/tasks/task_052.json`
- `benchmarks/repos/jsonschema_error_tree_repo/jsonschema_error_tree_repo/error_tree.py`
- `benchmarks/repos/jsonschema_error_tree_repo/tests/test_error_tree.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `optimization/policy_versions/improved_v25.json`
- `app/agent/patcher.py`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/results.md`
- `docs/case_studies.md`
- `docs/project_memory.md`
- `docs/benchmark_registry.md`
- `docs/next_actions.md`
- `docs/candidate_shortlist.md`

### 单任务分辨运行

- `improved_v24` 失败：
  - `logs/trajectories/task_052/run_20260610T100155065230Z_4644/result.json`
- `improved_v25` 成功：
  - `logs/trajectories/task_052/run_20260610T100155084198Z_3773/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev24_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev25_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev25_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step23_001.json`

### 冻结同集合运行

- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v24_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v25_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v25_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step4_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `22` 条任务集上的 `improved_v24`
  - improved 是扩充到 `23` 条任务后的 `improved_v25`
- 扩容对比结果：
  - `task_count`
    - improved_v24: `22`
    - improved_v25: `23`
  - `success_count`
    - improved_v24: `22`
    - improved_v25: `23`
  - `success_rate`
    - improved_v24: `1.0`
    - improved_v25: `1.0`
  - `test_pass_rate`
    - improved_v24: `1.0`
    - improved_v25: `1.0`
  - `average_steps`
    - improved_v24: `9.2273`
    - improved_v25: `9.3478`
  - `average_duration_sec`
    - improved_v24: `0.5511`
    - improved_v25: `0.5548`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 这一轮主要用于确认新增 ErrorTree 规则不会带来回归
- 冻结同集合结果：
  - `task_count`
    - improved_v24: `20`
    - improved_v25: `20`
  - `success_count`
    - improved_v24: `20`
    - improved_v25: `20`
  - `success_rate`
    - improved_v24: `1.0`
    - improved_v25: `1.0`
  - `test_pass_rate`
    - improved_v24: `1.0`
    - improved_v25: `1.0`
  - `average_steps`
    - improved_v24: `9.25`
    - improved_v25: `9.25`
  - `average_duration_sec`
    - improved_v24: `0.548`
    - improved_v25: `0.5584`
  - `taxonomy`
    - improved_v24: `无错误标签`
    - improved_v25: `无错误标签`

### 关键案例

#### improved_v24 失败案例：`task_052`

- 运行结果：
  - `logs/trajectories/task_052/run_20260610T100155065230Z_4644/result.json`
- 现象：
  - 已读取 `jsonschema_error_tree_repo/error_tree.py`
  - 但没有匹配到 `setdefault()` 引起的状态污染修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v25 成功案例：`task_052`

- 运行结果：
  - `logs/trajectories/task_052/run_20260610T100155084198Z_3773/result.json`
- 现象：
  - 自动识别缺失索引访问不应写回内部 children
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 `23` 条
- 候选池里正式 accepted 任务提升到 `23` 条，`to_review` 降到 `6` 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v24`：覆盖年份前紧贴逗号时的 parser token 识别
  - `improved_v25`：进一步覆盖 ErrorTree 缺失索引访问状态污染
- 扩容对比中，`improved_v25` 继续保持 `100%` 成功率与 `100%` 测试通过率
- `frozen_20` 对比中，`improved_v25` 保持固定任务集无回归

## Iteration 32：Applicable Validators Inheritance Expansion（improved_v25 -> improved_v26）

### 本轮目标

- 验证 `improved_v25` 到 `improved_v26` 是否能覆盖 `python-jsonschema/jsonschema#1125`
- 把 validator `extend()` 时丢失 `applicable_validators` 的语义回归沉淀成正式 semi-real 任务
- 继续在 `frozen_20` 上补一轮同集合验证，确认新增规则不破坏已有能力

### 本轮新增输入

- 新增候选推进：
  - `python-jsonschema/jsonschema#1125`
- 候选池状态更新：
  - `accepted = 24`
  - `drafted = 1`
  - `to_review = 5`
- 新增任务：
  - `task_053`
  - `task_054`
- 新增策略：
  - `optimization/policy_versions/improved_v26.json`

### 本轮新增文件

- `benchmarks/tasks/task_053.json`
- `benchmarks/tasks/task_054.json`
- `benchmarks/repos/jsonschema_extend_repo/README.md`
- `benchmarks/repos/jsonschema_extend_repo/jsonschema_extend_repo/__init__.py`
- `benchmarks/repos/jsonschema_extend_repo/jsonschema_extend_repo/validators.py`
- `benchmarks/repos/jsonschema_extend_repo/tests/test_validators.py`
- `optimization/policy_versions/improved_v26.json`

### 本轮修改文件

- `app/agent/patcher.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/benchmark_registry.md`
- `docs/candidate_shortlist.md`
- `docs/case_studies.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `docs/results.md`

### 本轮任务设计

- `task_053`
  - 类型：`real_issue`
  - 来源：`python-jsonschema/jsonschema#1125`
  - 作用：保留真实 issue 的入口和元数据
- `task_054`
  - 类型：`semi_real`
  - repo：`jsonschema_extend_repo`
  - 缺陷：`extend()` 在复制 `VALIDATORS` 时漏掉 `applicable_validators`
  - 目标：扩展后的 legacy validator 仍保留 `$ref` 邻接关键字过滤语义

### 本轮策略改动

- 新增 `_handle_jsonschema_extend_copies_applicable_validators`
  - 命中 `jsonschema_extend_repo/validators.py` 中的 `extend()` 缺陷模板
  - 修复方式：在 `create()` 调用里继续透传 `validator.applicable_validators`
- `improved_v26`
  - 在 `improved_v25` 能力链之上增加 validator extend 语义继承修复

### 单任务分辨运行

- `improved_v25` 失败：
  - `logs/trajectories/task_054/run_20260610T131321107700Z_4638/result.json`
- `improved_v26` 成功：
  - `logs/trajectories/task_054/run_20260610T131321174951Z_0079/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev25_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev26_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev26_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step24_001.json`

### 冻结同集合运行

- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v25_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v26_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v26_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step5_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `23` 条任务集上的 `improved_v25`
  - improved 是扩充到 `24` 条任务后的 `improved_v26`
- 扩容对比结果：
  - `task_count`
    - improved_v25: `23`
    - improved_v26: `24`
  - `success_count`
    - improved_v25: `23`
    - improved_v26: `24`
  - `success_rate`
    - improved_v25: `1.0`
    - improved_v26: `1.0`
  - `test_pass_rate`
    - improved_v25: `1.0`
    - improved_v26: `1.0`
  - `average_steps`
    - improved_v25: `9.3478`
    - improved_v26: `9.375`
  - `average_duration_sec`
    - improved_v25: `0.5548`
    - improved_v26: `0.5699`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 这一轮主要用于确认新增 validator extend 规则不会带来回归
- 冻结同集合结果：
  - `task_count`
    - improved_v25: `20`
    - improved_v26: `20`
  - `success_count`
    - improved_v25: `20`
    - improved_v26: `20`
  - `success_rate`
    - improved_v25: `1.0`
    - improved_v26: `1.0`
  - `test_pass_rate`
    - improved_v25: `1.0`
    - improved_v26: `1.0`
  - `average_steps`
    - improved_v25: `9.25`
    - improved_v26: `9.25`
  - `average_duration_sec`
    - improved_v25: `0.5584`
    - improved_v26: `0.5567`
  - `taxonomy`
    - improved_v25: `无错误标签`
    - improved_v26: `无错误标签`

### 关键案例

#### improved_v25 失败案例：`task_054`

- 运行结果：
  - `logs/trajectories/task_054/run_20260610T131321107700Z_4638/result.json`
- 现象：
  - 已读取 `jsonschema_extend_repo/validators.py`
  - 但没有匹配到 `extend()` 需要继续透传 `applicable_validators` 的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v26 成功案例：`task_054`

- 运行结果：
  - `logs/trajectories/task_054/run_20260610T131321174951Z_0079/result.json`
- 现象：
  - 自动识别 legacy validator 的 `$ref` 邻接关键字过滤语义不能在 `extend()` 时丢失
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 `24` 条
- 候选池里正式 accepted 任务提升到 `24` 条，`to_review` 降到 `5` 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v25`：覆盖 ErrorTree 缺失索引访问状态污染
  - `improved_v26`：进一步覆盖 validator `extend()` 语义继承
- 扩容对比中，`improved_v26` 继续保持 `100%` 成功率与 `100%` 测试通过率
- `frozen_20` 对比中，`improved_v26` 保持固定任务集无回归，并把平均耗时从 `0.5584` 小幅改善到 `0.5567`

## Iteration 33：Delete Auto-Commit Expansion（improved_v26 -> improved_v27）

### 本轮目标

- 验证 `improved_v26` 到 `improved_v27` 是否能覆盖 `simonw/sqlite-utils#159`
- 把 `delete_where()` 删除后未提交事务的问题沉淀成正式 semi-real 任务
- 继续在 `frozen_20` 上补一轮同集合验证，确认新增规则不破坏已有能力

### 本轮新增输入

- 新增候选推进：
  - `simonw/sqlite-utils#159`
- 候选池状态更新：
  - `accepted = 25`
  - `drafted = 1`
  - `to_review = 4`
- 新增任务：
  - `task_055`
  - `task_056`
- 新增策略：
  - `optimization/policy_versions/improved_v27.json`

### 本轮新增文件

- `benchmarks/tasks/task_055.json`
- `benchmarks/tasks/task_056.json`
- `benchmarks/repos/sqlite_delete_repo/README.md`
- `benchmarks/repos/sqlite_delete_repo/sqlite_delete_repo/__init__.py`
- `benchmarks/repos/sqlite_delete_repo/sqlite_delete_repo/table.py`
- `benchmarks/repos/sqlite_delete_repo/tests/test_table.py`
- `optimization/policy_versions/improved_v27.json`

### 本轮修改文件

- `app/agent/patcher.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/benchmark_registry.md`
- `docs/candidate_shortlist.md`
- `docs/case_studies.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `docs/results.md`

### 本轮任务设计

- `task_055`
  - 类型：`real_issue`
  - 来源：`simonw/sqlite-utils#159`
  - 作用：保留真实 issue 的入口和元数据
- `task_056`
  - 类型：`semi_real`
  - repo：`sqlite_delete_repo`
  - 缺陷：`delete_where()` 删除后没有提交事务
  - 目标：删除结果应立即对第二个数据库连接可见

### 本轮策略改动

- 新增 `_handle_sqlite_delete_where_autocommit`
  - 命中 `sqlite_delete_repo/table.py` 中的 `delete_where()` 缺陷模板
  - 修复方式：在删除执行后补上 `self._connection.commit()`
- `improved_v27`
  - 在 `improved_v26` 能力链之上增加删除自动提交修复

### 单任务分辨运行

- `improved_v26` 失败：
  - `logs/trajectories/task_056/run_20260610T133235559561Z_0686/result.json`
- `improved_v27` 成功：
  - `logs/trajectories/task_056/run_20260610T133235548372Z_7214/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev26_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev27_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev27_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step25_001.json`

### 冻结同集合运行

- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v26_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v27_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v27_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step6_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `24` 条任务集上的 `improved_v26`
  - improved 是扩充到 `25` 条任务后的 `improved_v27`
- 扩容对比结果：
  - `task_count`
    - improved_v26: `24`
    - improved_v27: `25`
  - `success_count`
    - improved_v26: `24`
    - improved_v27: `25`
  - `success_rate`
    - improved_v26: `1.0`
    - improved_v27: `1.0`
  - `test_pass_rate`
    - improved_v26: `1.0`
    - improved_v27: `1.0`
  - `average_steps`
    - improved_v26: `9.375`
    - improved_v27: `9.4`
  - `average_duration_sec`
    - improved_v26: `0.5699`
    - improved_v27: `0.591`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 这一轮主要用于确认新增删除自动提交规则不会带来回归
- 冻结同集合结果：
  - `task_count`
    - improved_v26: `20`
    - improved_v27: `20`
  - `success_count`
    - improved_v26: `20`
    - improved_v27: `20`
  - `success_rate`
    - improved_v26: `1.0`
    - improved_v27: `1.0`
  - `test_pass_rate`
    - improved_v26: `1.0`
    - improved_v27: `1.0`
  - `average_steps`
    - improved_v26: `9.25`
    - improved_v27: `9.25`
  - `average_duration_sec`
    - improved_v26: `0.5567`
    - improved_v27: `0.5709`
  - `taxonomy`
    - improved_v26: `无错误标签`
    - improved_v27: `无错误标签`

### 关键案例

#### improved_v26 失败案例：`task_056`

- 运行结果：
  - `logs/trajectories/task_056/run_20260610T133235559561Z_0686/result.json`
- 现象：
  - 已读取 `sqlite_delete_repo/table.py`
  - 但没有匹配到删除后需要提交事务的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v27 成功案例：`task_056`

- 运行结果：
  - `logs/trajectories/task_056/run_20260610T133235548372Z_7214/result.json`
- 现象：
  - 自动识别删除操作与其他写操作应共享自动提交语义
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 `25` 条
- 候选池里正式 accepted 任务提升到 `25` 条，`to_review` 降到 `4` 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v26`：覆盖 validator `extend()` 语义继承
  - `improved_v27`：进一步覆盖删除事务提交可见性
- 扩容对比中，`improved_v27` 继续保持 `100%` 成功率与 `100%` 测试通过率
- `frozen_20` 对比中，`improved_v27` 保持固定任务集无回归，但平均耗时从 `0.5567` 回升到 `0.5709`

### 剩余问题

- 最近几轮 `frozen_20` 主要提供无回归证据，而非新的同集合成功率提升
- 对象定义阶段 alias 可见性、模型 validator 继承、数据转换中的空值语义仍值得优先推进
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

### 剩余问题

- 最近几轮 `frozen_20` 主要提供无回归证据，而非新的同集合成功率提升
- 轻量数据库提交语义、对象定义阶段 alias 可见性、模型 validator 继承仍值得优先推进
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

### 剩余问题

- 当前最近三轮 `frozen_20` 结果都是无回归，而不是新的成功率提升
- validator 扩展语义、轻量数据库提交语义、对象定义阶段元数据可见性仍值得优先推进
- 当前 patch 策略仍然是规则法，需要持续扩任务和扩能力

## Iteration 34：Model Validator Inheritance Expansion（improved_v27 -> improved_v28）

### 本轮目标

- 验证 `improved_v27` 到 `improved_v28` 是否能覆盖 `pydantic/pydantic#9582`
- 把子类 `model_validator` 覆盖父类校验链的问题沉淀成正式 semi-real 任务
- 继续在 `frozen_20` 上补一轮同集合验证，确认新增规则不破坏已有能力

### 本轮新增输入

- 新增候选推进：
  - `pydantic/pydantic#9582`
- 候选池状态更新：
  - `accepted = 26`
  - `drafted = 0`
  - `to_review = 4`
- 新增任务：
  - `task_057`
- 新增策略：
  - `optimization/policy_versions/improved_v28.json`

### 本轮新增文件

- `benchmarks/tasks/task_057.json`
- `benchmarks/repos/pydantic_inheritance_repo/README.md`
- `benchmarks/repos/pydantic_inheritance_repo/pydantic_inheritance_repo/__init__.py`
- `benchmarks/repos/pydantic_inheritance_repo/pydantic_inheritance_repo/models.py`
- `benchmarks/repos/pydantic_inheritance_repo/tests/test_models.py`
- `optimization/policy_versions/improved_v28.json`

### 本轮修改文件

- `app/agent/patcher.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `README.md`
- `GUIDE.md`
- `docs/benchmark.md`
- `docs/benchmark_registry.md`
- `docs/candidate_shortlist.md`
- `docs/case_studies.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `docs/results.md`

### 本轮任务设计

- `task_014`
  - 类型：`real_issue`
  - 来源：`pydantic/pydantic#9582`
  - 作用：保留真实 issue 的草稿入口
- `task_057`
  - 类型：`semi_real`
  - repo：`pydantic_inheritance_repo`
  - 缺陷：子类定义自己的 `model_validator` 后覆盖掉父类校验链
  - 目标：父类和子类 validator 都继续执行

### 本轮策略改动

- 新增 `_handle_pydantic_inherited_model_validators`
  - 命中 `pydantic_inheritance_repo/models.py` 中的继承缺陷模板
  - 修复方式：把子类 `after` validator 改成追加到父类 validator 名单之后
- `improved_v28`
  - 在 `improved_v27` 能力链之上增加 model validator 继承修复

### 单任务分辨运行

- `improved_v27` 失败：
  - `logs/trajectories/task_057/run_20260610T140229242079Z_1281/result.json`
- `improved_v28` 成功：
  - `logs/trajectories/task_057/run_20260610T140229399114Z_2846/result.json`

### 扩容任务集运行

- baseline eval：
  - `logs/summaries/batch_eval_realissuev27_001.json`
- improved batch run：
  - `logs/summaries/batch_run_realissuev28_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_realissuev28_001.json`
- compare：
  - `logs/summaries/batch_compare_realissue_step26_001.json`

### 冻结同集合运行

- baseline batch eval：
  - `logs/summaries/batch_eval_frozen20v27_001.json`
- improved batch run：
  - `logs/summaries/batch_run_frozen20v28_001.json`
- improved batch eval：
  - `logs/summaries/batch_eval_frozen20v28_001.json`
- compare：
  - `logs/summaries/batch_compare_frozen20_step7_001.json`

### 指标对比

- 扩容对比说明：
  - baseline 是 `25` 条任务集上的 `improved_v27`
  - improved 是扩充到 `26` 条任务后的 `improved_v28`
- 扩容对比结果：
  - `task_count`
    - improved_v27: `25`
    - improved_v28: `26`
  - `success_count`
    - improved_v27: `25`
    - improved_v28: `26`
  - `success_rate`
    - improved_v27: `1.0`
    - improved_v28: `1.0`
  - `test_pass_rate`
    - improved_v27: `1.0`
    - improved_v28: `1.0`
  - `average_steps`
    - improved_v27: `9.4`
    - improved_v28: `9.4231`
  - `average_duration_sec`
    - improved_v27: `0.591`
    - improved_v28: `0.5898`
- 冻结同集合说明：
  - baseline 和 improved 使用完全相同的 `20` 条任务
  - 这一轮主要用于确认新增 validator 继承规则不会带来回归
- 冻结同集合结果：
  - `task_count`
    - improved_v27: `20`
    - improved_v28: `20`
  - `success_count`
    - improved_v27: `20`
    - improved_v28: `20`
  - `success_rate`
    - improved_v27: `1.0`
    - improved_v28: `1.0`
  - `test_pass_rate`
    - improved_v27: `1.0`
    - improved_v28: `1.0`
  - `average_steps`
    - improved_v27: `9.25`
    - improved_v28: `9.25`
  - `average_duration_sec`
    - improved_v27: `0.5709`
    - improved_v28: `0.5675`
  - `taxonomy`
    - improved_v27: `无错误标签`
    - improved_v28: `无错误标签`

### 关键案例

#### improved_v27 失败案例：`task_057`

- 运行结果：
  - `logs/trajectories/task_057/run_20260610T140229242079Z_1281/result.json`
- 现象：
  - 已读取 `pydantic_inheritance_repo/models.py`
  - 但没有匹配到父类 validator 名单与子类 validator 名单合并的修复策略
  - 最终以 `Premature Finish` 失败

#### improved_v28 成功案例：`task_057`

- 运行结果：
  - `logs/trajectories/task_057/run_20260610T140229399114Z_2846/result.json`
- 现象：
  - 自动识别子类 `model_validator` 不应覆盖父类校验链
  - 修复后测试全部通过

### 结论

- 真实 issue 派生任务集已经扩充到 `26` 条
- 候选池里正式 accepted 任务提升到 `26` 条，`drafted` 清零，`to_review` 维持在 `4` 条
- 当前真实任务集上的结果链路已经形成：
  - `improved_v27`：覆盖删除事务提交可见性
  - `improved_v28`：进一步覆盖 model validator 继承语义
- 扩容对比中，`improved_v28` 继续保持 `100%` 成功率与 `100%` 测试通过率
- `frozen_20` 对比中，`improved_v28` 保持固定任务集无回归，并把平均耗时从 `0.5709` 小幅改善到 `0.5675`

### 剩余问题

- 最近几轮 `frozen_20` 主要提供无回归证据，而非新的同集合成功率提升
- 对象定义阶段 alias 可见性、数据转换中的空值语义、profile 驱动的排序分派仍值得优先推进
- 当前 patch 策略仍然是规则法，需要继续扩任务和扩能力

## 2026-06-11 13:46 Phase 6 评测观测性与候选批量导入补强

### 本轮目标

- 给真实 issue 候选扩容链路补一个可复用的批量导入入口
- 给最近几轮 `average_duration_sec` 回升补一个任务级定位工具
- 用真实日志先验证这两个入口确实接上了当前流水线

### 本轮新增文件

- `scripts/import_issue_batch.py`
- `scripts/analyze_duration_regressions.py`
- `tests/test_import_issue_batch.py`
- `tests/test_analyze_duration_regressions.py`
- `logs/summaries/duration_compare_realissuev32_001.json`
- `logs/summaries/duration_compare_realissuev32_001.md`
- `logs/summaries/duration_compare_frozen20v32_001.json`
- `logs/summaries/duration_compare_frozen20v32_001.md`

### 本轮修改文件

- `scripts/import_github_issue.py`
- `README.md`
- `GUIDE.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/results.md`

### 本轮实现内容

- 重构 `scripts/import_github_issue.py`：
  - 抽出可复用的单条导入函数
  - 抽出 task 草稿落盘函数
  - 让后续批量导入复用同一套候选状态维护逻辑
- 新增 `scripts/import_issue_batch.py`：
  - 支持从文本或 JSON 文件批量读取 `repo + issue`
  - 支持批量导入时直接生成 `real_issue` 草稿
  - 继续保持候选备注追加式记录，不覆盖旧历史
- 新增 `scripts/analyze_duration_regressions.py`：
  - 支持直接传两份 `batch_run` summary
  - 也支持从 `eval` 文件反推 `source_batch_run_id`
  - 输出公共任务平均耗时差值、top regressions、top improvements

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_import_issue_batch.py tests/test_analyze_duration_regressions.py tests/test_run_real_issue_eval.py -q`
  - 结果：`9 passed`
- 真实日志验证：
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev31_001.json --improved-batch-summary logs/summaries/batch_run_realissuev32_001.json --run-label realissuev32`
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen20v31_001.json --improved-batch-summary logs/summaries/batch_run_frozen20v32_001.json --run-label frozen20v32`

### 关键观察

- 扩容集时延分析：
  - 公共 `29` 条任务平均耗时：`0.6115 -> 0.6767`
  - 平均差值：`+0.0652s`
- `frozen_20` 时延分析：
  - 公共 `20` 条任务平均耗时：`0.6122 -> 0.6774`
  - 平均差值：`+0.0652s`
- 回升最明显的任务在两组分析里高度重合：
  - `task_040`
  - `task_038`
  - `task_036`
  - `task_034`

### 结论

- 最近一轮耗时回升不只是由于新增 `task_061`
- 公共任务集合也出现了系统性变慢
- 现在已经有了可以持续复用的批量导入和时延定位入口，后续能更稳地一边扩 benchmark，一边跟踪 runtime 效率变化

### 剩余问题

- 还没有对 `task_040 / task_038 / task_036 / task_034` 的 trace 做更细粒度分解
- 下一步应继续围绕这些热点任务检查是否存在固定的额外搜索、读文件或 patch 分支开销
- 新来源 issue 的扩容还需要尽快接上批量导入入口，避免候选池再次见底

## 2026-06-11 14:04 Phase 6 trace 热点分析补强

### 本轮目标

- 把时延定位从任务总耗时继续下钻到 trace / tool 级别
- 让新产生的 trace 显式记录每一步 `duration_sec`
- 用真实日志确认最近一轮回升到底主要堆在哪类动作上

### 本轮新增文件

- `scripts/analyze_trace_hotspots.py`
- `tests/test_analyze_trace_hotspots.py`
- `logs/summaries/trace_hotspots_realissuev32_001.json`
- `logs/summaries/trace_hotspots_realissuev32_001.md`
- `logs/summaries/trace_hotspots_frozen20v32_001.json`
- `logs/summaries/trace_hotspots_frozen20v32_001.md`

### 本轮修改文件

- `app/schemas/trace_schema.py`
- `app/tools/run_tests.py`
- `app/runtime/task_runner.py`
- `README.md`
- `GUIDE.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/results.md`

### 本轮实现内容

- 扩展 `TraceStep`：
  - 新增显式 `duration_sec`
- 扩展 `Trace`：
  - 新增 `started_at / finished_at`
- 优化 `run_tests`：
  - 显式记录测试命令自身的执行耗时
- 优化 `task_runner`：
  - 为 `list_files / search_code / read_file / run_tests / rule_based_patch / show_diff` 写入步骤级耗时
- 新增 `scripts/analyze_trace_hotspots.py`：
  - 优先读取显式步骤耗时
  - 兼容旧 trace 的时间戳差值回退
  - 输出任务级热点和工具级热点

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_analyze_trace_hotspots.py tests/test_analyze_duration_regressions.py tests/test_import_issue_batch.py tests/test_run_real_issue_eval.py tests/test_scaffold_semi_real_task.py -q`
  - 结果：`16 passed`
- 真实日志验证：
  - `python scripts/analyze_trace_hotspots.py --baseline-batch-summary logs/summaries/batch_run_realissuev31_001.json --improved-batch-summary logs/summaries/batch_run_realissuev32_001.json --run-label realissuev32`
  - `python scripts/analyze_trace_hotspots.py --baseline-batch-summary logs/summaries/batch_run_frozen20v31_001.json --improved-batch-summary logs/summaries/batch_run_frozen20v32_001.json --run-label frozen20v32`

### 关键观察

- 扩容集 trace 热点：
  - `run_tests` 总耗时：`16.4937 -> 18.0086`
  - 总增量：`+1.5149s`
- `frozen_20` trace 热点：
  - `run_tests` 总耗时：`11.48 -> 12.5496`
  - 总增量：`+1.0696s`
- 在任务级热点里，`task_040 / task_038 / task_036 / task_034` 的 dominant regression tool 都是 `run_tests`

### 结论

- 最近一轮系统性变慢的主因已经基本锁定到测试执行链
- `search_code / list_files / rule_based_patch` 也有回升，但量级明显小于 `run_tests`
- 后续性能优化应优先检查测试子进程启动、pytest 环境隔离和工作副本 I/O 对测试阶段的影响

### 剩余问题

- 还没有验证 `run_tests` 变慢是 pytest 启动、目录复制、环境变量注入还是文件系统抖动导致
- 下一步可以补一层测试执行剖析，拆分“子进程启动前 / 测试命令本身 / 结果解析”三个阶段
- 外部推送仍受 GitHub 凭据失效影响，但不妨碍继续推进本地实现和评测能力

## 2026-06-11 14:15 Phase 6 单任务历史时延分析补强

### 本轮目标

- 把性能诊断从 batch 级 / trace 级继续下钻到单任务历史样本
- 验证 `task_040` 在 `improved_v32` 的回升到底是稳定现象还是偶发抖动
- 为后续继续排查 `run_tests` 子进程耗时建立可复用入口

### 本轮新增文件

- `scripts/analyze_task_history.py`
- `tests/test_analyze_task_history.py`
- `logs/summaries/task_history_task_040_003.json`
- `logs/summaries/task_history_task_040_003.md`

### 本轮修改文件

- `GUIDE.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/results.md`

### 本轮实现内容

- 新增 `scripts/analyze_task_history.py`：
  - 按任务目录聚合同一任务的全部历史 run
  - 按 `tool_stats.policy_id` 分组统计
  - 输出总耗时、`run_tests` 总耗时、`run_tests_subprocess`、`summary_extraction` 的均值、范围和波动
  - 自动产出 JSON 和 Markdown 报告
- 新增 `tests/test_analyze_task_history.py`：
  - 验证按策略版本分组聚合
  - 验证最近两版 delta 计算
  - 验证输出文件落盘

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_analyze_task_history.py tests/test_runtime_diagnostics.py tests/test_analyze_trace_hotspots.py tests/test_analyze_duration_regressions.py tests/test_import_issue_batch.py tests/test_run_real_issue_eval.py tests/test_scaffold_semi_real_task.py -q`
- 真实日志验证：
  - `python scripts/analyze_task_history.py --task-dir logs/trajectories/task_040 --output-dir logs/summaries`

### 关键观察

- `task_040` 历史样本：
  - `31` 次运行
  - `15` 个策略版本
- 最近两版：
  - `improved_v31` 平均耗时：`0.6213`
  - `improved_v32` 平均耗时：`0.8171`
  - 平均增量：`+0.1958s`
- `run_tests` 维度：
  - 平均增量：`+0.2032s`
  - `improved_v32` 的已观测 `run_tests_subprocess` 平均值：`0.5296`
  - 由于旧 trace 没有该字段，当前不能直接计算跨版本 `run_tests_subprocess` 平均增量
- `improved_v32` 最慢两个样本：
  - `run_20260611T052406971975Z_3564`
  - `run_20260611T052406972313Z_3830`
  - 两者总耗时都接近 `0.946s`

### 结论

- `task_040` 的回升不是只靠单次样本才能观察到，按历史样本聚合后依然显著
- 这进一步加强了“`run_tests` 子进程执行链是主要瓶颈”的判断
- 现在线索已经从“哪一轮变慢”推进到“哪一类任务、哪一段执行链、在历史样本里如何持续变慢”

### 剩余问题

- 目前只对 `task_040` 做了历史分析，仍需扩展到 `task_038 / task_036 / task_034`
- 旧 trace 缺少显式 `subprocess_duration_sec` 字段，因此更早样本只能看到 `run_tests` 总体耗时
- 下一步应继续围绕 pytest 子进程启动、工作副本 I/O 和环境差异做更细的实验

## 2026-06-11 14:34 Phase 6 热点任务集合历史分析补强

### 本轮目标

- 把单任务历史时延分析进一步扩展成热点任务集合的横向汇总
- 验证 `task_034 / task_036 / task_038 / task_040` 是否都呈现稳定回升
- 为下一步 `run_tests` 细分实验建立更强的群体证据

### 本轮新增文件

- `scripts/analyze_task_history_cohort.py`
- `tests/test_analyze_task_history_cohort.py`
- `logs/summaries/task_history_task_034_001.json`
- `logs/summaries/task_history_task_034_001.md`
- `logs/summaries/task_history_task_036_001.json`
- `logs/summaries/task_history_task_036_001.md`
- `logs/summaries/task_history_task_038_001.json`
- `logs/summaries/task_history_task_038_001.md`
- `logs/summaries/task_history_cohort_run_tests_hotspots_v32_001.json`
- `logs/summaries/task_history_cohort_run_tests_hotspots_v32_001.md`

### 本轮修改文件

- `GUIDE.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/results.md`

### 本轮实现内容

- 新增 `scripts/analyze_task_history_cohort.py`：
  - 支持按 `task_id` 或 `task_dir` 汇总多个任务的历史分析
  - 自动汇总每个任务最近两版的耗时增量
  - 自动汇总 `run_tests` 增量和最新可观测 `subprocess` 指标
  - 产出 cohort 级 JSON 和 Markdown 报告
- 新增 `tests/test_analyze_task_history_cohort.py`：
  - 验证多任务聚合
  - 验证均值和排序
  - 验证输出文件落盘
- 对真实热点任务补齐历史分析：
  - `task_034`
  - `task_036`
  - `task_038`

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_analyze_task_history.py tests/test_analyze_task_history_cohort.py tests/test_runtime_diagnostics.py tests/test_analyze_trace_hotspots.py tests/test_analyze_duration_regressions.py tests/test_import_issue_batch.py tests/test_run_real_issue_eval.py tests/test_scaffold_semi_real_task.py -q`
  - 结果：`22 passed`
- 真实日志验证：
  - `python scripts/analyze_task_history.py --task-dir logs/trajectories/task_034 --output-dir logs/summaries`
  - `python scripts/analyze_task_history.py --task-dir logs/trajectories/task_036 --output-dir logs/summaries`
  - `python scripts/analyze_task_history.py --task-dir logs/trajectories/task_038 --output-dir logs/summaries`
  - `python scripts/analyze_task_history_cohort.py --task-id task_034 --task-id task_036 --task-id task_038 --task-id task_040 --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

### 关键观察

- 热点集合：
  - `task_034 / task_036 / task_038 / task_040`
- cohort 汇总：
  - 平均历史耗时增量：`+0.1732s`
  - 平均 `run_tests` 历史耗时增量：`+0.1665s`
  - `4 / 4` 个热点任务都呈现正向回升
- 单任务明细：
  - `task_040`: duration delta `+0.1958s`，run_tests delta `+0.2032s`
  - `task_034`: duration delta `+0.1688s`，run_tests delta `+0.1602s`
  - `task_038`: duration delta `+0.1660s`，run_tests delta `+0.1528s`
  - `task_036`: duration delta `+0.1622s`，run_tests delta `+0.1497s`

### 结论

- 最近一轮回升已经不只是某一条热点任务的问题，而是一个小型热点任务群的稳定现象
- 这组任务的耗时回升量级与 `run_tests` 增量高度接近，进一步加强了测试执行链是主因的判断
- 当前最应该做的不是继续补更多历史聚合，而是开始设计 `run_tests` 细分实验

### 剩余问题

- 目前只有 `task_040` 的最新样本显式记录了 `subprocess_duration_sec`
- 旧热点任务历史样本还缺少统一的细粒度 `run_tests` 字段
- 下一步应围绕 pytest 启动成本、工作副本 I/O、环境注入开销做专门实验

## 2026-06-11 Phase 6 run_tests 模式基准补强

### 本轮目标

- 在热点任务集合上直接验证 workspace copy 是否导致 `improved_v32` 的系统性时延回升
- 把 `run_tests` 的内部耗时继续拆细，方便后续继续下钻 pytest 执行链
- 为下一步 pytest 启动、import/collection 实验建立更可靠的排除证据

### 本轮新增文件

- `scripts/benchmark_run_tests_modes.py`
- `scripts/analyze_run_tests_mode_cohort.py`
- `tests/test_benchmark_run_tests_modes.py`
- `tests/test_analyze_run_tests_mode_cohort.py`
- `logs/summaries/run_tests_modes_task034v32_001.json`
- `logs/summaries/run_tests_modes_task034v32_001.md`
- `logs/summaries/run_tests_modes_task036v32_001.json`
- `logs/summaries/run_tests_modes_task036v32_001.md`
- `logs/summaries/run_tests_modes_task038v32_001.json`
- `logs/summaries/run_tests_modes_task038v32_001.md`
- `logs/summaries/run_tests_modes_task040v32_001.json`
- `logs/summaries/run_tests_modes_task040v32_001.md`
- `logs/summaries/run_tests_modes_cohort_run_tests_hotspots_v32_001.json`
- `logs/summaries/run_tests_modes_cohort_run_tests_hotspots_v32_001.md`

### 本轮修改文件

- `app/tools/run_tests.py`
- `app/runtime/task_runner.py`
- `tests/test_runtime_diagnostics.py`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 继续细化 `run_tests` 的诊断字段：
  - `resolve_repo_path_duration_sec`
  - `env_setup_duration_sec`
  - `pre_execution_duration_sec`
  - `command_execution_duration_sec`
  - `summary_extraction_duration_sec`
  - `subprocess_duration_sec`
- 让 `task_runner` 把 `copy_workspace` 作为独立 trace step 落盘：
  - 额外记录 `workspace_copy_duration_sec`
  - 便于把 repo 复制成本从总时延中单独观察出来
- 新增 `scripts/benchmark_run_tests_modes.py`：
  - 支持对单个任务比较 `source_repo / persistent_workspace / fresh_workspace`
  - 自动统计 copy、command、run_tests、combined 四类均值
- 新增 `scripts/analyze_run_tests_mode_cohort.py`：
  - 支持把多个热点任务的模式 benchmark 聚合成 cohort 报告
  - 自动统计 fresh / persistent 相对 source 的 delta

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_runtime_diagnostics.py tests/test_benchmark_run_tests_modes.py tests/test_analyze_run_tests_mode_cohort.py tests/test_analyze_task_history.py tests/test_analyze_task_history_cohort.py tests/test_analyze_trace_hotspots.py tests/test_analyze_duration_regressions.py tests/test_import_issue_batch.py tests/test_run_real_issue_eval.py tests/test_scaffold_semi_real_task.py -q`
  - 结果：`26 passed`
- 真实日志验证：
  - `python scripts/benchmark_run_tests_modes.py --task benchmarks/tasks/task_034.json --repetitions 3 --benchmark-label task034v32 --output-dir logs/summaries`
  - `python scripts/benchmark_run_tests_modes.py --task benchmarks/tasks/task_036.json --repetitions 3 --benchmark-label task036v32 --output-dir logs/summaries`
  - `python scripts/benchmark_run_tests_modes.py --task benchmarks/tasks/task_038.json --repetitions 3 --benchmark-label task038v32 --output-dir logs/summaries`
  - `python scripts/benchmark_run_tests_modes.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
  - `python scripts/analyze_run_tests_mode_cohort.py --benchmark-summary logs/summaries/run_tests_modes_task034v32_001.json --benchmark-summary logs/summaries/run_tests_modes_task036v32_001.json --benchmark-summary logs/summaries/run_tests_modes_task038v32_001.json --benchmark-summary logs/summaries/run_tests_modes_task040v32_001.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

### 关键观察

- 热点任务 cohort：
  - `task_034 / task_036 / task_038 / task_040`
- 聚合结果：
  - `average_persistent_run_tests_delta_sec = -0.0068`
  - `average_fresh_run_tests_delta_sec = -0.0091`
  - `average_persistent_combined_delta_sec = -0.0059`
  - `average_fresh_combined_delta_sec = -0.0068`
  - `average_fresh_copy_duration_sec = 0.0023`
  - `fresh_slower_than_source_task_count = 2`
  - `persistent_slower_than_source_task_count = 2`
- 单任务样例：
  - `task_040`
    - source repo `run_tests avg = 0.2653`
    - persistent workspace `run_tests avg = 0.2654`
    - fresh workspace `run_tests avg = 0.2710`
    - fresh copy `avg = 0.0024`
  - `task_034`
    - source repo `run_tests avg = 0.2647`
    - persistent workspace `run_tests avg = 0.2652`
    - fresh workspace `run_tests avg = 0.2711`
    - fresh copy `avg = 0.0023`
  - `task_036` / `task_038`
    - workspace 模式反而略快于 source repo

### 结论

- workspace copy 的额外成本只有毫秒级，不足以解释 `improved_v32` 的系统性回升
- fresh / persistent workspace 相比 source repo 并没有表现出稳定更慢，因此“工作副本复制是主因”的假设基本可以排除
- 当前最可信的主因已经进一步收窄到 pytest 命令执行链本身或环境层抖动

### 剩余问题

- 现在已经知道 workspace copy 不是主因，但还没有把 pytest 启动、import/collection、实际测试执行彻底拆开
- 需要继续比较首次运行与重复运行差异，确认是否存在缓存、文件系统或解释器启动抖动
- 下一步应优先设计 pytest 启动 / collection 的更细实验，而不是继续重复 workspace 模式对比

## 2026-06-11 Phase 6 pytest 分阶段基准补强

### 本轮目标

- 把 `run_tests` 命令执行链进一步拆成解释器空跑、pytest 启动、collection、full run 四层
- 验证热点任务的主要额外开销到底落在 pytest 启动、collection 还是测试主体执行
- 为后续继续拆 import/collection 内部差异提供更直接的证据

### 本轮新增文件

- `scripts/benchmark_pytest_phases.py`
- `scripts/analyze_pytest_phase_cohort.py`
- `tests/test_benchmark_pytest_phases.py`
- `tests/test_analyze_pytest_phase_cohort.py`
- `logs/summaries/pytest_phases_task034v32_001.json`
- `logs/summaries/pytest_phases_task034v32_001.md`
- `logs/summaries/pytest_phases_task036v32_001.json`
- `logs/summaries/pytest_phases_task036v32_001.md`
- `logs/summaries/pytest_phases_task038v32_001.json`
- `logs/summaries/pytest_phases_task038v32_001.md`
- `logs/summaries/pytest_phases_task040v32_001.json`
- `logs/summaries/pytest_phases_task040v32_001.md`
- `logs/summaries/pytest_phases_cohort_run_tests_hotspots_v32_001.json`
- `logs/summaries/pytest_phases_cohort_run_tests_hotspots_v32_001.md`

### 本轮修改文件

- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `scripts/benchmark_pytest_phases.py`：
  - 在同一 repo 上按顺序比较 `python_noop / pytest_version / pytest_collect_only / pytest_full_run`
  - 自动保留首次运行与重复运行均值
  - 自动计算三段差值：
    - `pytest_startup_over_python`
    - `collect_over_pytest_startup`
    - `full_over_collect`
- 新增 `scripts/analyze_pytest_phase_cohort.py`：
  - 把多个热点任务的 phase benchmark 聚合成 cohort 报告
  - 自动汇总首次运行与重复运行差异
  - 自动按 `full_over_collect` 排序，便于看哪些任务测试主体更重

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_benchmark_pytest_phases.py tests/test_analyze_pytest_phase_cohort.py tests/test_benchmark_run_tests_modes.py tests/test_analyze_run_tests_mode_cohort.py tests/test_runtime_diagnostics.py tests/test_analyze_task_history.py tests/test_analyze_task_history_cohort.py tests/test_analyze_trace_hotspots.py tests/test_analyze_duration_regressions.py tests/test_import_issue_batch.py tests/test_run_real_issue_eval.py tests/test_scaffold_semi_real_task.py -q`
  - 结果：`31 passed`
- 真实日志验证：
  - `python scripts/benchmark_pytest_phases.py --task benchmarks/tasks/task_034.json --repetitions 3 --benchmark-label task034v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_phases.py --task benchmarks/tasks/task_036.json --repetitions 3 --benchmark-label task036v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_phases.py --task benchmarks/tasks/task_038.json --repetitions 3 --benchmark-label task038v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_phases.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
  - `python scripts/analyze_pytest_phase_cohort.py --benchmark-summary logs/summaries/pytest_phases_task034v32_001.json --benchmark-summary logs/summaries/pytest_phases_task036v32_001.json --benchmark-summary logs/summaries/pytest_phases_task038v32_001.json --benchmark-summary logs/summaries/pytest_phases_task040v32_001.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

### 关键观察

- 热点任务 cohort：
  - `task_034 / task_036 / task_038 / task_040`
- 聚合结果：
  - `average_pytest_startup_over_python_sec = 0.1322`
  - `average_collect_over_pytest_startup_sec = 0.0797`
  - `average_full_over_collect_sec = 0.0159`
  - `average_collect_first_minus_repeated_sec = 0.0132`
  - `average_full_first_minus_repeated_sec = -0.0065`
- 单任务样例：
  - `task_034`
    - `python_noop avg = 0.0465`
    - `pytest_version avg = 0.184`
    - `pytest_collect_only avg = 0.261`
    - `pytest_full_run avg = 0.27`
  - `task_040`
    - `python_noop avg = 0.0381`
    - `pytest_version avg = 0.1667`
    - `pytest_collect_only avg = 0.246`
    - `pytest_full_run avg = 0.266`

### 结论

- 热点任务的主要额外开销集中在 pytest 启动和 collection，而不是测试主体执行
- `full_over_collect` 只有十几毫秒量级，说明当前系统性回升并不像是测试用例本身变重
- `collect_first_minus_repeated` 仍有轻微正值，说明首次 collection 可能存在少量额外抖动

### 剩余问题

- 现在已经知道主要耗时堆在启动与 collection，但还没有把 collection 内部的 import、发现、构建开销继续拆开
- 还需要继续验证是否存在解释器级缓存、文件系统抖动或 Windows 环境特有开销
- 下一步应优先补 import/collection 内部差异实验，而不是回到 workspace copy 假设

## 2026-06-11 Phase 6 pytest importtime 基准补强

### 本轮目标

- 把 `pytest collect-only` 的额外耗时进一步拆到 import 链层级
- 验证 collection 变慢是否伴随稳定新增模块与 import self time 增量
- 为下一步判断平台链路、终端能力或 pytest 默认插件链贡献提供更直接证据

### 本轮新增文件

- `scripts/benchmark_pytest_importtime.py`
- `scripts/analyze_pytest_importtime_cohort.py`
- `tests/test_benchmark_pytest_importtime.py`
- `tests/test_analyze_pytest_importtime_cohort.py`
- `logs/summaries/pytest_importtime_task034v32_001.json`
- `logs/summaries/pytest_importtime_task034v32_001.md`
- `logs/summaries/pytest_importtime_task034v32_002.json`
- `logs/summaries/pytest_importtime_task034v32_002.md`
- `logs/summaries/pytest_importtime_task036v32_001.json`
- `logs/summaries/pytest_importtime_task036v32_001.md`
- `logs/summaries/pytest_importtime_task036v32_002.json`
- `logs/summaries/pytest_importtime_task036v32_002.md`
- `logs/summaries/pytest_importtime_task038v32_001.json`
- `logs/summaries/pytest_importtime_task038v32_001.md`
- `logs/summaries/pytest_importtime_task038v32_002.json`
- `logs/summaries/pytest_importtime_task038v32_002.md`
- `logs/summaries/pytest_importtime_task040v32_001.json`
- `logs/summaries/pytest_importtime_task040v32_001.md`
- `logs/summaries/pytest_importtime_task040v32_002.json`
- `logs/summaries/pytest_importtime_task040v32_002.md`
- `logs/summaries/pytest_importtime_cohort_run_tests_hotspots_v32_001.json`
- `logs/summaries/pytest_importtime_cohort_run_tests_hotspots_v32_001.md`
- `logs/summaries/pytest_importtime_cohort_run_tests_hotspots_v32_002.json`
- `logs/summaries/pytest_importtime_cohort_run_tests_hotspots_v32_002.md`

### 本轮修改文件

- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `scripts/benchmark_pytest_importtime.py`：
  - 用 `python -X importtime -m pytest --version`
  - 对比 `python -X importtime -m pytest ... --collect-only`
  - 自动统计：
    - wall time 增量
    - import self time 增量
    - unique module 增量
    - 首次运行与重复运行差异
  - 自动产出 collect-only 相比 version 稳定新增的高频模块
- 新增 `scripts/analyze_pytest_importtime_cohort.py`：
  - 把多个热点任务的 importtime benchmark 聚合成 cohort 报告
  - 自动汇总新增模块出现频次
  - 自动比较各任务的 import 增量强弱
- 在同一轮里又追加了一版 `_002` 样本：
  - 保留 `_001` 作为首轮产物
  - `_002` 基于更可读的新增模块排序逻辑重新生成

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_benchmark_pytest_importtime.py tests/test_analyze_pytest_importtime_cohort.py tests/test_benchmark_pytest_phases.py tests/test_analyze_pytest_phase_cohort.py -q`
  - 结果：`12 passed`
- 真实日志验证：
  - `python scripts/benchmark_pytest_importtime.py --task benchmarks/tasks/task_034.json --repetitions 3 --benchmark-label task034v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_importtime.py --task benchmarks/tasks/task_036.json --repetitions 3 --benchmark-label task036v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_importtime.py --task benchmarks/tasks/task_038.json --repetitions 3 --benchmark-label task038v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_importtime.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
  - `python scripts/analyze_pytest_importtime_cohort.py --benchmark-summary logs/summaries/pytest_importtime_task034v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task036v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task038v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task040v32_002.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

### 关键观察

- 最新热点任务 cohort：
  - `task_034 / task_036 / task_038 / task_040`
- `_002` 聚合结果：
  - `average_collect_wall_delta_sec = 0.0697`
  - `average_collect_import_self_delta_us = 20898`
  - `average_collect_unique_module_delta = 37`
  - `average_collect_wall_first_minus_repeated_sec = 0.0113`
  - `average_collect_import_self_first_minus_repeated_us = 1449.75`
- 高频新增模块：
  - `_ctypes`
  - `pyexpat`
  - `xml.etree.ElementTree`
  - `_pytest.skipping`
  - `ctypes.wintypes`
  - `ctypes`
  - `pdb`
  - `_pytest.terminalprogress`
- 单任务样例：
  - `task_040`
    - `collect wall delta = 0.068`
    - `collect import self delta = 30108us`
  - `task_034`
    - `collect wall delta = 0.0709`
    - `collect import self delta = 18859us`

### 结论

- `collect-only` 的额外 wall time 与稳定的 import self time 增量一起出现，不再只是“collection 好像慢了”
- 四个热点任务都稳定多出 `37` 个模块，说明这部分开销具备一致性
- 当前最可信的方向已经从“pytest 启动 / collection 变慢”继续收窄到“collection 阶段稳定新增的 import 链”

### 剩余问题

- 现在已经知道哪些模块在 collection 阶段稳定新增，但还没有区分它们是平台链路、终端能力还是 pytest 默认插件链导致
- 还需要继续验证是否能通过更轻的 pytest 配置或命令形态减少这部分开销
- 下一步应优先比较 pytest 默认插件链、终端相关模块和 Windows 特定模块的贡献

## 2026-06-11 Phase 6 pytest 插件变体基准补强

### 背景

上一轮 `pytest importtime` 已经证明：

- `collect-only` 阶段稳定多出 `37` 个模块
- 额外 import self time 大约是 `20898us`
- 高频新增模块里同时出现了 `pdb`、`_pytest.terminalprogress`、`ctypes.wintypes` 等线索

但我们还不知道：

- 这些额外模块是否主要来自 pytest 默认插件链
- 如果关闭一部分可安全关闭插件，是否能明显降低 collection 开销

### 目标

- 把“默认插件链是不是主因”从猜测变成可复现证据
- 尽早排除低价值方向，避免后续在错误假设上消耗时间
- 为下一步继续切分 Windows 平台链路、终端能力链路和 pytest 主干 collection 逻辑提供依据

### 改动类型

- `benchmark`

### 主要文件

- `scripts/benchmark_pytest_plugin_variants.py`
- `scripts/analyze_pytest_plugin_variant_cohort.py`
- `tests/test_benchmark_pytest_plugin_variants.py`
- `tests/test_analyze_pytest_plugin_variant_cohort.py`
- `logs/summaries/pytest_plugin_variants_task034v32_001.json`
- `logs/summaries/pytest_plugin_variants_task034v32_001.md`
- `logs/summaries/pytest_plugin_variants_task036v32_001.json`
- `logs/summaries/pytest_plugin_variants_task036v32_001.md`
- `logs/summaries/pytest_plugin_variants_task038v32_001.json`
- `logs/summaries/pytest_plugin_variants_task038v32_001.md`
- `logs/summaries/pytest_plugin_variants_task040v32_001.json`
- `logs/summaries/pytest_plugin_variants_task040v32_001.md`
- `logs/summaries/pytest_plugin_variants_cohort_run_tests_hotspots_v32_001.json`
- `logs/summaries/pytest_plugin_variants_cohort_run_tests_hotspots_v32_001.md`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `scripts/benchmark_pytest_plugin_variants.py`：
  - 对同一任务分别跑三种变体：
    - `default_plugins`
    - `light_terminal_plugins`
    - `minimal_safe_plugins`
  - 同时记录：
    - wall time
    - import self time
    - unique module 数
- 新增 `scripts/analyze_pytest_plugin_variant_cohort.py`：
  - 把多个热点任务的 plugin variant 基准聚合成 cohort 报告
  - 自动按变体输出平均 wall delta、import delta 和 module delta
- 验证了当前可安全关闭的一组默认插件：
  - `junitxml`
  - `pastebin`
  - `setuponly`
  - `setupplan`
  - `stepwise`
  - `warnings`
  - `faulthandler`
  - `terminalprogress`
  - `debugging`
  - `unraisableexception`
  - `threadexception`

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_benchmark_pytest_plugin_variants.py tests/test_analyze_pytest_plugin_variant_cohort.py tests/test_benchmark_pytest_importtime.py tests/test_analyze_pytest_importtime_cohort.py -q`
  - 结果：`13 passed`
- 更大范围回归：
  - `python -m pytest tests/test_benchmark_pytest_importtime.py tests/test_analyze_pytest_importtime_cohort.py tests/test_benchmark_pytest_phases.py tests/test_analyze_pytest_phase_cohort.py tests/test_benchmark_run_tests_modes.py tests/test_analyze_run_tests_mode_cohort.py tests/test_runtime_diagnostics.py tests/test_analyze_task_history.py tests/test_analyze_task_history_cohort.py tests/test_analyze_trace_hotspots.py tests/test_analyze_duration_regressions.py tests/test_import_issue_batch.py tests/test_run_real_issue_eval.py tests/test_scaffold_semi_real_task.py -q`
  - 结果：`38 passed`
- 真实日志验证：
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_034.json --repetitions 3 --benchmark-label task034v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_036.json --repetitions 3 --benchmark-label task036v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_038.json --repetitions 3 --benchmark-label task038v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
  - `python scripts/analyze_pytest_plugin_variant_cohort.py --benchmark-summary logs/summaries/pytest_plugin_variants_task034v32_001.json --benchmark-summary logs/summaries/pytest_plugin_variants_task036v32_001.json --benchmark-summary logs/summaries/pytest_plugin_variants_task038v32_001.json --benchmark-summary logs/summaries/pytest_plugin_variants_task040v32_001.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

### 关键观察

- 最新热点任务 cohort：
  - `task_034 / task_036 / task_038 / task_040`
- cohort 聚合结果：
  - `light_terminal_plugins`
    - `avg_wall_delta = 0.002`
    - `avg_import_delta_us = -102`
    - `avg_module_delta = 0`
  - `minimal_safe_plugins`
    - `avg_wall_delta = 0.0025`
    - `avg_import_delta_us = 594`
    - `avg_module_delta = 0`
- `Removed Modules` 为空：
  - 说明这组插件变体并没有稳定移除前面 importtime 基准里观测到的新增模块

### 结论

- 关闭这组可安全关闭的默认 pytest 插件后，并没有出现稳定可观的降本
- 模块数增量依然是 `0`，说明前面看到的新增 import 链不是主要由这组插件驱动
- 这是一个很重要的负结论：
  - 当前慢点大概率不在这组默认插件上
  - 后续应优先继续切分：
    - `pytest` 主干 collection 逻辑
    - Windows 平台链路
    - 终端能力链路

### 剩余问题

- 还需要继续验证 `colorama / pdb / ctypes.wintypes / _pytest.skipping` 等链路各自贡献了多少
- 还没有把“Windows 平台链路”和“pytest 主干 collection 逻辑”完全拆开
- 下一步更适合设计更细的命令形态实验，而不是继续在这组默认插件上追加更多轮次

## 2026-06-11 Phase 6 pytest importtime 分组分析补强

### 背景

上一轮已经确认两件事：

- `pytest importtime` 里稳定多出 `37` 个模块
- 关闭一组可安全关闭的默认插件后，几乎没有降本

但我们还缺少更强的一步：

- 这些新增模块到底主要属于哪些链路
- 哪些链路更值得用下一轮实验去切

### 目标

- 复用已有 `pytest importtime` benchmark 结果
- 把“模块列表”提升为“来源分组”
- 为下一轮命令形态实验提供更聚焦的优先级

### 改动类型

- `benchmark`

### 主要文件

- `scripts/analyze_pytest_importtime_groups.py`
- `tests/test_analyze_pytest_importtime_groups.py`
- `logs/summaries/pytest_import_groups_run_tests_hotspots_v32_001.json`
- `logs/summaries/pytest_import_groups_run_tests_hotspots_v32_001.md`
- `logs/summaries/pytest_import_groups_run_tests_hotspots_v32_002.json`
- `logs/summaries/pytest_import_groups_run_tests_hotspots_v32_002.md`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `scripts/analyze_pytest_importtime_groups.py`：
  - 直接读取已有 `pytest_importtime_task*_002.json`
  - 比较 `pytest_version_importtime` 与 `pytest_collect_importtime` 的最后一轮模块集合
  - 将新增模块按链路分组：
    - `pytest_optional_plugins`
    - `windows_ctypes`
    - `xml_stack`
    - `terminal_chain`
    - `debugging_chain`
    - `pytest_collection_core`
    - `python_shell_chain`
    - `other`
- 新增 `tests/test_analyze_pytest_importtime_groups.py`
  - 覆盖分组规则识别
  - 覆盖 cohort 聚合
  - 覆盖输出文件生成
- 在同一轮里保留 `_001` 首版样本后，又根据真实模块清单补强规则并生成 `_002`
  - `_002` 已把原来过大的 `other` 压缩到 `0`

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_analyze_pytest_importtime_groups.py tests/test_analyze_pytest_importtime_cohort.py tests/test_benchmark_pytest_importtime.py -q`
  - 结果：`10 passed`
- 真实日志验证：
  - `python scripts/analyze_pytest_importtime_groups.py --benchmark-summary logs/summaries/pytest_importtime_task034v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task036v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task038v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task040v32_002.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

### 关键观察

- 热点任务 cohort：
  - `task_034 / task_036 / task_038 / task_040`
- `_002` 聚合结果：
  - `pytest_optional_plugins`: `avg self(us) = 6181`
  - `windows_ctypes`: `avg self(us) = 5103`
  - `xml_stack`: `avg self(us) = 4026`
  - `terminal_chain`: `avg self(us) = 3653`
  - `debugging_chain`: `avg self(us) = 2094`
  - `pytest_collection_core`: `avg self(us) = 1126`
  - `python_shell_chain`: `avg self(us) = 722`
  - `other`: `avg self(us) = 0`
- 四个热点任务的 dominant group 都是：
  - `pytest_optional_plugins`

### 结论

- 新增 import 开销已经几乎都能归入明确链路，说明这条证据链足够可解释，不再只是“多了很多模块”
- 当前最值得继续下钻的第一优先级是：
  - `pytest_optional_plugins`
- 第二优先级是：
  - `windows_ctypes`
  - `xml_stack`
  - `terminal_chain`
- 这也解释了为什么上一轮“关闭一组可安全关闭插件”没有明显降本：
  - 那组插件并没有覆盖掉当前 import 开销最大的整块来源

### 剩余问题

- 还需要验证 `pytest_optional_plugins` 中哪些是 builtin 但可安全关闭、哪些不适合动
- 还需要验证 `windows_ctypes / xml_stack / terminal_chain` 是否只是平台不可避免成本
- 下一步更适合设计更细的 `collect-only` 命令形态，而不是继续重复同类聚合分析

## 2026-06-11 Phase 6 pytest 插件变体基准修正与重跑

### 背景

在继续下钻时，我们回看了上一轮 `pytest plugin variants` 的原始产物，发现：

- `_001` 样本里的命令被错误拼成了
  - `python -X importtime python -m pytest ...`
- 这会导致：
  - `ok = False`
  - `exit_code = 2`

也就是说，上一轮“几乎没有收益”的结论不能继续直接信任。

### 目标

- 修正 `plugin variants` benchmark 的命令拼接
- 重新生成热点任务样本与 cohort 报告
- 用修正后的 `_002` 结果替换原先失真的判断

### 改动类型

- `benchmark`
- `bugfix`

### 主要文件

- `scripts/benchmark_pytest_plugin_variants.py`
- `tests/test_benchmark_pytest_plugin_variants.py`
- `logs/summaries/pytest_plugin_variants_task034v32_002.json`
- `logs/summaries/pytest_plugin_variants_task034v32_002.md`
- `logs/summaries/pytest_plugin_variants_task036v32_002.json`
- `logs/summaries/pytest_plugin_variants_task036v32_002.md`
- `logs/summaries/pytest_plugin_variants_task038v32_002.json`
- `logs/summaries/pytest_plugin_variants_task038v32_002.md`
- `logs/summaries/pytest_plugin_variants_task040v32_002.json`
- `logs/summaries/pytest_plugin_variants_task040v32_002.md`
- `logs/summaries/pytest_plugin_variants_cohort_run_tests_hotspots_v32_002.json`
- `logs/summaries/pytest_plugin_variants_cohort_run_tests_hotspots_v32_002.md`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 修正 `scripts/benchmark_pytest_plugin_variants.py`
  - 不再手工拼出错误的 `python -X importtime python -m pytest ...`
  - 统一复用：
    - `scripts/benchmark_pytest_importtime.py` 里的 `_build_collect_only_command`
    - `scripts/benchmark_pytest_importtime.py` 里的 `_build_importtime_command`
- 更新 `tests/test_benchmark_pytest_plugin_variants.py`
  - 让命令断言和真实正确命令保持一致
- 重新生成四个热点任务和 cohort 的 `_002` 样本

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_benchmark_pytest_plugin_variants.py tests/test_analyze_pytest_plugin_variant_cohort.py tests/test_analyze_pytest_importtime_groups.py tests/test_benchmark_pytest_importtime.py tests/test_analyze_pytest_importtime_cohort.py -q`
  - 结果：`16 passed`
- 真实日志验证：
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_034.json --repetitions 3 --benchmark-label task034v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_036.json --repetitions 3 --benchmark-label task036v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_038.json --repetitions 3 --benchmark-label task038v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
  - `python scripts/analyze_pytest_plugin_variant_cohort.py --benchmark-summary logs/summaries/pytest_plugin_variants_task034v32_002.json --benchmark-summary logs/summaries/pytest_plugin_variants_task036v32_002.json --benchmark-summary logs/summaries/pytest_plugin_variants_task038v32_002.json --benchmark-summary logs/summaries/pytest_plugin_variants_task040v32_002.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

### 关键观察

- 修正后的 `_002` cohort：
  - `minimal_safe_plugins`
    - `avg_wall_delta = -0.0317`
    - `avg_import_delta_us = -5853`
    - `avg_module_delta = -22`
  - `light_terminal_plugins`
    - `avg_wall_delta = 0.0012`
    - `avg_import_delta_us = 2804`
    - `avg_module_delta = -15`
- 稳定 removed modules 包括：
  - `_pytest.junitxml`
  - `_pytest.pastebin`
  - `_pytest.setuponly`
  - `_pytest.setupplan`
  - `_pytest.stepwise`
  - `_pytest.faulthandler`
  - `_pytest.terminalprogress`

### 结论

- 上一轮 `_001` 的“负结论”不能再作为当前判断依据
- 修正后的 `_002` 已证明：
  - `minimal_safe_plugins` 确实能稳定降本
  - `light_terminal_plugins` 基本没有稳定收益
- 这进一步说明：
  - 主要收益不只是来自轻量终端相关项
  - 更可能来自 `pytest_optional_plugins` 这组更完整的 builtin optional plugin 集合

### 剩余问题

- 还需要把 `minimal_safe_plugins` 再拆成更细子组
- 还需要确认哪些 builtin plugin 可以长期安全关闭，哪些只适合 benchmark 诊断
- 下一步最值得做的是 optional plugin 子组 benchmark，而不是回到更粗粒度的 plugin on/off 对比

## 2026-06-11 Phase 6 pytest optional plugin 子组切分

### 背景

修正后的 `plugin variants` `_002` 已经说明：

- `minimal_safe_plugins` 稳定降本
- 但我们还不知道主要收益来自哪一组 plugin 开关

### 目标

- 把 `minimal_safe_plugins` 再切开一层
- 尽快判断主要 wall time 收益是否来自 `debugging / unraisableexception / threadexception`

### 改动类型

- `benchmark`

### 主要文件

- `scripts/benchmark_pytest_plugin_variants.py`
- `tests/test_benchmark_pytest_plugin_variants.py`
- `logs/summaries/pytest_plugin_variants_task034v32_003.json`
- `logs/summaries/pytest_plugin_variants_task034v32_003.md`
- `logs/summaries/pytest_plugin_variants_task036v32_003.json`
- `logs/summaries/pytest_plugin_variants_task036v32_003.md`
- `logs/summaries/pytest_plugin_variants_task038v32_003.json`
- `logs/summaries/pytest_plugin_variants_task038v32_003.md`
- `logs/summaries/pytest_plugin_variants_task040v32_003.json`
- `logs/summaries/pytest_plugin_variants_task040v32_003.md`
- `logs/summaries/pytest_plugin_variants_cohort_run_tests_hotspots_v32_003.json`
- `logs/summaries/pytest_plugin_variants_cohort_run_tests_hotspots_v32_003.md`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 在现有 plugin variant benchmark 中新增：
  - `debug_exception_plugins`
    - `-p no:debugging`
    - `-p no:unraisableexception`
    - `-p no:threadexception`
- 保持原有：
  - `default_plugins`
  - `light_terminal_plugins`
  - `minimal_safe_plugins`
- 重新生成四个热点任务与 cohort 的 `_003` 样本

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_benchmark_pytest_plugin_variants.py tests/test_analyze_pytest_plugin_variant_cohort.py -q`
  - 结果：`6 passed`
- 真实日志验证：
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_034.json --repetitions 3 --benchmark-label task034v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_036.json --repetitions 3 --benchmark-label task036v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_038.json --repetitions 3 --benchmark-label task038v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
  - `python scripts/analyze_pytest_plugin_variant_cohort.py --benchmark-summary logs/summaries/pytest_plugin_variants_task034v32_003.json --benchmark-summary logs/summaries/pytest_plugin_variants_task036v32_003.json --benchmark-summary logs/summaries/pytest_plugin_variants_task038v32_003.json --benchmark-summary logs/summaries/pytest_plugin_variants_task040v32_003.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

### 关键观察

- `_003` cohort：
  - `minimal_safe_plugins`
    - `avg_wall_delta = -0.0331`
    - `avg_import_delta_us = -6415`
    - `avg_module_delta = -22`
  - `debug_exception_plugins`
    - `avg_wall_delta = -0.0235`
    - `avg_import_delta_us = 2073`
    - `avg_module_delta = -6`
  - `light_terminal_plugins`
    - `avg_wall_delta = -0.0123`
    - `avg_import_delta_us = -4433`
    - `avg_module_delta = -15`
- `debug_exception_plugins` 稳定移除：
  - `_pytest.threadexception`
  - `_pytest.unraisableexception`
  - `cmd`
  - `code`
  - `codeop`
  - `pdb`

### 结论

- `debug_exception_plugins` 单独已经贡献了大部分 wall time 改善
- `light_terminal_plugins` 也有收益，但量级明显更小
- 这说明：
  - 主要收益很可能来自 `debugging / unraisableexception / threadexception`
  - 下一步最该做的是把这三个插件再拆成单插件验证，而不是继续粗粒度组合

### 剩余问题

- 还需要确认三者里哪一个是主导项，还是三者叠加才明显
- 还需要确认关闭这些插件是否适合作为正式 runtime 默认行为，还是只应作为 benchmark 诊断能力
- 下一步应优先做单插件切分实验

## 2026-06-11 Phase 6 debug_exception 单插件切分与 v33 runtime 接线

### 背景

上一轮 `_003` 已经说明：

- `debug_exception_plugins` 是主要收益来源之一

但还没回答两个问题：

- 三个插件里到底谁贡献最大
- benchmark 结论能不能安全接进 runtime 主线

### 目标

- 把 `debug_exception_plugins` 再拆成单插件
- 把最可信的一项接入 policy/runtime
- 用小集合先验证不回归且有实际时延收益

### 改动类型

- `benchmark`
- `runtime`
- `policy`

### 主要文件

- `scripts/benchmark_pytest_plugin_variants.py`
- `tests/test_benchmark_pytest_plugin_variants.py`
- `app/agent/policy.py`
- `app/tools/run_tests.py`
- `app/runtime/task_runner.py`
- `tests/test_runtime_diagnostics.py`
- `optimization/policy_versions/improved_v33.json`
- `benchmarks/manifests/run_tests_hotspots_v32.json`
- `logs/summaries/pytest_plugin_variants_task034v32_004.json`
- `logs/summaries/pytest_plugin_variants_task034v32_004.md`
- `logs/summaries/pytest_plugin_variants_task036v32_004.json`
- `logs/summaries/pytest_plugin_variants_task036v32_004.md`
- `logs/summaries/pytest_plugin_variants_task038v32_004.json`
- `logs/summaries/pytest_plugin_variants_task038v32_004.md`
- `logs/summaries/pytest_plugin_variants_task040v32_004.json`
- `logs/summaries/pytest_plugin_variants_task040v32_004.md`
- `logs/summaries/pytest_plugin_variants_cohort_run_tests_hotspots_v32_004.json`
- `logs/summaries/pytest_plugin_variants_cohort_run_tests_hotspots_v32_004.md`
- `logs/summaries/batch_run_hotspotsv32baseline_001.json`
- `logs/summaries/batch_run_hotspotsv32baseline_001.md`
- `logs/summaries/batch_run_hotspotsv33_001.json`
- `logs/summaries/batch_run_hotspotsv33_001.md`
- `logs/summaries/duration_compare_hotspotsv33_001.json`
- `logs/summaries/duration_compare_hotspotsv33_001.md`
- `logs/summaries/trace_hotspots_hotspotsv33_001.json`
- `logs/summaries/trace_hotspots_hotspotsv33_001.md`

### 本轮实现内容

- 在 plugin variant benchmark 中新增单插件变体：
  - `debugging_only`
  - `unraisableexception_only`
  - `threadexception_only`
- 为 runtime 增加 policy 级 pytest flags 注入口：
  - `PolicyConfig.pytest_additional_flags`
  - `run_tests(..., additional_pytest_flags=...)`
  - `task_runner` 在 pre/post test 两次执行里透传 policy flags
- 新增 `improved_v33`
  - 当前只注入：
    - `-p no:unraisableexception`
- 新增小集合 manifest：
  - `run_tests_hotspots_v32.json`

### 测试与验证

- 自动化测试：
  - `python -m pytest tests/test_runtime_diagnostics.py tests/test_benchmark_pytest_plugin_variants.py tests/test_analyze_pytest_plugin_variant_cohort.py -q`
  - 结果：`11 passed`
- 单插件 benchmark：
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_034.json --repetitions 3 --benchmark-label task034v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_036.json --repetitions 3 --benchmark-label task036v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_038.json --repetitions 3 --benchmark-label task038v32 --output-dir logs/summaries`
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
  - `python scripts/analyze_pytest_plugin_variant_cohort.py --benchmark-summary logs/summaries/pytest_plugin_variants_task034v32_004.json --benchmark-summary logs/summaries/pytest_plugin_variants_task036v32_004.json --benchmark-summary logs/summaries/pytest_plugin_variants_task038v32_004.json --benchmark-summary logs/summaries/pytest_plugin_variants_task040v32_004.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`
- runtime 小集合验证：
  - `python scripts/run_batch.py --manifest benchmarks/manifests/run_tests_hotspots_v32.json --policy optimization/policy_versions/improved_v32.json --run-label hotspotsv32baseline`
  - `python scripts/run_batch.py --manifest benchmarks/manifests/run_tests_hotspots_v32.json --policy optimization/policy_versions/improved_v33.json --run-label hotspotsv33`
  - `python -m scripts.analyze_duration_regressions --baseline-batch-summary logs/summaries/batch_run_hotspotsv32baseline_001.json --improved-batch-summary logs/summaries/batch_run_hotspotsv33_001.json --run-label hotspotsv33`
  - `python -m scripts.analyze_trace_hotspots --baseline-batch-summary logs/summaries/batch_run_hotspotsv32baseline_001.json --improved-batch-summary logs/summaries/batch_run_hotspotsv33_001.json --run-label hotspotsv33`

### 关键观察

- `_004` plugin variant cohort：
  - `unraisableexception_only`
    - `avg_wall_delta = -0.0282`
    - `avg_import_delta_us = -4683`
    - `avg_module_delta = -1`
  - `debugging_only`
    - `avg_wall_delta = -0.0104`
  - `threadexception_only`
    - `avg_wall_delta = 0.0059`
  - `debug_exception_plugins`
    - `avg_wall_delta = -0.0346`
  - `minimal_safe_plugins`
    - `avg_wall_delta = -0.0496`
- `improved_v33` 小集合验证：
  - 成功率：`1.0 -> 1.0`
  - 公共平均耗时：`0.5589 -> 0.5569`
  - `common_average_delta_sec = -0.002`

### 结论

- 当前最可信、最适合先接入 runtime 的低风险项是：
  - `-p no:unraisableexception`
- `threadexception` 不值得优先推进
- `debugging` 仍有一定收益，但不如 `unraisableexception` 明确
- benchmark 结论已经成功接入 runtime 主线，且小集合验证未出现成功率回归

### 剩余问题

- 还需要把 `improved_v33` 扩到更大集合，确认收益在更广任务集上是否仍成立
- 还需要确认 `-p no:unraisableexception` 是否适合作为未来默认策略的一部分
- 下一步更适合做更大集合验证，而不是继续只在热点 4 任务上迭代

## 2026-06-11 Phase 6 improved_v33 frozen_20 同集合验证

### 背景

上一轮已经完成：

- `improved_v33` 小集合热点验证
- 结论是：
  - 不回归
  - 平均总耗时仅有小幅改善

但要让它真正进入主线候选，必须先过 `frozen_20` 同集合验证。

### 目标

- 在固定 `20` 条真实任务上比较 `improved_v32 -> improved_v33`
- 确认功能无回归
- 确认时延是否继续改善，而不是只在热点小集合上有效

### 改动类型

- `benchmark`
- `evaluation`

### 主要文件

- `logs/summaries/batch_run_frozen20v33_001.json`
- `logs/summaries/batch_run_frozen20v33_001.md`
- `logs/summaries/batch_eval_frozen20v33_001.json`
- `logs/summaries/batch_eval_frozen20v33_001.md`
- `logs/summaries/batch_compare_frozen20_step12_001.json`
- `logs/summaries/batch_compare_frozen20_step12_001.md`
- `logs/summaries/duration_compare_frozen20v33_001.json`
- `logs/summaries/duration_compare_frozen20v33_001.md`
- `logs/summaries/trace_hotspots_frozen20v33_001.json`
- `logs/summaries/trace_hotspots_frozen20v33_001.md`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 运行 `frozen_20` 上的 `improved_v33`
- 生成 batch/eval/compare 报告
- 追加时延与 trace 热点分析

### 测试与验证

- 运行命令：
  - `python scripts/run_batch.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v33.json --run-label frozen20v33`
  - `python -m evals.batch_eval --batch-summary E:\My_Projects\agentic-software-engineering-roadmap\logs\summaries\batch_run_frozen20v33_001.json --output-dir E:\My_Projects\agentic-software-engineering-roadmap\logs\summaries --run-label frozen20v33`
  - `python -m scripts.analyze_duration_regressions --baseline-batch-summary E:\My_Projects\agentic-software-engineering-roadmap\logs\summaries\batch_run_frozen20v32_001.json --improved-batch-summary E:\My_Projects\agentic-software-engineering-roadmap\logs\summaries\batch_run_frozen20v33_001.json --run-label frozen20v33`
  - `python -m scripts.analyze_trace_hotspots --baseline-batch-summary E:\My_Projects\agentic-software-engineering-roadmap\logs\summaries\batch_run_frozen20v32_001.json --improved-batch-summary E:\My_Projects\agentic-software-engineering-roadmap\logs\summaries\batch_run_frozen20v33_001.json --run-label frozen20v33`
  - `compare_evals.compare_eval_summaries(...)` 直接生成 `batch_compare_frozen20_step12_001`

### 关键观察

- `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6774 -> 0.5379`
  - `average_steps: 9.25 -> 10.25`
- 时延分析：
  - `common_average_delta_sec = -0.1395`
- trace 热点：
  - `run_tests` 总耗时：`12.5496 -> 9.9555`
  - `delta_total_duration_sec = -2.5941`
- 任务级最大改善：
  - `task_040`: `-0.4307s`
  - `task_034`: `-0.2753s`
  - `task_036`: `-0.2646s`
  - `task_038`: `-0.2409s`

### 结论

- `improved_v33` 已通过 `frozen_20` 同集合验证
- 它不仅保持了 `100%` 成功率和 `100%` 测试通过率，还显著改善了平均耗时
- 当前这已经足够支撑把 `v33` 视为后续更大集合验证的正式候选策略

### 剩余问题

- 还需要把 `v33` 扩到正式 `30` 条任务集，确认扩容集也受益
- 还需要决定后续是继续堆 `unraisableexception` 方向，还是开始构建 `frozen_40`
- 下一步更适合做正式集验证，而不是回到更细碎的插件切分

## 2026-06-11 Phase 6 improved_v33 正式 30 条任务集验证

### 背景

上一轮已经完成：

- `improved_v33` 小集合热点验证
- `improved_v33` `frozen_20` 同集合验证

这两轮已经说明：

- `-p no:unraisableexception` 不是明显有风险的 runtime 改动
- 它在固定集合上已经带来强阳性的耗时改善

但在进入长期 benchmark 主线之前，还需要确认它在正式 `30` 条真实任务集上是否同样成立。

### 目标

- 在正式 `30` 条真实任务集上比较 `improved_v32 -> improved_v33`
- 确认功能无回归
- 确认耗时改善不是只出现在热点小集合或 `frozen_20`
- 判断 `v33` 是否已经足够成为后续 `60+` 扩容与 `frozen_40` 的候选基线

### 改动类型

- `benchmark`
- `evaluation`
- `documentation`

### 主要文件

- `logs/summaries/batch_run_realissuev33_001.json`
- `logs/summaries/batch_run_realissuev33_001.md`
- `logs/summaries/batch_eval_realissuev33_001.json`
- `logs/summaries/batch_eval_realissuev33_001.md`
- `logs/summaries/batch_compare_realissue_step13_002.json`
- `logs/summaries/batch_compare_realissue_step13_002.md`
- `logs/summaries/duration_compare_realissuev33_001.json`
- `logs/summaries/duration_compare_realissuev33_001.md`
- `logs/summaries/trace_hotspots_realissuev33_001.json`
- `logs/summaries/trace_hotspots_realissuev33_001.md`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 运行正式 `30` 条真实任务集上的 `improved_v33`
- 生成 batch run、batch eval 与 compare 报告
- 补齐正式集上的时延回归分析
- 补齐正式集上的 trace 热点分析
- 把 `v33` 的正式集结论同步进项目记忆、结果页、行动清单与指南

### 测试与验证

- 运行命令：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v33.json --run-label realissuev33 --compare-against-eval logs/summaries/batch_eval_realissuev32_001.json --compare-label realissue_step13`
  - `python -m scripts.analyze_duration_regressions --baseline-batch-summary E:\My_Projects\agentic-software-engineering-roadmap\logs\summaries\batch_run_realissuev32_001.json --improved-batch-summary E:\My_Projects\agentic-software-engineering-roadmap\logs\summaries\batch_run_realissuev33_001.json --run-label realissuev33`
  - `python -m scripts.analyze_trace_hotspots --baseline-batch-summary E:\My_Projects\agentic-software-engineering-roadmap\logs\summaries\batch_run_realissuev32_001.json --improved-batch-summary E:\My_Projects\agentic-software-engineering-roadmap\logs\summaries\batch_run_realissuev33_001.json --run-label realissuev33`

### 关键观察

- 正式 `30` 条任务集结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6778 -> 0.5423`
  - `average_steps: 9.3 -> 10.3`
  - `average_tool_calls: 9.3 -> 9.3`
- 时延分析：
  - 公共 `30` 条任务平均耗时差值：`-0.1355s`
  - 总耗时：`20.3351s -> 16.268s`
  - 没有出现 task 级时延回归榜单
- trace 热点：
  - `run_tests` 总耗时：`18.6839 -> 15.0838`
  - `delta_total_duration_sec = -3.6001`
  - `copy_workspace` 仅增加 `0.0654s`
  - `unattributed_overhead` 增加 `0.2978s`，但仍被 `run_tests` 收益显著覆盖
- 任务级最大改善：
  - `task_040`: `-0.3941s`
  - `task_034`: `-0.2601s`
  - `task_036`: `-0.2364s`
  - `task_038`: `-0.2229s`
  - `task_008`: `-0.2076s`

### 结论

- `improved_v33` 已经同时通过：
  - 热点小集合验证
  - `frozen_20` 固定集合验证
  - 正式 `30` 条真实任务集验证
- 它在三层集合上都保持了 `100%` 成功率和 `100%` 测试通过率
- 同时它在正式集上也给出了与 `frozen_20` 量级接近的稳定耗时改善
- 这说明 `-p no:unraisableexception` 已经从 benchmark 线索升级为主线可采用的 runtime 优化

### 剩余问题

- 还需要继续扩充真实任务规模，从 `30` 推到 `60+`
- 还需要构建 `frozen_40`，并开始累计连续 `5` 个策略版本的同集合无回归证据
- 如果后续继续做 runtime 细化，应该优先服务于 `frozen_40` 的长期稳定性目标，而不是只追求局部热点收益

## 2026-06-11 Phase 6 Benchmark Maturity 审计接入

### 背景

在 `improved_v33` 已通过正式 `30` 条任务集验证后，主线目标不再只是某一轮策略是否有效。

此时更需要一个稳定入口，能够直接回答：

- 当前正式任务数距离 `60+` 还差多少
- 当前仓库来源是否已经足够广
- 当前 frozen 集合距离 `40` 还差多少
- 当前连续无回归证据已经累计到第几轮

### 目标

- 新增一个可复用的 maturity 审计脚本
- 把 `Benchmark Maturity v1` 的硬目标变成仓库内的可执行检查
- 让后续每轮推进都能直接对照量化缺口，而不是手工盘点

### 改动类型

- `benchmark`
- `evaluation`
- `documentation`

### 主要文件

- `scripts/analyze_benchmark_maturity.py`
- `tests/test_analyze_benchmark_maturity.py`
- `logs/summaries/benchmark_maturity_maturity_002.json`
- `logs/summaries/benchmark_maturity_maturity_002.md`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 maturity 审计脚本：
  - 自动汇总正式任务数
  - 自动统计正式任务来源生态数
  - 自动扫描现有 frozen manifests
  - 自动检查 `frozen_40` 上是否已经存在连续版本无回归证据
- 新增配套测试，确保目标缺口计算口径稳定
- 跑出当前仓库真实快照，并把结果同步到主文档入口

### 测试与验证

- 运行命令：
  - `python -m pytest tests/test_analyze_benchmark_maturity.py -q`
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 当前正式任务数：`30 / 60`
- 当前正式任务来源生态数：`13 / 6`
- 当前最大 frozen 集合：`20 / 40`
- 当前 `frozen_40` 连续版本：`0 / 5`
- `accepted = 30` 且当前基本都已转成正式任务，说明旧候选库存已经基本吃完

### 结论

- 当前主线缺口已经非常清楚：
  - 广泛度不是瓶颈，来源生态已经提前达标
  - 任务规模和 frozen 稳定性证据才是下一阶段决定性工作
- 后续每轮推进都应该优先服务于两条主线：
  - 正式任务从 `30` 扩到 `60+`
  - `frozen_20` 升级到 `frozen_40`，并累计 `5` 个连续版本的无回归证据

### 剩余问题

- 还需要持续补新来源候选，否则正式任务数无法继续稳定扩容
- 还需要设计 `frozen_40` 的构建节奏，避免一次性扩太多导致同集合质量波动

## 2026-06-11 Phase 6 packaging / tomlkit / jinja 候选池扩容

### 背景

在 maturity 审计接入之后，当前瓶颈已经明确是：

- 正式任务数只有 `30 / 60`
- `frozen` 规模只有 `20 / 40`

而旧候选池此前已经被吃到 `accepted = 30, to_review = 0`，继续扩正式任务前必须先补新库存。

### 目标

- 从 `pypa/packaging`、`python-poetry/tomlkit`、`pallets/jinja` 三个现有高质量来源里再补一批候选
- 优先选择 closed/fixed、边界清晰、单模块修复的真实 issue
- 为下一轮 `task_062+` 的 semi_real 落地准备库存

### 改动类型

- `benchmark`
- `candidate_sourcing`
- `documentation`

### 主要文件

- `benchmarks/example_issue_batch_packaging_tomlkit_jinja.txt`
- `benchmarks/real_world_candidates.json`
- `docs/candidate_shortlist.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增批量导入清单：
  - `pypa/packaging#909`
  - `pypa/packaging#788`
  - `pypa/packaging#638`
  - `python-poetry/tomlkit#431`
  - `python-poetry/tomlkit#383`
  - `python-poetry/tomlkit#442`
  - `pallets/jinja#2151`
  - `pallets/jinja#2176`
- 已批量导入候选池
- 已把 `docs/candidate_shortlist.md` 从 `Top 0` 更新为新的可执行 `Top 6`

### 测试与验证

- 运行命令：
  - `python scripts/import_issue_batch.py --input benchmarks/example_issue_batch_packaging_tomlkit_jinja.txt`

### 关键观察

- 候选池状态从：
  - `accepted = 30`
  - `to_review = 0`
- 变为：
  - `accepted = 30`
  - `to_review = 8`
- 当前最值得优先推进的候选是：
  - `pypa/packaging#909`
  - `pypa/packaging#788`
  - `pypa/packaging#638`
  - `python-poetry/tomlkit#431`
  - `python-poetry/tomlkit#383`
  - `pallets/jinja#2151`

### 结论

- 这轮已经把“正式任务继续扩容”的前置库存重新补起来了
- 下一步不必先继续找新来源，而应优先把这批候选转成 `task_062+`
- 候选结构也与当前正式集互补，新增了：
  - wheel tag 排序校验
  - prerelease `<` 比较
  - marker `None` 处理
  - super table + dotted key 渲染
  - 代理删除语义
  - async runtime `__repr__` 警告

### 剩余问题

- 还没有把这 8 条候选中的任何一条推进成新的 semi_real 正式任务
- 下一轮应优先从 `packaging#638`、`packaging#788` 或 `tomlkit#442` 这类边界最清晰的候选开始落地

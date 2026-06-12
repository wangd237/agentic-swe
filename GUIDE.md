# 项目实施指南

本文件用于同步记录每个 phase 已实现的功能、当前框架结构，以及你可以如何体验项目。

## 当前进度

| Phase | 名称 | 状态 | 说明 |
| --- | --- | --- | --- |
| Phase 0 | 项目初始化 | 已完成 | 已建立项目骨架、最小 benchmark repo、任务定义与说明文档 |
| Phase 1 | 观察型 Agent | 已完成 | 已实现 list/search/read、单任务观察闭环与 trace 落盘 |
| Phase 2 | 测试闭环 | 已完成 | 已实现 run_tests、失败摘要提取与测试输出落盘 |
| Phase 3 | Patch 闭环 | 已完成 | 已实现 write_file、show_diff、patch 应用与修复前后测试对比 |
| Phase 4 | 批量运行 | 已完成 | 已实现 batch runner、manifest 任务集与批量汇总结果 |
| Phase 5 | 评测系统 | 已完成 | 已实现 metrics、taxonomy、batch eval 与 baseline 报告 |
| Phase 6 | 优化系统 | 进行中 | 已完成 `baseline_v1 -> improved_v55` 多轮策略迭代，正式真实任务扩充到 `52` 条，已建立 `frozen_40 v1`；`v50` 仍是当前稳定基线，`v55` 已继续把正式任务数推高，并已补上 `frozen_40` 首轮同集合验证，功能继续全绿且相对 `v52r2` 更快，但由于固定 `40` 条集合耗时仍高于 `improved_v32` 阈值，因此稳定 `streak` 仍保持 `8` |
| Phase 7 | 可选训练增强 | 未开始 | 将实现轻量训练实验预留能力 |

## Phase 0 已实现内容

### 1. 项目骨架

已经创建以下主目录：

- `app/`
- `benchmarks/`
- `docs/`
- `evals/`
- `logs/`
- `optimization/`
- `scripts/`

其中 `app/` 下已经按规格书拆分为：

- `app/agent`
- `app/tools`
- `app/runtime`
- `app/schemas`

### 2. 占位模块

为了后续 phase 可以稳定迭代，以下文件路径已经创建：

- `app/agent/prompts.py`
- `app/agent/planner.py`
- `app/agent/executor.py`
- `app/agent/policy.py`
- `app/tools/list_files.py`
- `app/tools/search_code.py`
- `app/tools/read_file.py`
- `app/tools/run_tests.py`
- `app/tools/write_file.py`
- `app/tools/show_diff.py`
- `app/runtime/repo_session.py`
- `app/runtime/task_runner.py`
- `app/runtime/logger.py`
- `app/schemas/task_schema.py`
- `app/schemas/trace_schema.py`
- `app/schemas/result_schema.py`
- `scripts/run_single_task.py`

当前这些模块的定位是：

- 先固定工程边界和接口落点
- 提前沉淀最小 schema
- 避免后面每个 phase 都改目录结构

新增的 harness 运行时骨架：

- `app/runtime/harness.py`

它的作用是提前固定：

- run 目录命名规则
- `task.json / result.json / trace.json / patch.diff / summary.md` 的标准位置
- 工作区边界检查

这样后面进入真实执行阶段时，状态落盘方式不会反复变。

### 3. 首个 benchmark repo

已创建最小仓库：

- `benchmarks/repos/sample_repo`

这个仓库里包含：

- 一个带 bug 的实现：`sample_repo/parser.py`
- 一组可运行测试：`tests/test_parser.py`

bug 设计如下：

- 当前 `parse_items([])` 会抛出 `IndexError`
- 预期行为应当是返回空列表

这个设计是故意保留的，方便我们后续在 Phase 2 和 Phase 3 中验证：

- Agent 能否定位相关文件
- Agent 能否理解失败测试
- Agent 能否自动生成并验证修复

### 4. 首条任务定义

已创建：

- `benchmarks/tasks/task_001.json`

这条任务已经包含规格书要求的最小字段：

- `task_id`
- `repo_name`
- `repo_path`
- `issue_title`
- `issue_text`
- `test_command`
- `success_criteria`
- `difficulty`
- `tags`

### 5. 当前可体验入口

已提供脚本：

- `scripts/run_single_task.py`

当前脚本还不是完整 Agent runner，它在 Phase 0 的作用是：

- 验证任务 JSON 结构是否完整
- 检查目标 repo 是否存在
- 输出当前任务的关键信息

## Phase 6 最新补充

### 1. 当前最新落地到 `improved_v55`

这一轮新增的真实 issue 来自：

- `pytest-dev/pytest#14189`

新增产物：

- `benchmarks/tasks/task_104.json`
- `benchmarks/tasks/task_105.json`
- `benchmarks/repos/pytest_caplog_filter_repo/`
- `optimization/policy_versions/improved_v55.json`

当前最关键的新增能力：

- agent 已能修复一种新的 pytest 嵌套过滤上下文问题
- 场景是“嵌套使用相同 filter 时，内层退出会把外层仍在使用的 filter 提前移除”
- 这让正式真实任务总数从 `51` 提升到 `52`

### 2. 这一轮框架结构变化

Phase 6 当前在真实任务扩容侧已经形成稳定模板：

- 先导入 GitHub issue，生成 `real_issue` 草稿
- 再生成 `semi_real` 可运行 repo
- 在 `app/agent/patcher.py` 中补一条专用规则
- 为每轮扩容生成新的 `optimization/policy_versions/improved_vXX.json`
- 最后跑正式集、`frozen_20`、`frozen_40`、maturity 审计并同步文档

最新新增的目录入口：

- `benchmarks/repos/pytest_caplog_filter_repo`

### 3. 你现在可以怎么体验

如果你想直接体验这轮新题，可以按下面顺序：

1. 先看任务定义：
   - `benchmarks/tasks/task_105.json`
2. 再看最小 repo：
   - `benchmarks/repos/pytest_caplog_filter_repo`
3. 先手工验证原始失败：
   - `python -m pytest benchmarks/repos/pytest_caplog_filter_repo/tests/test_logging_utils.py -q`
4. 再跑单任务闭环：
   - `python scripts/run_single_task.py --task benchmarks/tasks/task_105.json --policy optimization/policy_versions/improved_v55.json`
5. 如果你想看全量扩容效果：
   - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v55.json --run-label realissuev55r2`
6. 如果你想看固定 `40` 条集合验证：
   - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v55.json --run-label frozen40v55r1 --compare-against-eval logs/summaries/batch_eval_frozen40v52r2_001.json --compare-label frozen40_step10`

### 4. 当前最准确的状态口径

- 正式真实任务数：`52`
- 当前稳定基线：`improved_v50`
- 当前最新扩容版本：`improved_v55`
- 当前 `frozen_40 streak`：`8`

注意：

- `v55` 这一轮已经完成“扩容成功 + `frozen_40` 首轮功能验证”
- 它在 `frozen_40` 上相对 `v52r2` 的 `average_duration_sec` 从 `0.6824` 回落到 `0.6527`
- 但它还不是新的稳定版本
- 因为相对 `improved_v32` 基线阈值 `0.5514` 仍然偏高，所以当前稳定 `streak` 仍然只能保持在 `8`

## 当前框架结构

```text
app/
  agent/
    prompts.py
    planner.py
    executor.py
    policy.py
  tools/
    list_files.py
    search_code.py
    read_file.py
    run_tests.py
    write_file.py
    show_diff.py
  runtime/
    repo_session.py
    task_runner.py
    logger.py
  schemas/
    task_schema.py
    trace_schema.py
    result_schema.py
benchmarks/
  tasks/
    task_001.json
  repos/
    sample_repo/
docs/
  architecture.md
  benchmark.md
  eval_design.md
  optimization.md
  results.md
  case_studies.md
scripts/
  run_single_task.py
```

## Phase 1 已实现内容

### 1. 三个基础工具已可用

已经实现：

- `app/tools/list_files.py`
- `app/tools/search_code.py`
- `app/tools/read_file.py`

当前能力如下：

- `list_files`
  - 返回仓库相对路径列表
  - 忽略 `.git`、`__pycache__`、`.pytest_cache` 等明显无关目录
- `search_code`
  - 基于文本关键词搜索代码
  - 返回命中文件、行号和文本片段
- `read_file`
  - 读取指定相对路径文件
  - 默认对超长内容做截断，避免观察阶段上下文失控

### 2. schema 已切换到 pydantic

已经升级：

- `app/schemas/task_schema.py`
- `app/schemas/trace_schema.py`
- `app/schemas/result_schema.py`

这样做的价值是：

- 任务输入校验更稳定
- 运行结果结构更统一
- 后面做 eval 和 batch run 更省心

### 3. 观察型 Agent 最小闭环已打通

当前入口：

- `scripts/run_single_task.py`

当前行为：

1. 加载并校验任务
2. 创建 `logs/trajectories/<task_id>/<run_id>/`
3. 复制 benchmark repo 到 `workspace/`
4. 运行 `list_files`
5. 根据 issue 文本生成搜索词并运行 `search_code`
6. 读取候选文件
7. 保存运行产物

### 4. 当前会落哪些文件

每次运行当前都会生成：

- `task.json`
- `result.json`
- `trace.json`
- `patch.diff`
- `summary.md`
- `workspace/`

说明：

- `patch.diff` 在 Phase 1 里会是空文件，因为当前还没有 patch 行为
- 但先把文件位固定下来，可以避免后面阶段改协议

### 5. 当前观察结果长什么样

对 `task_001` 运行后，当前观察型 Agent 能明确推荐：

- `sample_repo/parser.py`
- `tests/test_parser.py`

这满足规格书里对 Phase 1 的核心要求：

- Agent 能给出“应读哪些文件及原因”

## Phase 2 已实现内容

### 1. `run_tests` 已可用

已经实现：

- `app/tools/run_tests.py`

当前能力如下：

- 在目标 `workspace/` 内运行测试命令
- 通过子进程环境关闭 `pytest` 自动插件加载，减少环境噪声
- 返回退出码、stdout、stderr
- 尝试从测试输出中提取失败测试与失败位置
- 区分普通失败和超时

### 2. 单任务 runner 已接入测试闭环

当前入口：

- `scripts/run_single_task.py`

当前行为在 Phase 1 的基础上新增：

1. 运行目标测试命令
2. 把测试结论写入 `result.json`
3. 把完整测试输出写入：
   - `test_stdout.txt`
   - `test_stderr.txt`
4. 在 `trace.json` 中记录 `run_tests` 步骤
5. 在 `summary.md` 中总结失败位置

### 3. 当前测试结论长什么样

对 `task_001` 运行后，当前系统已经能稳定总结：

- 失败测试：`tests/test_parser.py::ParseItemsTests::test_empty_input_returns_empty_list`
- 失败位置：`sample_repo/parser.py:6 (IndexError)`

这满足规格书里对 Phase 2 的核心要求：

- Agent 能读取 issue、搜索代码、运行测试并总结失败现状

## Phase 3 已实现内容

### 1. `write_file` 与 `show_diff` 已可用

已经实现：

- `app/tools/write_file.py`
- `app/tools/show_diff.py`

当前能力如下：

- `write_file`
  - 仅允许写入当前 repo 边界内部
  - 返回结构化写入结果
- `show_diff`
  - 对比原始 repo 与当前 workspace
  - 忽略 `.pytest_cache`、`__pycache__` 等无关文件
  - 输出统一 diff 文本，用于落盘 `patch.diff`

### 2. 最小 patch 生成器已接入

已经实现：

- `app/agent/patcher.py`

当前策略是：

- 优先服务最小闭环
- 对 `task_001` 这种“空输入导致 IndexError”的问题
- 在目标函数里自动加入空输入保护逻辑

这不是最终的通用修复器，但已经满足当前阶段目标：

- 至少 1 条任务自动修复成功

### 3. 单任务 runner 已接入完整 patch 闭环

当前入口：

- `scripts/run_single_task.py`

当前行为在 Phase 2 的基础上新增：

1. 运行修复前测试
2. 生成并应用最小 patch
3. 运行修复后测试
4. 生成 `patch.diff`
5. 将修复前后测试结果写入 `result.json`

### 4. 当前会新增哪些文件

在 Phase 3 中，每次运行除了原有产物，还会稳定生成：

- `pre_test_stdout.txt`
- `pre_test_stderr.txt`
- `post_test_stdout.txt`
- `post_test_stderr.txt`
- 非空的 `patch.diff`

### 5. 当前成功样例

对 `task_001` 运行后，当前系统已经能自动完成：

- pre-test 失败定位到 `sample_repo/parser.py:6 (IndexError)`
- 自动写入空输入保护逻辑
- post-test 通过
- `patch.diff` 仅包含目标修复改动

这满足规格书里对 Phase 3 的核心要求：

- 至少 1 条任务自动修复成功

## Phase 4 已实现内容

### 1. batch runner 已可用

已经实现：

- `scripts/run_batch.py`
- `app/runtime/batch_runner.py`

当前能力如下：

- 支持从 `benchmarks/tasks/` 扫描任务
- 支持优先读取 manifest 指定任务顺序
- 复用现有单任务 patch 闭环
- 为每条任务创建独立 run 目录
- 生成批量汇总 JSON 和 Markdown

### 2. manifest 任务集已接入

已经创建：

- `benchmarks/manifests/dev_tasks.json`

当前用途：

- 作为 Phase 4 的开发任务集
- 固定 batch runner 的任务顺序
- 为后续 baseline / improved 对比打基础

### 3. 第二条开发任务已补充

已经创建：

- `benchmarks/tasks/task_002.json`

当前策略：

- 先扩充开发任务集，保证 batch runner 有多条任务可运行
- 当前两条任务都复用 `sample_repo`，目的是先打通多任务批量运行主线

### 4. 当前批量结果长什么样

当前已生成：

- `logs/summaries/batch_run_001.json`
- `logs/summaries/batch_run_001.md`

在这一轮验证中：

- task_count: `2`
- success_count: `2`
- success_rate: `1.0`

### 5. 当前为什么算完成了 Phase 4

因为现在已经满足规格书里对 Phase 4 的核心要求：

- 能对多个任务连续运行
- 能为每个 task 保存独立 run 目录
- 能输出批量汇总结果

## Phase 5 已实现内容

### 1. metrics 已可用

已经实现：

- `evals/metrics.py`

当前能力如下：

- 计算 `Success Rate`
- 计算 `Test Pass Rate`
- 计算 `Partial Fix Rate`
- 计算平均步数、平均工具调用数、平均耗时、平均修改文件数
- 统计关键文件读取率、测试执行率、重复搜索率、合理结束率

### 2. error taxonomy 已可用

已经实现：

- `evals/error_taxonomy.py`

当前策略：

- 纯规则法
- 成功任务返回空标签
- 失败任务按 `Wrong File Selection / Wrong Root Cause / Patch Incorrect / No Test Execution / Over-editing / Premature Finish / Looping / Repeated Search` 分类

### 3. batch eval 入口已可用

已经实现：

- `evals/batch_eval.py`

当前行为：

1. 读取 `batch_run_001.json`
2. 跟随其中的路径加载每个任务的 `task/result/trace/patch`
3. 计算指标
4. 生成错误分类汇总
5. 输出：
   - `logs/summaries/batch_eval_001.json`
   - `logs/summaries/batch_eval_001.md`

### 4. 当前 baseline 结果

当前已生成：

- `logs/summaries/batch_eval_001.json`
- `logs/summaries/batch_eval_001.md`

本轮 baseline 指标：

- success_rate: `1.0`
- test_pass_rate: `1.0`
- partial_fix_rate: `0.0`
- average_steps: `9.0`
- average_tool_calls: `9.0`
- average_duration_sec: `0.5406`

当前 taxonomy 结果：

- 没有命中任何错误标签

说明：

- 这代表当前开发任务集过于简单
- Phase 5 的评测链路已经打通，但后续要补更多正式任务，才能让错误分类真正有分析价值

## Phase 6 已实现内容

### 1. policy 版本化对比已可用

已经实现：

- `optimization/policy_versions/baseline.json`
- `optimization/policy_versions/improved.json`

当前能力如下：

- 能冻结 baseline policy
- 能切换 improved policy
- 能在相同 report set 上运行真实对比

### 2. report set 已建立

已经创建：

- `benchmarks/manifests/report_tasks.json`
- `benchmarks/tasks/task_003.json`
- `benchmarks/repos/multi_bug_repo`

当前用途：

- 不再只验证“系统能不能跑通”
- 而是验证“优化前后是否真的有差异”

当前 report set 的任务是：

- `task_001`
- `task_003`
- `task_004`

### 3. 自动 compare 报告已可用

已经实现：

- `evals/compare_evals.py`

当前行为：

1. 读取 baseline eval JSON
2. 读取 improved eval JSON
3. 自动计算 metric delta
4. 自动对比 taxonomy 变化
5. 输出追加式 compare JSON 与 Markdown

当前已生成：

- `logs/summaries/batch_compare_phase6_002.json`
- `logs/summaries/batch_compare_phase6_002.md`
- `logs/summaries/batch_compare_phase6v2_step1_001.json`
- `logs/summaries/batch_compare_phase6v2_step2_001.json`

### 4. 当前 Phase 6 的结论

当前第一轮优化结果已经明确说明：

- `success_rate: 0.5 -> 1.0`
- `test_pass_rate: 0.5 -> 1.0`
- `partial_fix_rate: 0.5 -> 0.0`

同时：

- `average_steps` 保持 `9.0`
- `average_tool_calls` 保持 `9.0`

这说明 improved_v1 的收益不是靠增加额外步骤换来的。

### 4.1 当前最新推进状态

截至目前，Phase 6 主线已经继续推进到：

- 正式 `semi_real` 真实任务数：`52`
- 冻结集合：`frozen_40 v1`
- 当前稳定 streak：`8`
- 当前稳定基线策略：`improved_v50`
- 当前最新扩容策略：`improved_v55`

其中最新一轮新增的是：

- 来源 issue：`pytest-dev/pytest#14189`
- draft 任务：`task_104`
- 正式 semi_real 任务：`task_105`
- semi_real repo：`benchmarks/repos/pytest_caplog_filter_repo`

这轮新增能力覆盖的场景是：

- 嵌套使用相同 filter 的过滤上下文时
- 内层退出后不能提前移除外层仍在使用的 filter
- 最终必须保持外层过滤语义直到最外层上下文结束

当前这一轮的关键结论要分开看：

- 功能面：
  - `improved_v55` 已在正式 `52` 条任务集与 `frozen_20` 上保持 `100%` 成功率和 `100%` 测试通过率
- 性能面：
  - `v55` 的正式集复跑口径对比 `v54` 是 `average_duration_sec = 0.6544 -> 0.6551`
  - `v55` 的 `frozen_20` 复跑口径对比 `v54` 是 `average_duration_sec = 0.6697 -> 0.6835`
  - 正式集公共 `51` 条任务平均耗时增量首轮为 `+0.0251s`，复跑后整体收敛到近乎持平
  - `frozen_20` 公共 `20` 条任务平均耗时增量首轮为 `+0.0345s`，复跑后回落到 `+0.0138s`

因此当前更可信的判断是：

- `v55` 已经成功把正式任务数从 `51` 扩到 `52`
- 它在复跑口径下把相对 `v54` 的性能回升压缩到了很小范围
- 但这轮还没有补 `frozen_40` 的同集合验证
- 因此这轮仍应记为“扩容成功、性能恢复中”，而不是新的稳定 streak 版本

### 5. 当前新增的 improved_v2 结论

本轮继续扩充 report set 后，新的结果是：

- `baseline_v1`
  - success_rate: `0.3333`
- `improved_v1`
  - success_rate: `0.6667`
- `improved_v2`
  - success_rate: `1.0`

新增差异点来自：

- `task_004`
- 缺陷模式：首元素 `None`
- 代表能力：不仅处理中间 `None`，还要在归一化前做全量清洗

### 6. 真实 issue 接入前的基础设施

当前已经补充：

- `Task.source_type`
- `benchmarks/real_world_candidates.json`
- `scripts/validate_tasks.py`
- `scripts/import_github_issue.py`
- `scripts/import_issue_batch.py`
- `scripts/analyze_duration_regressions.py`
- `scripts/analyze_trace_hotspots.py`
- `scripts/analyze_task_history.py`
- `scripts/analyze_task_history_cohort.py`
- `scripts/benchmark_run_tests_modes.py`
- `scripts/analyze_run_tests_mode_cohort.py`
- `scripts/benchmark_pytest_plugin_variants.py`
- `scripts/analyze_pytest_plugin_variant_cohort.py`
- `scripts/analyze_pytest_importtime_groups.py`

它们的作用是：

- 让任务来源显式区分 `synthetic / semi_real / real_issue`
- 先维护一份 GitHub 真实 issue 候选清单
- 在真实任务真正接入前，先把格式与校验入口固定下来
- 在出现性能回升时，既能看 batch 公共任务整体变化，也能继续下钻到单任务历史样本
- 当前已成功导入十五条候选：`psf/requests#6432`、`psf/requests#7234`、`Textualize/rich#4090`、`pytest-dev/pytest#14329`、`Textualize/rich#3877`、`pydantic/pydantic#9582`、`pallets/click#3111`、`dateutil/dateutil#1442`、`dateutil/dateutil#1432`、`python-attrs/attrs#1479`、`pallets/jinja#2069`、`pallets/jinja#2118`、`python-poetry/tomlkit#494`、`python-poetry/tomlkit#495`、`pypa/packaging#873`

最新又继续补进：

- `pallets/click#3125`
- `pallets/click#3571`

其中：

- `click#3125` 已落地为 `task_095`
- `click#3571` 已落地为 `task_097`
- `jinja#2108` 已落地为 `task_099`

### 7. 当前新增的性能诊断链

目前 Phase 6 的性能定位已经形成七层递进：

1. `scripts/analyze_duration_regressions.py`
   - 看相邻两轮 batch run 的公共任务总体时延变化
2. `scripts/analyze_trace_hotspots.py`
   - 看热点主要堆在哪个工具上
3. `scripts/analyze_task_history.py`
   - 看单个热点任务在不同策略版本和多次运行里的历史分布
4. `scripts/analyze_task_history_cohort.py`
   - 把多个热点任务横向汇总，判断回升是否具有群体一致性
5. `scripts/benchmark_run_tests_modes.py` + `scripts/analyze_run_tests_mode_cohort.py`
   - 直接比较 source repo、persistent workspace、fresh workspace 三种运行模式下的 `run_tests` 开销
6. `scripts/benchmark_pytest_plugin_variants.py` + `scripts/analyze_pytest_plugin_variant_cohort.py`
   - 直接比较默认插件链、轻量终端插件链和最小安全插件链
   - 判断 pytest 默认插件链里哪些部分值得继续怀疑，哪些部分已经可以先排除
7. `scripts/analyze_pytest_importtime_groups.py`
   - 复用已有 importtime 基准结果
   - 把新增模块再按 `pytest_optional_plugins / windows_ctypes / xml_stack / terminal_chain / debugging_chain` 等来源分组
   - 把“哪些模块变多了”推进到“哪一类链路更值得继续切分”

你可以这样体验：

- 看扩容集的总体回升：
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev31_001.json --improved-batch-summary logs/summaries/batch_run_realissuev32_001.json --run-label realissuev32`
- 看热点工具：
  - `python scripts/analyze_trace_hotspots.py --baseline-batch-summary logs/summaries/batch_run_realissuev31_001.json --improved-batch-summary logs/summaries/batch_run_realissuev32_001.json --run-label realissuev32`
- 看热点任务 `task_040` 的历史分布：
  - `python scripts/analyze_task_history.py --task-dir logs/trajectories/task_040 --output-dir logs/summaries`
- 看热点任务集合 `task_034 / task_036 / task_038 / task_040` 的横向汇总：
  - `python scripts/analyze_task_history_cohort.py --task-id task_034 --task-id task_036 --task-id task_038 --task-id task_040 --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`
- 对单个热点任务做 `run_tests` 模式基准：
  - `python scripts/benchmark_run_tests_modes.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
- 汇总多个热点任务的 `run_tests` 模式基准：
  - `python scripts/analyze_run_tests_mode_cohort.py --benchmark-summary logs/summaries/run_tests_modes_task034v32_001.json --benchmark-summary logs/summaries/run_tests_modes_task036v32_001.json --benchmark-summary logs/summaries/run_tests_modes_task038v32_001.json --benchmark-summary logs/summaries/run_tests_modes_task040v32_001.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`
- 对单个热点任务做 `pytest` 分阶段基准：
  - `python scripts/benchmark_pytest_phases.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
- 汇总多个热点任务的 `pytest` 分阶段基准：
  - `python scripts/analyze_pytest_phase_cohort.py --benchmark-summary logs/summaries/pytest_phases_task034v32_001.json --benchmark-summary logs/summaries/pytest_phases_task036v32_001.json --benchmark-summary logs/summaries/pytest_phases_task038v32_001.json --benchmark-summary logs/summaries/pytest_phases_task040v32_001.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`
- 对单个热点任务做 `pytest importtime` 基准：
  - `python scripts/benchmark_pytest_importtime.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
- 汇总多个热点任务的 `pytest importtime` 基准：
  - `python scripts/analyze_pytest_importtime_cohort.py --benchmark-summary logs/summaries/pytest_importtime_task034v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task036v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task038v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task040v32_002.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`
- 对单个热点任务做 `pytest` 插件变体基准：
  - `python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_040.json --repetitions 3 --benchmark-label task040v32 --output-dir logs/summaries`
- 汇总多个热点任务的 `pytest` 插件变体基准：
  - `python scripts/analyze_pytest_plugin_variant_cohort.py --benchmark-summary logs/summaries/pytest_plugin_variants_task034v32_001.json --benchmark-summary logs/summaries/pytest_plugin_variants_task036v32_001.json --benchmark-summary logs/summaries/pytest_plugin_variants_task038v32_001.json --benchmark-summary logs/summaries/pytest_plugin_variants_task040v32_001.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`
- 对多个热点任务做 `pytest importtime` 分组分析：
  - `python scripts/analyze_pytest_importtime_groups.py --benchmark-summary logs/summaries/pytest_importtime_task034v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task036v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task038v32_002.json --benchmark-summary logs/summaries/pytest_importtime_task040v32_002.json --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

当前这层新增能力的意义是：

- 不再只能看到“v32 变慢了”
- 还能判断它是公共任务系统性回升，还是少数任务高方差抖动
- 还能继续区分 `run_tests` 里的总耗时、子进程耗时和摘要提取耗时
- 还能进一步确认“热点任务群”是否都在同一执行链上一起变慢
- 还能直接验证“工作副本复制”是不是主因，而不是只做推测

当前最新结论：

- `run_tests` 已新增更细的诊断字段：
  - `resolve_repo_path_duration_sec`
  - `env_setup_duration_sec`
  - `pre_execution_duration_sec`
  - `command_execution_duration_sec`
  - `summary_extraction_duration_sec`
  - `subprocess_duration_sec`
- `task_runner` 现在会把 `copy_workspace` 作为独立 trace step 写入，并记录 `workspace_copy_duration_sec`
- 热点任务集合 `task_034 / task_036 / task_038 / task_040` 的模式基准汇总表明：
  - `average_fresh_copy_duration_sec = 0.0023`
  - `average_fresh_combined_delta_sec = -0.0068`
  - `average_persistent_combined_delta_sec = -0.0059`
- 这说明 workspace copy 的额外成本只有毫秒级，且整体并不稳定更慢，因此它不是最近 `improved_v32` 系统性回升的主因
- `pytest` 分阶段 cohort 基准进一步表明：
  - `average_pytest_startup_over_python_sec = 0.1322`
  - `average_collect_over_pytest_startup_sec = 0.0797`
  - `average_full_over_collect_sec = 0.0159`
  - `average_collect_first_minus_repeated_sec = 0.0132`
- 这说明热点任务的主要开销堆在 `pytest` 启动和 collection，真正 full run 相对 collect-only 只多了十几毫秒量级
- `pytest importtime` cohort 基准又进一步表明：
  - `average_collect_wall_delta_sec = 0.0697`
  - `average_collect_import_self_delta_us = 20898`
  - `average_collect_unique_module_delta = 37`
  - 高频新增模块包括：`_ctypes`、`pyexpat`、`xml.etree.ElementTree`、`_pytest.skipping`、`ctypes.wintypes`
- 这说明 collection 的额外耗时里，有一块可以直接归因到稳定新增的 import 链，而不是纯粹随机抖动
- `pytest` 插件变体 cohort 基准进一步表明：
  - `_001` 样本曾因为命令拼接 bug 失真
  - 推进到 `_004` 样本后又进一步表明：
    - `unraisableexception_only`：`avg wall delta = -0.0282`
    - `debugging_only`：`avg wall delta = -0.0104`
    - `threadexception_only`：`avg wall delta = 0.0059`
    - `debug_exception_plugins`：`avg wall delta = -0.0346`
    - `minimal_safe_plugins`：`avg wall delta = -0.0496`
    - `minimal_safe_plugins`：`avg import delta(us) = -17930`
    - `minimal_safe_plugins`：`avg module delta = -22`
- 这说明当前最强的单插件信号是 `-p no:unraisableexception`
- `pytest importtime` 分组分析进一步表明：
  - `pytest_optional_plugins`：`avg self(us) = 6181`
  - `windows_ctypes`：`avg self(us) = 5103`
  - `xml_stack`：`avg self(us) = 4026`
  - `terminal_chain`：`avg self(us) = 3653`
  - `other` 已压到 `0`
- 这说明新增 import 开销已经几乎都能归到可解释链路，后续不应再停留在“大概是 collection 变慢了”的层面
- runtime 侧也已补齐 policy 注入能力：
  - 可以在策略 JSON 里配置 `pytest_additional_flags`
  - 当前 `improved_v33` 已先验证 `-p no:unraisableexception`
- `improved_v33` 已进一步在 `frozen_20` 上验证：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6774 -> 0.5379`
  - `run_tests` 总耗时下降：`-2.5941s`
- `improved_v33` 已进一步在正式 `30` 条任务集上验证：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6778 -> 0.5423`
  - `run_tests` 总耗时下降：`-3.6001s`
- 这说明 `v33` 已经是当前主线里的强候选基线，而不只是局部热点优化
- 当前还新增了一条 maturity 审计链：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`
  - 它会自动汇总正式任务数、来源生态数、frozen 集合规模和 `frozen_40` 连续无回归版本数
  - 当前最新审计结果是：
    - 正式任务数：`34 / 60`
    - 来源生态数：`13 / 6`
    - frozen 集合：`20 / 40`
    - `frozen_40` 连续版本：`0 / 5`
- 当前已经继续新增 `packaging#638` 派生的 `task_063`，并落地 `improved_v34`
  - 新增 repo：`benchmarks/repos/packaging_marker_repo`
  - 新增策略：`optimization/policy_versions/improved_v34.json`
  - 新规则覆盖 `Marker.evaluate(extra=None)` 不应因 `None.lower()` 抛错
  - 正式 `31` 条任务集验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5423 -> 0.5391`
  - `frozen_20` 同集合验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5379 -> 0.5368`
- 这说明当前主线已经不只是维持 `v33`，而是成功把正式任务集推进到 `31` 条，同时保持功能与时延都无回归
- 当前已经继续新增 `packaging#788` 派生的 `task_065`，并落地 `improved_v35`
  - 新增 repo：`benchmarks/repos/packaging_prerelease_repo`
  - 新增策略：`optimization/policy_versions/improved_v35.json`
  - 新规则覆盖 `< prerelease` 场景下更早 prerelease 不应被提前拒绝
  - 正式 `32` 条任务集验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5391 -> 0.535`
  - `frozen_20` 同集合验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5368 -> 0.5402`
- 这说明当前主线已经成功把正式任务集推进到 `32` 条；`frozen_20` 上仅有 `+0.0034s` 的轻微时延波动，但功能仍然完全无回归
- 当前已经继续新增 `packaging#909` 派生的 `task_067`，并落地 `improved_v36`
  - 新增 repo：`benchmarks/repos/packaging_tag_order_repo`
  - 新增策略：`optimization/policy_versions/improved_v36.json`
  - 新规则覆盖 wheel compressed tag set 未排序时应直接拒绝
  - 正式 `33` 条任务集验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.535 -> 0.5312`
  - `frozen_20` 同集合验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5402 -> 0.5386`
- 这说明当前主线已经成功把正式任务集推进到 `33` 条，并且这次扩容在正式集和固定集上都继续带来了小幅时延改善
- 当前已经继续新增 `tomlkit#442` 派生的 `task_069`，并落地 `improved_v37`
  - 新增 repo：`benchmarks/repos/tomlkit_boolean_repo`
  - 新增策略：`optimization/policy_versions/improved_v37.json`
  - 新规则覆盖 `boolean(True)` 被错误序列化为 `false` 的场景
  - 正式 `34` 条任务集验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5312 -> 0.6038`
  - `frozen_20` 同集合验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5386 -> 0.5687`
- 这说明当前主线已经成功把正式任务集推进到 `34` 条，但这轮扩容伴随时延回升，后续需要继续做性能回收
- 当前已经继续新增 `tomlkit#383` 派生的 `task_071`，并落地 `improved_v38`
  - 新增 repo：`benchmarks/repos/tomlkit_proxy_repo`
  - 新增策略：`optimization/policy_versions/improved_v38.json`
  - 新规则覆盖 `OutOfOrderTableProxy.pop()` 返回值正确但未同步删除底层键的场景
  - 正式 `35` 条任务集验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.6038 -> 0.553`
  - `frozen_20` 同集合验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5687 -> 0.5427`
- 这说明当前主线已经成功把正式任务集推进到 `35` 条，而且这一轮还把前一版的时延回升重新拉回来了
- 当前已经继续新增 `tomlkit#431` 派生的 `task_073`，并落地 `improved_v39`
  - 新增 repo：`benchmarks/repos/tomlkit_super_table_repo`
  - 新增策略：`optimization/policy_versions/improved_v39.json`
  - 新规则覆盖 super table 下新增 dotted key 时父级前缀丢失的场景
  - 正式 `36` 条任务集验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.553 -> 0.5453`
  - `frozen_20` 同集合验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5427 -> 0.5443`
- 这说明当前主线已经成功把正式任务集推进到 `36` 条，并且这轮扩容在正式集上继续带来了小幅时延改善
- 当前已经继续新增 `jinja#2151` 派生的 `task_075`，并落地 `improved_v40`
  - 新增 repo：`benchmarks/repos/jinja_async_repr_repo`
  - 新增策略：`optimization/policy_versions/improved_v40.json`
  - 新规则覆盖 AsyncLoopContext.__repr__ 暴露协程对象并触发未 awaited 警告的场景
  - 正式 `37` 条任务集验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5453 -> 0.5717`
  - `frozen_20` 同集合验证结果：
    - `success_rate: 1.0 -> 1.0`
    - `test_pass_rate: 1.0 -> 1.0`
    - `average_duration_sec: 0.5443 -> 0.5682`
- 这说明当前主线已经成功把正式任务集推进到 `37` 条，但这轮扩容伴随了时延回升，后续需要继续做性能回收
- 这说明当前真正缺的不是来源多样性，而是规模和稳定性证据
- 下一步应该把重点切到两条主线：
  - 继续扩真实 issue 正式任务，朝 `60+` 推进
  - 构建 `frozen_40`，并累计连续 `5` 个策略版本的固定集合无回归证据
- 最新又补了一层环境级校验：
  - `logs/summaries/batch_compare_frozen40_envcheck_v50_001.json`
  - 它直接比较了同一策略 `improved_v50` 在当前环境下的两次 `frozen_40` 结果
  - `average_duration_sec` 从 `0.5410` 回升到 `0.6616`
- 这说明当前 `v51` 看到的耗时回升，并不充分支持“是新规则让系统变慢了”这个结论
- 更可信的解释是当前运行环境或测试执行链路出现了整体漂移
- 因此后续应继续把“扩容成功”和“性能门控是否通过”分开记录

### 7. 真实 issue 导入入口已可用

当前已经新增：

- `scripts/import_github_issue.py`

当前能力如下：

- 读取 GitHub issue 元数据
- 追加到 `benchmarks/real_world_candidates.json`
- 可选生成 `real_issue` task 草稿
- 保留已有候选状态并按时间追加备注
- 把“候选收集”和“任务补全”拆成两步，避免一次性要求把所有字段都补齐
- 支持从文本或 JSON 批量导入多个 issue，便于后续持续扩新来源

### 8. 真实 issue 批量导入入口已可用

当前已经新增：

- `scripts/import_issue_batch.py`

当前能力如下：

- 从文本或 JSON 文件批量读取多个 `repo + issue`
- 逐条复用单 issue 导入逻辑
- 支持批量导入时直接生成 `real_issue` 草稿
- 保持候选备注继续采用追加式记录

### 9. 性能诊断入口已可用

当前已经新增：

- `scripts/analyze_duration_regressions.py`
- `scripts/analyze_trace_hotspots.py`
- `scripts/analyze_task_history.py`
- `scripts/analyze_task_history_cohort.py`

当前能力如下：

- 先在 `result.json` 层面对比两轮 batch run 的任务总耗时差异
- 再在 `trace.json` 层面继续下钻到工具级热点
- 再按单任务历史 run 聚合策略版本差异和波动范围
- 再按热点任务集合做横向汇总，判断群体一致性
- 新产生的 trace 已开始显式记录每一步 `duration_sec`
- 旧 trace 没有显式耗时时，也可以回退到时间戳差值估算
- 旧 trace 没有 `subprocess_duration_sec` 等细粒度字段时，会明确标记为“未观测”

### 10. 真实 issue 草稿到 semi_real 的脚手架入口已可用

当前已经新增：

- `scripts/scaffold_semi_real_task.py`

当前能力如下：

- 从 `real_issue` 草稿生成 `semi_real` 任务骨架
- 自动创建本地 repo 目录、包文件、模块文件、测试文件和 README
- 自动维护候选状态：
  - `drafted`
  - `scaffolded`
  - `accepted`
- 在 `--ready` 模式下自动把任务追加到 `benchmarks/manifests/real_issue_tasks.json`

### 11. 真实 issue 已推进到可运行 semi_real 任务

当前已经完成：

- `task_005`
  - 类型：`real_issue`
  - 状态：草稿，仍需人工补齐本地 repo_path 与测试命令
- `task_006`
  - 类型：`semi_real`
  - 来源：`psf/requests#6432`
  - 状态：已可运行
- `task_007`
  - 类型：`real_issue`
  - 状态：草稿，仍需人工补齐本地 repo_path 与测试命令
- `task_008`
  - 类型：`semi_real`
  - 来源：`psf/requests#7234`
  - 状态：已可运行
- `task_009`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `Textualize/rich#4090` 的真实入口记录
- `task_010`
  - 类型：`semi_real`
  - 来源：`Textualize/rich#4090`
  - 状态：已可运行
- `task_011`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `pytest-dev/pytest#14329` 的真实入口记录
- `task_012`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `Textualize/rich#3877` 的真实入口记录
- `task_013`
  - 类型：`semi_real`
  - 来源：`Textualize/rich#3877`
  - 状态：已可运行
- `task_014`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `pydantic/pydantic#9582` 的真实入口记录
- `task_015`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `pallets/click#3111` 的真实入口记录
- `task_016`
  - 类型：`semi_real`
  - 来源：`pallets/click#3111`
  - 状态：已可运行
- `task_018`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `dateutil/dateutil#1432` 的真实入口记录
- `task_017`
  - 类型：`semi_real`
  - 来源：`pytest-dev/pytest#14329`
  - 状态：已可运行
- `task_019`
  - 类型：`semi_real`
  - 来源：`dateutil/dateutil#1432`
  - 状态：已可运行
- `task_021`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `dateutil/dateutil#1442` 的真实入口记录
- `task_022`
  - 类型：`semi_real`
  - 来源：`dateutil/dateutil#1442`
  - 状态：已可运行
- `task_023`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `pallets/jinja#2069` 的真实入口记录
- `task_024`
  - 类型：`semi_real`
  - 来源：`pallets/jinja#2069`
  - 状态：已可运行
- `task_025`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `pallets/jinja#2118` 的真实入口记录
- `task_026`
  - 类型：`semi_real`
  - 来源：`pallets/jinja#2118`
  - 状态：已可运行
- `task_027`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `python-poetry/tomlkit#494` 的真实入口记录
- `task_028`
  - 类型：`semi_real`
  - 来源：`python-poetry/tomlkit#494`
  - 状态：已可运行
- `task_029`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `python-poetry/tomlkit#495` 的真实入口记录
- `task_030`
  - 类型：`semi_real`
  - 来源：`python-poetry/tomlkit#495`
  - 状态：已可运行
- `task_031`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `pypa/packaging#873` 的真实入口记录
- `task_032`
  - 类型：`semi_real`
  - 来源：`pypa/packaging#873`
  - 状态：已可运行
- `task_033`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `python-jsonschema/jsonschema#1157` 的真实入口记录
- `task_034`
  - 类型：`semi_real`
  - 来源：`python-jsonschema/jsonschema#1157`
  - 状态：已可运行
- `task_035`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `python-jsonschema/jsonschema#1121` 的真实入口记录
- `task_036`
  - 类型：`semi_real`
  - 来源：`python-jsonschema/jsonschema#1121`
  - 状态：已可运行
- `task_037`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `python-jsonschema/jsonschema#1159` 的真实入口记录
- `task_038`
  - 类型：`semi_real`
  - 来源：`python-jsonschema/jsonschema#1159`
  - 状态：已可运行
- `task_039`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `pypa/packaging#845` 的真实入口记录
- `task_040`
  - 类型：`semi_real`
  - 来源：`pypa/packaging#845`
  - 状态：已可运行
- `task_041`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `pallets/click#2402` 的真实入口记录
- `task_042`
  - 类型：`semi_real`
  - 来源：`pallets/click#2402`
  - 状态：已可运行
- `task_043`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `dateutil/dateutil#384` 的真实入口记录
- `task_044`
  - 类型：`semi_real`
  - 来源：`dateutil/dateutil#384`
  - 状态：已可运行
- `task_045`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `python-jsonschema/jsonschema#1162` 的真实入口记录
- `task_046`
  - 类型：`semi_real`
  - 来源：`python-jsonschema/jsonschema#1162`
  - 状态：已可运行
- `task_047`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `pypa/packaging#810` 的真实入口记录
- `task_048`
  - 类型：`semi_real`
  - 来源：`pypa/packaging#810`
  - 状态：已可运行
- `task_049`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `dateutil/dateutil#1191` 的真实入口记录
- `task_050`
  - 类型：`semi_real`
  - 来源：`dateutil/dateutil#1191`
  - 状态：已可运行
- `task_051`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `python-jsonschema/jsonschema#1328` 的真实入口记录
- `task_052`
  - 类型：`semi_real`
  - 来源：`python-jsonschema/jsonschema#1328`
  - 状态：已可运行
- `task_053`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `python-jsonschema/jsonschema#1125` 的真实入口记录
- `task_054`
  - 类型：`semi_real`
  - 来源：`python-jsonschema/jsonschema#1125`
  - 状态：已可运行
- `task_055`
  - 类型：`real_issue`
  - 状态：草稿，已作为 `simonw/sqlite-utils#159` 的真实入口记录
- `task_056`
  - 类型：`semi_real`
  - 来源：`simonw/sqlite-utils#159`
  - 状态：已可运行
- `task_057`
  - 类型：`semi_real`
  - 来源：`pydantic/pydantic#9582`
  - 状态：已可运行
- `optimization/policy_versions/improved_v3.json`
  - 作用：新增 urllib3 依赖上界放宽修复能力
- `optimization/policy_versions/improved_v4.json`
  - 作用：新增 quoted charset 去引号修复能力
- `optimization/policy_versions/improved_v5.json`
  - 作用：新增 ANSI 文本 CRLF 行尾拆分修复能力
- `optimization/policy_versions/improved_v6.json`
  - 作用：新增 RichHandler 时区偏移保留修复能力
- `optimization/policy_versions/improved_v7.json`
  - 作用：新增负向 boolean flag 默认值修复能力
- `optimization/policy_versions/improved_v8.json`
  - 作用：新增最近 marker 覆盖优先修复能力
- `optimization/policy_versions/improved_v9.json`
  - 作用：新增 tzstr 在 UTC/GMT 无 offset 场景下回落为零偏移的修复能力
- `optimization/policy_versions/improved_v10.json`
  - 作用：新增 9 位时间串按 HHMMSSmmm 解析的修复能力
- `optimization/policy_versions/improved_v11.json`
  - 作用：新增模板分析中所有分支都已赋值的变量不再被判定为 undeclared 的修复能力
- `optimization/policy_versions/improved_v12.json`
  - 作用：新增 Jinja slice filter 在整除场景下不应错误补入 `fill_with` 的修复能力
- `optimization/policy_versions/improved_v13.json`
  - 作用：新增 toml 数组下一行逗号风格下 append 后不应生成双逗号的修复能力
- `optimization/policy_versions/improved_v14.json`
  - 作用：新增 dotted inline table 追加新键值对时补上合法分隔、避免输出损坏的修复能力
- `optimization/policy_versions/improved_v15.json`
  - 作用：新增 wheel 文件名中未 normalized 版本号应被拒绝的修复能力
- `optimization/policy_versions/improved_v16.json`
  - 作用：新增 mixed-type extras 排序失败时回落到原顺序渲染、避免 `TypeError` 的修复能力
- `optimization/policy_versions/improved_v17.json`
  - 作用：新增 hostname 格式检查在空字符串场景下回落为普通校验失败的修复能力
- `optimization/policy_versions/improved_v18.json`
  - 作用：新增 integer-valued `multipleOf` 浮点数按数学整数处理的修复能力
- `optimization/policy_versions/improved_v19.json`
  - 作用：新增 packaging `Requirement.__str__` 在复合 marker 中统一规范化 extra 名称的修复能力
- `optimization/policy_versions/improved_v20.json`
  - 作用：新增 click alias group 在 `cmd is None` 场景下保持普通返回语义的修复能力
- `optimization/policy_versions/improved_v21.json`
  - 作用：新增 `MM.YYYY` 在点号分隔场景下按月年格式解析的修复能力
- `optimization/policy_versions/improved_v22.json`
  - 作用：新增 single-label hostname 应通过 hostname 格式校验的修复能力
- `optimization/policy_versions/improved_v23.json`
  - 作用：新增 `Specifier >` 在 `dev+local` 场景下按 public version 比较的修复能力
- `optimization/policy_versions/improved_v24.json`
  - 作用：新增年份前紧贴逗号时仍能识别 year token 的修复能力
- `optimization/policy_versions/improved_v25.json`
  - 作用：新增 ErrorTree 访问缺失索引时保持只读、不污染内部 children 的修复能力
- `optimization/policy_versions/improved_v26.json`
  - 作用：新增 `extend()` 保留原始 `applicable_validators`、避免 legacy `$ref` 语义回归的修复能力
- `optimization/policy_versions/improved_v27.json`
  - 作用：新增 `delete_where()` 删除后自动提交事务、保证多连接可见性的修复能力
- `optimization/policy_versions/improved_v28.json`
  - 作用：新增父子 `model_validator` 在继承链上追加执行、避免父类校验被覆盖的修复能力
- `optimization/policy_versions/improved_v29.json`
  - 作用：新增 `field_transformer` 运行前提前暴露默认 alias 的修复能力
- `optimization/policy_versions/improved_v30.json`
  - 作用：新增数值列转换时把空字符串回落为 `None` 的修复能力
- `optimization/policy_versions/improved_v31.json`
  - 作用：新增 extract 维表提取时跳过 `None` 的修复能力
- `optimization/policy_versions/improved_v32.json`
  - 作用：新增 tuple 格式化分支继承 profile 布局策略的修复能力

当前这条链路已经从“真实 issue 候选”推进到“可运行任务 + 可比较策略结果”。

## 你现在可以怎么体验

### 方式 1：运行 Patch 闭环

在仓库根目录运行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_001.json
```

你会看到：

- 任务 ID
- run_id
- 最终状态
- 推荐阅读文件
- 修复前后测试结果会被写入结果文件
- patch.diff 会被落到 run 目录
- trace / result / summary 的落盘路径

### 方式 2：直接运行 benchmark 测试

在仓库根目录执行：

```bash
cd benchmarks/repos/sample_repo
python -m pytest tests/test_parser.py -q
```

你会看到：

- 当前测试是失败的
- 失败点会落在空输入处理逻辑

这正是后续 Agent 要自动修复的问题。

### 方式 3：运行批量任务

在仓库根目录执行：

```bash
python scripts/run_batch.py
```

你会看到：

- batch_run_id
- task_count
- success_count
- success_rate
- 批量汇总文件路径

### 方式 4：运行 baseline 评测

在仓库根目录执行：

```bash
python -m evals.batch_eval --batch-summary logs/summaries/batch_run_001.json --output-dir logs/summaries
```

你会看到：

- eval_id
- source_batch_run_id
- success_rate
- test_pass_rate
- 评测报告文件路径

### 方式 5：运行 baseline vs improved 自动对比

在仓库根目录执行：

```bash
python -m evals.compare_evals --baseline-eval logs/summaries/batch_eval_baseline_001.json --improved-eval logs/summaries/batch_eval_improved_001.json --output-dir logs/summaries --run-label phase6
```

你会看到：

- compare_id
- baseline_eval_id
- improved_eval_id
- success_rate_delta
- test_pass_rate_delta
- 对比报告文件路径

### 方式 6：校验任务与真实 issue 候选清单

在仓库根目录执行：

```bash
python scripts/validate_tasks.py
```

你会看到：

- 任务 schema 是否通过
- `source_type` 是否合法
- 真实 issue 候选清单结构是否通过

### 方式 7：导入一个真实 GitHub issue 候选

在仓库根目录执行：

```bash
python scripts/import_github_issue.py --repo psf/requests --issue 10000
```

你会看到：

- candidate_id
- issue_title
- issue_url
- 更新后的 candidate_file 路径

如果再加 `--draft-task`，还会额外生成一个 `real_issue` task 草稿文件。

### 方式 8：批量导入一组真实 GitHub issue 候选

在仓库根目录执行：

```bash
python scripts/import_issue_batch.py --input benchmarks/example_issue_batch.txt
```

你会看到：

- 本次批量导入的总数
- `created_count`
- `updated_count`
- `drafted_count`
- 每条 issue 对应的 `candidate_id`

如果你加上 `--draft-task`：

- 每条 issue 会在导入后继续生成一个 `real_issue` 草稿
- 候选状态会自动追加草稿备注

### 方式 9：分析两轮 batch run 的时延回归

在仓库根目录执行：

```bash
python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev31_001.json --improved-batch-summary logs/summaries/batch_run_realissuev32_001.json --run-label realissuev32
```

你会看到：

- 公共任务平均耗时变化
- top regressions / top improvements
- 是否存在新增或移除的任务

### 方式 10：分析两轮 batch run 的 trace 热点

在仓库根目录执行：

```bash
python scripts/analyze_trace_hotspots.py --baseline-batch-summary logs/summaries/batch_run_realissuev31_001.json --improved-batch-summary logs/summaries/batch_run_realissuev32_001.json --run-label realissuev32
```

你会看到：

- 哪些任务最慢
- 每个慢任务里哪个工具是主要热点
- 工具级汇总里 `run_tests / search_code / show_diff` 等动作的总耗时变化

### 方式 11：从 real_issue 草稿生成 semi_real 脚手架

在仓库根目录执行：

```bash
python scripts/scaffold_semi_real_task.py --draft-task benchmarks/tasks/task_007.json --semi-repo-name requests_encoding_repo --module-path requests_encoding_repo/utils.py --test-path tests/test_utils.py --ready --success-criteria "Quoted 和 unquoted charset 都能正确解析，且测试全部通过。" --expected-failure-test "HeaderEncodingTests.test_double_quoted_charset_is_detected" --tag header-parsing --tag charset
```

你会看到：

- 新生成的 `semi_real_task` 路径
- scaffold 目标 repo 路径
- 模块文件与测试文件路径
- 当前是否以 `ready` 模式生成

如果不加 `--ready`：

- 候选状态会更新为 `scaffolded`
- 任务 metadata 会带 `draft_status`
- 适合先做人工缩题和最小复现

### 方式 12：运行首条真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_006.json --policy optimization/policy_versions/improved_v3.json
```

你会看到：

- `task_006` 被成功修复
- 修改文件是 `setup.py`
- patch 原因是放宽 urllib3 依赖上界

### 方式 13：运行第 2 条真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_008.json --policy optimization/policy_versions/improved_v4.json
```

你会看到：

- `task_008` 被成功修复
- 修改文件是 `requests_encoding_repo/utils.py`
- patch 原因是给 quoted charset 增加去引号逻辑

### 方式 11：运行第 3 条真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_010.json --policy optimization/policy_versions/improved_v5.json
```

你会看到：

- `task_010` 被成功修复
- 修改文件是 `rich_ansi_repo/ansi.py`
- patch 原因是把 ANSI 文本拆分逻辑改为兼容 CRLF 的流程

### 方式 12：运行第 4 条真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_013.json --policy optimization/policy_versions/improved_v6.json
```

你会看到：

- `task_013` 被成功修复
- 修改文件是 `rich_handler_repo/logging.py`
- patch 原因是让 RichHandler 的时间格式化显式保留时区信息

### 方式 13：运行第 5 条真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_016.json --policy optimization/policy_versions/improved_v7.json
```

你会看到：

- `task_016` 被成功修复
- 修改文件是 `click_flag_repo/core.py`
- patch 原因是修正负向 boolean flag 的 `default=True` 默认行为

### 方式 14：运行第 6 条真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_017.json --policy optimization/policy_versions/improved_v8.json
```

你会看到：

- `task_017` 被成功修复
- 修改文件是 `pytest_marker_repo/markers.py`
- patch 原因是把 marker 查找顺序改为优先返回继承链中最近的定义

### 方式 15：一键运行真实 issue 评测流水线

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v8.json --run-label realissuev8 --compare-against-eval logs/summaries/batch_eval_realissuev7r2_001.json --compare-label realissue_step6
```

你会看到：

- 真实 issue manifest 的任务总数
- 当前 `semi_real / real_issue / synthetic` 任务计数
- 本轮 batch summary 路径
- 本轮 eval summary 路径
- 如果提供 baseline eval，还会自动产出 compare 报告路径

### 方式 16：运行 dateutil tzstr 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_019.json --policy optimization/policy_versions/improved_v9.json
```

你会看到：

- `task_019` 被成功修复
- 修改文件是 `dateutil_tz_repo/tz.py`
- patch 原因是让 UTC 和 GMT 在未显式提供 offset 时回落为零偏移

### 方式 17：运行 dateutil 9 位时间串真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_022.json --policy optimization/policy_versions/improved_v10.json
```

你会看到：

- `task_022` 被成功修复
- 修改文件是 `dateutil_parser_repo_v2/parser.py`
- patch 原因是让 9 位时间串按 HHMMSSmmm 解析

### 方式 18：运行 jinja 模板变量分析真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_024.json --policy optimization/policy_versions/improved_v11.json
```

你会看到：

- `task_024` 被成功修复
- 修改文件是 `jinja_meta_repo/meta.py`
- patch 原因是让所有分支都已赋值的变量不再被判定为 undeclared

### 方式 19：运行 jinja slice fill_with 边界真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_026.json --policy optimization/policy_versions/improved_v12.json
```

你会看到：

- `task_026` 被成功修复
- 修改文件是 `jinja_slice_repo/filters.py`
- patch 原因是只在存在余数时才给 slice 尾部分片补入 `fill_with`

### 方式 20：运行 tomlkit 数组下一行逗号风格真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_028.json --policy optimization/policy_versions/improved_v13.json
```

你会看到：

- `task_028` 被成功修复
- 修改文件是 `tomlkit_array_repo/formatter.py`
- patch 原因是保留原始下一行逗号风格，避免 append 后生成双逗号

### 方式 21：运行 tomlkit dotted inline table 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_030.json --policy optimization/policy_versions/improved_v14.json
```

你会看到：

- `task_030` 被成功修复
- 修改文件是 `tomlkit_inline_table_repo/formatter.py`
- patch 原因是为 dotted inline table 新增键值对补上逗号和空格分隔

### 方式 22：运行 packaging wheel version normalization 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_032.json --policy optimization/policy_versions/improved_v15.json
```

你会看到：

- `task_032` 被成功修复
- 修改文件是 `packaging_wheel_repo/utils.py`
- patch 原因是拒绝未 normalized 的 wheel 版本号

### 方式 23：运行 jsonschema mixed-type extras 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_034.json --policy optimization/policy_versions/improved_v16.json
```

你会看到：

- `task_034` 被成功修复
- 修改文件是 `jsonschema_extras_repo/utils.py`
- patch 原因是 mixed-type extras 在 `sorted(extras)` 时会抛出 `TypeError`，需要在排序失败时回落到稳定输出

### 方式 24：运行 jsonschema hostname ValueError 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_036.json --policy optimization/policy_versions/improved_v17.json
```

你会看到：

- `task_036` 被成功修复
- 修改文件是 `jsonschema_hostname_repo/hostname.py`
- patch 原因是 hostname 格式检查在空字符串场景下不应再直接抛出 `ValueError`

### 方式 25：运行 jsonschema integer-valued multipleOf float 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_038.json --policy optimization/policy_versions/improved_v18.json
```

你会看到：

- `task_038` 被成功修复
- 修改文件是 `jsonschema_multipleof_repo/validator.py`
- patch 原因是整数值浮点数 `11.0` 不应走纯浮点误差路径，而应按数学整数 `11` 处理

### 方式 26：运行 packaging Requirement extra normalisation 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_040.json --policy optimization/policy_versions/improved_v19.json
```

你会看到：

- `task_040` 被成功修复
- 修改文件是 `packaging_requirement_repo/requirements.py`
- patch 原因是复合 marker 表达式里的 extra 名称也应统一规范化为连字符风格

### 方式 27：运行 click resolve_command None 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_042.json --policy optimization/policy_versions/improved_v20.json
```

你会看到：

- `task_042` 被成功修复
- 修改文件是 `click_alias_repo/cli.py`
- patch 原因是 `cmd is None` 时应保持普通返回语义，而不是直接访问 `cmd.name`

### 方式 28：运行冻结 15 条任务的同集合评测

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_15_v1.json --policy optimization/policy_versions/improved_v16.json --run-label frozen15v16
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_15_v1.json --policy optimization/policy_versions/improved_v17.json --run-label frozen15v17 --compare-against-eval logs/summaries/batch_eval_frozen15v16_001.json --compare-label frozen15_step1
```

你会看到：

- 冻结 manifest 始终固定为同一组 15 条任务
- `improved_v16 -> improved_v17` 在同集合上从 `0.9333` 提升到 `1.0`
- `task_036` 从 `Premature Finish` 变为完全通过

### 方式 29：运行冻结 18 条任务的同集合评测

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_18_v1.json --policy optimization/policy_versions/improved_v19.json --run-label frozen18v19
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_18_v1.json --policy optimization/policy_versions/improved_v20.json --run-label frozen18v20 --compare-against-eval logs/summaries/batch_eval_frozen18v19_001.json --compare-label frozen18_step1
```

你会看到：

- 冻结 manifest 始终固定为同一组 18 条任务
- `improved_v19 -> improved_v20` 在同集合上从 `0.9444` 提升到 `1.0`
- `task_042` 从 `Premature Finish` 变为完全通过

### 方式 30：运行 `MM.YYYY` 月年解析真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_044.json --policy optimization/policy_versions/improved_v21.json
```

你会看到：

- `task_044` 被成功修复
- 修改文件是 `dateutil_month_year_repo/dateutil_month_year_repo/parser.py`
- patch 原因是点号分隔的 `MM.YYYY` 应当走月年格式解析，而不是沿用仅支持斜杠分隔的旧逻辑

### 方式 31：运行 single-label hostname 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_046.json --policy optimization/policy_versions/improved_v22.json
```

你会看到：

- `task_046` 被成功修复
- 修改文件是 `jsonschema_single_label_hostname_repo/jsonschema_single_label_hostname_repo/validators.py`
- patch 原因是 `localhost` 这类 single-label hostname 应作为合法主机名通过，而不是被错误拒绝

### 方式 32：运行冻结 20 条任务的同集合评测

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v21.json --run-label frozen20v21
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v22.json --run-label frozen20v22 --compare-against-eval logs/summaries/batch_eval_frozen20v21_001.json --compare-label frozen20_step1
```

你会看到：

- 冻结 manifest 始终固定为同一组 `20` 条任务
- `improved_v21 -> improved_v22` 在同集合上从 `0.95` 提升到 `1.0`
- `task_046` 从 `Premature Finish` 变为完全通过

### 方式 33：运行 packaging Specifier dev+local 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_048.json --policy optimization/policy_versions/improved_v23.json
```

你会看到：

- `task_048` 被成功修复
- 修改文件是 `packaging_specifier_repo/packaging_specifier_repo/specifiers.py`
- patch 原因是带 `local` 段的版本在 `>` 比较时不应只看 `base_version`，而应按 `public version` 判断

### 方式 34：运行 `frozen_20` 上的无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v23.json --run-label frozen20v23 --compare-against-eval logs/summaries/batch_eval_frozen20v22_001.json --compare-label frozen20_step2
```

你会看到：

- 固定 `20` 条任务集继续保持 `100%` 成功率与 `100%` 测试通过率
- `average_duration_sec` 从 `0.5569` 降到 `0.554`
- 说明新增 `packaging` 规则没有破坏已有能力

### 方式 35：运行 attached comma year 真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_050.json --policy optimization/policy_versions/improved_v24.json
```

你会看到：

- `task_050` 被成功修复
- 修改文件是 `dateutil_attached_comma_repo/dateutil_attached_comma_repo/parser.py`
- patch 原因是年份前紧贴逗号时，也应当先清理标点再识别 year token

### 方式 36：运行 `frozen_20` 的下一轮无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v24.json --run-label frozen20v24 --compare-against-eval logs/summaries/batch_eval_frozen20v23_001.json --compare-label frozen20_step3
```

你会看到：

- 固定 `20` 条任务集继续保持 `100%` 成功率与 `100%` 测试通过率
- `average_duration_sec` 从 `0.554` 降到 `0.548`
- 说明新增日期 parser 规则也没有破坏已有能力

### 方式 37：运行 ErrorTree 状态污染真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_052.json --policy optimization/policy_versions/improved_v25.json
```

你会看到：

- `task_052` 被成功修复
- 修改文件是 `jsonschema_error_tree_repo/jsonschema_error_tree_repo/error_tree.py`
- patch 原因是访问缺失索引时不应通过 `setdefault()` 把空节点写回内部状态

### 方式 38：运行 `frozen_20` 的最新无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v28.json --run-label frozen20v28 --compare-against-eval logs/summaries/batch_eval_frozen20v27_001.json --compare-label frozen20_step7
```

你会看到：

- 固定 `20` 条任务集继续保持 `100%` 成功率与 `100%` 测试通过率
- `average_duration_sec` 从 `0.5709` 小幅下降到 `0.5675`
- 说明新增 validator 继承规则没有造成功能回归，且固定集合效率略有改善

### 方式 39：运行 validator extend 语义保持任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_054.json --policy optimization/policy_versions/improved_v26.json
```

你会看到：

- `task_054` 被成功修复
- 修改文件是 `jsonschema_extend_repo/jsonschema_extend_repo/validators.py`
- patch 原因是 `extend()` 需要保留原始 `applicable_validators`

### 方式 40：运行 sqlite 删除自动提交任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_056.json --policy optimization/policy_versions/improved_v27.json
```

你会看到：

- `task_056` 被成功修复
- 修改文件是 `sqlite_delete_repo/sqlite_delete_repo/table.py`
- patch 原因是 `delete_where()` 需要在删除后立即提交事务

### 方式 41：运行 pydantic validator 继承任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_057.json --policy optimization/policy_versions/improved_v28.json
```

你会看到：

- `task_057` 被成功修复
- 修改文件是 `pydantic_inheritance_repo/pydantic_inheritance_repo/models.py`
- patch 原因是子类 `model_validator` 需要在父类 validator 之后继续追加执行

### 方式 42：运行 attrs alias 定义阶段可见性任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_058.json --policy optimization/policy_versions/improved_v29.json
```

你会看到：

- `task_058` 被成功修复
- 修改文件是 `attrs_alias_repo/attrs_alias_repo/model.py`
- patch 原因是 `field_transformer` 运行前就应能看到最终 alias

### 方式 43：运行 sqlite transform 空字符串转 null 任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_059.json --policy optimization/policy_versions/improved_v30.json
```

你会看到：

- `task_059` 被成功修复
- 修改文件是 `sqlite_transform_repo/sqlite_transform_repo/transform.py`
- patch 原因是数值列转换时空字符串应回落为 `None`

### 方式 44：运行 sqlite extract 跳过 null 任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_060.json --policy optimization/policy_versions/improved_v31.json
```

你会看到：

- `task_060` 被成功修复
- 修改文件是 `sqlite_extract_repo/sqlite_extract_repo/extract.py`
- patch 原因是 `extract` 不应为 `None` 生成维表记录

### 方式 45：运行 isort profile 布局继承任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_061.json --policy optimization/policy_versions/improved_v32.json
```

你会看到：

- `task_061` 被成功修复
- 修改文件是 `isort_profile_repo/isort_profile_repo/formatter.py`
- patch 原因是 tuple 格式化分支需要继承 profile 对应的布局策略

## 当前实现中的环境偏差

规格书默认测试框架是 `pytest`，现在当前环境已经完成安装。

因此当前项目已经切回默认路线：

- benchmark 测试命令改为 `pytest`
- 任务里的 `test_command` 已同步更新

测试文件仍然保留 `unittest.TestCase` 风格，这样可以：

- 兼容 `pytest`
- 保持测试代码简单
- 在必要时也能被 `unittest` 直接执行

## 从 learn-claude-code 吸收了什么

我已经阅读了 `learn-claude-code` 中与 harness 最相关的几部分，当前决定吸收以下优点：

### 1. Loop 保持简单，复杂度放到 Harness

我们不会一开始就把 Agent 写成巨大流程图，而是把复杂度放在：

- 工具定义
- 路径安全
- 运行目录
- 状态持久化
- 后续的恢复与隔离

### 2. 状态文件是真实状态源

参考它的 task system / worktree isolation 设计，我们项目会把以下文件视为 run 的真实状态源：

- `task.json`
- `result.json`
- `trace.json`
- `patch.diff`
- `summary.md`

日志事件可以增加，但不会替代这些核心状态文件。

### 3. 隔离优先

参考它的 worktree / cwd 隔离思路，我们项目会坚持：

- benchmark 原仓库不直接改
- 每次 task run 都使用独立工作副本
- 所有写操作最终都只能落在 run workspace

### 4. 安全边界前置

参考它的 `safe_path` 思路，我们项目会尽早在运行时层实现：

- 工作区边界校验
- 禁止路径逃逸
- 后续工具统一走边界检查

## 每个 phase 未来会补什么

### Phase 1

- 已完成 `list_files`
- 已完成 `search_code`
- 已完成 `read_file`
- 已完成最小 trace 与 observation summary 落盘

### Phase 2

- 已完成 `run_tests`
- 已把测试输出接入结果文件
- 已能总结失败发生位置

### Phase 3

- 已完成 `write_file` 与 patch 应用
- 已完成 `patch.diff` 记录
- 已让 `task_001` 自动修复成功

### Phase 4

- 已完成 `scripts/run_batch.py`
- 已支持多任务独立 run 目录
- 已产出可批量读取的日志结构

### Phase 5

- 已完成 `evals/metrics.py`
- 已完成 `evals/error_taxonomy.py`
- 已完成最小可用的 `batch_eval.py`

### Phase 6

- 已引入 baseline 与 improved 对比
- 已建立 report set
- 已补充自动 compare 报告
- 已把优化过程沉淀到 `docs/optimization_log.md`
- 已补充 `task_004` 与 `improved_v2`
- 已补充 `task_005` / `task_006` 与 `improved_v3`
- 已补充 `task_007` / `task_008` 与 `improved_v4`
- 已补充 `task_009` / `task_010` 与 `improved_v5`
- 已补充 `task_012` / `task_013` 与 `improved_v6`
- 已补充 `task_015` / `task_016` 与 `improved_v7`
- 已补充 `task_011` / `task_017` 与 `improved_v8`
- 已补充 `task_018` / `task_019` 与 `improved_v9`
- 已补充 `task_021` / `task_022` 与 `improved_v10`
- 已补充 `task_023` / `task_024` 与 `improved_v11`
- 已补充 `task_025` / `task_026` 与 `improved_v12`
- 已补充 `task_027` / `task_028` 与 `improved_v13`
- 已补充 `task_029` / `task_030` 与 `improved_v14`
- 已补充 `task_031` / `task_032` 与 `improved_v15`
- 已补充 `task_033` / `task_034` 与 `improved_v16`
- 已补充 `task_035` / `task_036` 与 `improved_v17`
- 已补充 `task_037` / `task_038` 与 `improved_v18`
- 已补充 `task_039` / `task_040` 与 `improved_v19`
- 已补充 `task_041` / `task_042` 与 `improved_v20`
- 已补充 `task_043` / `task_044` 与 `improved_v21`
- 已补充 `task_045` / `task_046` 与 `improved_v22`
- 已补充 `task_047` / `task_048` 与 `improved_v23`
- 已补充 `task_049` / `task_050` 与 `improved_v24`
- 已补充 `task_051` / `task_052` 与 `improved_v25`
- 已补充 `task_053` / `task_054` 与 `improved_v26`
- 已补充 `task_055` / `task_056` 与 `improved_v27`
- 已补充 `task_014` / `task_057` 与 `improved_v28`
- 已补充 `task_058` 与 `improved_v29`
- 已补充 `task_059` 与 `improved_v30`
- 已补充 `task_060` 与 `improved_v31`
- 已补充 `task_061` 与 `improved_v32`
- 已补充 `task_063` 与 `improved_v34`
- 已补充 `task_065` 与 `improved_v35`
- 已补充 `task_067` 与 `improved_v36`
- 已补充 `task_093` 与 `improved_v49`
- 已补充 `task_095` 与 `improved_v50`
- 已补充 `task_097` 与 `improved_v51`
- 已补充 `task_099` 与 `improved_v52`
- 已补充冻结 15 条真实任务的同集合评测 manifest 与 compare 结果
- 已补充冻结 18 条真实任务的同集合评测 manifest 与 compare 结果
- 已补充冻结 20 条真实任务的同集合评测 manifest 与 compare 结果
- 已补充冻结 40 条真实任务的同集合评测 manifest 与 compare 结果
- 已补充真实 issue 任务集的一键 batch/eval/compare 流水线入口
- 已补充真实 issue 候选的批量导入入口
- 已补充 batch run 时延回归分析入口
- 已补充 trace 热点分析入口
- 已补充单任务历史时延分析入口
- 已补充热点任务集合历史分析入口
- 已让新 trace 记录显式步骤耗时
- 已补充环境级复跑对比，能判断“策略变慢”还是“当前环境整体漂移”
- 下一步会继续扩新来源、定位时延回归并扩充任务与优化策略

### 方式 45：运行 packaging marker `extra=None` 回归任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_063.json --policy optimization/policy_versions/improved_v34.json
```

你会看到：

- `task_063` 被成功修复
- 修改文件是 `packaging_marker_repo/markers.py`
- patch 原因是 `extra` 为 `None` 时应直接返回 `False`，而不是继续做小写化处理

### 方式 46：运行正式 `31` 条任务集上的 `improved_v34`

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v34.json --run-label realissuev34 --compare-against-eval logs/summaries/batch_eval_realissuev33_001.json --compare-label realissue_step14
```

你会看到：

- 正式任务集已经从 `30` 条扩到 `31` 条
- `improved_v34` 在正式 `31` 条任务集上保持 `31/31` 成功
- 平均耗时从 `0.5423` 小幅改善到 `0.5391`

### 方式 47：运行 `frozen_20` 上的 `improved_v34` 无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v34.json --run-label frozen20v34 --compare-against-eval logs/summaries/batch_eval_frozen20v33_001.json --compare-label frozen20_step13
```

你会看到：

- `frozen_20` 固定集合保持无回归
- `success_rate` 和 `test_pass_rate` 继续维持 `1.0`
- 平均耗时从 `0.5379` 小幅改善到 `0.5368`

### 方式 48：运行 packaging `< prerelease` 回归任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_065.json --policy optimization/policy_versions/improved_v35.json
```

你会看到：

- `task_065` 被成功修复
- 修改文件是 `packaging_prerelease_repo/specifiers.py`
- patch 原因是 specifier 自身为 prerelease 时，更早但不相等的 prerelease 仍应允许命中

### 方式 49：运行正式 `32` 条任务集上的 `improved_v35`

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v35.json --run-label realissuev35 --compare-against-eval logs/summaries/batch_eval_realissuev34_001.json --compare-label realissue_step15
```

你会看到：

- 正式任务集已经从 `31` 条扩到 `32` 条
- `improved_v35` 在正式 `32` 条任务集上保持 `32/32` 成功
- 平均耗时从 `0.5391` 继续改善到 `0.535`

### 方式 50：运行 `frozen_20` 上的 `improved_v35` 无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v35.json --run-label frozen20v35 --compare-against-eval logs/summaries/batch_eval_frozen20v34_001.json --compare-label frozen20_step14
```

你会看到：

- `frozen_20` 固定集合保持无功能回归
- `success_rate` 和 `test_pass_rate` 继续维持 `1.0`
- 平均耗时从 `0.5368` 小幅波动到 `0.5402`

### 方式 51：运行 packaging wheel compressed tag order 回归任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_067.json --policy optimization/policy_versions/improved_v36.json
```

你会看到：

- `task_067` 被成功修复
- 修改文件是 `packaging_tag_order_repo/utils.py`
- patch 原因是 compressed tag set 必须按排序顺序出现，未排序时应直接拒绝

### 方式 52：运行正式 `33` 条任务集上的 `improved_v36`

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v36.json --run-label realissuev36 --compare-against-eval logs/summaries/batch_eval_realissuev35_001.json --compare-label realissue_step16
```

你会看到：

- 正式任务集已经从 `32` 条扩到 `33` 条
- `improved_v36` 在正式 `33` 条任务集上保持 `33/33` 成功
- 平均耗时从 `0.535` 继续改善到 `0.5312`

### 方式 53：运行 `frozen_20` 上的 `improved_v36` 无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v36.json --run-label frozen20v36 --compare-against-eval logs/summaries/batch_eval_frozen20v35_001.json --compare-label frozen20_step15
```

你会看到：

- `frozen_20` 固定集合保持无功能回归
- `success_rate` 和 `test_pass_rate` 继续维持 `1.0`
- 平均耗时从 `0.5402` 小幅改善到 `0.5386`

### 方式 54：运行 tomlkit boolean(True) 回归任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_069.json --policy optimization/policy_versions/improved_v37.json
```

你会看到：

- `task_069` 被成功修复
- 修改文件是 `tomlkit_boolean_repo/items.py`
- patch 原因是 `boolean(True)` 应返回 `true`，而不是错误地继续返回 `false`

### 方式 55：运行正式 `34` 条任务集上的 `improved_v37`

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v37.json --run-label realissuev37 --compare-against-eval logs/summaries/batch_eval_realissuev36_001.json --compare-label realissue_step17
```

你会看到：

- 正式任务集已经从 `33` 条扩到 `34` 条
- `improved_v37` 在正式 `34` 条任务集上保持 `34/34` 成功
- 平均耗时从 `0.5312` 回升到 `0.6038`

### 方式 56：运行 `frozen_20` 上的 `improved_v37` 无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v37.json --run-label frozen20v37 --compare-against-eval logs/summaries/batch_eval_frozen20v36_001.json --compare-label frozen20_step16
```

你会看到：

- `frozen_20` 固定集合继续保持无功能回归
- `success_rate` 和 `test_pass_rate` 继续维持 `1.0`
- 平均耗时从 `0.5386` 回升到 `0.5687`

### 方式 57：运行 tomlkit 代理删除回归任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_071.json --policy optimization/policy_versions/improved_v38.json
```

你会看到：

- `task_071` 被成功修复
- 修改文件是 `tomlkit_proxy_repo/proxy.py`
- patch 原因是代理 `pop()` 应真正删除底层键，而不是只返回原值

### 方式 58：运行正式 `35` 条任务集上的 `improved_v38`

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v38.json --run-label realissuev38 --compare-against-eval logs/summaries/batch_eval_realissuev37_001.json --compare-label realissue_step18
```

你会看到：

- 正式任务集已经从 `34` 条扩到 `35` 条
- `improved_v38` 在正式 `35` 条任务集上保持 `35/35` 成功
- 平均耗时从 `0.6038` 回落到 `0.553`

### 方式 59：运行 `frozen_20` 上的 `improved_v38` 无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v38.json --run-label frozen20v38 --compare-against-eval logs/summaries/batch_eval_frozen20v37_001.json --compare-label frozen20_step17
```

你会看到：

- `frozen_20` 固定集合继续保持无功能回归
- `success_rate` 和 `test_pass_rate` 继续维持 `1.0`
- 平均耗时从 `0.5687` 回落到 `0.5427`

### 方式 60：运行 tomlkit super table dotted key 回归任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_073.json --policy optimization/policy_versions/improved_v39.json
```

你会看到：

- `task_073` 被成功修复
- 修改文件是 `tomlkit_super_table_repo/renderer.py`
- patch 原因是 super table 下新增 dotted key 时应继续保留父级前缀

### 方式 61：运行正式 `36` 条任务集上的 `improved_v39`

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v39.json --run-label realissuev39 --compare-against-eval logs/summaries/batch_eval_realissuev38_001.json --compare-label realissue_step19
```

你会看到：

- 正式任务集已经从 `35` 条扩到 `36` 条
- `improved_v39` 在正式 `36` 条任务集上保持 `36/36` 成功
- 平均耗时从 `0.553` 继续回落到 `0.5453`

### 方式 62：运行 `frozen_20` 上的 `improved_v39` 无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v39.json --run-label frozen20v39 --compare-against-eval logs/summaries/batch_eval_frozen20v38_001.json --compare-label frozen20_step18
```

你会看到：

- `frozen_20` 固定集合继续保持无功能回归
- `success_rate` 和 `test_pass_rate` 继续维持 `1.0`
- 平均耗时只从 `0.5427` 轻微波动到 `0.5443`

### 方式 63：运行 jinja async repr 回归任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_075.json --policy optimization/policy_versions/improved_v40.json
```

你会看到：

- `task_075` 被成功修复
- 修改文件是 `jinja_async_repr_repo/runtime.py`
- patch 原因是 AsyncLoopContext 的 repr 不应再暴露协程对象

### 方式 64：运行正式 `37` 条任务集上的 `improved_v40`

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v40.json --run-label realissuev40 --compare-against-eval logs/summaries/batch_eval_realissuev39_001.json --compare-label realissue_step20
```

你会看到：

- 正式任务集已经从 `36` 条扩到 `37` 条
- `improved_v40` 在正式 `37` 条任务集上保持 `37/37` 成功
- 平均耗时从 `0.5453` 回升到 `0.5717`

### 方式 65：运行 `frozen_20` 上的 `improved_v40` 无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v40.json --run-label frozen20v40 --compare-against-eval logs/summaries/batch_eval_frozen20v39_001.json --compare-label frozen20_step19
```

你会看到：

- `frozen_20` 固定集合继续保持无功能回归
- `success_rate` 和 `test_pass_rate` 继续维持 `1.0`
- 平均耗时从 `0.5443` 回升到 `0.5682`

### 方式 66：运行 jinja indent 首行空白回归任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_077.json --policy optimization/policy_versions/improved_v41.json
```

你会看到：

- `task_077` 被成功修复
- 修改文件是 `jinja_indent_repo/filters.py`
- patch 原因是 `first=True` 时，空白首行仍应继续遵守 `blank=False`

### 方式 67：运行正式 `38` 条任务集上的 `improved_v41`

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v41.json --run-label realissuev41 --compare-against-eval logs/summaries/batch_eval_realissuev40_001.json --compare-label realissue_step21
```

你会看到：

- 正式任务集已经从 `37` 条扩到 `38` 条
- `improved_v41` 在正式 `38` 条任务集上保持 `38/38` 成功
- 平均耗时从 `0.5717` 回落到 `0.5173`

### 方式 68：运行 `frozen_20` 上的 `improved_v41` 无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v41.json --run-label frozen20v41 --compare-against-eval logs/summaries/batch_eval_frozen20v40_001.json --compare-label frozen20_step20
```

你会看到：

- `frozen_20` 固定集合继续保持无功能回归
- `success_rate` 和 `test_pass_rate` 继续维持 `1.0`
- 平均耗时从 `0.5682` 回落到 `0.5185`

### 方式 69：运行 tomlkit inline table 缺少换行回归任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_079.json --policy optimization/policy_versions/improved_v42.json
```

你会看到：

- `task_079` 被成功修复
- 修改文件是 `tomlkit_inline_newline_repo/renderer.py`
- patch 原因是 dotted inline table 后续追加普通键时必须落到下一行

### 方式 70：运行正式 `39` 条任务集上的 `improved_v42`

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v42.json --run-label realissuev42 --compare-against-eval logs/summaries/batch_eval_realissuev41_001.json --compare-label realissue_step22
```

你会看到：

- 正式任务集已经从 `38` 条扩到 `39` 条
- `improved_v42` 在正式 `39` 条任务集上保持 `39/39` 成功
- 平均耗时从 `0.5173` 进一步小幅回落到 `0.5157`

### 方式 71：运行 `frozen_20` 上的 `improved_v42` 无回归验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v42.json --run-label frozen20v42 --compare-against-eval logs/summaries/batch_eval_frozen20v41_001.json --compare-label frozen20_step21
```

你会看到：

- `frozen_20` 固定集合继续保持无功能回归
- `success_rate` 和 `test_pass_rate` 继续维持 `1.0`
- 平均耗时仅从 `0.5185` 轻微波动到 `0.5186`

### Phase 7

- 在主线稳定后，尝试轻量 SFT / preference / LoRA 实验

## 建议的阅读顺序

如果你想快速理解项目，建议按这个顺序看：

1. `README.md`
2. `GUIDE.md`
3. `docs/project_memory.md`
4. `docs/next_actions.md`
5. `docs/candidate_shortlist.md`
6. `docs/benchmark_registry.md`
7. `benchmarks/tasks/task_001.json`
8. `benchmarks/repos/sample_repo/`
9. `app/schemas/task_schema.py`
10. `scripts/run_single_task.py`
11. `docs/harness.md`
12. `scripts/run_batch.py`
13. `logs/summaries/batch_run_001.json`
14. `logs/summaries/batch_compare_phase6_002.json`

## 下一轮我会做什么

下一轮进入 `Phase 6` 时，我会继续补齐：

- baseline 配置冻结
- improved prompt / policy / grader 版本
- 扩充 report set
- 逐步引入 GitHub 真实仓库 issue 作为正式评测候选
- 持续把真实 issue 缩题成可运行 semi_real 任务，并沉淀指标对比
- 用新增的时延分析脚本定位最近几轮 `average_duration_sec` 回升原因
- 沿 `run_tests` 链继续定位系统性时延回升来源
- 扩新来源，把正式真实任务从 `39` 条继续推向 `40+` 再到 `60+`
- 再补 `1` 条正式任务后立刻创建 `frozen_40` manifest
- 继续追加优化前后差异说明

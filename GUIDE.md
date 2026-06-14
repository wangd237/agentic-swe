# 项目实施指南

本文件是历史实施日志和上手索引，保留大量 phase 过程记录。当前对外主线已经切到 LLM coding agent；如果是为了求职展示或恢复最新方向，请优先阅读：

- [README.md](/E:/My_Projects/agentic-software-engineering-roadmap/README.md)
- [docs/agent_overview.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_overview.md)
- [docs/agent_eval_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_eval_summary.md)
- [docs/agent_case_studies.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_case_studies.md)
- [docs/next_actions.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/next_actions.md)

下面的 phase 记录仍有工程追溯价值，但不要把它理解成当前主线；benchmark、maturity、stability 等内容现在是 agent 的验证底座。

## 当前进度

| Phase | 名称 | 状态 | 说明 |
| --- | --- | --- | --- |
| Phase 0 | 项目初始化 | 已完成 | 已建立项目骨架、最小 benchmark repo、任务定义与说明文档 |
| Phase 1 | 观察型 Agent | 已完成 | 已实现 list/search/read、单任务观察闭环与 trace 落盘 |
| Phase 2 | 测试闭环 | 已完成 | 已实现 run_tests、失败摘要提取与测试输出落盘 |
| Phase 3 | Patch 闭环 | 已完成 | 已实现 write_file、show_diff、patch 应用与修复前后测试对比 |
| Phase 4 | 批量运行 | 已完成 | 已实现 batch runner、manifest 任务集与批量汇总结果 |
| Phase 5 | 评测系统 | 已完成 | 已实现 metrics、taxonomy、batch eval 与 baseline 报告 |
| Phase 6 | 优化系统 | 进行中 | 已完成 `baseline_v1 -> improved_v72` 多轮策略迭代，正式真实任务扩充到 `66` 条，challenge 任务扩充到 `6` 条，已建立 `frozen_40 v1`；`v72` 是当前最新 challenge 扩展版本，新增了 `Textualize/rich#2457` 对应的 Windows-like `no_color` 修复规则，`v71` 仍保留为上一轮主扩容版本，`v50` 保留为 `frozen_40` 的历史稳定锚点；当前 `task_133` 已正式接入 challenge manifest，challenge 线已从“评估第 6 条候选”推进到“重新 sourcing 第 7 条 challenge 候选”；相对上一轮，challenge 集规模从 `5 -> 6`，但 `challengev72_r6` 的成功率 / 测试通过率仍只有 `0.5`，说明 challenge 线仍以边界展示为主、还需要继续补强；下一步要继续做 challenge sourcing、hard case 稳定性复核，以及正式主集与冻结集的性能回归控制 |
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

## Phase 6 历史扩容样例

### 1. 以 `improved_v63` 为例说明一次完整扩容闭环

这一节保留的是一个历史样例，用来解释“真实 issue 扩容一轮通常会产出什么、如何验证、如何体验”。

它不是当前最新状态；当前实时口径请以本文件前面的“当前进度”和“当前最准确的状态口径”为准。

这轮历史样例新增的真实 issue 来自：

- `python-poetry/tomlkit#412`

新增产物：

- `benchmarks/issue_batch_v63_candidates.json`
- `benchmarks/tasks/task_120.json`
- `benchmarks/tasks/task_121.json`
- `benchmarks/repos/tomlkit_int_key_repo/`
- `optimization/policy_versions/improved_v63.json`

当前最关键的新增能力：

- agent 已能修复一种新的 tomlkit 容器 int key 规范化问题
- 场景是“解析路径已经接受 `4 = 5` 这种整数 key，但 `add(4, 5)` 与 `setdefault(4, 5)` 仍会把 `int` 当成可迭代对象并崩溃”
- 同时这一轮再次验证了 patcher 版本继承链是高频回归点，`v63r1` 首轮暴露出从 `v47` 到 `v43` 的多段旧规则集合遗漏 `improved_v63`，`v63r2` 修复后恢复正式集回归
- 这让正式真实任务总数从 `59` 提升到 `60`

### 2. 这轮样例体现出的框架结构

Phase 6 当前在真实任务扩容侧已经形成稳定模板：

- 先导入 GitHub issue，生成 `real_issue` 草稿
- 再生成 `semi_real` 可运行 repo
- 在 `app/agent/patcher.py` 中补一条专用规则
- 为每轮扩容生成新的 `optimization/policy_versions/improved_vXX.json`
- 最后跑正式集、`frozen_20`、`frozen_40`、maturity 审计并同步文档

这轮样例对应的目录入口：

- `benchmarks/repos/tomlkit_int_key_repo`

### 3. 你现在可以怎么体验这个历史样例

如果你想直接体验这条历史扩容样例，可以按下面顺序：

1. 先看任务定义：
   - `benchmarks/tasks/task_121.json`
2. 再看最小 repo：
   - `benchmarks/repos/tomlkit_int_key_repo`
3. 先手工验证原始失败：
   - `python -m pytest benchmarks/repos/tomlkit_int_key_repo/tests/test_container.py -q`
4. 再跑单任务闭环：
   - `python scripts/run_single_task.py --task benchmarks/tasks/task_121.json --policy optimization/policy_versions/improved_v63.json`
5. 如果你想看这轮正式集扩容验证：
   - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v63.json --run-label realissuev63r2`
6. 如果你想体验新的结构化 issue 导入入口：
   - `python -m scripts.import_issue_batch --input benchmarks/issue_batch_v63_candidates.json --candidate-file benchmarks/real_world_candidates.json`

### 4. 当前最准确的状态口径

- 正式真实任务数：`66`
- 来源生态数：`16`
- 当前主版本：`improved_v71`
- 当前长期对比锚点：`improved_v50`
- 当前最近完成正式集全绿与冻结集最小验证的版本：`improved_v71`
- 当前 `frozen_40 streak`：`8`

注意：

- `v71` 是当前最新扩容成功版本：它把正式任务从 `65` 条推进到 `66` 条，并保持了三线功能全绿
- 它在正式集、`frozen_20`、`frozen_40` 上分别达到：
  - `66 / 66`
  - `20 / 20`
  - `40 / 40`
- `v71` 的稳定性复跑当前已补到：
  - `frozen_20`
    - mean = `0.5727`
    - std = `0.0177`
    - conclusion = `stable`
  - `frozen_40`
    - mean = `0.5637`
    - std = `0.0099`
    - conclusion = `stable`
- 但相对 `v70`，`v71` 的性能信号也是分裂的：
  - 正式集：`0.5924 -> 0.5617`
  - `frozen_20`：`0.5803 -> 0.5974`
  - `frozen_40`：`0.5582 -> 0.5794`
- 因此更准确的表述是：
  - `v71` 是当前主版本与最新扩容版本
  - `v70` 是上一轮主扩容参考
  - `v50` 继续作为历史稳定锚点保留

### 5. 当前展示层口径校准说明

为了避免后续阅读时把“历史阶段记录”和“当前状态”混在一起，当前文档约定统一如下：

- 所有标注“当前”“最新”“现在”的展示层入口
  - 统一以 `improved_v71 / 66` 条正式任务 / `3` 条 challenge / `16` 个生态为准
- 所有按时间顺序展开的历史记录
  - 保留当时真实语境，不强行改写成今天的数字
- 如果后续继续升级到 `v71+`
  - 优先同步：
    - `README.md`
    - `docs/experiment_summary.md`
    - `docs/project_memory.md`
    - 本文件这一节

补充一条当前非常重要的性能口径：

- `improved_v68` 与 `improved_v69` 的 `pytest_additional_flags` 完全相同
- 因此当前仓库里关于 `v68 / v69` 的 `pytest phases / importtime / matrix / matrix-set` 结果
  - 应优先看作 `runtime-equivalent noise probe`
  - 不应继续直接解释成“pytest runtime flags 差异导致的主因实验”
- 这意味着后续如果继续看这批结果，正确用途是：
  - 观察环境噪声
  - 观察稳定性
  - 观察总链路是否有需要继续下钻的阶段

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

- 正式 `semi_real` 真实任务数：`54`
- 冻结集合：`frozen_40 v1`
- 当前稳定 streak：`8`
- 当前稳定基线策略：`improved_v50`
- 当前最新扩容策略：`improved_v57`

其中最新一轮新增的是：

- 来源 issue：`pypa/packaging#1231`
- draft 任务：`task_108`
- 正式 semi_real 任务：`task_109`
- semi_real repo：`benchmarks/repos/packaging_name_normalization_repo`

这轮新增能力覆盖的场景是：

- 名称已经是 `canonicalize_name()` 的稳定输出时
- `is_normalized_name()` 不应继续错误拒绝前后带连字符的 canonicalized 名称
- 必须继续保持普通中间连字符名称的既有行为不回归

当前这一轮的关键结论要分开看：

- 功能面：
  - `improved_v57` 已在正式 `54` 条任务集、`frozen_20` 与 `frozen_40` 上保持 `100%` 成功率和 `100%` 测试通过率
- 性能面：
  - `v57` 的正式集复跑口径对比 `v56` 是 `average_duration_sec = 0.5237 -> 0.523`
  - `v57` 的 `frozen_20` 复跑口径对比 `v56` 是 `average_duration_sec = 0.5313 -> 0.5385`
  - `v57` 的 `frozen_40` 复跑口径对比 `v56` 是 `average_duration_sec = 0.5293 -> 0.5437`
  - 当前固定 `40` 条集合已经重新落回 `improved_v32` 阈值 `0.5514` 以内

因此当前更可信的判断是：

- `v57` 已经成功把正式任务数从 `53` 扩到 `54`
- 它在复跑口径下继续保持正式集、`frozen_20`、`frozen_40` 三线功能全绿
- 它在正式集上相对 `v56` 继续小幅降低平均耗时
- 它仍然不改变当前稳定基线是 `v50` 这一事实
- 但这轮已经重新把后续版本带回“可以继续积累稳定证据”的轨道

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
- 支持 `--from-candidate` 自动推断模块路径、测试路径、成功标准和额外标签
- 支持 `--dry-run` 只打印推断结果，不写任务、不写 repo、也不改候选状态
- 候选状态机当前按最小版维护：
  - `imported`
  - `screened`
  - `accepted`
  - `completed`
  - `blocked`
- 在 `--ready` 模式下自动把任务追加到 `benchmarks/manifests/real_issue_tasks.json`
- 配套脚本也已同步：
  - `scripts/screen_candidate.py` 负责人工筛选
  - `scripts/screen_candidate.py` 也支持按 `imported` 批量逐条筛选
  - `scripts/import_issue_batch.py` 的批量导入摘要改用 `draft_task_count`
  - `scripts/validate_tasks.py` 会校验新状态集合

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
- `draft_task_count`
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

或者使用候选驱动的半自动模式：

```bash
python scripts/scaffold_semi_real_task.py --from-candidate pypa_distlib_issue_238 --candidate-file benchmarks/real_world_candidates.json --dry-run
```

你会看到：

- 新生成的 `semi_real_task` 路径
- scaffold 目标 repo 路径
- 模块文件与测试文件路径
- 当前是否以 `ready` 模式生成

如果使用 `--from-candidate` 且不加 `--dry-run`：

- 候选状态必须先是 `screened` 或 `accepted`
- 非 `ready` 模式也会落盘脚手架，但不会把状态提升成显式的 `scaffolded`
- 适合先做人工缩题和最小复现，再决定是否切到 `--ready`

如果只想先检查自动推断结果：

- 使用 `--dry-run`
- 不会写入任务文件
- 不会创建 repo 脚手架
- 不会修改 candidate 状态

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
- 扩新来源，把正式真实任务从 `54` 条继续推向 `60+`
- 持续在 `frozen_40` 上累计后续版本的无回归证据
- 继续追加优化前后差异说明

## Phase 6 当前最新补充：稳定性复跑与 maturity 流水线

### 1. 这次新增了什么

在 `v63` 把正式真实任务集推进到 `60` 条之后，项目新增了两类非常关键的基础设施能力：

- `stability recheck`
  - 解决“单次采样偏高，会不会误判策略退化”的问题
- `maturity audit in pipeline`
  - 让正式任务数、生态数、冻结集规模、连续无回归版本数，能够在评测结束后自动审计

新增脚本：

- `scripts/stability_recheck.py`

增强脚本：

- `scripts/run_real_issue_eval.py`

### 2. 这部分解决了什么问题

在这之前，`frozen_40` 的一次运行如果恰好偏高，比如 `v63r2 = 0.5594`，我们很难立刻判断：

- 这是策略真的变慢了
- 还是单次环境波动

现在有了稳定性复跑之后，我们可以对同一策略、同一 manifest 连跑多次，再看：

- `average_duration_sec` 的均值和标准差
- 是否有 outlier
- `success_rate` 和 `test_pass_rate` 是否完全一致
- 结论是 `stable`、`borderline` 还是 `unstable`

### 3. 当前这部分的真实结果

基于 `improved_v63` 在 `frozen_40` 上的 3 次复跑：

- run1：`0.602`
- run2：`0.5508`
- run3：`0.5489`

聚合后得到：

- `average_duration_mean_sec = 0.5672`
- `average_duration_std_sec = 0.0301`
- `success_rate_mean = 1.0`
- `test_pass_rate_mean = 1.0`
- `functional_consistent = true`
- `conclusion = borderline`

这说明：

- 功能层面完全一致，没有回归
- 性能层面有轻微波动，但没有证据说明策略逻辑已经系统性退化

### 4. 你现在可以怎么体验

#### 方式 72：直接跑当前最新单任务代表案例

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_121.json --policy optimization/policy_versions/improved_v63.json
```

你会看到：

- `task_121` 被成功修复
- 修改文件是 `tomlkit_int_key_repo/container.py`
- 修复的是 `add(4, 5)` / `setdefault(4, 5)` 遇到整数 key 时的规范化问题

#### 方式 73：跑当前正式 `60` 条任务集

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v63.json --run-label realissuev63r2
```

你会看到：

- 当前正式真实任务集规模是 `60`
- `improved_v63` 在正式集上保持 `60 / 60`
- 会生成新的 batch run / batch eval 摘要

#### 方式 74：跑带稳定性检查的评测流水线

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v63.json --run-label frozen20_v63_pipeline_rerun --stability-check --stability-repetitions 2 --stability-manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json
```

你会看到：

- 一次命令完成 batch run、batch eval、stability recheck、maturity audit
- 终端最后会打印 maturity 摘要
- `logs/summaries/` 下会生成稳定性和 maturity 报告

#### 方式 75：单独做 `frozen_40` 稳定性复跑

在仓库根目录执行：

```bash
python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v63.json --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --repetitions 3 --run-label frozen40_v63_stability
```

你会看到：

- 每次 run 的 `success_rate / test_pass_rate / average_duration_sec`
- 聚合均值、标准差、outlier 检测
- 最终稳定性结论

#### 方式 76：查看 benchmark maturity 审计结果

直接打开：

- `logs/summaries/benchmark_maturity_maturity_046.md`

你会看到当前项目的成熟度口径：

- `formal_task_count = 63 / 60`
- `ecosystem_count = 16 / 6`
- `latest_frozen_count = 40 / 40`
- `frozen_40_streak = 8 / 5`

### 5. 当前最准确的项目状态口径

- 正式真实任务数：`63`
- 来源生态数：`16`
- 当前主版本策略：`improved_v68`
- 当前长期对比锚点：`improved_v50`
- 当前 `frozen_40 streak`：`8`
- 当前同版复跑性能证据：
  - `frozen_20 mean = 0.5617`
  - `frozen_40 mean = 0.5529`
- 当前稳定性结论：`stable`

### 6. 现在这套框架和最开始相比，有什么质变

现在项目已经不只是：

- “能跑单任务”
- “能自动改一段代码”

而是已经具备：

- 正式真实任务集
- 冻结集
- 批量评测
- 策略版本化
- 同版稳定性复跑
- maturity 自动审计

这意味着它已经从一个课程式工程练习，进化成了一个可持续迭代的 benchmark 基础设施雏形。

### 7. 后面你看代码时，建议优先看哪里

如果你想直接理解这轮新增能力，优先看下面这些文件：

1. `scripts/stability_recheck.py`
2. `scripts/run_real_issue_eval.py`
3. `logs/summaries/stability_recheck_frozen40_v63_stability_001.json`
4. `logs/summaries/benchmark_maturity_maturity_046.md`
5. `docs/experiment_summary.md`
6. `docs/case_studies.md`

## Phase 6 当前最新补充：`fsspec#979` 脚手架推进

### 1. 这次新增了什么

这轮不是继续加新工具，而是把 A2/C 线里最靠前的一条真实新来源候选真正推进到了可落盘脚手架阶段：

- 候选：`fsspec/filesystem_spec#979`
- 生成任务：`benchmarks/tasks/task_122.json`
- 生成仓库：`benchmarks/repos/fsspec_unstrip_protocol_repo`

### 2. 当前处在什么状态

这条任务目前已经不是纯 TODO 脚手架，而是：

- 已从 `screened` 推进到 `accepted`
- 已补齐 `expected_target_files`
- 已成功跑通非 `dry-run` 脚手架
- 已把 TODO 模块与 TODO 测试补成 ready 口径的 semi_real 回归任务
- 当前已纳入 challenge manifest，是否升格为正式 manifest 留作后续决策

这一步的价值是：

- 证明 `--from-candidate` 不只是能演示 dry-run，而是真的能把候选落盘为 task + repo
- 证明这条链路还能继续从“落盘脚手架”走到“ready semi_real”
- 后续扩新来源时，可以复用同一条“搜索 -> 筛选 -> 脚手架 -> ready”链路

### 3. 你现在可以怎么体验

#### 方式 77：查看新生成的 draft semi_real task

直接打开：

- `benchmarks/tasks/task_122.json`

你会看到：

- 目标文件提示已经落到 `fsspec/spec.py`
- 测试入口已经落到 `fsspec/tests/test_spec.py`
- 当前 metadata 已切到 `repo_scaffold_status = ready`
- `expected_failure_test` 已明确指向首个核心回归测试

#### 方式 78：查看自动生成的脚手架仓库

直接打开：

- `benchmarks/repos/fsspec_unstrip_protocol_repo`

你会看到：

- `fsspec/spec.py` 中已经还原了最小 `unstrip_protocol` 缺陷实现
- `fsspec/tests/test_spec.py` 中已经补成了 3 个稳定回归测试
- `README.md` 仍保留了这个仓库是由脚手架生成的上下文

#### 方式 79：直接验证 `task_122` 的 repo 测试

在仓库根目录执行：

```bash
python -m pytest benchmarks/repos/fsspec_unstrip_protocol_repo/fsspec/tests/test_spec.py -q
```

你会看到：

- 当前 3 个回归测试全部通过
- 这说明 `task_122` 已经不是空壳脚手架，而是 ready 口径的 semi_real 任务

### 4. 当前最准确的下一步

如果接着做这条线，优先顺序应该是：

1. 为 `improved_v64` 补正式集 / frozen 集验证
2. 继续把 `anyio#1109 / anyio#1111` 中的一条推进到 `screened`
3. 继续扩并发与协程 / 文件路径与 IO 两个缺口家族
4. 在扩容同时维持 frozen 集与 maturity 审计口径

### 5. 这条线的当前正式状态

- `task_122` 已纳入 `benchmarks/manifests/real_issue_tasks.json`
- 正式任务总数已从 `60` 推进到 `61`
- 已确认：
  - `improved_v63` 对带 bug 的 `task_122` 单任务失败
  - `improved_v64` 对带 bug 的 `task_122` 单任务成功
- `improved_v64` 的正式集 / `frozen_20` / `frozen_40` 最小验证也已经完成

这说明：

- 这次不是“把修好的 repo 塞进正式集”
- 而是已经形成了真正符合 benchmark 口径的闭环：
  - 带 bug repo
  - 失败基线
  - 新策略修复成功

### 6. `improved_v64` 当前最准确的结果

- 正式集：
  - `60 -> 61` 条
  - `success_count: 60 -> 61`
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `average_duration_sec: 0.5411 -> 0.5551`
- `frozen_20`：
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `average_duration_sec: 0.5704 -> 0.5773`
- `frozen_40`：
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `average_duration_sec: 0.5594 -> 0.5686`

所以这轮更准确的表述是：

- 扩容成功
- 功能无回归
- 单次 compare 里性能有轻微回升
- 但稳定性复跑结果是：
  - `frozen_20` mean = `0.5475`，conclusion = `stable`
  - `frozen_40` mean = `0.5432`，conclusion = `stable`
- 因此更合理的结论是：单次回升更像采样波动，不足以定性为长期退化

## Phase 6 历史补充：`anyio#1109` 进入 screened

### 1. 这次新增了什么

在 `fsspec#979` 这条线完成正式接入和稳定性复跑之后，当前主焦点已经切回并发与协程家族。

这轮先把：

- `agronholm/anyio#1109`

从 `imported` 推进到了 `screened`。

### 2. 当前处在什么状态

- `anyio#1109` 已通过人工筛选
- `scaffold_semi_real_task.py --from-candidate --dry-run` 已跑通
- 当前 dry-run 自动推断结果仍偏保守：
  - `module_file = anyio_taskgroup_reentry_repo/module.py`
  - `test_file = tests/test_module.py`

这说明：

- 这条 issue 已经足够进入 semi_real 缩题阶段
- 但在真正非 `dry-run` 落盘前，最好先手工补一个更可信的 target file 提示

### 3. 当前最准确的下一步

如果沿这条线继续做，优先顺序应该是：

1. 给 `agronholm/anyio#1109` 补 `expected_target_files`
2. 跑非 `dry-run` 脚手架
3. 把它推进到 ready semi_real
4. 再判断是否进入正式 manifest

## Phase 6 当前最新补充：`task_123` 正式接入与 `improved_v65`

### 1. 这次补了什么

这一轮把并发与协程方向的第一条正式任务真正打通了：

- 来源：`agronholm/anyio#1109`
- 正式任务：`task_123`
- 新策略：`improved_v65`

它解决的问题是：

- 同一个 `TaskGroup` 被重复进入时
- 旧实现会泄漏内部状态，最终抛出 `AttributeError`
- 新策略把这个场景收口为受控 `RuntimeError("TaskGroup cannot be re-entered")`

### 2. 这一轮为什么重要

这不只是“又多了一题”，而是补上了一个之前正式集里还没有的生态：

- 新增生态：`agronholm/anyio`
- 正式任务总数：`61 -> 62`
- 来源生态数：`15 -> 16`

也就是说，当前 benchmark 不再只覆盖同步解析、格式化、序列化这类题，还开始把并发与协程边界纳入正式集。

### 3. 这一轮是怎么验证的

这次仍然坚持正式接入前的完整证据链：

1. 先把 `anyio#1109` 缩成 ready 口径 semi_real repo
2. 验证带 bug repo 确实失败
3. 验证旧策略 `improved_v64` 单任务失败
4. 新增 `improved_v65`
5. 验证 `improved_v65` 单任务成功
6. 再补正式集、`frozen_20`、`frozen_40` 三线最小验证

### 4. 当前最准确的结果

- 正式集：
  - `61 -> 62` 条
  - `62 / 62` 成功
  - `average_duration_sec: 0.5551 -> 0.5434`
- `frozen_20`：
  - `20 / 20` 成功
  - `average_duration_sec: 0.5773 -> 0.5611`
- `frozen_40`：
  - `40 / 40` 成功
  - `average_duration_sec: 0.5686 -> 0.5520`

所以这轮当前最准确的表述是：

- 扩容成功
- 三线无回归
- 平均耗时相对 `v64` 小幅改善

### 5. 你现在可以怎么体验

#### 方式 83：直接跑 `task_123` 的单任务修复

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_123.json --policy optimization/policy_versions/improved_v65.json
```

你会看到：

- agent 只修改 `anyio/_backends/_asyncio.py`
- 最终状态为成功
- 对应 patch 会落到当前 run 目录里

#### 方式 84：跑 `improved_v65` 的正式集评测

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v65.json --run-label realissuev65r3 --compare-against-eval logs/summaries/batch_eval_realissuev64r1_001.json --compare-label realissue_step50_r3
```

你会看到：

- 正式任务总数是 `62`
- `success_rate = 1.0`
- `test_pass_rate = 1.0`
- maturity 摘要会自动出现在流水线末尾

#### 方式 85：跑 `improved_v65` 的 `frozen_40` 同集合验证

在仓库根目录执行：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v65.json --run-label frozen40v65r3 --compare-against-eval logs/summaries/batch_eval_frozen40v64r1_001.json --compare-label frozen40_step24_r3
```

你会看到：

- `40 / 40` 成功
- 当前 compare 口径平均耗时是 `0.5520`
- 说明这轮扩容没有把固定冻结集打坏

### 6. 接下来最合理的方向

如果顺着这一轮继续做，优先顺序建议是：

1. 继续推进 `agronholm/anyio#1111`
2. 继续补并发与协程家族的新题
3. 继续推进 `agronholm/anyio#1111`
4. 再决定是否把更多新生态扩容和展示层收口并行推进

## Phase 6 当前最新补充：缺陷覆盖 gap 分析

### 1. 这次新增了什么

这轮新增了一个面向后续扩容决策的分析脚本：

- `scripts/analyze_defect_coverage.py`

它的定位不是再跑一次成功率，而是回答：

- 我们现在到底已经覆盖了哪些缺陷家族
- 哪些家族其实已经很密集
- 哪些家族还明显空白，值得优先去 GitHub 上找题

### 2. 这个脚本怎么工作

它会同时读取：

- `benchmarks/manifests/real_issue_tasks.json`
- `docs/benchmark_registry.md`

然后做两层分析：

1. exact defect type
   - 保留注册表里每条任务的原始缺陷类型描述
2. family 级归一化
   - 把这些近乎全唯一的精细描述压缩成更适合扩容决策的家族：
   - `解析与字符串语义`
   - `序列化与反序列化`
   - `继承、优先级与控制流`
   - `格式化与渲染`
   - `数值与计算语义`
   - `状态机与生命周期`
   - `数据库与事务`
   - `并发与协程`
   - `文件路径与 IO`

### 3. 当前这份分析最重要的结论

基于：

- `logs/summaries/defect_coverage_v2_gap_analysis_002.json`
- `logs/summaries/defect_coverage_v2_gap_analysis_002.md`

当前最重要的结论是：

- 覆盖最重的两类已经是：
  - `解析与字符串语义 = 15`
  - `序列化与反序列化 = 15`
- 当前真正应该优先补的缺口是：
  - `并发与协程 = 0`
  - `文件路径与 IO = 0`
- `继承、优先级与控制流` 虽然已经是强项，但还可以再补 `1` 条，而且更应该去新生态里补

### 4. 这对后续扩容意味着什么

后面如果继续找真实 issue，不建议再优先去做：

- 又一条 tomlkit 序列化小 bug
- 又一条 packaging 解析边界

而更建议优先去找：

- `asyncio / trio / anyio`
- `pathlib / watchfiles / fsspec`

这会让 benchmark 的“家族覆盖面”更健康，而不是只继续堆当前已经很强的语义类型。

### 5. 你现在可以怎么体验这部分

#### 方式 77：重新生成缺陷覆盖分析

在仓库根目录执行：

```bash
python scripts/analyze_defect_coverage.py --output-dir logs/summaries --run-label v2_gap_analysis
```

你会看到：

- 当前正式任务数和生态数
- top covered families
- ecosystem × family 矩阵
- 当前最值得优先补的缺口

#### 方式 78：直接看当前首份可信报告

直接打开：

- `logs/summaries/defect_coverage_v2_gap_analysis_002.md`

你会看到：

- `解析与字符串语义` 与 `序列化与反序列化` 是当前最密集的两类
- `并发与协程` 与 `文件路径与 IO` 当前是明显空白

### 6. 这一步为什么重要

这意味着后续 benchmark 扩容第一次具备了“结构化选题依据”。

从现在开始，我们不只是知道：

- “可以继续找真实 issue”

还知道：

- “应该优先找什么类型、什么生态的真实 issue”

### 7. 如果你要让 Claude 帮你继续查 GitHub，应该给它什么

现在最推荐直接交给 Claude 的不是一段口头说明，而是这两个文件：

1. `docs/issue_sourcing_spec.md`
2. `docs/issue_sourcing_brief_a2.md`

其中：

- `issue_sourcing_spec.md`
  - 负责定义“什么样的 issue 适合做 benchmark”
- `issue_sourcing_brief_a2.md`
  - 负责定义“当前这一个阶段最优先补什么家族和生态”

当前最应该优先找的方向是：

- `并发与协程`
  - 目标仓库：`asyncio / trio / anyio`
- `文件路径与 IO`
  - 目标仓库：`pathlib / watchfiles / fsspec`
- 次优先级：
  - 来自新生态的 `继承、优先级与控制流`

### 8. 现在这一步和后面的自动化是什么关系

这一步虽然还是文档化 brief，但它实际上是在给后续 `C` 线自动化铺路。

因为后面如果继续做：

- `search_candidate_issues.py`
- `screen_candidate.py`
- `--from-candidate` 的半自动脚手架

这些自动化都需要一个清楚的“当前阶段优先级输入”。

而 `docs/issue_sourcing_brief_a2.md` 就是当前最适合当这个输入的材料。

## Phase 6 当前最新补充：候选 issue 半自动搜索入口

### 1. 这次新增了什么

这一轮把 roadmap 里的 `C1` 落成了一个可运行脚本：

- `scripts/search_candidate_issues.py`

它的作用不是自动判题，而是把“去 GitHub 上找候选 issue”从手工浏览页面，推进到可以直接跑一条命令得到结构化候选结果。

### 2. 它现在能做什么

这个脚本当前支持：

- 指定目标仓库 `--repo`
- 指定关键词 `--query`
- 指定 issue 状态 `--state`
- 指定标签过滤 `--labels`
- 控制返回上限 `--limit`
- 输出 `json` 或 `markdown`

同时它会把原始 issue 搜索结果再整理成更适合人工筛选的结构：

- `repo`
- `family`
- `issue`
- `title`
- `url`
- `labels`
- `why_it_fits`
- `expected_target_files`
- `expected_test_shape`
- `estimated_difficulty`
- `risk_notes`
- `recommendation`

### 3. 它和当前 A2 brief 的关系

当前这个脚本本身不直接读取 `docs/issue_sourcing_brief_a2.md`，但它已经和 brief 是同一套思路：

- 先根据仓库和 query 拉候选
- 再按 family、风险、可测试性做结构化整理
- 最后仍由人工决定哪些 issue 真正进入 shortlist

所以你后面最推荐的组合是：

1. 先看 `docs/issue_sourcing_brief_a2.md`
2. 再用 `scripts/search_candidate_issues.py` 去拉目标仓库候选
3. 最后人工筛选进入 shortlist

### 4. 你现在可以怎么体验

#### 方式 79：查看脚本帮助

在仓库根目录执行：

```bash
python scripts/search_candidate_issues.py --help
```

你会看到：

- 支持的 repo / query / labels / state / format / output 参数

#### 方式 80：搜索某个仓库的候选并输出 Markdown

在仓库根目录执行：

```bash
python scripts/search_candidate_issues.py --repo python-jsonschema/jsonschema --labels bug --state closed --limit 10 --format markdown --run-label jsonschema_bug_scan
```

如果 `gh` 认证和网络正常，你会得到：

- 一份 `logs/summaries/candidate_search_*.md`
- 里面已经按更适合 benchmark 筛选的结构排好候选

如果当前想优先补 A2 的 0 覆盖家族，也可以直接启用搜索预设：

```bash
python scripts/search_candidate_issues.py --repo trio/trio --labels bug --state closed --limit 10 --target-family 并发与协程 --format markdown --run-label trio_async_scan
```

或者：

```bash
python scripts/search_candidate_issues.py --repo fsspec/filesystem_spec --labels bug --state closed --limit 10 --target-family "文件路径与 IO" --format markdown --run-label fsspec_path_scan
```

这会自动在基础 `bug` query 上追加更贴近目标家族的关键词，减少手工反复试 query 的成本。

### 5. 当前已知边界

当前脚本的边界也很明确：

- 它只解决“找题”环节
- 不自动更新 `real_world_candidates.json`
- 不自动判题
- 不自动进入 shortlist

也就是说，这一步是半自动，而不是全自动。

但这已经足够把后续的找题效率往前推一大步了。

#### 方式 81：把搜索结果导入候选池

在仓库根目录执行：

```bash
python scripts/import_search_results.py --search-result logs/summaries/candidate_search_textualize_rich_001.json --candidate-file benchmarks/real_world_candidates.json --recommendation high
```

你会看到：

- 导入了多少条搜索结果
- 新建了多少条 candidate
- 更新了多少条已有 candidate
- 每条记录的 `status` 与 `recommendation`

这一步的定位是：

- 把 `search_candidate_issues.py` 的 JSON 结果接入候选池
- 默认以 `imported` 状态进入 `real_world_candidates.json`
- 如果 candidate 已存在，则保留原有人工状态，只追加“重新同步元数据”备注

#### 方式 82：按状态批量筛 imported 候选

在仓库根目录执行：

```bash
python scripts/screen_candidate.py --candidate-file benchmarks/real_world_candidates.json --status imported --limit 5
```

你会看到：

- 本次命中的候选数量
- `screened_count`
- `blocked_count`
- `skipped_count`
- 每条 candidate 的状态变化

如果想非交互式快速验证，也可以统一传入：

```bash
python scripts/screen_candidate.py --candidate-file benchmarks/real_world_candidates.json --status imported --limit 3 --decision s
```

## Phase 6 当前最新补充：`anyio#1111` 进入 ready bug repo

### 1. 这次补了什么

这一轮没有继续停留在 `task_123`，而是把下一条并发候选真正往前推进了一格：

- 候选：`agronholm/anyio#1111`
- 生成任务：`task_124`
- 生成仓库：`benchmarks/repos/anyio_cancellation_spin_repo`

### 2. 当前处在什么状态

- `anyio#1111` 已从 `imported` 推进到 `screened`
- `--dry-run` 已跑通，而且自动命中了：
  - `module_file = anyio/_backends/_asyncio.py`
- 已执行非 `dry-run`，生成了：
  - `benchmarks/tasks/task_124.json`
  - `benchmarks/repos/anyio_cancellation_spin_repo`
- 已把 TODO 脚手架补成 ready 口径最小 bug repo

### 3. 当前 bug 是如何被最小化还原的

这次还原的不是“真实 CPU 打满”本身，而是它背后的核心语义：

- `CancelScope._tasks` 中残留一个已完成 task
- `_deliver_cancellation` 没有先做 `task.done()` 过滤
- 于是会持续 `call_soon` 重排自己
- 在最小复现里，这种无限重排最终表现为受控 `RuntimeError("Detected cancellation spin")`

### 4. 当前测试状态

在仓库根目录执行：

```bash
python -m pytest tests/test__asyncio.py -q
```

当前结果是：

- `1 passed`
- `1 failed`

具体含义：

- 正常路径：
  - `test_pending_task_is_cancelled_once_without_spin`
  - 通过
- 目标回归：
  - `test_completed_task_is_ignored_during_cancellation_delivery`
  - 失败

这说明 `task_124` 已经达到我们熟悉的 ready 口径：

- bug 可复现
- 相邻正常路径保留
- 失败点直接对齐 issue 语义

### 5. 接下来最合理的方向

如果沿这条线继续做，优先顺序应该是：

1. 跑 `improved_v65` 的单任务验证，确认旧策略失败
2. 在 `app/agent/patcher.py` 中补 `_deliver_cancellation` 的规则型修复
3. 新增下一版策略
4. 再做正式集 / frozen 集最小验证

## Phase 6 当前最新补充：`anyio#1111` 已完成 `v65` 失败 / `v66` 成功闭环

### 1. 这次补了什么

这一轮把 `task_124` 从“ready bug repo”继续推进成了真正可纳入正式 benchmark 的任务：

- 在 `app/agent/patcher.py` 中新增了 `improved_v66` 规则
- 新增策略文件：
  - `optimization/policy_versions/improved_v66.json`
- 把 `task_124` 纳入正式 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`

### 2. `improved_v66` 具体修了什么

这条新规则专门处理 `anyio/_backends/_asyncio.py` 里的 `_deliver_cancellation`：

- 旧 bug：
  - 遇到已完成 task 时，只设置 `should_retry = True`
  - 但没有把这个已完成 task 从 `_tasks` 里清掉
  - 结果回调会一直 `call_soon` 自己，进入 cancellation spin
- 新规则：
  - 如果 `task.done()` 为真，就直接从 `_tasks` 中移除
  - 不再触发后续重排

### 3. 我们现在拿到了什么证据

单任务闭环已经满足正式纳入条件：

- 基准 repo 保持带 bug 状态
- 旧策略失败：
  - `improved_v65` 在 `task_124` 上失败
- 新策略成功：
  - `improved_v66` 在 `task_124` 上成功
- patch 命中单文件：
  - `anyio/_backends/_asyncio.py`

对应产物在：

- 旧策略失败：
  - `logs/trajectories/task_124/run_20260613T080448188084Z_1975`
- 新策略成功：
  - `logs/trajectories/task_124/run_20260613T081144377715Z_2752`

### 4. 你现在可以如何体验

如果你想先看“基准 repo 仍然带 bug”：

```bash
cd benchmarks/repos/anyio_cancellation_spin_repo
python -m pytest tests/test__asyncio.py -q
```

你会看到：

- `1 passed`
- `1 failed`

如果你想看 agent 用新策略自动修复：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_124.json --policy optimization/policy_versions/improved_v66.json
```

你会看到这条任务在隔离工作副本里修复成功。

### 5. 接下来最自然的动作

当前最合理的下一步已经不是继续做 `task_124` 单任务，而是：

1. 补 `improved_v66` 的正式集最小验证
2. 补 `frozen_20 / frozen_40` 最小验证
3. 如果三线都稳定，再决定是否补 stability recheck

## Phase 6 当前最新补充：`improved_v66` 已完成三线最小验证

### 1. 这次真正验证了什么

上一节只说明了 `task_124` 的单任务闭环已经打通。

这一轮继续把 `improved_v66` 推进到了 benchmark 口径的三线验证：

- 正式集：
  - `63 / 63`
- `frozen_20`：
  - `20 / 20`
- `frozen_40`：
  - `40 / 40`

### 2. 中间暴露了什么问题

`v66r1` 首轮并不是一次过的。

它先暴露出一个很典型的版本继承链问题：

- `task_123` 在正式集里出现了 `Premature Finish`
- 根因是：
  - `improved_v65` 的 `TaskGroup` 规则没有继续继承到 `improved_v66`
- 修复方式很小：
  - 让 `improved_v66` 继续复用 `_handle_anyio_taskgroup_reentry_guard`

修完后，`task_123` 和 `task_124` 单任务都重新回到成功，`v66r2` 才真正恢复三线全绿。

### 3. `v66` 当前最准确的结论

这一轮不能简单写成“又成功了一版”，更准确的口径是：

- `v66` 扩容成功
- 正式任务数从 `62` 推进到 `63`
- 新增任务是：
  - `task_124`
  - 来源：`agronholm/anyio#1111`
- 正式集、`frozen_20`、`frozen_40` 三线功能都保持全绿

但同时也要保留一个重要提醒：

- 正式集平均耗时：
  - `0.5434 -> 0.5514`
- `frozen_20` 平均耗时：
  - `0.5611 -> 0.5867`
- `frozen_40` 平均耗时：
  - `0.5520 -> 0.5732`

所以当前不能把 `v66` 直接当作新的稳定基线。

### 4. 这对你理解项目阶段有什么帮助

这轮很适合作为 Phase 6 的一个典型例子：

- 功能扩容成功
- 继承链缺陷被快速暴露并修复
- 评测不只看成功率，还看冻结集和时延

也就是说，我们现在已经不只是“会把 bug 修掉”，而是在按 benchmark 基础设施的标准管理策略升级：

- 单任务先验
- 正式集扩容
- 冻结集回归
- 性能复核

### 5. 你现在可以如何体验

如果你想直接看 `v66` 的单任务体验：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_124.json --policy optimization/policy_versions/improved_v66.json
```

如果你想看 `v66` 的正式集最小验证结果：

```bash
python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v66.json --run-label realissuev66r2 --compare-against-eval logs/summaries/batch_eval_realissuev65r3_001.json --compare-label realissue_step52_r2
```

如果你想继续看为什么它慢了一点：

```bash
python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev65r3_001.json --improved-batch-summary logs/summaries/batch_run_realissuev66r2_001.json --run-label realissuev66r2
```

## Phase 6 当前最新补充：`v67` 否证，`v68` 收回性能

### 1. 为什么会有 `v67` / `v68`

在 `v66` 三线功能全绿之后，我们继续做了一轮性能下钻。

证据最后收敛到：

- 热点任务的主要回升来自 `run_tests`
- 更具体地说，是 `run_tests` 里的 subprocess / pytest collection 链路
- 对代表任务做 `pytest` phase / importtime / plugin variant 基准后，看到：
  - `collect-only` 相对 `pytest --version` 稳定多出约 `37` 个模块
  - 某些 pytest 默认插件裁剪能明显降低 wall time

### 2. `v67` 为什么失败

`v67` 当时走的是一个更激进的 runtime 裁剪方向：

- `-p no:debugging`
- `-p no:unraisableexception`
- `-p no:threadexception`

单看局部 benchmark，这组 flag 看起来很有希望。

但一旦放进真实评测闭环，立刻大面积失败：

- 正式集只有 `2 / 63`
- `frozen_20` 变成 `0 / 20`
- `frozen_40` 变成 `0 / 40`

根因也很明确：

- 关闭 `debugging` 插件后
- `_pytest.unittest` 仍会走到 `_pytest.debugging` 里的 tracing 路径
- 结果 `config.getvalue("trace")` 拿不到对应 option
- 直接报：
  - `ValueError: no option named 'trace'`

这说明一件很重要的事：

- “局部基准更快” 不等于 “真实 benchmark 闭环可用”

### 3. `v68` 做了什么

`v68` 保留了同样的修复能力，但把 runtime 裁剪收得更保守：

- 继续保留：
  - `-p no:unraisableexception`
- 只额外追加：
  - `-p no:threadexception`

也就是说，`v68` 不再去碰 `debugging` 插件。

### 4. `v68` 当前的真实结论

这一轮结果是正向的，而且比 `v66` 更完整：

- 正式集：
  - `63 / 63`
- `frozen_20`：
  - `20 / 20`
- `frozen_40`：
  - `40 / 40`

相对 `v66` 的平均耗时变化：

- 正式集：
  - `0.5514 -> 0.5424`
- `frozen_20`：
  - `0.5867 -> 0.5609`
- `frozen_40`：
  - `0.5732 -> 0.5589`

并且 stability recheck 也已经补上：

- `frozen_20`
  - mean = `0.5617`
  - std = `0.0166`
  - conclusion = `stable`
- `frozen_40`
  - mean = `0.5529`
  - std = `0.0031`
  - conclusion = `stable`

### 5. 这轮带来的真正方法论收获

这次不是简单地“找到一个更快 flag”。

真正有价值的是，我们把一条性能优化链路跑完整了：

1. 先看到整体回升
2. 用 duration compare 缩到热点任务
3. 用 trace hotspots 缩到 `run_tests`
4. 用单任务历史确认主要增量在 subprocess
5. 用 pytest phase / importtime / plugin variant 找到可能的 runtime 开关
6. 先用 `v67` 做失败试验，否证过激方案
7. 再收成 `v68` 这种更保守且可落地的版本

### 6. 现在最合理的下一步

当前主线已经从“继续解释 `v66` 为什么慢”切换成：

1. 把 `v69` 视为当前最新扩容版本继续推进
2. 回到真实 issue 扩容
3. 保留 `watchfiles#266` 作为 challenge 题，而不是直接污染正式主集

如果你现在想直接体验 challenge 集入口，可以运行：

```bash
python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v69.json --run-label challengev69
```

这条命令的定位是：

- 单独评测 challenge manifest
- 生成 batch run / batch eval 产物
- 同时继续带出 maturity 摘要，方便和正式集一起看当前全局状态

如果你想继续往 challenge 线推进下一条题，当前优先看：

- [docs/challenge_shortlist.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/challenge_shortlist.md)

当前更准确的状态是：

- `task_126 / samuelcolvin/watchfiles#266` 是当前唯一已落地 challenge 题
- 本地 challenge shortlist 目前为空
- 下一条 challenge 候选需要重新 sourcing
- 不应再把 `dateutil/dateutil#1191`、`PyCQA/isort#1815`、`pallets/click#2402` 视为 challenge 候选，因为它们已经进入正式主集
- 如果要继续找第 `2` 条 challenge 题，优先使用：
  - [docs/challenge_sourcing_brief_a3.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/challenge_sourcing_brief_a3.md)
- 如果你修改了 challenge shortlist，建议顺手运行：
  - `python scripts/validate_challenge_shortlist.py`
- 如果你想跑仓库级总校验入口，直接运行：
  - `python scripts/validate_tasks.py`
  - 它现在也会覆盖 challenge shortlist 与正式主集冲突检查
- 如果你想最快恢复“当前 roadmap 已推进到什么程度”，直接运行：
  - `python scripts/snapshot_roadmap_status.py --run-label roadmap`
  - 它会把正式集、challenge 集、候选池、frozen 和当前主线状态压成一份快照
- 如果你想一键刷新 roadmap 追踪产物，直接运行：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 它会顺序执行总校验、semi-real pipeline audit、maturity 审计和 roadmap 状态快照
- 刷新完成后，如果你只想看最新结果，不必自己找编号文件：
  - 直接看 `logs/summaries/roadmap_tracking_latest_refresh.json`
  - 或 `logs/summaries/roadmap_tracking_latest_refresh.md`
  - 当前 latest summary 还会补出相对上一次 latest 的高信号变化摘要：
    - `previous_latest_summary_json_path`
    - `changed_fields`
    - `delta.field_changes`
    - `refresh_outcome`
    - `history_overview`
  - 最适合快速判断：
    - 这次 refresh 是否真的有推进
    - 推进主要落在正式任务数、生态数、候选数、frozen 数量还是 streak
    - 以及这次结果更像：
      - 首次快照
      - 无实质变化
      - 正向推进
      - 需要关注的回退
  - 现在 latest markdown 的 `Outputs` 里还会显式挂出：
    - `history_summary_json_path / md_path`
    - `action_board_json_path / md_path`
    - `status_card_json_path / md_path`
  - 当前如果推进发生在“候选状态流转”而不是“正式集任务数变化”，latest 也会直接暴露：
    - `screened_candidate_count`
    - `imported_candidate_count`
    - `challenge_shortlist_candidate_count`
    - `challenge_next_candidate_issue_ref`
  - 同时 `## Fast Paths` 会直接提示三条最短阅读路径：
    - `status_card`：适合 30 秒内接管当前状态
    - `action_board`：适合直接开始执行下一步动作
    - `history_summary`：适合回看最近几轮 refresh 趋势
  - 如果你不想自己从日志目录里找文件，先打开 latest markdown，再按 `Outputs + Fast Paths` 跳转通常最快
  - 如果你想看连续几轮 refresh 的走势，而不是只看当前 latest：
    - 直接看 `logs/summaries/roadmap_tracking_history_latest_refresh.json`
    - 或 `logs/summaries/roadmap_tracking_history_latest_refresh.md`
  - 它会汇总：
    - `total_refresh_count`
    - `category_counts`
    - `recent_no_material_change_streak`
    - 最近几轮 refresh 的 outcome 时间线
    - `advice`
  - 如果你不想自己解释 history，优先读：
    - `advice.category`
    - `advice.summary`
    - `advice.recommended_actions`
  - 如果你想直接看“现在该做什么”，优先打开：
    - `logs/summaries/roadmap_action_board_latest_refresh.json`
    - `logs/summaries/roadmap_action_board_latest_refresh.md`
  - 它会把：
    - 当前 latest 状态
    - history advice
    - 当前 top priorities
    统一收口到一个稳定入口
  - 当前每个 priority 还会直接带：
    - `commands`
    - `docs`
    - `done_signal`
    - `when_to_refresh`
    - `expected_tracking_signals`
  - 也就是说，如果只是想恢复工作并立刻开始推进，通常可以直接从 action board 抄命令执行
  - 做完一轮动作后，也可以直接按 `when_to_refresh` 判断什么时候该回到 tracking 入口
  - refresh 之后如果想快速判断“这一轮有没有真的动到关键口径”，优先对照 `expected_tracking_signals`
  - 如果你只是想在 30 秒内接管当前状态，优先看：
    - `logs/summaries/roadmap_status_card_latest_refresh.json`
    - `logs/summaries/roadmap_status_card_latest_refresh.md`
  - status card 只保留最小必要信息：
    - 当前 headline
    - history advice
    - 连续无变化 streak
    - `candidate / screened / imported`
    - challenge shortlist 当前是否已有下一候选
    - 当前 top priority
    - 第一条命令

## Phase 6 当前最新补充：`anyio#1113` 进入 ready bug repo 阶段

### 1. 这次推进了什么

这轮继续沿并发与协程主线前进，把：

- `agronholm/anyio#1113`

从：

- `imported`

推进到了：

- `screened`
- ready 口径最小 bug repo

新增产物：

- `benchmarks/tasks/task_125.json`
- `benchmarks/repos/anyio_check_cancelled_repo`

### 2. 这次具体补了什么

这次不是只停在自动脚手架，而是把 repo 继续补成了最小可验证形态：

- `anyio/from_thread.py`
  - 补成最小 backend 分派模型
  - 保留 `asyncio` backend 下 `CancelledError` 泄漏的 bug
  - 保留 `trio` backend 作为对照正常路径
- `tests/test_from_thread.py`
  - 补成 2 条稳定测试
  - `trio` 路径通过
  - `asyncio` 目标回归失败
- `anyio/pytest_plugin.py`
  - 新增最小占位插件
  - 避免本地 `anyio` 包遮住环境安装包后，pytest 自动加载入口点直接失败

这样后续就可以直接进入：

- 旧策略单任务失败
- 新策略单任务成功
- 再决定是否正式接入

### 3. 这轮顺手补了什么泛化能力

为了让 `anyio#1113` 这种 issue 更容易落脚手架，这轮还增强了：

- `scripts/scaffold_semi_real_task.py`

新增能力是：

- 当 issue 文本里没有显式文件路径
- 但出现了 Python 符号名，例如：
  - `from_thread.check_cancelled`
- 脚本现在会尝试把它自动还原成模块文件路径：
  - `anyio/from_thread.py`

这不是只对 `anyio#1113` 有用，后面其它“正文只有符号名”的 issue 也能直接受益。

### 4. 你现在可以怎么体验

#### 方式 86：看这条候选当前的脚手架任务

直接打开：

- `benchmarks/tasks/task_125.json`

你会看到：

- 当前任务已经带：
  - `expected_failure_test = test_asyncio_backend_does_not_leak_cancelled_error`
  - `repo_scaffold_status = ready`
- 自动推断的 target files 是：
  - `anyio/from_thread.py`
  - `tests/test_from_thread.py`

#### 方式 87：重新体验这条候选的 dry-run 自动推断

在仓库根目录执行：

```bash
python scripts/scaffold_semi_real_task.py --from-candidate agronholm_anyio_issue_1113 --candidate-file benchmarks/real_world_candidates.json --semi-repo-name anyio_check_cancelled_repo --dry-run
```

你会看到：

- `module_file = anyio/from_thread.py`
- `test_file = tests/test_from_thread.py`

#### 方式 88：查看这次实际落盘的脚手架 repo

直接打开：

- `benchmarks/repos/anyio_check_cancelled_repo`

你会看到：

- 当前已经不是 TODO 脚手架
- 而是一个 ready 口径最小 bug repo：
  - `trio` 对照路径通过
  - `asyncio` 目标回归稳定失败

### 5. 当前最准确的下一步

如果下一轮继续沿这条线推进，最合理的顺序是：

1. 先验证旧策略在 `task_125` 上单任务失败
2. 再判断是否需要新增一个 `improved_v69`
3. 如果新版本单任务成功，再补正式集与冻结集验证
4. `task_126` 这类保守题则优先进入 challenge manifest，再视代表性决定是否升格

## Phase 6 当前最新补充：`v69` 接入 `task_125`

### 1. 这次推进了什么

这轮把：

- `agronholm/anyio#1113`

从：

- ready bug repo

继续推进到了：

- `improved_v68` 单任务失败
- `improved_v69` 单任务成功
- 正式 manifest 接入

新增产物：

- `optimization/policy_versions/improved_v69.json`

### 2. `v69` 做了什么

这轮新增的是一条很小的规则型修复能力：

- 目标文件：
  - `anyio/from_thread.py`
- 修复语义：
  - 让 `asyncio` backend 下的 `CancelledError`
  - 也像 `trio` 对照路径一样，通过传入的 `cancel scope` 被吃掉

而 runtime 配置仍然保持和 `v68` 一样：

- `-p no:unraisableexception`
- `-p no:threadexception`

也就是说，这轮尽量只新增一个功能变量，不额外改性能开关。

### 3. 这轮验证结果

单任务：

- `improved_v68`
  - `task_125` 失败
- `improved_v69`
  - `task_125` 成功

正式集：

- `64 / 64`
- `average_duration_sec: 0.5424 -> 0.5656`

`frozen_20`：

- `20 / 20`
- `average_duration_sec: 0.5609 -> 0.5975`

`frozen_40`：

- `40 / 40`
- `average_duration_sec: 0.5589 -> 0.5861`

### 4. 这轮最准确的口径

这轮已经证明：

- `task_125` 确实值得正式接入
- `v69` 功能上完成了从 `63` 到 `64` 条正式任务的扩容
- 且冻结集没有功能回归

但这轮也同时说明：

- 相比 `v68`
- `v69` 的平均耗时在三条线上都有回升

所以当前最准确的结论不是“新的稳定基线已经产生”，而是：

- `v69` 是当前最新扩容成功版本
- `frozen_20 / frozen_40` 的 stability recheck 已补齐，且结论都是 `stable`
- 性能仍需继续复核

### 5. 已经补上的性能定位结论

为了避免只凭直觉判断，这一轮又补了 `v68 -> v69` 的 batch 时延分析和 trace 热点分析。

当前已经确认：

- 正式集公共 `63` 条任务平均增量：`+0.0241s`
- `frozen_20` 公共 `20` 条任务平均增量：`+0.0366s`
- `frozen_40` 公共 `40` 条任务平均增量：`+0.0272s`

而且这次回升不是只出在新增 `task_125` 上。

正式集 trace 热点显示：

- 第一主因仍然是 `run_tests`
  - 总增量：`+0.8885s`
- 第二主因是 `search_code`
  - 总增量：`+0.5797s`

这意味着如果下一步要做 `v70`，更合理的目标不是继续扩题，而是：

- 保留 `task_125` 的修复能力
- 尽量把 `run_tests` 和 `search_code` 的回升一起收回来

### 6. `search_code` 这条线现在已经明确到什么程度

这轮我又补了一个专项分析脚本：

- `scripts/analyze_search_code_regressions.py`

它直接对比两次 batch run 里每个任务的：

- 搜索查询词
- 命中数
- 命中文件数
- 每次 `search_code` 的耗时

当前已经确认：

- 公共 `63` 条任务里，`63 / 63` 的查询签名完全一样
- 其中 `56 / 63` 个任务是在“查询不变”的情况下变慢
- `search_code` 总增量 `+0.5797s` 中，有 `+0.5614s` 来自第一条搜索

这说明现在更像是：

- `search_code` 执行层的冷启动或抖动问题

而不是：

- planner 生成了更差的搜索词
- 搜索轮数变多了
- 命中范围系统性扩大了

### 7. 冷启动 / 热启动基准又说明了什么

我又补了一个新脚本：

- `scripts/benchmark_search_code_cold_warm.py`

它会直接复用真实 trace 里的搜索词序列，反复在同一个 repo 上跑 `search_code`，看：

- 第 1 轮冷启动
- 后续多轮热启动

之间到底差多少。

当前在两个真实热点任务上的结果是：

- `task_123`
  - `cold_total_duration_sec = 0.0037`
  - `warm_mean_total_duration_sec = 0.0036`
- `task_119`
  - `cold_total_duration_sec = 0.0009`
  - `warm_mean_total_duration_sec = 0.0006`

也就是说，在当前环境里单独把 `search_code` 拿出来跑时，并没有复现之前 batch run 里看到的 `20ms ~ 60ms` 级别回升。

所以当前更稳妥的理解是：

- `search_code` 仍然是一个可疑线索
- 但它暂时还不像一个已经被稳定复现的“函数本体退化”
- 更像是 batch run 当时上下文里的噪声、冷态或调度因素

### 8. 现在怎么继续把这个判断做实

我又补了一个更直接的复核入口：

- `scripts/recheck_policy_pair_tasks.py`

它会对同一组热点任务重复运行两个策略版本，然后同时汇总：

- 总耗时
- `search_code_total_duration_sec`
- `run_tests_total_duration_sec`

如果你想继续推进这一条，可以先跑：

```bash
python scripts/recheck_policy_pair_tasks.py --task benchmarks/tasks/task_123.json --task benchmarks/tasks/task_119.json --task benchmarks/tasks/task_097.json --task benchmarks/tasks/task_034.json --baseline-policy optimization/policy_versions/improved_v68.json --improved-policy optimization/policy_versions/improved_v69.json --repetitions 3 --run-label v68_v69_hotspots
```

它最直接回答的问题是：

- `v68 -> v69` 的回升现在还能不能稳定复现
- 如果不能，是不是该把 `search_code` 降级为次要线索
- 下一步应不应该把 `run_tests` 重新升为 `v70` 主攻方向

### 9. 当前这条复核已经跑出了什么

我已经用这条脚本对下面这组热点任务跑了一轮真实复核：

- `task_123`
- `task_119`
- `task_097`
- `task_034`

产物：

- `logs/summaries/policy_pair_recheck_v68_v69_hotspots_001.json`
- `logs/summaries/policy_pair_recheck_v68_v69_hotspots_001.md`

当前聚合结果是：

- `average_duration_delta_sec = -0.0149`
- `average_search_code_delta_sec = -0.0095`
- `average_run_tests_delta_sec = -0.0041`
- `reproduced_search_code_task_count = 0 / 4`
- `reproduced_run_tests_task_count = 1 / 4`

这说明在当前环境里：

- 没有复现“`v69` 的 `search_code` 普遍更慢”
- 甚至这组热点任务整体上是 `v69` 略快

所以当前更稳妥的判断已经更新为：

- `search_code` 回升更像当时 batch run 里的噪声线索
- 它暂时不应该再被当作 `v70` 的首要优化目标
- 下一步应把重点重新切回 `run_tests`

### 10. 为了推进 `v70`，诊断脚本现在也升级了

我刚把下面三条 `pytest` 诊断脚本都补成了支持 `--policy`：

- `scripts/benchmark_pytest_phases.py`
- `scripts/benchmark_pytest_importtime.py`
- `scripts/benchmark_pytest_plugin_variants.py`

这一步很关键，因为之前这些脚本虽然能跑，但没有真正带上策略版本里的 `pytest_additional_flags`，所以它们不能严格解释 `v68 / v69` 这种 runtime 级差异。

现在你可以直接按策略版本做诊断，例如：

```bash
python scripts/benchmark_pytest_phases.py --task benchmarks/tasks/task_123.json --repo-root . --policy optimization/policy_versions/improved_v69.json --repetitions 3 --benchmark-label task123_v69_phases
```

```bash
python scripts/benchmark_pytest_importtime.py --task benchmarks/tasks/task_123.json --repo-root . --policy optimization/policy_versions/improved_v69.json --repetitions 3 --benchmark-label task123_v69_importtime
```

```bash
python scripts/benchmark_pytest_plugin_variants.py --task benchmarks/tasks/task_123.json --repo-root . --policy optimization/policy_versions/improved_v69.json --repetitions 3 --benchmark-label task123_v69_plugins
```

所以从现在开始，`v70` 的性能回收已经不只是“怀疑 run_tests”，而是可以基于真实策略版本做分阶段和插件层的可复验分析。

### 11. `run_tests` 现在又被拆得更细了

我又把双策略复跑脚本扩了一步：

- `scripts/recheck_policy_pair_tasks.py`

现在除了总 `run_tests` 时长，还会额外记录：

- `run_tests_first_duration_sec`
- `run_tests_second_duration_sec`

也就是把：

- 修复前测试
- 修复后测试

拆开看。

当前这组热点任务的真实结果在：

- `logs/summaries/policy_pair_recheck_v68_v69_hotspots_split_001.json`

聚合结论是：

- `average_run_tests_delta_sec = -0.018`
- `average_run_tests_first_delta_sec = -0.0117`
- `average_run_tests_second_delta_sec = -0.0064`

这说明在当前环境里：

- `v69` 并没有在 `run_tests` 总体上更慢
- 如果要继续下钻，第一次 `run_tests` 对应的 pre-test / collect 链路更值得优先盯

### 12. 现在连 benchmark 摘要也可以直接做双策略 compare

我又补了一个更省上下文的小工具：

- `scripts/compare_pytest_policy_pair.py`

它可以直接拿两份同任务的策略版摘要做对照，目前支持：

- `pytest phases`
- `pytest importtime`

比如现在已经跑出的真实 compare 包括：

- `pytest_policy_pair_task123_phase_v68_v69_001.json`
- `pytest_policy_pair_task123_importtime_v68_v69_001.json`
- `pytest_policy_pair_task119_phase_v68_v69_001.json`
- `pytest_policy_pair_task119_importtime_v68_v69_001.json`

从这四份结果看，当前更稳妥的理解是：

- `task_123` 确实有一点首轮 full run 波动，但 phase 差异总体不大
- `task_123` importtime 虽然有 `+5753us` 的 collect import self 增量，但 wall time 没有同步变差
- `task_119` 的 phase / importtime 差异基本接近噪声

所以目前证据还不支持“立刻为了 `v70` 去改 runtime 实现”，更像是应该继续保持：

- 先积累更多任务上的策略版诊断 compare
- 再判断是否存在一致性的系统回升

## Phase 6 当前最新补充：环境基线快照 `B4` 首版落地

### 1. 这次补了什么

这一轮不是继续扩题，而是把 `docs/v2_roadmap.md` 里原本挂起的 `B4` 补成了可运行能力：

- 新增：
  - `scripts/snapshot_env_baseline.py`
- 增强：
  - `scripts/analyze_duration_regressions.py --env-baseline`

它们解决的问题是：

- 当某一轮 `frozen_20 / frozen_40` 或正式集平均耗时回升时
- 我们不再只能凭经验猜“是环境慢了”还是“策略真的慢了”
- 现在至少可以先用一组固定轻量命令采环境基线，再把这份漂移信号带回时延 compare

### 2. 当前实现细节

环境基线快照脚本当前会重复采样两类固定命令：

- `python -c "pass"`
- `python -m pytest --version`

默认每条命令采样 `10` 次，并输出：

- `mean_sec`
- `min_sec`
- `max_sec`
- `std_sec`
- 原始 `samples_sec`

落盘位置：

- `logs/env_baselines/env_baseline_*.json`
- `logs/env_baselines/env_baseline_*.md`

如果你再传一份旧快照给 `--compare-against`，它还会自动算：

- `mean_delta_sec`
- `max_delta_sec`
- `mean_ratio`
- 每条命令各自的漂移情况

### 3. 它和现有性能分析怎么接

现在 `scripts/analyze_duration_regressions.py` 多了一个可选参数：

- `--env-baseline`

当传入的环境快照里已经包含 comparison 段时，时延 compare 会额外给出：

- `env_adjusted_common_average_delta_sec`

你可以把它理解成：

- 原始任务集平均回升
- 减去当前环境本身相对参考环境的平均漂移

它不是严格的因果归因器，但已经足够把“可能只是环境更慢了”这类情况先单独标出来。

### 4. 你现在可以怎么体验

先采一份当前环境基线：

```bash
python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines
```

如果后面怀疑环境漂移，再基于旧快照做对比：

```bash
python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines --compare-against logs/env_baselines/env_baseline_xxx.json
```

然后把这份快照带回时延 compare：

```bash
python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev65r3_001.json --improved-batch-summary logs/summaries/batch_run_realissuev66r2_001.json --run-label realissuev66r2 --env-baseline logs/env_baselines/env_baseline_xxx.json
```

### 5. 这一轮对 roadmap 的意义

这轮的价值不在于直接多过一题，而在于：

1. `B4` 不再只是 roadmap 里的想法，而是已经有脚本、测试和落盘产物
2. 性能治理链路现在从：
   - compare
   - trace hotspots
   - pytest phase / importtime / plugin variants
   继续补到了：
   - environment baseline
3. 后续如果再出现无法解释的时延回升，我们会更容易判断：
   - 是机器环境在抖
   - 还是策略版本真的引入了额外开销

## Phase 6 当前最新补充：`task_097 / task_034` 的策略版 pytest compare

### 1. 这次补了什么

我继续沿当前最优先的性能复核主线，把另外两个热点任务也纳入了真实策略版 compare：

- `task_097`
- `task_034`

这次没有改 runtime，也没有生成新的 `improved_v70`。

我做的是更稳妥的一步：继续积累 `v68 / v69` 的真实对照证据，避免因为样本太少而误判。

### 2. 这次怎么做的

对每个任务都补了两类基准：

- `pytest phases`
- `pytest importtime`

并且两类基准都分别对比：

- `improved_v68`
- `improved_v69`

对应产物包括：

- `pytest_policy_pair_task097_phase_v68_v69_001.json`
- `pytest_policy_pair_task097_importtime_v68_v69_001.json`
- `pytest_policy_pair_task034_phase_v68_v69_001.json`
- `pytest_policy_pair_task034_importtime_v68_v69_001.json`

### 3. 当前结果怎么看

`task_097` 的结果是：

- phase 侧：
  - `pytest_startup_over_python_delta_sec = -0.0051`
  - `collect_over_pytest_startup_delta_sec = +0.0114`
  - `full_over_collect_delta_sec = +0.0098`
- importtime 侧：
  - `collect_wall_delta_sec = -0.0182`
  - `collect_import_self_delta_us = -12204`
  - `collect_unique_module_delta = 0`

这说明它的信号有点“拧巴”：

- `collect / full` 看起来略慢
- 但 importtime 又变轻了

`task_034` 的结果是：

- phase 侧：
  - `pytest_startup_over_python_delta_sec = -0.0539`
  - `collect_over_pytest_startup_delta_sec = +0.0446`
  - `full_over_collect_delta_sec = +0.0093`
- importtime 侧：
  - `collect_wall_delta_sec = +0.0277`
  - `collect_import_self_delta_us = +14898`
  - `collect_unique_module_delta = 0`

这个任务就更接近“collect 确实变重了”的信号。

### 4. 当前最稳妥的结论

把前面的 `task_123 / task_119` 再加上这次的 `task_097 / task_034` 放在一起看，当前更稳妥的结论是：

- 还看不到单一、稳定、跨任务一致的主因
- `collect` 链路仍然是最值得继续扩样本的方向
- 但现阶段还不应该只凭这几组结果就直接做 `v70` runtime 改动

也就是说，这一步的价值不是“立刻找到答案”，而是把我们从“凭感觉怀疑”推进到了“知道该继续盯哪一段链路”。

### 5. 你现在可以怎么体验

#### 方式 96：自己重跑 `task_097` 的策略版 compare

```bash
python scripts/benchmark_pytest_phases.py --task benchmarks/tasks/task_097.json --repo-root . --policy optimization/policy_versions/improved_v68.json --repetitions 3 --benchmark-label task097_v68_phases_policy
python scripts/benchmark_pytest_phases.py --task benchmarks/tasks/task_097.json --repo-root . --policy optimization/policy_versions/improved_v69.json --repetitions 3 --benchmark-label task097_v69_phases_policy
python scripts/compare_pytest_policy_pair.py --baseline-summary logs/summaries/pytest_phases_task097_v68_phases_policy_001.json --improved-summary logs/summaries/pytest_phases_task097_v69_phases_policy_001.json --compare-label task097_phase_v68_v69
```

#### 方式 97：自己重跑 `task_034` 的策略版 importtime compare

```bash
python scripts/benchmark_pytest_importtime.py --task benchmarks/tasks/task_034.json --repo-root . --policy optimization/policy_versions/improved_v68.json --repetitions 3 --benchmark-label task034_v68_importtime_policy
python scripts/benchmark_pytest_importtime.py --task benchmarks/tasks/task_034.json --repo-root . --policy optimization/policy_versions/improved_v69.json --repetitions 3 --benchmark-label task034_v69_importtime_policy
python scripts/compare_pytest_policy_pair.py --baseline-summary logs/summaries/pytest_importtime_task034_v68_importtime_policy_001.json --improved-summary logs/summaries/pytest_importtime_task034_v69_importtime_policy_001.json --compare-label task034_importtime_v68_v69
```

#### 方式 98：查看四任务对照后应该记住什么

如果你只想抓住这一轮最关键的判断，那就是：

1. `task_123 / task_119 / task_097 / task_034` 还没有把主因收敛成一个单点。
2. 当前最值得继续加样本的是 `collect` 链路，而不是重新把 `search_code` 升回主线。
3. 在证据继续变强之前，不要为了“赶紧做 v70”而过早改 runtime。

## Phase 6 当前最新补充：多任务策略版 compare 现在可以直接看 cohort

### 1. 这次补了什么

前面我们已经能做：

- 单任务 `pytest phases` compare
- 单任务 `pytest importtime` compare

但如果每次都要手工读一堆 `pytest_policy_pair_*.json`，后面继续扩样本会越来越费劲。

所以我这次补了一个更适合长期追踪的收口工具：

- `scripts/analyze_pytest_policy_pair_cohort.py`

它的作用是把多份同类型 compare 结果直接聚合成 cohort 摘要。

### 2. 它解决了什么问题

它最直接回答的是：

- 多个任务平均下来，哪个 delta 仍然偏正？
- 有多少任务是在同一个方向上变慢？
- 当前 evidence 是“已经收敛”还是“仍然互相打架”？

这一步很重要，因为 roadmap 当前强调的是“持续追踪”，而不是“单次看一题就下结论”。

### 3. 当前真实 cohort 结果

我已经用这条新脚本把 4 个热点任务的真实策略版 compare 聚合了一轮：

- `task_123`
- `task_119`
- `task_097`
- `task_034`

phase cohort 的结果是：

- `average_pytest_startup_over_python_delta_sec = -0.0139`
- `average_collect_over_pytest_startup_delta_sec = +0.0118`
- `average_full_over_collect_delta_sec = +0.0054`
- `collect_slower_task_count = 2 / 4`
- `full_slower_task_count = 3 / 4`

importtime cohort 的结果是：

- `average_collect_wall_delta_sec = +0.0026`
- `average_collect_import_self_delta_us = +1197`
- `collect_wall_slower_task_count = 2 / 4`
- `collect_import_self_higher_task_count = 2 / 4`

### 4. 这组 cohort 应该怎么理解

当前更稳妥的理解是：

- phase 聚合下，`collect` 仍然偏正向变慢，说明这条线还值得继续盯
- 但 importtime 聚合已经明显收敛到接近噪声
- 所以现在还不能把 `v68 -> v69` 的回升简单讲成“pytest import 链稳定恶化”

也就是说，我们离“知道该盯哪里”更近了一步，但还没到“可以放心改 runtime”的程度。

### 5. 你现在可以怎么体验

#### 方式 99：直接看 4 任务 phase cohort

```bash
python scripts/analyze_pytest_policy_pair_cohort.py --compare-summary logs/summaries/pytest_policy_pair_task123_phase_v68_v69_001.json --compare-summary logs/summaries/pytest_policy_pair_task119_phase_v68_v69_001.json --compare-summary logs/summaries/pytest_policy_pair_task097_phase_v68_v69_001.json --compare-summary logs/summaries/pytest_policy_pair_task034_phase_v68_v69_001.json --cohort-label v68_v69_hotspots_phase
```

#### 方式 100：直接看 4 任务 importtime cohort

```bash
python scripts/analyze_pytest_policy_pair_cohort.py --compare-summary logs/summaries/pytest_policy_pair_task123_importtime_v68_v69_001.json --compare-summary logs/summaries/pytest_policy_pair_task119_importtime_v68_v69_001.json --compare-summary logs/summaries/pytest_policy_pair_task097_importtime_v68_v69_001.json --compare-summary logs/summaries/pytest_policy_pair_task034_importtime_v68_v69_001.json --cohort-label v68_v69_hotspots_importtime
```

#### 方式 101：这一步最该记住什么

如果你只记一个结论，那就是：

1. 现在我们已经不只是在看单任务 compare，而是在看跨任务聚合。
2. `collect` 仍然值得继续追，但 importtime 聚合暂时还不支持“稳定恶化”的说法。
3. 所以下一步仍然应该继续扩样本，而不是急着产出 `v70`。

## Phase 6 当前最新补充：多任务策略版 pytest 对照现在可以一键跑 matrix

### 1. 这次补了什么

前面我们已经能做：

- 单任务 benchmark
- 单任务 compare
- 多任务 cohort

但真正持续追踪 roadmap 时，还是要手工敲很多条命令。

所以这次我又把整条链路往前收了一步，新增：

- `scripts/run_pytest_policy_pair_matrix.py`

它会一把串起：

- `pytest phases benchmark`
- `pytest importtime benchmark`
- 单任务 compare
- 多任务 cohort

### 2. 它的意义是什么

这一步的意义很直接：

- 以后我们再补 2 到 4 个热点任务时，不需要重新拼十几条命令
- 追踪逻辑会更稳定
- 也更符合“把 roadmap 作为持续 goal 追踪”的方式

### 3. 当前真实 matrix 结果

我已经用下面这组任务跑了一轮真实 matrix：

- `task_123`
- `task_119`
- `task_097`
- `task_034`

phase cohort 的结果是：

- `average_pytest_startup_over_python_delta_sec = +0.0101`
- `average_collect_over_pytest_startup_delta_sec = -0.0235`
- `average_full_over_collect_delta_sec = +0.0159`
- `startup_slower_task_count = 4 / 4`
- `collect_slower_task_count = 0 / 4`
- `full_slower_task_count = 3 / 4`

importtime cohort 的结果是：

- `average_collect_wall_delta_sec = -0.0047`
- `average_collect_import_self_delta_us = +1672`
- `collect_wall_slower_task_count = 1 / 4`
- `collect_import_self_higher_task_count = 2 / 4`

### 4. 这轮结果应该怎么理解

这一步很关键，因为它把我们前面的判断又校正了一次。

现在更稳妥的理解已经变成：

- `collect` 并没有表现成“跨任务普遍更慢”
- 更值得继续观察的反而是：
  - `pytest startup`
  - `full run`
- `importtime` 聚合整体也没有支持稳定恶化

也就是说，这一轮 matrix 让我们少走了一步弯路：

- 现阶段不应该继续过度押注“collect 就是主因”
- 更不应该急着直接做 `v70`

### 5. 你现在可以怎么体验

#### 方式 102：直接一键跑 4 任务 matrix

```bash
python scripts/run_pytest_policy_pair_matrix.py --task benchmarks/tasks/task_123.json --task benchmarks/tasks/task_119.json --task benchmarks/tasks/task_097.json --task benchmarks/tasks/task_034.json --repo-root . --baseline-policy optimization/policy_versions/improved_v68.json --improved-policy optimization/policy_versions/improved_v69.json --repetitions 3 --matrix-label v68_v69_hotspots_matrix
```

#### 方式 103：这一步最该记住什么

如果你只记一个结论，那就是：

1. 现在我们已经能一键复跑多任务策略版 pytest 对照。
2. 这轮更完整编排下，`startup` 和 `full run` 比 `collect` 更值得继续观察。
3. 所以下一步仍然应该继续扩样本或重复 matrix，而不是急着做 `v70`。

## Phase 6 当前最新补充：历史 run_tests 热点集合也已经跑进 matrix

### 1. 这次为什么还要再跑一轮

前一轮 matrix 虽然已经把：

- `task_123`
- `task_119`
- `task_097`
- `task_034`

串起来了，但它更像“当前热点 + 代表任务”的混合集。

如果我们真的要判断 `v68 -> v69` 的性能差异该不该做成 `v70`，还是得回到最早那批真正把 `run_tests` 拉高的历史热点任务：

- `task_034`
- `task_036`
- `task_038`
- `task_040`

### 2. 这轮 matrix 的结果

phase cohort 的结果是：

- `average_pytest_startup_over_python_delta_sec = +0.004`
- `average_collect_over_pytest_startup_delta_sec = -0.0047`
- `average_full_over_collect_delta_sec = -0.0152`
- `startup_slower_task_count = 2 / 4`
- `collect_slower_task_count = 2 / 4`
- `full_slower_task_count = 1 / 4`

importtime cohort 的结果是：

- `average_collect_wall_delta_sec = +0.0024`
- `average_collect_import_self_delta_us = +8255`
- `collect_wall_slower_task_count = 1 / 4`
- `collect_import_self_higher_task_count = 3 / 4`

### 3. 这一步最关键的含义

这一轮很关键，因为它又把结论往“更保守、更真实”拉了一步。

现在更准确的理解是：

- `startup` 只有轻微正向
- `collect` 方向重新分裂
- `full run` 甚至整体更快
- `importtime` 有一点偏正，但还不够单独定责

所以到这一步，最应该记住的不是“终于找到主因了”，而是：

- 我们还没有稳定的单主因
- 继续扩样本和重复 matrix，比急着做 `v70` 更稳

### 4. 你现在可以怎么体验

#### 方式 104：直接跑历史热点集合 matrix

```bash
python scripts/run_pytest_policy_pair_matrix.py --task benchmarks/tasks/task_034.json --task benchmarks/tasks/task_036.json --task benchmarks/tasks/task_038.json --task benchmarks/tasks/task_040.json --repo-root . --baseline-policy optimization/policy_versions/improved_v68.json --improved-policy optimization/policy_versions/improved_v69.json --repetitions 3 --matrix-label v68_v69_run_tests_hotspots_matrix
```

#### 方式 105：这一步最该记住什么

如果你只记一个结论，那就是：

1. 历史热点集合没有把主因稳定收敛到 `startup`、`collect` 或 `full run` 中的任何一条。
2. `importtime` 虽然有一点偏正，但也还不够强。
3. 所以下一步依然应该继续扩样本或重复 matrix，而不是急着做 `v70`。

## Phase 6 当前最新补充：三轮 matrix 已经收口成 matrix set

### 1. 这次又往前推进了什么

前面我们已经能看：

- 单任务 compare
- 单轮 matrix

但如果要真的把 roadmap 当成持续追踪的目标，还是需要一个更高层的入口，把多轮 matrix 的判断统一起来。

所以这次又新增了：

- `scripts/analyze_pytest_policy_pair_matrix_set.py`

它的作用是：直接把多轮 matrix summary 再向上聚合。

### 2. 当前三轮 matrix 放在一起后的结果

这次聚合了三轮：

- `v68_v69_hotspots_matrix`
- `v68_v69_run_tests_hotspots_matrix`
- `v68_v69_control_group_matrix`

聚合后的结果是：

- `average_startup_delta_sec = +0.0051`
- `average_collect_delta_sec = -0.0089`
- `average_full_delta_sec = -0.0023`
- `average_collect_wall_delta_sec = +0.0032`
- `average_collect_import_self_delta_us = +6506.3333`
- `startup_positive_matrix_count = 3 / 3`
- `collect_positive_matrix_count = 1 / 3`
- `full_positive_matrix_count = 1 / 3`
- `collect_import_positive_matrix_count = 3 / 3`

### 3. 这一轮最重要的结论

到这一步，当前最稳妥的理解终于比前面更清楚了：

- 真正持续偏正的是 `pytest startup`
- `collect` 并没有继续表现成稳定主因
- `full run` 也没有继续稳定正向
- `importtime` 有一点偏正，但更像辅助观察项

所以如果我们还继续沿性能主线推进，当前最合理的优先级应该是：

1. 先看 `pytest startup`
2. 再把 `importtime` 当辅助证据
3. 暂时不要再把 `collect` 当主嫌疑点

### 4. 这对下一步意味着什么

这一步其实已经在帮我们做一个节奏判断：

- 如果后面再补 1 到 2 轮 matrix，`startup` 这条线继续强化
  - 那就值得做一个更小粒度的 startup 定位实验
- 如果后面再补 1 到 2 轮后，趋势还是不继续强化
  - 那就应该暂时把性能追因降权
  - 切回 A 线继续扩真实 issue

### 5. 你现在可以怎么体验

#### 方式 106：直接跑三轮 matrix 的总聚合

```bash
python scripts/analyze_pytest_policy_pair_matrix_set.py --matrix-summary logs/summaries/pytest_policy_pair_matrix_v68_v69_hotspots_matrix_001.json --matrix-summary logs/summaries/pytest_policy_pair_matrix_v68_v69_run_tests_hotspots_matrix_001.json --matrix-summary logs/summaries/pytest_policy_pair_matrix_v68_v69_control_group_matrix_001.json --set-label v68_v69_triage
```

#### 方式 107：这一步最该记住什么

如果你只记一个结论，那就是：

1. 到当前为止，跨三轮 matrix 最稳定偏正的是 `pytest startup`。
2. `collect` 已经不再适合作为当前第一嫌疑点。
3. 下一步要么继续补 1 到 2 轮 matrix 验证 startup，要么就暂时切回 A 线扩题。

## Phase 6 当前最新补充：challenge tracking 口径校正

### 1. 这次补的是什么

这轮不是新增 benchmark 题，而是把 roadmap tracking 的 challenge 口径校正到和真实项目状态一致。

之前已经发生的真实推进是：

- `watchfiles#110` 已落地成 `task_127`
- 已纳入 `real_issue_tasks_challenge_v1.json`
- challenge manifest 已从 `1` 条扩到 `2` 条

但 challenge shortlist 和 tracking 的“下一候选”口径还残留着旧描述，导致 latest refresh 里仍会把 `watchfiles#110` 误当成“下一条最值得补的候选”。

### 2. 这次具体修了哪里

核心修正分两层：

- 文档层：
  - `docs/challenge_shortlist.md`
  - 不再把 `watchfiles#110` 写在“下一条 challenge 候选”区段
  - 改为明确它已经是已落地 challenge 题
- 脚本层：
  - `scripts/validate_challenge_shortlist.py`
  - `scripts/snapshot_roadmap_status.py`
  - `scripts/refresh_roadmap_tracking.py`

现在脚本会额外做两件事：

1. challenge shortlist 提取时，自动过滤已经在 challenge manifest 里的 issue
2. `next_action` 不再写死成“重新 sourcing 第 2 条”，而是根据当前 challenge 数动态生成

### 3. 这部分解决了什么问题

修完之后，roadmap tracking 才真正能反映当时那个阶段：

- challenge 已有 `2` 条
- `watchfiles#110` 不再是下一候选
- shortlist 暂时为空时，下一步应是：
  - `重新 sourcing 第 3 条 challenge 候选`

后续这个口径已经继续推进：

- `watchfiles#169` 已落地成第 `3` 条 challenge 题
- 当前 challenge manifest 已有 `3` 条
- 因此现在 shortlist 暂时为空时，下一步应是：
  - `重新 sourcing 第 4 条 challenge 候选`

这很重要，因为如果 tracking 继续引用旧口径，后续 action board、status card 和 handoff 文档都会把人引回已经完成的动作。

### 4. 这次你可以怎么验证

#### 方式 108：跑这次相关测试

```bash
python -m pytest tests/test_validate_challenge_shortlist.py tests/test_snapshot_roadmap_status.py tests/test_refresh_roadmap_tracking.py tests/test_validate_tasks.py -q
```

你会看到：

- 相关测试当前通过
- 说明 challenge shortlist 提取、snapshot 和 refresh 的新口径已经对齐

#### 方式 109：刷新最新 tracking

```bash
python scripts/validate_tasks.py
python scripts/refresh_roadmap_tracking.py --run-label refresh
```

你会看到：

- latest refresh 不应再把 `watchfiles#110` 写成 `next_candidate_issue_ref`
- challenge 下一步会更接近：
  - 继续观察 `task_127`
  - 继续观察 `task_130`
  - 重新 sourcing 第 `4` 条 challenge 候选

### 5. 当前这部分最准确的状态

- 正式任务：`66`
- challenge 任务：`3`
- 当前 challenge manifest：
  - `task_126`
  - `task_127`
-  `task_130`
- 当前 challenge shortlist：
  - 暂时为空
- 当前更准确的下一步：
  - 继续观察 `task_127` 与 `task_130` 的 hard case 价值
  - 重新 sourcing 第 `4` 条 challenge 候选

## Phase 6 当前最新补充：`anyio#88` 已形成 `v69` 失败 / `v70` 成功闭环

### 1. 这次补的是什么

这轮不是直接扩正式集，而是把一个 ready 候选真正推进到“可以决定要不要接入正式集”的程度。

对应 issue 是：

- `agronholm/anyio#88`
- 标题：`Parent task spuriously cancelled with asyncio`

它当前对应的本地任务是：

- `benchmarks/tasks/task_129.json`

### 2. 这次具体推进到了哪里

这一条线现在已经形成完整阶段链：

- `imported`
- `screened`
- `task_129`
- `ready`
- `accepted`

同时它不再只是“有了脚手架”，而是已经有 ready bug repo 证据：

- 正常路径测试通过
- 目标 asyncio 路径测试失败

也就是说，这条题已经可以用来做真正的策略版单任务验证。

### 3. 这次又新增了什么策略能力

当前新增了：

- `optimization/policy_versions/improved_v70.json`

它的目标很明确：

- 在 `improved_v69` 的基础上
- 新增对 `anyio#88` 这个“父任务被额外取消”场景的规则型修复能力

也就是说：

- `v69` 主要覆盖的是 `from_thread.check_cancelled()` 这类 anyio 取消语义
- `v70` 在此基础上继续补了父任务清理这条并发边界

### 4. 当前已经验证了什么

这轮最关键的是，已经形成一条很干净的对照证据链：

1. `improved_v69` 跑 `task_129`：
   - `failed`
2. `improved_v70` 跑 `task_129`：
   - `success`

这意味着：

- `task_129` 不是“理论上也许能修”
- 而是已经能稳定充当：
  - 新策略是否真的带来增量能力
  - 的验证样本

### 5. 你现在可以怎么体验

#### 方式 110：先看 `v69` 的失败

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_129.json --policy optimization/policy_versions/improved_v69.json
```

你会看到：

- 单任务闭环完成
- 但最终状态是 `failed`

#### 方式 111：再看 `v70` 的成功

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_129.json --policy optimization/policy_versions/improved_v70.json
```

你会看到：

- 单任务闭环完成
- 最终状态变成 `success`

#### 方式 112：跑这轮相关测试

```bash
python -m pytest tests/test_patcher_anyio_v70.py tests/test_scaffold_semi_real_task.py tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_audit_semi_real_pipeline.py -q
```

你会看到：

- 相关回归测试通过
- 说明：
  - `v70` 的 patch 规则存在
  - `task_129` 的脚手架推断链是稳定的
  - tracking 也能看见 ready / accepted 阶段变化

### 6. 这一步对后续意味着什么

这一步非常重要，因为它把 `task_129` 从“候选库存里的一个题”推进成了：

- 一个 ready bug repo
- 一个 `旧策略失败 / 新策略成功` 的证据点
- 一个可以认真考虑接入正式集的下一条扩容题

所以当前更合理的下一步不是再泛泛地找题，而是：

1. 决定 `task_129` 是否接入正式 manifest
2. 如果接入，就对 `v70` 做正式集 / frozen 集最小验证
3. 再决定它是否升级为新的主策略版本

## Challenge Tracking 最新体验（refresh_051）

如果你现在想最快理解 challenge 线是否真的能继续搜题，不需要先翻长日志。

你可以直接看：

- `logs/summaries/roadmap_status_card_latest_refresh.md`
- `logs/summaries/roadmap_action_board_latest_refresh.md`

现在这两个 latest 入口除了会告诉你：

- 当前 `challenge_track` 是否还是第一优先级
- 下一条动作是不是“重新 sourcing 第 4 条 challenge 候选”

还会额外直接显示 challenge 本地认证准备度，例如：

- `challenge_auth_env_token_present`
- `challenge_auth_env_token_looks_valid`
- `challenge_auth_gh_logged_in`
- `challenge_auth_token_exportable`
- `challenge_auth_preferred_search_mode`

这组字段的意义是：

- 帮你区分当前更像是环境变量污染
- 还是 `gh` 会话不可用
- 还是 token 不可导出但可以走 `gh session fallback`

当前 `refresh_051` 的一个真实例子是：

- latest 已显示：
  - `challenge_auth_preferred_search_mode = env_token`

这说明当前 shell 里残留着一个看起来像有效 token 的环境变量，所以后续如果 challenge 搜题失败，第一步应先清理 `GITHUB_TOKEN`，而不是直接把问题都归因到网络。

## Challenge Tracking 最新体验（refresh_054）

如果你现在想判断 challenge 本地认证状态变化，是否真的会影响 roadmap tracking，而不只是展示层，可以直接做下面这组观察：

1. 先看：
   - `logs/summaries/roadmap_tracking_latest_refresh.json`
2. 再看：
   - `logs/summaries/roadmap_action_board_latest_refresh.md`
   - `logs/summaries/roadmap_status_card_latest_refresh.md`
3. 重点关注：
   - `changed_fields`
   - `delta.field_changes`
   - `refresh_outcome`
   - `challenge_auth_*`

现在的实现已经不是“只显示 readiness 字段”。

它已经会把下面这些字段纳入 tracking 高信号比较：

- `challenge_auth_env_token_present`
- `challenge_auth_env_token_looks_valid`
- `challenge_auth_gh_logged_in`
- `challenge_auth_token_exportable`
- `challenge_auth_preferred_search_mode`

这意味着：

- 如果 challenge 本地认证状态真的变了
- latest 不只会显示不同字段值
- 还会在 `delta / history / progress_track` 层面把它识别为 challenge 线变化

当前 `refresh_054` 的真实结果仍然是：

- `no_material_change`

这里要正确理解：

- 不是 readiness 接线没成功
- 而是 `refresh_053` 到 `refresh_054` 之间，本地 readiness 状态没有发生真实变化

所以如果你想亲自体验这条链路，最好的方式不是连续空跑 refresh，而是先做一轮真实的 challenge 认证预检动作，例如：

```powershell
Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue
gh auth status
python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4
python scripts/refresh_roadmap_tracking.py --run-label refresh
```

然后再回来看：

- `changed_fields` 是否出现 `challenge_auth_*`
- `refresh_outcome.category` 是否从 `no_material_change` 变成更接近 challenge 推进的信号

## Challenge Tracking 最新体验（refresh_056）

如果你现在想体验“challenge 第 4 条候选已经恢复”这件事，不需要再从候选池和搜索日志手工拼上下文。

你可以直接看：

- `logs/summaries/roadmap_tracking_latest_refresh.json`
- `logs/summaries/roadmap_action_board_latest_refresh.md`
- `logs/summaries/roadmap_status_card_latest_refresh.md`

当前这几份 latest 已经会直接告诉你：

- `challenge_shortlist_candidate_count = 1`
- `challenge_next_candidate_issue_ref = samuelcolvin/watchfiles#215`
- `refresh_outcome = progress`
- `top_priority_track = challenge_track`

这表示 challenge 线已经从：

- “空 shortlist，需要重新 sourcing”

恢复到：

- “已有第 4 条明确候选，下一步是继续评估它能否压成 semi-real challenge 题”

如果你想继续沿这条线亲自体验下一步，最自然的顺序是：

```powershell
Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue
gh issue view 215 --repo samuelcolvin/watchfiles
python scripts/scaffold_semi_real_task.py --from-candidate samuelcolvin_watchfiles_issue_215 --dry-run
python scripts/refresh_roadmap_tracking.py --run-label refresh
```

这条路径现在特别值得体验的原因是：

- 它不只是“多了一个候选”
- 而是 latest 已经会把这次变化识别成真正的 `challenge_track progress`

## Challenge Tracking 最新体验（refresh_059）

如果你现在想体验“challenge 第 4 条候选已经进入本地 task 脚手架阶段”，可以直接看：

- `logs/summaries/roadmap_tracking_latest_refresh.json`
- `logs/summaries/roadmap_action_board_latest_refresh.md`
- `logs/summaries/roadmap_status_card_latest_refresh.md`

当前 latest 已经不只是告诉你：

- `watchfiles#215` 是下一条 challenge 候选

而是会进一步告诉你：

- `challenge_shortlist_candidate_count = 1`
- `challenge_shortlist_screened_with_task_count = 1`
- `next_candidate_issue_ref = samuelcolvin/watchfiles#215`
- 当前 top priority 已稳定回到 `challenge_track`

这意味着当前最自然的体验动作已经从“继续找题”切换成：

- 看 `task_131`
- 看 `watchfiles_215_repo`
- 然后继续把它压成 ready challenge 草稿

如果你想继续沿这条线做最直接的一轮体验，推荐顺序是：

```powershell
python -m pytest benchmarks/repos/watchfiles_215_repo/tests/test_main.py -q
python scripts/run_single_task.py --task benchmarks/tasks/task_131.json --policy optimization/policy_versions/improved_v71.json
python scripts/refresh_roadmap_tracking.py --run-label refresh
```

其中当前最值得注意的一点是：

- `watchfiles#215` 还不是 ready 题
- 它现在处在：
  - `screened_with_task`
  - `repo_scaffold_status = needs_manual_completion`

所以这一步体验的重点，不是看它已经能解，而是看 challenge 线如何从候选逐步推进到真正可评测的问题。

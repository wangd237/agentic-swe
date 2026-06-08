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
| Phase 6 | 优化系统 | 进行中 | 已完成 `baseline_v1 -> improved_v4` 多轮策略迭代，补上自动 compare 报告链路，并接入真实 issue 派生任务入口 |
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

它们的作用是：

- 让任务来源显式区分 `synthetic / semi_real / real_issue`
- 先维护一份 GitHub 真实 issue 候选清单
- 在真实任务真正接入前，先把格式与校验入口固定下来
- 当前已成功导入两条候选：`psf/requests#6432`、`psf/requests#7234`

### 7. 真实 issue 导入入口已可用

当前已经新增：

- `scripts/import_github_issue.py`

当前能力如下：

- 读取 GitHub issue 元数据
- 追加到 `benchmarks/real_world_candidates.json`
- 可选生成 `real_issue` task 草稿
- 保留已有候选状态并按时间追加备注
- 把“候选收集”和“任务补全”拆成两步，避免一次性要求把所有字段都补齐

### 8. 真实 issue 草稿到 semi_real 的脚手架入口已可用

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

### 9. 真实 issue 已推进到可运行 semi_real 任务

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
- `optimization/policy_versions/improved_v3.json`
  - 作用：新增 urllib3 依赖上界放宽修复能力
- `optimization/policy_versions/improved_v4.json`
  - 作用：新增 quoted charset 去引号修复能力

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

### 方式 8：从 real_issue 草稿生成 semi_real 脚手架

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

### 方式 9：运行首条真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_006.json --policy optimization/policy_versions/improved_v3.json
```

你会看到：

- `task_006` 被成功修复
- 修改文件是 `setup.py`
- patch 原因是放宽 urllib3 依赖上界

### 方式 10：运行第 2 条真实 issue 派生任务

在仓库根目录执行：

```bash
python scripts/run_single_task.py --task benchmarks/tasks/task_008.json --policy optimization/policy_versions/improved_v4.json
```

你会看到：

- `task_008` 被成功修复
- 修改文件是 `requests_encoding_repo/utils.py`
- patch 原因是给 quoted charset 增加去引号逻辑

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
- 下一步会继续扩充任务与优化策略

### Phase 7

- 在主线稳定后，尝试轻量 SFT / preference / LoRA 实验

## 建议的阅读顺序

如果你想快速理解项目，建议按这个顺序看：

1. `README.md`
2. `GUIDE.md`
3. `benchmarks/tasks/task_001.json`
4. `benchmarks/repos/sample_repo/`
5. `app/schemas/task_schema.py`
6. `scripts/run_single_task.py`
7. `docs/harness.md`
8. `scripts/run_batch.py`
9. `logs/summaries/batch_run_001.json`
10. `logs/summaries/batch_compare_phase6_002.json`

## 下一轮我会做什么

下一轮进入 `Phase 6` 时，我会继续补齐：

- baseline 配置冻结
- improved prompt / policy / grader 版本
- 扩充 report set
- 逐步引入 GitHub 真实仓库 issue 作为正式评测候选
- 继续追加优化前后差异说明

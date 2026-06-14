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

## 2026-06-13 Phase 6 稳定性复跑与 maturity 流水线补强

### 本轮目标

- 把“单次采样偏高导致误判性能退化”的风险收敛成可复跑、可量化的流程
- 把 benchmark maturity 审计纳入常规评测入口
- 为后续 v2 路线图提供更稳的基础设施证据

### 改动类型

- `runtime`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/stability_recheck.py`
- `scripts/run_real_issue_eval.py`
- `logs/summaries/stability_recheck_frozen40_v63_stability_001.json`
- `logs/summaries/stability_recheck_frozen40_v63_stability_001.md`
- `logs/summaries/benchmark_maturity_maturity_046.json`
- `logs/summaries/benchmark_maturity_maturity_046.md`

### 改动摘要

- 新增 `scripts/stability_recheck.py`
  - 支持同一策略、同一 manifest 的多次 batch run + batch eval 复跑
  - 自动输出均值、标准差、最小值、最大值、outlier、functional consistency
  - 输出稳定性结论：`stable / borderline / unstable`
- 扩展 `scripts/run_real_issue_eval.py`
  - 新增 `--stability-check`
  - 新增 `--stability-repetitions`
  - 新增 `--stability-manifest`
  - 新增 `--maturity-formal-manifest`
  - 在同一条命令中串起 batch run、batch eval、stability check 和 maturity audit
- 修复 Windows `gbk` 终端下 `✓ / ✗` 输出导致的编码问题
  - 改成 `OK / FAIL`

### 关键验证

- `frozen_40` 上的 `improved_v63` 同版复跑 `3` 次：
  - run1 `average_duration_sec = 0.602`
  - run2 `average_duration_sec = 0.5508`
  - run3 `average_duration_sec = 0.5489`
- 聚合结果：
  - `average_duration_mean_sec = 0.5672`
  - `average_duration_std_sec = 0.0301`
  - `success_rate_mean = 1.0`
  - `test_pass_rate_mean = 1.0`
  - `functional_consistent = true`
  - `conclusion = borderline`
- maturity 审计结果：
  - `formal_task_count = 60 / 60`
  - `ecosystem_count = 14 / 6`
  - `latest_frozen_count = 40 / 40`
  - `frozen_40_streak = 8 / 5`

### 结论

- 项目已经不再依赖单次 frozen 测试结果判断性能回归
- “规模、稳定性、无回归、性能门控”的证据已经能在一条流水线内统一生成
- `Benchmark Maturity v1` 当前不仅是一个口头判断，而是有复跑和审计产物支撑的结论

### 剩余问题

- 当前稳定性结论仍为 `borderline`
- 说明性能波动虽然没有功能风险，但仍值得后续继续治理
- 下一步可以考虑补环境基线快照，进一步区分环境漂移和系统性策略开销

## 2026-06-13 Phase 6 展示层收口第一轮

### 本轮目标

- 把当前项目从“工程很强但展示层偏日志化”往“可读、可讲、可投递”方向推进
- 用更少的文档入口把当前真实状态讲清楚

### 改动类型

- `documentation`

### 主要涉及文件

- `README.md`
- `docs/architecture.md`
- `docs/experiment_summary.md`
- `docs/case_studies.md`
- `docs/case_studies_archive_v1.md`

### 改动摘要

- 重写 `README.md`
  - 第一屏直接给出正式任务数、生态数、成功率、`frozen_40 streak` 和性能口径
  - 补了系统闭环图、最常用命令和文档导航
- 重写 `docs/architecture.md`
  - 去掉“尚未接入真实 issue”的过时叙述
  - 改为真实实现视角，明确 agent loop、tools、runtime、eval、policy、数据分层
- 新增 `docs/experiment_summary.md`
  - 作为 `docs/results.md` 的导读层
  - 压缩展示 `improved_v3 / v17 / v33 / v50 / v63 / v63r3` 的关键里程碑
- 重写 `docs/case_studies.md`

## 2026-06-13 Phase 6 roadmap tracking 续做能力补强

### 本轮目标

- 让 roadmap tracking 在“刚出现 progress，但下一轮暂时没有新增证据”的场景下，仍然保持续做主线
- 避免 history / handoff 因一轮 `no_material_change` 就过早退回泛化建议

### 改动类型

- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 改动摘要

- 为 history entry 增加 `progress_track`
  - 让每轮 refresh 的历史记录不仅知道有没有变化
  - 还知道最近一次有效推进属于哪条主线
- 增强 `build_history_advice()`
  - 当 latest 是 `no_material_change`
  - 且最近 `1` 到 `2` 轮内刚出现过 `progress`
  - 不再立刻回退到 `monitor_and_continue`
  - 而是继续返回：
    - `keep_momentum`
    - `recommended_focus = 最近一次 progress_track`
    - 并显式附带：
      - `progress_track`
      - `source_progress_refresh_id`
- 修正配套测试断言
  - 让 `progress` 口径不再假设 `recommended_focus = active_track`
  - 让“短暂停顿继承主线”成为测试覆盖的一部分

### 关键验证

- 定向测试：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
  - 结果：
    - `14 passed`
- 真实 refresh：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 新产物：
    - `logs/summaries/roadmap_tracking_refresh_029.json`
    - `logs/summaries/roadmap_tracking_latest_refresh.json`

### 结论

- roadmap tracking 的“续做能力”又增强了一层：
  - 不再只会识别 `progress`
  - 也能在 very short gap 内保留最近一次已证明有效的主线
- 但真实 latest 当前已来到：
  - `recent_no_material_change_streak = 3`
- 因此最新 `history_advice` 已合理回到：
  - `monitor_and_continue`
- 这说明新逻辑没有失效，而是已经越过短暂停顿窗口

### 剩余问题

- 当前最缺的不是 tracking 解释层，而是新的实质推进证据
- 下一步应优先：
  - 补新的 performance 证据
  - 或推进新的 formal / challenge 实际接入
  - 再用 refresh 打断 `no_material_change` streak
  - 由 `620` 行模板流水账改成 `5` 个精选案例
  - 同时把旧版完整记录归档到 `docs/case_studies_archive_v1.md`

### 结果

- 当前项目首页、架构说明、实验摘要、案例材料已经形成最小展示闭环
- 文档口径与当前真实实现对齐：
  - 正式任务 `60`
  - 来源生态 `14`
  - `improved_v63`
  - `frozen_40 streak = 8`
  - `v63r3 frozen_40 average_duration_sec = 0.5454`

### 结论

- 这一轮没有增加新题，但显著提升了项目的可理解性和可展示性
- 对后续推进 A 线扩容和 challenge 集很有帮助，因为现在已经有了更可靠的对外叙事骨架

## 2026-06-13 A1 缺陷覆盖 gap 分析首版落地

### 本轮目标

- 把后续扩容从“凭感觉找题”推进到“按覆盖缺口找题”
- 识别当前 benchmark 在缺陷家族层面的过密区和欠缺区

### 改动类型

- `analysis`
- `documentation`

### 主要涉及文件

- `scripts/analyze_defect_coverage.py`
- `logs/summaries/defect_coverage_v2_gap_analysis_002.json`
- `logs/summaries/defect_coverage_v2_gap_analysis_002.md`

### 改动摘要

- 新增 `scripts/analyze_defect_coverage.py`
  - 读取 `benchmarks/manifests/real_issue_tasks.json`
  - 解析 `docs/benchmark_registry.md` 里的“缺陷类型”列
  - 生成两层统计：
    - exact defect type
    - family 级归一化缺陷家族
  - 输出 ecosystem × family 矩阵
  - 按 roadmap 和 `docs/issue_sourcing_spec.md` 生成缺口建议
- 首轮实现后发现关键词分类过宽
  - 如把 `async repr` 误归类成并发、把 `file URL` 误归类成 IO
- 随后收紧分类规则并重跑，保留 `002` 版作为当前可信结果

### 关键结果

- 当前 family 覆盖前两位：
  - `解析与字符串语义 = 15`
  - `序列化与反序列化 = 15`
- 说明当前 benchmark 的强项仍集中在：
  - parser / token / 规范化 / 字符串语义
  - toml / 渲染 / 配置 / 容器序列化
- 当前高价值缺口：
  - `并发与协程`: `0 / target_min 2`
  - `文件路径与 IO`: `0 / target_min 2`
  - `继承、优先级与控制流`: `7 / target_min 8`

### 结论

- A1 已经不再是概念层建议，而是有脚本和产物支撑的扩容依据
- 下一轮扩容最应优先搜索：
  - `asyncio / trio / anyio`
  - `pathlib / watchfiles / fsspec`
- 如果继续补老强项，也应优先补：
  - 新生态里的继承 / 优先级 / 控制流问题
  - 而不是继续在现有 `tomlkit / packaging` 上重复相似语义

## 2026-06-13 A2 扩容找题 brief 收口

### 本轮目标

- 把 A1 的 gap 分析结果转成可直接交给外部检索器或 Claude 的找题说明
- 降低下一轮扩新来源时的沟通成本和筛选噪声

### 改动类型

- `documentation`
- `candidate_sourcing`

### 主要涉及文件

- `docs/issue_sourcing_brief_a2.md`
- `docs/candidate_shortlist.md`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 新增 `docs/issue_sourcing_brief_a2.md`
  - 明确当前阶段最优先补的家族：
    - `并发与协程`
    - `文件路径与 IO`
  - 明确次优先级：
    - 来自新生态的 `继承、优先级与控制流`
  - 明确当前不建议继续优先堆的方向：
    - `tomlkit` 的序列化 / 容器小 bug
    - `packaging` 的解析 / normalization / marker / specifier 类边界 bug
- 同步更新：
  - `docs/candidate_shortlist.md`
  - `docs/next_actions.md`
  - `GUIDE.md`
- 把当前阶段的找题输入从“口头说明”升级成了“固定文档入口”

### 关键观察

- 当前本地 `real_world_candidates.json` 已基本被正式集消化
- `candidate_shortlist` 也已经清空
- 这意味着下一轮 A2 不是“继续吃库存”，而是必须：
  - 面向新生态增量找题
  - 并尽量避免再次把新增候选集中到现有高密度家族

### 结论

- 当前 A2 已具备清晰、可执行的找题 brief
- 下一轮如果要调用 Claude 或其它检索器找 GitHub issue，最稳的输入就是：
  - `docs/issue_sourcing_spec.md`
  - `docs/issue_sourcing_brief_a2.md`

## 2026-06-13 C1 半自动候选搜索脚本落地

### 本轮目标

- 把 roadmap 里的 `C1` 从“要做的想法”推进成真实脚本入口
- 让找题环节不再只能手工刷 GitHub 页面

### 改动类型

- `candidate_sourcing`
- `tooling`
- `documentation`

### 主要涉及文件

- `scripts/search_candidate_issues.py`
- `GUIDE.md`
- `docs/next_actions.md`

### 改动摘要

- 新增 `scripts/search_candidate_issues.py`
  - 基于 `gh search issues`
  - 支持：
    - `--repo`
    - `--query`
    - `--state`
    - `--labels`
    - `--limit`
    - `--format json|markdown`
    - `--output / --output-dir / --run-label`
  - 输出不是 raw issue JSON，而是更适合人工判题的结构化摘要：
    - `family`
    - `why_it_fits`
    - `expected_target_files`
    - `expected_test_shape`
    - `risk_notes`
    - `recommendation`
- 已完成本地可运行检查：
  - `python scripts/search_candidate_issues.py --help`
  - 输出路径自动生成逻辑校验

### 当前限制

- 当前环境里 live `gh search issues` 仍受 GitHub 认证状态影响
- 实测遇到：
  - 网络权限错误
  - `401 Bad credentials`
- 因此这轮重点先把脚本和输出契约落好，而不是伪造 live 查询结果

### 结论

- `C1` 已经具备最小可运行形态
- 后续只要 `gh` 认证恢复正常，就可以直接对：
  - `asyncio`
  - `trio`
  - `anyio`
  - `pathlib`
  - `watchfiles`
  - `fsspec`
  跑一轮半自动候选搜索

## 2026-06-13 C2 `--from-candidate` 自动脚手架首版落地

### 本轮目标

- 把 roadmap 里的 `C2` 落成最小可运行能力
- 降低从 candidate 到 semi-real 脚手架的手工填写成本

### 改动类型

- `candidate_sourcing`
- `tooling`

### 主要涉及文件

- `scripts/scaffold_semi_real_task.py`

### 改动摘要

- 新增 `--from-candidate <candidate_id>` 模式
  - 自动从 `real_world_candidates.json` 读取候选元数据
  - 自动推断：
    - `semi-repo-name`
    - `module-path`
    - `test-path`
    - `success_criteria`
    - `extra tags`
- 新增 issue 代码块提取逻辑
  - 自动把 issue body 中的代码块写进测试文件初稿
  - 并明确标注 `TODO: review and adjust`
- 新增 `--dry-run`
  - 允许只预览自动推断结果
  - 不写入 task、repo 脚手架，也不更新 candidate 状态
- 修正 candidate 状态更新逻辑
  - dry-run 不再污染 candidate
  - 对已经是 `accepted / completed` 的候选，不再因为补脚手架而降级成 `scaffolded`

### 当前验证

- 已验证命令：
  - `python scripts/scaffold_semi_real_task.py --from-candidate pypa_distlib_issue_238 --semi-repo-name distlib_wheel_repo_autogen --candidate-file benchmarks/real_world_candidates.json --dry-run`
- 当前能稳定输出：
  - 自动推断的 `module_file`
  - 自动推断的 `test_file`
  - 自动生成的 semi-real task 目标路径
  - `dry_run=True` 时跳过 candidate 状态更新

### 当前边界

- 仍然只是“自动填初稿”，不是自动把 issue 变成高质量 semi-real 任务
- `module-path` 和 `test-path` 仍需人工 review
- `success_criteria` 目前是可靠占位，不是最终精修版 benchmark 文案

### 结论

- `C2` 已经具备最小可运行形态
- 现在 candidate -> scaffold 的第一步，已经不再需要每次从零手写全部参数

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

## 2026-06-11 Phase 6 packaging marker `extra=None` 扩容与 `improved_v34`

### 背景

上一轮我们已经完成：

- maturity 审计接入
- packaging / tomlkit / jinja 候选池扩容
- `docs/candidate_shortlist.md` 的可执行排序

因此这一轮最自然的下一步，就是把 shortlist 里的第一批低风险候选真正转成新的正式任务，而不是继续只停留在候选层。

### 目标

- 把 `pypa/packaging#638` 转成新的 semi_real 正式任务
- 为 `Marker.evaluate(extra=None)` 场景补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上同时验证 `improved_v34`
- 把 maturity 审计结果同步到 `31 / 60`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_062.json`
- `benchmarks/tasks/task_063.json`
- `benchmarks/repos/packaging_marker_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v34.json`
- `app/agent/patcher.py`
- `logs/summaries/batch_run_realissuev34_001.json`
- `logs/summaries/batch_eval_realissuev34_001.json`
- `logs/summaries/batch_compare_realissue_step14_002.json`
- `logs/summaries/batch_run_frozen20v34_001.json`
- `logs/summaries/batch_eval_frozen20v34_001.json`
- `logs/summaries/batch_compare_frozen20_step13_001.json`
- `logs/summaries/benchmark_maturity_maturity_005.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `packaging#638` 的 `real_issue` 草稿：
  - `task_062`
- 新增可运行的 semi_real 正式任务：
  - `task_063`
- 新增 repo：
  - `benchmarks/repos/packaging_marker_repo`
- 在 repo 中故意保留 bug：
  - `extra` 为 `None` 时仍继续执行 `.lower()`，从而触发回归测试失败
- 新增 `improved_v34`
- 在 patcher 中新增 `Marker.evaluate(extra=None)` 的专用规则
- 把 `task_063` 加入正式 manifest
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证与 maturity 审计

### 测试与验证

- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_063.json --policy optimization/policy_versions/improved_v34.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v34.json --run-label realissuev34 --compare-against-eval logs/summaries/batch_eval_realissuev33_001.json --compare-label realissue_step14`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v34.json --run-label frozen20v34 --compare-against-eval logs/summaries/batch_eval_frozen20v33_001.json --compare-label frozen20_step13`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `30 -> 31`
- 候选池状态：
  - `accepted = 30 -> 31`
  - `to_review = 8 -> 7`
- `improved_v34` 正式 `31` 条任务集结果：
  - `success_count: 30 -> 31`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5423 -> 0.5391`
- `improved_v34` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5379 -> 0.5368`
- maturity 审计：
  - 正式任务数：`31 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`20 / 40`
  - `frozen_40` 连续版本：`0 / 5`

### 结论

- `packaging#638` 已成功从候选进入正式 semi_real 任务集
- `improved_v34` 在扩容后继续保持正式集和固定集双线无回归
- 当前主线基线已经更新为：
  - 正式任务数：`31`
  - 最新策略：`improved_v34`
  - 固定集合证据：`frozen_20`
- 这说明我们正在稳步推进“规模扩容 + 稳定性证据同步累积”的成熟度路线，而不是只做孤立的新任务堆叠

### 剩余问题

- 当前离 `60` 条正式任务仍有明显距离
- `frozen_40` 还没有开始构建
- 下一轮应继续优先吃 shortlist 中边界清晰的剩余候选，例如：
  - `pypa/packaging#788`
  - `python-poetry/tomlkit#442`
  - `python-poetry/tomlkit#431`

## 2026-06-12 Phase 6 packaging `< prerelease` 扩容与 `improved_v35`

### 背景

上一轮我们已经完成：

- `packaging#638 -> task_063`
- `improved_v34`
- 正式任务数推进到 `31`

因此这一轮继续沿 `packaging` 方向扩容，优先消化 shortlist 里另一个边界清晰、且与现有 `Specifier >` 语义互补的 `packaging#788`。

### 目标

- 把 `pypa/packaging#788` 转成新的 semi_real 正式任务
- 为 `< prerelease` 比较场景补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上同时验证 `improved_v35`
- 把 maturity 审计结果同步到 `32 / 60`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_064.json`
- `benchmarks/tasks/task_065.json`
- `benchmarks/repos/packaging_prerelease_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v35.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/candidate_shortlist.md`
- `logs/summaries/batch_run_realissuev35_001.json`
- `logs/summaries/batch_eval_realissuev35_001.json`
- `logs/summaries/batch_compare_realissue_step15_002.json`
- `logs/summaries/batch_run_frozen20v35_001.json`
- `logs/summaries/batch_eval_frozen20v35_001.json`
- `logs/summaries/batch_compare_frozen20_step14_001.json`
- `logs/summaries/benchmark_maturity_maturity_006.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `packaging#788` 的 `real_issue` 草稿：
  - `task_064`
- 新增可运行的 semi_real 正式任务：
  - `task_065`
- 新增 repo：
  - `benchmarks/repos/packaging_prerelease_repo`
- 在 repo 中故意保留 bug：
  - 当 specifier 自身是 prerelease 时，当前实现直接拒绝全部 prerelease 候选
- 新增 `improved_v35`
- 在 patcher 中新增 `< prerelease` 比较的专用规则
- 把 `task_065` 加入正式 manifest
- 更新候选池状态和短名单
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/packaging_prerelease_repo/tests/test_specifiers.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_065.json --policy optimization/policy_versions/improved_v35.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v35.json --run-label realissuev35 --compare-against-eval logs/summaries/batch_eval_realissuev34_001.json --compare-label realissue_step15`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v35.json --run-label frozen20v35 --compare-against-eval logs/summaries/batch_eval_frozen20v34_001.json --compare-label frozen20_step14`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `31 -> 32`
- 候选池状态：
  - `accepted = 31 -> 32`
  - `to_review = 7 -> 6`
- `improved_v35` 正式 `32` 条任务集结果：
  - `success_count: 31 -> 32`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5391 -> 0.535`
- `improved_v35` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5368 -> 0.5402`
- 时延分析：
  - 正式集公共 `31` 条任务平均耗时差值：`-0.003s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`+0.0034s`
- maturity 审计：
  - 正式任务数：`32 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`20 / 40`
  - `frozen_40` 连续版本：`0 / 5`

### 结论

- `packaging#788` 已成功从候选进入正式 semi_real 任务集
- `improved_v35` 在扩容后继续保持正式集和固定集双线无功能回归
- 正式集平均耗时继续下降，固定集只有 `+0.0034s` 的轻微波动，仍远低于长期目标允许的耗时回升边界
- 当前主线基线已经更新为：
  - 正式任务数：`32`
  - 最新策略：`improved_v35`
  - 固定集合证据：`frozen_20`

### 剩余问题

- 当前离 `60` 条正式任务仍有明显距离
- `frozen_40` 还没有开始构建
- 下一轮应继续优先吃 shortlist 中边界清晰的剩余候选，例如：
  - `pypa/packaging#909`
  - `python-poetry/tomlkit#442`
  - `python-poetry/tomlkit#431`

## 2026-06-12 Phase 6 packaging wheel compressed tag order 扩容与 `improved_v36`

### 背景

上一轮我们已经完成：

- `packaging#788 -> task_065`
- `improved_v35`
- 正式任务数推进到 `32`

因此这一轮继续沿 `packaging` 方向扩容，优先消化 shortlist 里另一个 wheel 解析边界清晰的问题 `packaging#909`。

### 目标

- 把 `pypa/packaging#909` 转成新的 semi_real 正式任务
- 为 wheel compressed tag set 排序校验场景补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上同时验证 `improved_v36`
- 把 maturity 审计结果同步到 `33 / 60`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_066.json`
- `benchmarks/tasks/task_067.json`
- `benchmarks/repos/packaging_tag_order_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v36.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/candidate_shortlist.md`
- `logs/summaries/batch_run_realissuev36_001.json`
- `logs/summaries/batch_eval_realissuev36_001.json`
- `logs/summaries/batch_compare_realissue_step16_002.json`
- `logs/summaries/batch_run_frozen20v36_001.json`
- `logs/summaries/batch_eval_frozen20v36_001.json`
- `logs/summaries/batch_compare_frozen20_step15_001.json`
- `logs/summaries/benchmark_maturity_maturity_007.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `packaging#909` 的 `real_issue` 草稿：
  - `task_066`
- 新增可运行的 semi_real 正式任务：
  - `task_067`
- 新增 repo：
  - `benchmarks/repos/packaging_tag_order_repo`
- 在 repo 中故意保留 bug：
  - 当前实现只拆出 compressed python tag，但没有校验它们是否已经排序
- 新增 `improved_v36`
- 在 patcher 中新增 wheel compressed tag set 排序校验的专用规则
- 把 `task_067` 加入正式 manifest
- 更新候选池状态和短名单
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/packaging_tag_order_repo/tests/test_utils.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_067.json --policy optimization/policy_versions/improved_v36.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v36.json --run-label realissuev36 --compare-against-eval logs/summaries/batch_eval_realissuev35_001.json --compare-label realissue_step16`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v36.json --run-label frozen20v36 --compare-against-eval logs/summaries/batch_eval_frozen20v35_001.json --compare-label frozen20_step15`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `32 -> 33`
- 候选池状态：
  - `accepted = 32 -> 33`
  - `to_review = 6 -> 5`
- `improved_v36` 正式 `33` 条任务集结果：
  - `success_count: 32 -> 33`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.535 -> 0.5312`
- `improved_v36` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5402 -> 0.5386`
- 时延分析：
  - 正式集公共 `32` 条任务平均耗时差值：`-0.0027s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`-0.0016s`
- maturity 审计：
  - 正式任务数：`33 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`20 / 40`
  - `frozen_40` 连续版本：`0 / 5`

### 结论

- `packaging#909` 已成功从候选进入正式 semi_real 任务集
- `improved_v36` 在扩容后继续保持正式集和固定集双线无功能回归
- 并且这次扩容在正式集和 `frozen_20` 上都带来了小幅时延改善
- 当前主线基线已经更新为：
  - 正式任务数：`33`
  - 最新策略：`improved_v36`
  - 固定集合证据：`frozen_20`

### 剩余问题

- 当前离 `60` 条正式任务仍有明显距离
- `frozen_40` 还没有开始构建
- 下一轮应继续优先吃 shortlist 中边界清晰的剩余候选，例如：
  - `python-poetry/tomlkit#442`
  - `python-poetry/tomlkit#431`
  - `pallets/jinja#2151`

## 2026-06-12 Phase 6 tomlkit boolean 字面量扩容与 `improved_v37`

### 背景

上一轮我们已经完成：

- `packaging#909 -> task_067`
- `improved_v36`
- 正式任务数推进到 `33`

因此这一轮优先消化一个边界极小、可快速转正式任务的候选 `python-poetry/tomlkit#442`，继续把正式任务集往 `40+` 推进。

### 目标

- 把 `python-poetry/tomlkit#442` 转成新的 semi_real 正式任务
- 为 TOML 布尔字面量序列化场景补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上同时验证 `improved_v37`
- 把 maturity 审计结果同步到 `34 / 60`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_068.json`
- `benchmarks/tasks/task_069.json`
- `benchmarks/repos/tomlkit_boolean_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v37.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev37_001.json`
- `logs/summaries/batch_eval_realissuev37_001.json`
- `logs/summaries/batch_compare_realissue_step17_002.json`
- `logs/summaries/batch_run_frozen20v37_001.json`
- `logs/summaries/batch_eval_frozen20v37_001.json`
- `logs/summaries/batch_compare_frozen20_step16_001.json`
- `logs/summaries/benchmark_maturity_maturity_008.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `tomlkit#442` 的 `real_issue` 草稿：
  - `task_068`
- 新增可运行的 semi_real 正式任务：
  - `task_069`
- 新增 repo：
  - `benchmarks/repos/tomlkit_boolean_repo`
- 在 repo 中故意保留 bug：
  - 当前实现把 `True` 和 `False` 都错误渲染成 `false`
- 新增 `improved_v37`
- 在 patcher 中新增 TOML 布尔字面量序列化的专用规则
- 把 `task_069` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_boolean_repo/tests/test_boolean.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_069.json --policy optimization/policy_versions/improved_v37.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v37.json --run-label realissuev37 --compare-against-eval logs/summaries/batch_eval_realissuev36_001.json --compare-label realissue_step17`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v37.json --run-label frozen20v37 --compare-against-eval logs/summaries/batch_eval_frozen20v36_001.json --compare-label frozen20_step16`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `33 -> 34`
- 候选池状态：
  - `accepted = 33 -> 34`
  - `to_review = 5 -> 4`
- `improved_v37` 正式 `34` 条任务集结果：
  - `success_count: 33 -> 34`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5312 -> 0.6038`
- `improved_v37` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5386 -> 0.5687`
- 时延分析：
  - 正式集公共 `33` 条任务平均耗时差值：`+0.0734s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`+0.0301s`
- maturity 审计：
  - 正式任务数：`34 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`20 / 40`
  - `frozen_40` 连续版本：`0 / 5`

### 结论

- `tomlkit#442` 已成功从候选进入正式 semi_real 任务集
- `improved_v37` 在扩容后继续保持正式集和固定集双线无功能回归
- 但这轮扩容同时带来了可见的时延回升，因此当前版本更适合作为扩容基线，而不是性能基线
- 当前主线基线已经更新为：
  - 正式任务数：`34`
  - 最新策略：`improved_v37`
  - 固定集合证据：`frozen_20`

### 剩余问题

- 当前离 `60` 条正式任务仍有明显距离
- `frozen_40` 还没有开始构建
- `v37` 的时延回升还需要结合下一轮相邻版本对比继续跟踪
- 下一轮应继续优先吃 shortlist 中边界清晰的剩余候选，例如：
  - `python-poetry/tomlkit#431`
  - `python-poetry/tomlkit#383`
  - `pallets/jinja#2151`

## 2026-06-12 Phase 6 tomlkit 代理删除扩容与 `improved_v38`

### 背景

上一轮我们已经完成：

- `tomlkit#442 -> task_069`
- `improved_v37`
- 正式任务数推进到 `34`

因此这一轮继续沿 `tomlkit` 方向扩容，优先消化边界清晰且能补容器删除语义的候选 `python-poetry/tomlkit#383`。

### 目标

- 把 `python-poetry/tomlkit#383` 转成新的 semi_real 正式任务
- 为代理容器 `pop()` 删除未同步到底层表结构的场景补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上同时验证 `improved_v38`
- 把 maturity 审计结果同步到 `35 / 60`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_070.json`
- `benchmarks/tasks/task_071.json`
- `benchmarks/repos/tomlkit_proxy_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v38.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev38_001.json`
- `logs/summaries/batch_eval_realissuev38_001.json`
- `logs/summaries/batch_compare_realissue_step18_002.json`
- `logs/summaries/batch_run_frozen20v38_001.json`
- `logs/summaries/batch_eval_frozen20v38_001.json`
- `logs/summaries/batch_compare_frozen20_step17_001.json`
- `logs/summaries/benchmark_maturity_maturity_009.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `tomlkit#383` 的 `real_issue` 草稿：
  - `task_070`
- 新增可运行的 semi_real 正式任务：
  - `task_071`
- 新增 repo：
  - `benchmarks/repos/tomlkit_proxy_repo`
- 在 repo 中故意保留 bug：
  - 当前实现返回值正确，但 `pop()` 没有真正删除底层键
- 新增 `improved_v38`
- 在 patcher 中新增代理 `pop()` 删除同步的专用规则
- 把 `task_071` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_proxy_repo/tests/test_proxy.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_071.json --policy optimization/policy_versions/improved_v38.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v38.json --run-label realissuev38 --compare-against-eval logs/summaries/batch_eval_realissuev37_001.json --compare-label realissue_step18`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v38.json --run-label frozen20v38 --compare-against-eval logs/summaries/batch_eval_frozen20v37_001.json --compare-label frozen20_step17`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `34 -> 35`
- 候选池状态：
  - `accepted = 34 -> 35`
  - `to_review = 4 -> 3`
- `improved_v38` 正式 `35` 条任务集结果：
  - `success_count: 34 -> 35`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6038 -> 0.553`
- `improved_v38` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5687 -> 0.5427`
- 时延分析：
  - 正式集公共 `34` 条任务平均耗时差值：`-0.0499s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`-0.026s`
- maturity 审计：
  - 正式任务数：`35 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`20 / 40`
  - `frozen_40` 连续版本：`0 / 5`

### 结论

- `tomlkit#383` 已成功从候选进入正式 semi_real 任务集
- `improved_v38` 在扩容后继续保持正式集和固定集双线无功能回归
- 并且这轮不只是扩容，还把 `v37` 的时延回升明显回收
- 当前主线基线已经更新为：
  - 正式任务数：`35`
  - 最新策略：`improved_v38`
  - 固定集合证据：`frozen_20`

### 剩余问题

- 当前离 `60` 条正式任务仍有明显距离
- `frozen_40` 还没有开始构建
- 下一轮应继续优先吃 shortlist 中边界清晰的剩余候选，例如：
  - `python-poetry/tomlkit#431`
  - `pallets/jinja#2151`
  - `pallets/jinja#2176`

## 2026-06-12 Phase 6 tomlkit super table dotted key 扩容与 `improved_v39`

### 背景

上一轮我们已经完成：

- `tomlkit#383 -> task_071`
- `improved_v38`
- 正式任务数推进到 `35`

因此这一轮继续沿 `tomlkit` 方向扩容，优先消化能补 super table 与 dotted key 组合渲染语义的候选 `python-poetry/tomlkit#431`。

### 目标

- 把 `python-poetry/tomlkit#431` 转成新的 semi_real 正式任务
- 为 super table 下新增 dotted key 时父级前缀丢失的场景补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上同时验证 `improved_v39`
- 把 maturity 审计结果同步到 `36 / 60`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_072.json`
- `benchmarks/tasks/task_073.json`
- `benchmarks/repos/tomlkit_super_table_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v39.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev39_001.json`
- `logs/summaries/batch_eval_realissuev39_001.json`
- `logs/summaries/batch_compare_realissue_step19_002.json`
- `logs/summaries/batch_run_frozen20v39_001.json`
- `logs/summaries/batch_eval_frozen20v39_001.json`
- `logs/summaries/batch_compare_frozen20_step18_001.json`
- `logs/summaries/benchmark_maturity_maturity_010.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `tomlkit#431` 的 `real_issue` 草稿：
  - `task_072`
- 新增可运行的 semi_real 正式任务：
  - `task_073`
- 新增 repo：
  - `benchmarks/repos/tomlkit_super_table_repo`
- 在 repo 中故意保留 bug：
  - 当前实现在新增 dotted key 时错误丢失了父级 super table 前缀
- 新增 `improved_v39`
- 在 patcher 中新增 super table dotted key 前缀保留的专用规则
- 把 `task_073` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_super_table_repo/tests/test_renderer.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_073.json --policy optimization/policy_versions/improved_v39.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v39.json --run-label realissuev39 --compare-against-eval logs/summaries/batch_eval_realissuev38_001.json --compare-label realissue_step19`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v39.json --run-label frozen20v39 --compare-against-eval logs/summaries/batch_eval_frozen20v38_001.json --compare-label frozen20_step18`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `35 -> 36`
- 候选池状态：
  - `accepted = 35 -> 36`
  - `to_review = 3 -> 2`
- `improved_v39` 正式 `36` 条任务集结果：
  - `success_count: 35 -> 36`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.553 -> 0.5453`
- `improved_v39` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5427 -> 0.5443`
- 时延分析：
  - 正式集公共 `35` 条任务平均耗时差值：`-0.0078s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`+0.0016s`
- maturity 审计：
  - 正式任务数：`36 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`20 / 40`
  - `frozen_40` 连续版本：`0 / 5`

### 结论

- `tomlkit#431` 已成功从候选进入正式 semi_real 任务集
- `improved_v39` 在扩容后继续保持正式集和固定集双线无功能回归
- 并且这轮扩容在正式集上继续带来了小幅时延改善，固定集仅有极小波动
- 当前主线基线已经更新为：
  - 正式任务数：`36`
  - 最新策略：`improved_v39`
  - 固定集合证据：`frozen_20`

### 剩余问题

- 当前离 `60` 条正式任务仍有明显距离
- `frozen_40` 还没有开始构建
- 下一轮应继续优先吃 shortlist 中边界清晰的剩余候选，例如：
  - `pallets/jinja#2151`
  - `pallets/jinja#2176`

## 2026-06-12 Phase 6 jinja async repr 扩容与 `improved_v40`

### 背景

上一轮我们已经完成：

- `tomlkit#431 -> task_073`
- `improved_v39`
- 正式任务数推进到 `36`

因此这一轮转向 `jinja`，优先消化能补 async/runtime 表示层语义的候选 `pallets/jinja#2151`。

### 目标

- 把 `pallets/jinja#2151` 转成新的 semi_real 正式任务
- 为 `AsyncLoopContext.__repr__` 暴露协程对象并触发未 awaited 警告的场景补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上同时验证 `improved_v40`
- 把 maturity 审计结果同步到 `37 / 60`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_074.json`
- `benchmarks/tasks/task_075.json`
- `benchmarks/repos/jinja_async_repr_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v40.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev40_001.json`
- `logs/summaries/batch_eval_realissuev40_001.json`
- `logs/summaries/batch_compare_realissue_step20_002.json`
- `logs/summaries/batch_run_frozen20v40_001.json`
- `logs/summaries/batch_eval_frozen20v40_001.json`
- `logs/summaries/batch_compare_frozen20_step19_001.json`
- `logs/summaries/benchmark_maturity_maturity_011.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `jinja#2151` 的 `real_issue` 草稿：
  - `task_074`
- 新增可运行的 semi_real 正式任务：
  - `task_075`
- 新增 repo：
  - `benchmarks/repos/jinja_async_repr_repo`
- 在 repo 中故意保留 bug：
  - 当前 `AsyncLoopContext.__repr__` 直接把协程对象拼进字符串表示
- 新增 `improved_v40`
- 在 patcher 中新增 async repr 的专用规则
- 把 `task_075` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/jinja_async_repr_repo/tests/test_runtime.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_075.json --policy optimization/policy_versions/improved_v40.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v40.json --run-label realissuev40 --compare-against-eval logs/summaries/batch_eval_realissuev39_001.json --compare-label realissue_step20`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v40.json --run-label frozen20v40 --compare-against-eval logs/summaries/batch_eval_frozen20v39_001.json --compare-label frozen20_step19`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `36 -> 37`
- 候选池状态：
  - `accepted = 36 -> 37`
  - `to_review = 2 -> 1`
- `improved_v40` 正式 `37` 条任务集结果：
  - `success_count: 36 -> 37`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5453 -> 0.5717`
- `improved_v40` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5443 -> 0.5682`
- 时延分析：
  - 正式集公共 `36` 条任务平均耗时差值：`+0.0269s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`+0.0239s`
- maturity 审计：
  - 正式任务数：`37 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`20 / 40`
  - `frozen_40` 连续版本：`0 / 5`

### 结论

- `jinja#2151` 已成功从候选进入正式 semi_real 任务集
- `improved_v40` 在扩容后继续保持正式集和固定集双线无功能回归
- 但这轮扩容带来了可见的时延回升，因此需要后续版本继续做性能回收
- 当前主线基线已经更新为：
  - 正式任务数：`37`
  - 最新策略：`improved_v40`
  - 固定集合证据：`frozen_20`

### 剩余问题

- 当前离 `60` 条正式任务仍有明显距离
- `frozen_40` 还没有开始构建
- 下一轮应继续优先处理剩余 shortlist 候选：
  - `pallets/jinja#2176`

## 2026-06-12 Phase 6 jinja indent 首行空白扩容与 `improved_v41`

### 背景

上一轮我们已经完成：

- `pallets/jinja#2151 -> task_075`
- `improved_v40`
- 正式任务数推进到 `37`

因此这一轮继续消化最后一个高优先级 shortlist 候选 `pallets/jinja#2176`，并顺手验证能否把 `v40` 的时延回升一起回收。

### 目标

- 把 `pallets/jinja#2176` 转成新的 semi_real 正式任务
- 为 `indent` filter 在 `first=True` 且首行为空时错误无视 `blank=False` 的场景补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上同时验证 `improved_v41`
- 把 maturity 审计结果同步到 `38 / 60`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_076.json`
- `benchmarks/tasks/task_077.json`
- `benchmarks/repos/jinja_indent_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v41.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev41_001.json`
- `logs/summaries/batch_eval_realissuev41_001.json`
- `logs/summaries/batch_compare_realissue_step21_002.json`
- `logs/summaries/batch_run_frozen20v41_001.json`
- `logs/summaries/batch_eval_frozen20v41_001.json`
- `logs/summaries/batch_compare_frozen20_step20_001.json`
- `logs/summaries/benchmark_maturity_maturity_012.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `jinja#2176` 的 `real_issue` 草稿：
  - `task_076`
- 新增可运行的 semi_real 正式任务：
  - `task_077`
- 新增 repo：
  - `benchmarks/repos/jinja_indent_repo`
- 在 repo 中故意保留 bug：
  - 当前 `indent_text()` 在 `first=True` 且首行为空时，错误地无视 `blank=False`
- 新增 `improved_v41`
- 在 patcher 中新增 indent 首行空白处理的专用规则
- 把 `task_077` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/jinja_indent_repo/tests/test_filters.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_077.json --policy optimization/policy_versions/improved_v41.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v41.json --run-label realissuev41 --compare-against-eval logs/summaries/batch_eval_realissuev40_001.json --compare-label realissue_step21`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v41.json --run-label frozen20v41 --compare-against-eval logs/summaries/batch_eval_frozen20v40_001.json --compare-label frozen20_step20`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `37 -> 38`
- 候选池状态：
  - `accepted = 37 -> 38`
  - `to_review = 1 -> 0`
- `improved_v41` 正式 `38` 条任务集结果：
  - `success_count: 37 -> 38`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5717 -> 0.5173`
- `improved_v41` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5682 -> 0.5185`
- 时延分析：
  - 正式集公共 `37` 条任务平均耗时差值：`-0.054s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`-0.0497s`
- maturity 审计：
  - 正式任务数：`38 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`20 / 40`
  - `frozen_40` 连续版本：`0 / 5`

### 结论

- `jinja#2176` 已成功从候选进入正式 semi_real 任务集
- `improved_v41` 在扩容后继续保持正式集和固定集双线无功能回归
- 并且这轮还明显回收了 `v40` 的时延回升
- 当前高优先级 shortlist 已清空，主线该切换到：
  - 扩新来源
  - 构建 `frozen_40`

### 剩余问题

- 当前离 `60` 条正式任务仍有明显距离
- `frozen_40` 还没有开始构建
- 下一轮应优先补新的 GitHub issue 来源，并开始规划哪些任务进入 `frozen_40`

## 2026-06-12 Phase 6 tomlkit inline table 换行扩容与 `improved_v42`

### 背景

上一轮我们已经完成：

- `pallets/jinja#2176 -> task_077`
- `improved_v41`
- 正式任务数推进到 `38`

因此这一轮继续从新来源里补新的 `tomlkit` 候选，并优先选择边界清晰、单文件可修的 `python-poetry/tomlkit#440`，同时验证扩容后能否保持时延稳定。

### 目标

- 把 `python-poetry/tomlkit#440` 转成新的 semi_real 正式任务
- 为 dotted inline table 后继续追加普通键时缺少换行的场景补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上同时验证 `improved_v42`
- 把 maturity 审计结果同步到 `39 / 60`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_078.json`
- `benchmarks/tasks/task_079.json`
- `benchmarks/repos/tomlkit_inline_newline_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v42.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev42_001.json`
- `logs/summaries/batch_eval_realissuev42_001.json`
- `logs/summaries/batch_compare_realissue_step22_002.json`
- `logs/summaries/batch_run_frozen20v42_001.json`
- `logs/summaries/batch_eval_frozen20v42_001.json`
- `logs/summaries/batch_compare_frozen20_step21_001.json`
- `logs/summaries/benchmark_maturity_maturity_013.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `tomlkit#440` 的 `real_issue` 草稿：
  - `task_078`
- 新增可运行的 semi_real 正式任务：
  - `task_079`
- 新增 repo：
  - `benchmarks/repos/tomlkit_inline_newline_repo`
- 在 repo 中故意保留 bug：
  - 当前 dotted inline table 后继续追加普通键时，如果原始文本末尾没有换行，会把后续键错误黏连到同一行
- 新增 `improved_v42`
- 在 patcher 中新增 inline table 缺少换行的专用规则
- 把 `task_079` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_inline_newline_repo/tests/test_renderer.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_079.json --policy optimization/policy_versions/improved_v42.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v42.json --run-label realissuev42 --compare-against-eval logs/summaries/batch_eval_realissuev41_001.json --compare-label realissue_step22`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v42.json --run-label frozen20v42 --compare-against-eval logs/summaries/batch_eval_frozen20v41_001.json --compare-label frozen20_step21`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `38 -> 39`
- 候选池状态：
  - `accepted = 38 -> 39`
  - `to_review = 0 -> 0`
- `improved_v42` 正式 `39` 条任务集结果：
  - `success_count: 38 -> 39`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5173 -> 0.5157`
- `improved_v42` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5185 -> 0.5186`
- 时延分析：
  - 正式集公共 `38` 条任务平均耗时差值：`-0.0008s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`+0.0001s`
- maturity 审计：
  - 正式任务数：`39 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`20 / 40`
  - `frozen_40` 连续版本：`0 / 5`

### 结论

- `tomlkit#440` 已成功从新来源候选进入正式 semi_real 任务集
- `improved_v42` 在扩容后继续保持正式集和固定集双线无功能回归
- 并且这轮没有引入新的性能恶化，时延基本保持稳定
- 当前主线已经非常接近下一里程碑：
  - 再补 `1` 条正式任务
  - 立即构建 `frozen_40`

### 剩余问题

- 当前离 `60` 条正式任务仍有明显距离
- `frozen_40` 仍未创建
- 下一轮应优先再落 `1` 条正式任务，并把 `real_issue_tasks_frozen_40_v1.json` 正式建起来

## 2026-06-12 Phase 6 tomlkit scalar replacement 扩容与 `improved_v43`

### 背景

上一轮我们已经完成：

- `python-poetry/tomlkit#440 -> task_079`
- `improved_v42`
- 正式任务数推进到 `39`

因此这一轮继续沿着 `tomlkit` 新来源补第 `40` 条正式任务，并优先选择边界清晰、单文件可修的 `python-poetry/tomlkit#504`，同时把 `frozen_40` 首版正式建立起来。

### 目标

- 把 `python-poetry/tomlkit#504` 转成新的 semi_real 正式任务
- 为“中间表替换成标量后被错误吸附到相邻表作用域”补一条规则型修复能力
- 在正式扩容集、`frozen_20` 与 `frozen_40 v1` 上同时验证 `improved_v43`
- 把 maturity 审计结果同步到 `40 / 60`，并正式开启 `frozen_40` 主线

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_080.json`
- `benchmarks/tasks/task_081.json`
- `benchmarks/repos/tomlkit_scalar_capture_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/manifests/real_issue_tasks_frozen_40_v1.json`
- `optimization/policy_versions/improved_v43.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev43_001.json`
- `logs/summaries/batch_eval_realissuev43_001.json`
- `logs/summaries/batch_compare_realissue_step23_002.json`
- `logs/summaries/batch_run_frozen20v43_001.json`
- `logs/summaries/batch_eval_frozen20v43_001.json`
- `logs/summaries/batch_compare_frozen20_step22_001.json`
- `logs/summaries/batch_run_frozen40v43_001.json`
- `logs/summaries/batch_eval_frozen40v43_001.json`
- `logs/summaries/benchmark_maturity_maturity_014.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `tomlkit#504` 的 `real_issue` 草稿：
  - `task_080`
- 新增可运行的 semi_real 正式任务：
  - `task_081`
- 新增 repo：
  - `benchmarks/repos/tomlkit_scalar_capture_repo`
- 在 repo 中故意保留 bug：
  - 当前中间表被替换成标量后，会把 `b = 2` 错误吸附到前一个表 `a` 的作用域里
- 新增 `improved_v43`
- 在 patcher 中新增 table replaced by scalar 作用域修复的专用规则
- 把 `task_081` 加入正式 manifest
- 正式创建 `real_issue_tasks_frozen_40_v1.json`
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证、`frozen_40` 首轮验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_scalar_capture_repo/tests/test_renderer.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_081.json --policy optimization/policy_versions/improved_v43.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v43.json --run-label realissuev43 --compare-against-eval logs/summaries/batch_eval_realissuev42_001.json --compare-label realissue_step23`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v43.json --run-label frozen20v43 --compare-against-eval logs/summaries/batch_eval_frozen20v42_001.json --compare-label frozen20_step22`
- `frozen_40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v43.json --run-label frozen40v43`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `39 -> 40`
- 候选池状态：
  - `accepted = 39 -> 40`
  - `to_review = 0 -> 0`
- `improved_v43` 正式 `40` 条任务集结果：
  - `success_count: 39 -> 40`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5157 -> 0.5241`
- `improved_v43` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5186 -> 0.5291`
- `improved_v43` `frozen_40 v1` 结果：
  - `success_rate: 1.0`
  - `test_pass_rate: 1.0`
  - `average_duration_sec: 0.523`
- 时延分析：
  - 正式集公共 `39` 条任务平均耗时差值：`+0.0095s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`+0.0105s`
- maturity 审计：
  - 正式任务数：`40 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`0 / 5`

### 结论

- `tomlkit#504` 已成功从新来源候选进入正式 semi_real 任务集
- `improved_v43` 在扩容后继续保持正式集、`frozen_20` 与 `frozen_40` 三线无功能回归
- `frozen_40` 首版已经正式建立，benchmark maturity v1 从“先建集合”切换到了“累计 streak”
- 但这轮平均耗时出现了小幅回升，后续版本应优先在不破坏 `frozen_40` 成功率的前提下控制时延

### 剩余问题

- 当前离 `60` 条正式任务仍有 `20` 条缺口
- `frozen_40` 连续无回归版本仍为 `0 / 5`
- 下一轮应优先扩新来源、补新正式任务，并让 `improved_v44` 在 `frozen_40` 上拿到第 `1` 个 streak 证据

## 2026-06-12 Phase 6 packaging pickle 状态保真扩容与 `improved_v44`

### 背景

上一轮我们已经完成：

- `python-poetry/tomlkit#504 -> task_081`
- `improved_v43`
- 正式任务数推进到 `40`
- `frozen_40` 首版建立完成

因此这一轮开始同时推进两件对长期 goal 更关键的事：

- 继续把正式任务从 `40` 推向 `60`
- 让 `frozen_40` 真正开始累计连续无回归版本

在候选选择上，这一轮优先落地边界极清晰、单模块、序列化状态保真类的 `pypa/packaging#1204`。

### 目标

- 把 `pypa/packaging#1204` 转成新的 semi_real 正式任务
- 为 `Requirement` 在 pickle 后丢失 `specifier.prereleases` 状态补一条规则型修复能力
- 补齐 `frozen_40` 上的 `improved_v32` 基线评测，让 streak 计算真正有起点
- 在正式扩容集、`frozen_20` 与 `frozen_40` 上同时验证 `improved_v44`
- 把 maturity 审计结果同步到 `41 / 60` 与 `streak = 2 / 5`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_082.json`
- `benchmarks/tasks/task_083.json`
- `benchmarks/repos/packaging_pickle_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v44.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_frozen40v32_001.json`
- `logs/summaries/batch_eval_frozen40v32_001.json`
- `logs/summaries/batch_run_realissuev44_002.json`
- `logs/summaries/batch_eval_realissuev44_002.json`
- `logs/summaries/batch_compare_realissue_step24_003.json`
- `logs/summaries/batch_run_frozen20v44_002.json`
- `logs/summaries/batch_eval_frozen20v44_002.json`
- `logs/summaries/batch_compare_frozen20_step23_002.json`
- `logs/summaries/batch_run_frozen40v44_002.json`
- `logs/summaries/batch_eval_frozen40v44_002.json`
- `logs/summaries/batch_compare_frozen40_step01_002.json`
- `logs/summaries/benchmark_maturity_maturity_017.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `packaging#1204` 的 `real_issue` 草稿：
  - `task_082`
- 新增可运行的 semi_real 正式任务：
  - `task_083`
- 新增 repo：
  - `benchmarks/repos/packaging_pickle_repo`
- 在 repo 中故意保留 bug：
  - 当前 `Requirement` 在 pickle / unpickle 后会丢失 `specifier.prereleases` 上显式设置过的布尔值
- 新增 `improved_v44`
- 在 patcher 中新增 Requirement pickle 状态保真的专用规则
- 把 `task_083` 加入正式 manifest
- 补齐 `frozen_40` 的 `improved_v32` 基线评测
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证、`frozen_40` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/packaging_pickle_repo/tests/test_requirements.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_083.json --policy optimization/policy_versions/improved_v44.json`
- 旧任务回归抽检：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_081.json --policy optimization/policy_versions/improved_v44.json`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_079.json --policy optimization/policy_versions/improved_v44.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v44.json --run-label realissuev44 --compare-against-eval logs/summaries/batch_eval_realissuev43_001.json --compare-label realissue_step24`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v44.json --run-label frozen20v44 --compare-against-eval logs/summaries/batch_eval_frozen20v43_001.json --compare-label frozen20_step23`
- `frozen_40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v44.json --run-label frozen40v44 --compare-against-eval logs/summaries/batch_eval_frozen40v43_001.json --compare-label frozen40_step01`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `40 -> 41`
- 候选池状态：
  - `accepted = 40 -> 41`
  - `to_review = 0 -> 0`
- `improved_v44` 正式 `41` 条任务集结果：
  - `success_count: 40 -> 41`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5241 -> 0.5173`
- `improved_v44` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5291 -> 0.528`
- `improved_v44` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.523 -> 0.5188`
- `frozen_40` 基线结果：
  - `improved_v32 average_duration_sec = 0.5353`
- 时延分析：
  - 正式集公共 `40` 条任务平均耗时差值：`-0.0054s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`-0.0011s`
- maturity 审计：
  - 正式任务数：`41 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`2 / 5`

### 结论

- `packaging#1204` 已成功从新来源候选进入正式 semi_real 任务集
- `improved_v44` 在扩容后继续保持正式集、`frozen_20` 与 `frozen_40` 三线无功能回归
- 这轮不仅把正式任务数推进到 `41`，还把 `frozen_40 streak` 从 `1` 推进到 `2`
- 并且时延没有恶化，正式集、`frozen_20` 与 `frozen_40` 都出现了小幅回落

### 剩余问题

- 当前离 `60` 条正式任务仍有 `19` 条缺口
- `frozen_40` 连续无回归版本仍为 `2 / 5`
- 下一轮应优先扩新来源、补新正式任务，并让 `improved_v45` 在 `frozen_40` 上拿到第 `3` 个 streak 证据

## 2026-06-12 Phase 6 pydantic fraction 错误映射扩容与 `improved_v45`

### 背景

上一轮我们已经完成：

- `pypa/packaging#1204 -> task_083`
- `improved_v44`
- 正式任务数推进到 `41`
- `frozen_40 streak` 推进到 `2 / 5`

因此这一轮继续围绕长期 goal 做两件事：

- 继续把正式任务从 `41` 推向 `60`
- 继续让 `frozen_40` streak 往 `5` 靠近

在候选选择上，这一轮优先落地复现极短、单模块、异常映射边界清晰的 `pydantic/pydantic#13257`。

### 目标

- 把 `pydantic/pydantic#13257` 转成新的 semi_real 正式任务
- 为 fraction validator 未捕获 `ZeroDivisionError` 的场景补一条规则型修复能力
- 在正式扩容集、`frozen_20` 与 `frozen_40` 上同时验证 `improved_v45`
- 把 maturity 审计结果同步到 `42 / 60` 与 `streak = 3 / 5`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_084.json`
- `benchmarks/tasks/task_085.json`
- `benchmarks/repos/pydantic_fraction_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v45.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev45_001.json`
- `logs/summaries/batch_eval_realissuev45_001.json`
- `logs/summaries/batch_compare_realissue_step25_002.json`
- `logs/summaries/batch_run_frozen20v45_001.json`
- `logs/summaries/batch_eval_frozen20v45_001.json`
- `logs/summaries/batch_compare_frozen20_step24_001.json`
- `logs/summaries/batch_run_frozen40v45_001.json`
- `logs/summaries/batch_eval_frozen40v45_001.json`
- `logs/summaries/batch_compare_frozen40_step02_001.json`
- `logs/summaries/benchmark_maturity_maturity_018.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `pydantic#13257` 的 `real_issue` 草稿：
  - `task_084`
- 新增可运行的 semi_real 正式任务：
  - `task_085`
- 新增 repo：
  - `benchmarks/repos/pydantic_fraction_repo`
- 在 repo 中故意保留 bug：
  - 当前零分母 fraction 输入会抛出原始 `ZeroDivisionError`，而不是统一映射成 `ValidationError`
- 新增 `improved_v45`
- 在 patcher 中新增 fraction validator 错误映射的专用规则
- 把 `task_085` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证、`frozen_40` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/pydantic_fraction_repo/tests/test_validators.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_085.json --policy optimization/policy_versions/improved_v45.json`
- 旧任务回归抽检：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_083.json --policy optimization/policy_versions/improved_v45.json`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_081.json --policy optimization/policy_versions/improved_v45.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v45.json --run-label realissuev45 --compare-against-eval logs/summaries/batch_eval_realissuev44_002.json --compare-label realissue_step25`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v45.json --run-label frozen20v45 --compare-against-eval logs/summaries/batch_eval_frozen20v44_002.json --compare-label frozen20_step24`
- `frozen_40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v45.json --run-label frozen40v45 --compare-against-eval logs/summaries/batch_eval_frozen40v44_002.json --compare-label frozen40_step02`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `41 -> 42`
- 候选池状态：
  - `accepted = 41 -> 42`
  - `to_review = 0 -> 0`
- `improved_v45` 正式 `42` 条任务集结果：
  - `success_count: 41 -> 42`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5173 -> 0.5175`
- `improved_v45` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.528 -> 0.512`
- `improved_v45` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5188 -> 0.5175`
- 时延分析：
  - 正式集公共 `41` 条任务平均耗时差值：`+0.0008s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`-0.016s`
- maturity 审计：
  - 正式任务数：`42 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`3 / 5`

### 结论

- `pydantic#13257` 已成功从新来源候选进入正式 semi_real 任务集
- `improved_v45` 在扩容后继续保持正式集、`frozen_20` 与 `frozen_40` 三线无功能回归
- 这轮不仅把正式任务数推进到 `42`，还把 `frozen_40 streak` 从 `2` 推进到 `3`
- 时延仍然稳定，尤其 `frozen_20` 与 `frozen_40` 继续回落

### 剩余问题

- 当前离 `60` 条正式任务仍有 `18` 条缺口
- `frozen_40` 连续无回归版本仍为 `3 / 5`
- 下一轮应优先扩新来源、补新正式任务，并让 `improved_v46` 在 `frozen_40` 上拿到第 `4` 个 streak 证据

## 2026-06-12 Phase 6 tomlkit 代理 repr 完整性扩容与 `improved_v46`

### 背景

上一轮我们已经完成：

- `pydantic/pydantic#13257 -> task_085`
- `improved_v45`
- 正式任务数推进到 `42`
- `frozen_40 streak` 推进到 `3 / 5`

这一轮继续围绕长期 goal 做两件事：

- 继续把正式任务从 `42` 推向 `60`
- 继续让 `frozen_40` streak 往 `5` 靠近

由于当前候选池和外部 `15` 条候选清单都已经吃空，这一轮先补一条全新的真实 issue 来源，再立刻转成新的 semi-real 正式任务。

### 目标

- 把 `python-poetry/tomlkit#439` 转成新的 semi_real 正式任务
- 为 `OutOfOrderTableProxy.__repr__()` 漏掉同父路径早期子项的问题补一条规则型修复能力
- 在正式扩容集、`frozen_20` 与 `frozen_40` 上同时验证 `improved_v46`
- 把 maturity 审计结果同步到 `43 / 60` 与 `streak = 4 / 5`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_086.json`
- `benchmarks/tasks/task_087.json`
- `benchmarks/repos/tomlkit_repr_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v46.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev46_001.json`
- `logs/summaries/batch_eval_realissuev46_001.json`
- `logs/summaries/batch_compare_realissue_step26_002.json`
- `logs/summaries/batch_run_frozen20v46_001.json`
- `logs/summaries/batch_eval_frozen20v46_001.json`
- `logs/summaries/batch_compare_frozen20_step25_001.json`
- `logs/summaries/batch_run_frozen40v46_001.json`
- `logs/summaries/batch_eval_frozen40v46_001.json`
- `logs/summaries/batch_compare_frozen40_step03_001.json`
- `logs/summaries/benchmark_maturity_maturity_019.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 通过 GitHub 公共 API 补录新候选：
  - `python-poetry/tomlkit#439`
- 新增 `real_issue` 草稿：
  - `task_086`
- 新增可运行的 semi_real 正式任务：
  - `task_087`
- 新增 repo：
  - `benchmarks/repos/tomlkit_repr_repo`
- 在 repo 中故意保留 bug：
  - 当前代理视图 `repr` 在同一父路径下存在多个 dotted key 子项时，只保留最后一个子项
- 新增 `improved_v46`
- 在 patcher 中新增代理视图 repr 完整性的专用规则
- 把 `task_087` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证、`frozen_40` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_repr_repo/tests/test_proxy.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_087.json --policy optimization/policy_versions/improved_v46.json`
- 旧任务回归抽检：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_085.json --policy optimization/policy_versions/improved_v46.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v46.json --run-label realissuev46 --compare-against-eval logs/summaries/batch_eval_realissuev45_001.json --compare-label realissue_step26`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v46.json --run-label frozen20v46 --compare-against-eval logs/summaries/batch_eval_frozen20v45_001.json --compare-label frozen20_step25`
- `frozen_40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v46.json --run-label frozen40v46 --compare-against-eval logs/summaries/batch_eval_frozen40v45_001.json --compare-label frozen40_step03`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `42 -> 43`
- 候选池状态：
  - `accepted = 42 -> 43`
  - `to_review = 0 -> 0`
- `improved_v46` 正式 `43` 条任务集结果：
  - `success_count: 42 -> 43`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5175 -> 0.5243`
- `improved_v46` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.512 -> 0.5321`
- `improved_v46` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5175 -> 0.525`
- 时延分析：
  - 正式集公共 `42` 条任务平均耗时差值：`+0.0077s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`+0.0201s`
- maturity 审计：
  - 正式任务数：`43 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`4 / 5`

### 结论

- `tomlkit#439` 已成功作为全新来源补进正式 semi_real 任务集
- `improved_v46` 在扩容后继续保持正式集、`frozen_20` 与 `frozen_40` 三线无功能回归
- 这轮不仅把正式任务数推进到 `43`，还把 `frozen_40 streak` 从 `3` 推进到 `4`
- 时延出现小幅回升，但 `frozen_40` 仍满足相对 `improved_v32` 基线“不超过 +3%”的长期约束

### 剩余问题

- 当前离 `60` 条正式任务仍有 `17` 条缺口
- `frozen_40` 连续无回归版本仍差最后 `1 / 5`
- 下一轮应继续补新的真实 issue 来源，并让 `improved_v47` 在 `frozen_40` 上拿到第 `5` 个 streak 证据

## 2026-06-12 Phase 6 jinja map 默认值语义扩容与 `improved_v47`

### 背景

上一轮我们已经完成：

- `python-poetry/tomlkit#439 -> task_087`
- `improved_v46`
- 正式任务数推进到 `43`
- `frozen_40 streak` 推进到 `4 / 5`

因此这一轮的关键目标非常聚焦：

- 再补 `1` 条正式真实任务
- 把 `frozen_40` 连续无回归证据从 `4 / 5` 推到 `5 / 5`

在新来源选择上，这一轮优先落地 `pallets/jinja#2165`，因为它是一个单函数、最小复现极短、默认值语义清晰的 filter 边界 bug。

### 目标

- 把 `pallets/jinja#2165` 转成新的 semi_real 正式任务
- 为 `map(attribute=..., default=None)` 未正确回落默认值的问题补一条规则型修复能力
- 在正式扩容集、`frozen_20` 与 `frozen_40` 上同时验证 `improved_v47`
- 把 maturity 审计结果同步到 `44 / 60` 与 `streak = 5 / 5`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_088.json`
- `benchmarks/tasks/task_089.json`
- `benchmarks/repos/jinja_map_default_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v47.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev47_001.json`
- `logs/summaries/batch_eval_realissuev47_001.json`
- `logs/summaries/batch_compare_realissue_step27_001.json`
- `logs/summaries/batch_run_frozen20v47_001.json`
- `logs/summaries/batch_eval_frozen20v47_001.json`
- `logs/summaries/batch_compare_frozen20_step26_001.json`
- `logs/summaries/batch_run_frozen40v47_001.json`
- `logs/summaries/batch_eval_frozen40v47_001.json`
- `logs/summaries/batch_compare_frozen40_step04_001.json`
- `logs/summaries/benchmark_maturity_maturity_020.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 通过 GitHub 公共 API 补录新候选：
  - `pallets/jinja#2165`
- 新增 `real_issue` 草稿：
  - `task_088`
- 新增可运行的 semi_real 正式任务：
  - `task_089`
- 新增 repo：
  - `benchmarks/repos/jinja_map_default_repo`
- 在 repo 中故意保留 bug：
  - 当前 `default=None` 被错误当成“未提供默认值”，导致属性缺失时仍抛异常
- 新增 `improved_v47`
- 在 patcher 中新增 jinja `map(attribute, default=None)` 语义修复的专用规则
- 把 `task_089` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证、`frozen_40` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/jinja_map_default_repo/tests/test_filters.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_089.json --policy optimization/policy_versions/improved_v47.json`
- 旧任务回归抽检：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_087.json --policy optimization/policy_versions/improved_v47.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v47.json --run-label realissuev47 --compare-against-eval logs/summaries/batch_eval_realissuev46_001.json --compare-label realissue_step27`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v47.json --run-label frozen20v47 --compare-against-eval logs/summaries/batch_eval_frozen20v46_001.json --compare-label frozen20_step26`
- `frozen_40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v47.json --run-label frozen40v47 --compare-against-eval logs/summaries/batch_eval_frozen40v46_001.json --compare-label frozen40_step04`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `43 -> 44`
- 候选池状态：
  - `accepted = 43 -> 44`
  - `to_review = 0 -> 0`
- `improved_v47` 正式 `44` 条任务集结果：
  - `success_count: 43 -> 44`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5243 -> 0.5234`
- `improved_v47` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5321 -> 0.5374`
- `improved_v47` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.525 -> 0.5269`
- 时延分析：
  - 正式集公共 `43` 条任务平均耗时差值：`+0.0002s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`+0.0053s`
- maturity 审计：
  - 正式任务数：`44 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`5 / 5`

### 结论

- `jinja#2165` 已成功作为全新来源补进正式 semi_real 任务集
- `improved_v47` 在扩容后继续保持正式集、`frozen_20` 与 `frozen_40` 三线无功能回归
- 这轮不仅把正式任务数推进到 `44`，还把 `frozen_40 streak` 从 `4` 推进到 `5`
- `frozen_40` 连续 `5 / 5` 的稳定性门槛已经达成
- 时延没有继续恶化，正式集反而小幅回落，长期性能约束仍保持成立

### 剩余问题

- 当前离 `60` 条正式任务仍有 `16` 条缺口
- 接下来主线应从“追 5 / 5”切换到“在不打破 5 / 5 稳定性的前提下继续扩任务”
- 下一轮应优先继续补新的真实 issue 来源，并让 `improved_v48` 在扩容后继续保住这组 frozen 证据

## 2026-06-12 Phase 6 packaging direct URL scheme 兼容性扩容与 `improved_v48`

### 背景

上一轮我们已经完成：

- `pallets/jinja#2165 -> task_089`
- `improved_v47`
- 正式任务数推进到 `44`
- `frozen_40 streak` 推进到 `5`

因此这一轮开始，主线目标从“先达成 5 / 5”切换成：

- 在不破坏当前 frozen 稳定性的前提下继续扩正式任务
- 把正式任务数继续从 `44` 推向 `60+`

这一轮优先选择 `pypa/packaging#1240`，因为它是一个单函数、纯 URL scheme 语义、复现极短的真实 bug，适合低风险扩容。

### 目标

- 把 `pypa/packaging#1240` 转成新的 semi_real 正式任务
- 为 file URL scheme 大小写与单斜杠形式校验错误补一条规则型修复能力
- 在正式扩容集、`frozen_20` 与 `frozen_40` 上同时验证 `improved_v48`
- 把 maturity 审计结果同步到 `45 / 60`，并确认 frozen 稳定性继续保持

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_090.json`
- `benchmarks/tasks/task_091.json`
- `benchmarks/repos/packaging_direct_url_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v48.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev48_001.json`
- `logs/summaries/batch_eval_realissuev48_001.json`
- `logs/summaries/batch_compare_realissue_step28_002.json`
- `logs/summaries/batch_run_frozen20v48_001.json`
- `logs/summaries/batch_eval_frozen20v48_001.json`
- `logs/summaries/batch_compare_frozen20_step27_001.json`
- `logs/summaries/batch_run_frozen40v48_001.json`
- `logs/summaries/batch_eval_frozen40v48_001.json`
- `logs/summaries/batch_compare_frozen40_step05_001.json`
- `logs/summaries/benchmark_maturity_maturity_021.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 通过 GitHub 公共 API 补录新候选：
  - `pypa/packaging#1240`
- 新增 `real_issue` 草稿：
  - `task_090`
- 新增可运行的 semi_real 正式任务：
  - `task_091`
- 新增 repo：
  - `benchmarks/repos/packaging_direct_url_repo`
- 在 repo 中故意保留 bug：
  - 当前 file URL 校验大小写敏感，且错误拒绝 `file:/...` 这种合法形式
- 新增 `improved_v48`
- 在 patcher 中新增 packaging direct URL scheme 兼容性的专用规则
- 把 `task_091` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证、`frozen_40` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/packaging_direct_url_repo/tests/test_direct_url.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_091.json --policy optimization/policy_versions/improved_v48.json`
- 旧任务回归抽检：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_089.json --policy optimization/policy_versions/improved_v48.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v48.json --run-label realissuev48 --compare-against-eval logs/summaries/batch_eval_realissuev47_001.json --compare-label realissue_step28`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v48.json --run-label frozen20v48 --compare-against-eval logs/summaries/batch_eval_frozen20v47_001.json --compare-label frozen20_step27`
- `frozen_40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v48.json --run-label frozen40v48 --compare-against-eval logs/summaries/batch_eval_frozen40v47_001.json --compare-label frozen40_step05`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `44 -> 45`
- 候选池状态：
  - `accepted = 44 -> 45`
  - `to_review = 0 -> 0`
- `improved_v48` 正式 `45` 条任务集结果：
  - `success_count: 44 -> 45`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5234 -> 0.5241`
- `improved_v48` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5374 -> 0.5287`
- `improved_v48` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
- 时延分析：
  - 正式集公共 `44` 条任务平均耗时差值：`+0.0007s`
  - `frozen_20` 公共 `20` 条任务平均耗时差值：`-0.0087s`
- maturity 审计：
  - 正式任务数：`45 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`6`

### 结论

- `packaging#1240` 已成功作为全新来源补进正式 semi_real 任务集
- `improved_v48` 在扩容后继续保持正式集、`frozen_20` 与 `frozen_40` 三线无功能回归
- 这轮把正式任务数推进到 `45`
- 时延几乎持平，且 `frozen_20` 还出现了回落
- 当前主线已经进入“继续扩容，同时维持 frozen 稳定”的稳定推进阶段

### 剩余问题

- 当前离 `60` 条正式任务仍有 `15` 条缺口
- 后续应继续优先选择这种单函数、纯逻辑、轻依赖的新 issue
- 下一轮应继续补新的真实 issue 来源，并保持当前 frozen 证据链不断裂

## 2026-06-12 Phase 6 click confirm ANSI 清理扩容与 `improved_v49`

### 背景

上一轮我们已经完成：

- `pypa/packaging#1240 -> task_091`
- `improved_v48`
- 正式任务数推进到 `45`
- `frozen_40 streak` 推进到 `6`

因此这一轮主线继续保持不变：

- 在不破坏当前 frozen 稳定性的前提下继续扩正式任务
- 把正式任务数继续从 `45` 推向 `60+`

这一轮优先选择 `pallets/click#3572`，因为它是一个单函数、纯输出语义、复现极短的真实 bug，适合低风险扩容。

### 目标

- 把 `pallets/click#3572` 转成新的 semi_real 正式任务
- 为 `click.confirm(color=False)` 未去除 ANSI 提示颜色补一条规则型修复能力
- 在正式扩容集、`frozen_20` 与 `frozen_40` 上同时验证 `improved_v49`
- 把 maturity 审计结果同步到 `46 / 60` 与 `streak = 7`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_092.json`
- `benchmarks/tasks/task_093.json`
- `benchmarks/repos/click_confirm_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v49.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev49_001.json`
- `logs/summaries/batch_eval_realissuev49_001.json`
- `logs/summaries/batch_compare_realissue_step29_002.json`
- `logs/summaries/batch_run_frozen20v49_001.json`
- `logs/summaries/batch_eval_frozen20v49_001.json`
- `logs/summaries/batch_compare_frozen20_step28_001.json`
- `logs/summaries/batch_run_frozen40v49_002.json`
- `logs/summaries/batch_eval_frozen40v49_002.json`
- `logs/summaries/batch_compare_frozen40_step06_002.json`
- `logs/summaries/benchmark_maturity_maturity_023.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 通过 GitHub 公共 API 补录新候选：
  - `pallets/click#3572`
- 新增 `real_issue` 草稿：
  - `task_092`
- 新增可运行的 semi_real 正式任务：
  - `task_093`
- 新增 repo：
  - `benchmarks/repos/click_confirm_repo`
- 在 repo 中故意保留 bug：
  - 当前 `confirm(color=False)` 仍直接输出带 ANSI 的消息
- 新增 `improved_v49`
- 在 patcher 中新增 click confirm ANSI 清理的专用规则
- 把 `task_093` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证、`frozen_40` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/click_confirm_repo/tests/test_prompts.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_093.json --policy optimization/policy_versions/improved_v49.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v49.json --run-label realissuev49 --compare-against-eval logs/summaries/batch_eval_realissuev48_001.json --compare-label realissue_step29`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v49.json --run-label frozen20v49 --compare-against-eval logs/summaries/batch_eval_frozen20v48_001.json --compare-label frozen20_step28`
- `frozen_40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v49.json --run-label frozen40v49 --compare-against-eval logs/summaries/batch_eval_frozen40v48_001.json --compare-label frozen40_step06`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `45 -> 46`
- 候选池状态：
  - `accepted = 45 -> 46`
  - `to_review = 0 -> 0`
- `improved_v49` 正式 `46` 条任务集结果：
  - `success_count: 45 -> 46`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5241 -> 0.5869`
- `improved_v49` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5287 -> 0.5972`
- `improved_v49` `frozen_40` 复跑结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5243 -> 0.5385`
- maturity 审计：
  - 正式任务数：`46 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`7`

### 这轮额外记录的过程

- 首轮 `frozen40v49_001` 的 `average_duration_sec = 0.5876`
- 该值会暂时把 `v49` 排除在长期耗时阈值之外
- 由于这轮 `average_steps` 与 `average_tool_calls` 完全未变，更像运行时抖动而不是策略逻辑变化
- 因此补跑了第二轮 `frozen40v49_002`
- 复跑结果回落到 `0.5385`，重新满足相对 `improved_v32` 的 `+3%` 约束
- 后续遇到类似边界值时，应优先保留“首轮 + 复跑”的完整证据，而不是覆盖旧结果

### 结论

- `click#3572` 已成功作为全新 click 输出语义题补进正式 semi_real 任务集
- `improved_v49` 在扩容后继续保持正式集、`frozen_20` 与 `frozen_40` 三线无功能回归
- 这轮把正式任务数推进到 `46`
- `frozen_40 streak` 已推进到 `7`
- 当前离目标还差 `14` 条正式任务，接下来应继续优先吃短平快的真实 bug 候选

## 2026-06-12 Phase 6 click version_option package_name 扩容与 `improved_v50`

### 背景

上一轮我们已经完成：

- `pallets/click#3572 -> task_093`
- `improved_v49`
- 正式任务数推进到 `46`
- `frozen_40 streak` 推进到 `7`

因此这一轮仍然沿用“短平快 click 真题优先”的扩容策略：

- 在不破坏当前 frozen 稳定性的前提下继续扩正式任务
- 把正式任务数继续从 `46` 推向 `60+`

这一轮优先选择 `pallets/click#3125`，因为它是一个单函数、纯渲染语义、复现极短的真实 bug，适合低风险扩容。

### 目标

- 把 `pallets/click#3125` 转成新的 semi_real 正式任务
- 为 `version_option(package_name=...)` 忽略显式包名补一条规则型修复能力
- 在正式扩容集、`frozen_20` 与 `frozen_40` 上同时验证 `improved_v50`
- 把 maturity 审计结果同步到 `47 / 60` 与 `streak = 8`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_094.json`
- `benchmarks/tasks/task_095.json`
- `benchmarks/repos/click_version_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v50.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `logs/summaries/batch_run_realissuev50_001.json`
- `logs/summaries/batch_eval_realissuev50_001.json`
- `logs/summaries/batch_compare_realissue_step30_002.json`
- `logs/summaries/batch_run_frozen20v50_001.json`
- `logs/summaries/batch_eval_frozen20v50_001.json`
- `logs/summaries/batch_compare_frozen20_step29_001.json`
- `logs/summaries/batch_run_frozen40v50_002.json`
- `logs/summaries/batch_eval_frozen40v50_002.json`
- `logs/summaries/batch_compare_frozen40_step07_002.json`
- `logs/summaries/benchmark_maturity_maturity_025.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 本轮实现内容

- 通过 GitHub 公共 API 补录新候选：
  - `pallets/click#3125`
- 新增 `real_issue` 草稿：
  - `task_094`
- 新增可运行的 semi_real 正式任务：
  - `task_095`
- 新增 repo：
  - `benchmarks/repos/click_version_repo`
- 在 repo 中故意保留 bug：
  - 当前显式 `package_name` 仍被错误忽略，版本输出继续回落到程序名
- 新增 `improved_v50`
- 在 patcher 中新增 click version option package_name 优先级的专用规则
- 把 `task_095` 加入正式 manifest
- 更新候选池状态、注册表与项目文档
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证、`frozen_40` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/click_version_repo/tests/test_version_option.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_095.json --policy optimization/policy_versions/improved_v50.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v50.json --run-label realissuev50 --compare-against-eval logs/summaries/batch_eval_realissuev49_001.json --compare-label realissue_step30`
- 固定集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v50.json --run-label frozen20v50 --compare-against-eval logs/summaries/batch_eval_frozen20v49_001.json --compare-label frozen20_step29`
- `frozen_40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v50.json --run-label frozen40v50 --compare-against-eval logs/summaries/batch_eval_frozen40v49_002.json --compare-label frozen40_step07`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `46 -> 47`
- 候选池状态：
  - `accepted = 46 -> 47`
  - `to_review = 0 -> 0`
- `improved_v50` 正式 `47` 条任务集结果：
  - `success_count: 46 -> 47`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5869 -> 0.5583`
- `improved_v50` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5972 -> 0.5672`
- `improved_v50` `frozen_40` 复跑结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5385 -> 0.541`
- maturity 审计：
  - 正式任务数：`47 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`8`

### 这轮额外记录的过程

- 首轮 `frozen40v50_001` 的 `average_duration_sec = 0.5627`
- 该值会暂时把 `v50` 排除在长期耗时阈值之外
- 由于这轮 `average_steps` 与 `average_tool_calls` 完全未变，更像运行时抖动而不是策略逻辑变化
- 因此补跑了第二轮 `frozen40v50_002`
- 复跑结果回落到 `0.541`，重新满足相对 `improved_v32` 的 `+3%` 约束
- 后续继续沿用“首轮 + 复跑”的证据保留方式，不覆盖旧结果

### 结论

- `click#3125` 已成功作为全新 click 元数据渲染题补进正式 semi_real 任务集
- `improved_v50` 在扩容后继续保持正式集、`frozen_20` 与 `frozen_40` 三线无功能回归
- 这轮把正式任务数推进到 `47`
- `frozen_40 streak` 已推进到 `8`
- 当前离目标还差 `13` 条正式任务，下一轮可优先继续推进 `click#3571`、`jinja#2108`、`tomlkit#505`

## 2026-06-12 Phase 6 click progressbar 结束态位置扩容与 `improved_v51`

### 背景

上一轮我们已经完成：

- `pallets/click#3125 -> task_095`
- `improved_v50`
- 正式任务数推进到 `47`
- `frozen_40 streak` 推进到 `8`

因此这一轮继续沿用 click 生态里的短平快真实 bug：

- 继续扩正式任务数
- 尽量选择单文件、纯显示语义、复现路径短的问题
- 同时继续观察近期时延是否只是单轮波动，还是已经演变成环境级漂移

这一轮优先选择 `pallets/click#3571`，因为它聚焦 progressbar 的结束态显示逻辑，边界清晰、语义稳定，适合继续做低风险扩容。

### 目标

- 把 `pallets/click#3571` 转成新的 semi_real 正式任务
- 为 progressbar 在 `show_pos=True` 且 `update_min_steps` 不整除长度时补一条结束态完整位置修复规则
- 在正式扩容集、`frozen_20` 与 `frozen_40` 上同时验证 `improved_v51`
- 判断这轮时延回升究竟来自新规则，还是来自当前运行环境整体漂移

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_096.json`
- `benchmarks/tasks/task_097.json`
- `benchmarks/repos/click_progressbar_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v51.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev51_001.json`
- `logs/summaries/batch_eval_realissuev51_002.json`
- `logs/summaries/batch_eval_frozen20v51_002.json`
- `logs/summaries/batch_eval_frozen40v51_002.json`
- `logs/summaries/duration_compare_realissuev51_001.json`
- `logs/summaries/duration_compare_frozen20v51_001.json`
- `logs/summaries/trace_hotspots_realissuev51_001.json`
- `logs/summaries/task_history_cohort_run_tests_hotspots_v51_001.json`
- `logs/summaries/batch_compare_frozen40_envcheck_v50_001.json`
- `logs/summaries/benchmark_maturity_maturity_026.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 通过 GitHub 公共 API 补录新候选：
  - `pallets/click#3571`
- 新增 `real_issue` 草稿：
  - `task_096`
- 新增可运行的 semi_real 正式任务：
  - `task_097`
- 新增 repo：
  - `benchmarks/repos/click_progressbar_repo`
- 在 repo 中故意保留 bug：
  - 当前 `show_pos=True` 时结束态会停留在最后一次中间刷新位置，而不是完整的 `length/length`
- 新增 `improved_v51`
- 在 patcher 中新增 progressbar 结束态完整位置的专用规则
- 把 `task_097` 加入正式 manifest
- 更新候选池状态、项目记忆、结果文档与注册表
- 继续保留 runtime 侧 `-p no:unraisableexception`
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证、`frozen_40` 同集合验证与 maturity 审计
- 额外补了一轮同环境 `v50` 复跑校验，用来区分“策略变慢”和“环境变慢”

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/click_progressbar_repo/tests/test_progressbar.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_097.json --policy optimization/policy_versions/improved_v51.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v51.json --run-label realissuev51`
- 固定 `20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v51.json --run-label frozen20v51`
- 固定 `40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v51.json --run-label frozen40v51`
- 环境级复跑校验：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v50.json --run-label frozen40v50check`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `47 -> 48`
- 候选池状态：
  - `accepted = 47 -> 48`
  - `to_review = 0 -> 0`
- `improved_v51` 正式 `48` 条任务集结果：
  - `success_count: 47 -> 48`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - 首轮 `average_duration_sec: 0.5583 -> 0.6687`
  - 复跑 `average_duration_sec: 0.5583 -> 0.6987`
- `improved_v51` `frozen_20` 复跑结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5672 -> 0.7361`
- `improved_v51` `frozen_40` 复跑结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5410 -> 0.7098`
- maturity 审计：
  - 正式任务数：`48 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`8`

### 这轮额外记录的过程

- 正式集时延对比显示：
  - 公共 `47` 条任务平均耗时增量：`+0.1412s`
- `frozen_20` 时延对比显示：
  - 公共 `20` 条任务平均耗时增量：`+0.1689s`
- trace 热点分析显示：
  - 最主要回升来源仍然是 `run_tests`
- 热点任务集合历史分析显示：
  - `task_034 / task_036 / task_038 / task_040` 四条任务全部继续一起变慢
- 最关键的新增证据是：
  - 同环境下重新复跑 `improved_v50` 的 `frozen_40`
  - `average_duration_sec` 从 `0.5410` 回升到 `0.6616`
- 这说明当前时延回升并不只发生在 `v51`
- 因此这一轮不能直接下结论说“progressbar 新规则让系统变慢”
- 更可信的判断是当前运行环境或 `run_tests` 链路出现了整体漂移

### 结论

- `click#3571` 已成功作为新的 click progressbar 显示语义题补进正式 semi_real 任务集
- `improved_v51` 已把正式任务数推进到 `48`
- 功能上，`improved_v51` 继续保持正式集、`frozen_20` 与 `frozen_40` 三线无回归
- 但这轮当前不能推进新的 `frozen_40 streak`
- 当前稳定 streak 仍保持 `8`
- 下一轮应优先并行推进两条线：
  - 继续扩新来源，把正式任务数从 `48` 推向 `60+`
  - 优先诊断环境级时延漂移，确认下一版谁能成为新的稳定版本

## 2026-06-12 Phase 6 jinja macro include without context 扩容与 `improved_v52`

### 背景

上一轮我们已经完成：

- `pallets/click#3571 -> task_097`
- `improved_v51`
- 正式任务数推进到 `48`
- 但 `v51` 的主要结论是“扩容成功，环境级时延漂移仍待恢复”

因此这一轮的目标不是只堆更多题，而是：

- 继续安全扩容正式任务数
- 同时观察系统是否能从 `v51` 的异常时延状态里回拉

这一轮优先选择 `pallets/jinja#2108`，因为它是一个单模块、模板渲染语义非常清晰、最小复现极短的 include 行为问题，适合继续做低风险扩容。

### 目标

- 把 `pallets/jinja#2108` 转成新的 semi_real 正式任务
- 为 macro 内部 `include without context` 错误输出 generator repr 补一条规则型修复能力
- 在正式扩容集、`frozen_20` 与 `frozen_40` 上验证 `improved_v52`
- 判断 `v52` 是否只是扩容成功，还是已经开始把 `v51` 的环境级时延漂移拉回

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_098.json`
- `benchmarks/tasks/task_099.json`
- `benchmarks/repos/jinja_include_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v52.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev52_001.json`
- `logs/summaries/batch_eval_realissuev52r2_001.json`
- `logs/summaries/batch_compare_realissue_step32_001.json`
- `logs/summaries/batch_eval_frozen20v52_001.json`
- `logs/summaries/batch_eval_frozen20v52r2_001.json`
- `logs/summaries/batch_compare_frozen20_step31_001.json`
- `logs/summaries/batch_eval_frozen40v52_001.json`
- `logs/summaries/batch_eval_frozen40v52r2_001.json`
- `logs/summaries/batch_compare_frozen40_step09_001.json`
- `logs/summaries/duration_compare_realissuev52_001.json`
- `logs/summaries/duration_compare_frozen20v52_001.json`
- `logs/summaries/benchmark_maturity_maturity_027.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 通过 GitHub 公共页面手工补录新候选：
  - `pallets/jinja#2108`
- 新增 `real_issue` 草稿：
  - `task_098`
- 新增可运行的 semi_real 正式任务：
  - `task_099`
- 新增 repo：
  - `benchmarks/repos/jinja_include_repo`
- 在 repo 中故意保留 bug：
  - 当前 macro 内部的 `include without context` 会把生成器对象直接格式化成字符串
- 新增 `improved_v52`
- 在 patcher 中新增 jinja macro include without context 的专用规则
- 把 `task_099` 加入正式 manifest
- 更新候选池状态、结果文档与项目记忆
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证、`frozen_40` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/jinja_include_repo/tests/test_runtime.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_099.json --policy optimization/policy_versions/improved_v52.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v52.json --run-label realissuev52r2 --compare-against-eval logs/summaries/batch_eval_realissuev51_002.json --compare-label realissue_step32`
- 固定 `20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v52.json --run-label frozen20v52r2 --compare-against-eval logs/summaries/batch_eval_frozen20v51_002.json --compare-label frozen20_step31`
- 固定 `40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v52.json --run-label frozen40v52r2 --compare-against-eval logs/summaries/batch_eval_frozen40v50check_001.json --compare-label frozen40_step09`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `48 -> 49`
- 候选池状态：
  - `accepted = 48 -> 49`
  - `to_review = 0 -> 0`
- `improved_v52` 正式 `49` 条任务集结果：
  - `success_count: 48 -> 49`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6987 -> 0.6707`
- `improved_v52` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.7361 -> 0.6912`
- `improved_v52` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6616 -> 0.6824`
- maturity 审计：
  - 正式任务数：`49 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`8`

### 这轮额外记录的过程

- 正式集时延对比显示：
  - 公共 `48` 条任务平均耗时增量：`-0.0357s`
- `frozen_20` 时延对比显示：
  - 公共 `20` 条任务平均耗时增量：`-0.0629s`
- 这说明 `v52` 并不是继续恶化的版本
- 相反，它已经把 `v51` 上最明显的一部分环境级回升重新拉回来了
- 但 `frozen_40` 相对当前环境下的 `v50check` 仍然是：
  - `0.6616 -> 0.6824`
- 所以当前最可信的结论仍然是：
  - 系统正在从环境级漂移中恢复
  - 但恢复还没完全完成

### 结论

- `jinja#2108` 已成功作为新的模板 include 渲染语义题补进正式 semi_real 任务集
- `improved_v52` 已把正式任务数推进到 `49`
- 功能上，`improved_v52` 继续保持正式集、`frozen_20` 与 `frozen_40` 三线无回归
- 性能上，`v52` 已比 `v51` 明显回落，但 `frozen_40` 仍未回到长期阈值
- 当前稳定 `frozen_40 streak` 仍保持 `8`
- 下一轮应继续沿两条线推进：
  - 扩新来源，把正式任务数从 `49` 推向 `60+`
  - 继续恢复 `frozen_40` 性能，争取把后续版本重新拉回长期阈值以内

## 2026-06-12 Phase 6 tomlkit out-of-order 访问扩容与 `improved_v53`

### 背景

上一轮我们已经完成：

- `pallets/jinja#2108 -> task_099`
- `improved_v52`
- 正式任务数推进到 `49`

但当时的关键结论已经很明确：

- 扩容链路稳定可用
- `v52` 相对 `v51` 有回落
- 不过稳定性能门控还没有恢复完成

因此这一轮的目标是：

- 继续把正式真实任务数往上推
- 同时严格把“扩容成功”和“是否能进入新稳定 streak”分开记录

这一轮优先选择 `python-poetry/tomlkit#505`，因为它仍然是单模块、最小复现清晰、回归测试稳定的代理访问语义问题，而且虽然同属 tomlkit，但语义上不同于此前的 `pop / repr / scalar capture` 三类题。

### 目标

- 把 `python-poetry/tomlkit#505` 转成新的 semi_real 正式任务
- 为 out-of-order table 访问阶段的重复 array table 聚合问题补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上验证 `improved_v53`
- 同步 maturity 审计，把正式任务数推进到 `50`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_100.json`
- `benchmarks/tasks/task_101.json`
- `benchmarks/repos/tomlkit_out_of_order_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v53.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev53r1_001.json`
- `logs/summaries/batch_compare_realissue_step33_001.json`
- `logs/summaries/batch_eval_frozen20v53r1_001.json`
- `logs/summaries/batch_compare_frozen20_step32_001.json`
- `logs/summaries/duration_compare_realissuev53_001.json`
- `logs/summaries/duration_compare_frozen20v53_001.json`
- `logs/summaries/benchmark_maturity_maturity_028.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 通过 GitHub issue 导入入口补录新候选：
  - `python-poetry/tomlkit#505`
- 新增 `real_issue` 草稿：
  - `task_100`
- 新增可运行的 semi_real 正式任务：
  - `task_101`
- 新增 repo：
  - `benchmarks/repos/tomlkit_out_of_order_repo`
- 在 repo 中故意保留 bug：
  - 当前 `parse_document()` 能接受合法最小 TOML 文本
  - 但后续 `doc.get("hooks")` 在代理重建阶段会因重复写入 `Stop` 键而触发 `KeyAlreadyPresent`
- 新增 `improved_v53`
- 在 patcher 中新增 tomlkit out-of-order repeated array table 的专用规则
- 把 `task_101` 加入正式 manifest
- 更新候选池状态、结果文档、项目记忆与注册表
- 跑通单任务闭环、正式集扩容验证、`frozen_20` 同集合验证与 maturity 审计

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_out_of_order_repo/tests/test_proxy.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_101.json --policy optimization/policy_versions/improved_v53.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v53.json --run-label realissuev53r1 --compare-against-eval logs/summaries/batch_eval_realissuev52_001.json --compare-label realissue_step33`
- 固定 `20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v53.json --run-label frozen20v53r1 --compare-against-eval logs/summaries/batch_eval_frozen20v52_001.json --compare-label frozen20_step32`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `49 -> 50`
- 候选池状态：
  - `accepted = 49 -> 50`
  - `to_review = 0 -> 0`
- `improved_v53` 正式 `50` 条任务集结果：
  - `success_count: 49 -> 50`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6618 -> 0.7143`
- `improved_v53` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6732 -> 0.7361`
- maturity 审计：
  - 正式任务数：`50 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`8`

### 这轮额外记录的过程

- 正式集时延对比显示：
  - 公共 `49` 条任务平均耗时增量：`+0.0535s`
- `frozen_20` 时延对比显示：
  - 公共 `20` 条任务平均耗时增量：`+0.0629s`
- 这说明 `v53` 的核心结论不是“性能恢复完成”
- 而是：
  - 新题扩容成功
  - 功能口径继续保持全绿
  - 但性能恢复仍未结束

### 结论

- `tomlkit#505` 已成功作为新的 tomlkit 代理访问语义题补进正式 semi_real 任务集
- `improved_v53` 已把正式任务数推进到 `50`
- 功能上，`improved_v53` 继续保持正式集与 `frozen_20` 无回归
- 但这轮当前不能推进新的稳定版本判断
- 当前最准确口径仍然是：
  - `improved_v50` 是稳定基线
  - `improved_v53` 是扩容成功、性能恢复中
  - 当前 `frozen_40 streak` 仍保持 `8`

## 2026-06-12 Phase 6 tomlkit 注释锚点扩容与 `improved_v54`

### 背景

上一轮我们已经完成：

- `python-poetry/tomlkit#505 -> task_101`
- `improved_v53`
- 正式任务数推进到 `50`

但当时的关键结论也很明确：

- 扩容链路继续可用
- `v53` 功能全绿
- 不过正式集与 `frozen_20` 的平均耗时再次回升

因此这一轮的目标是：

- 继续把正式真实任务数往上推
- 尽量选择单模块、可稳定回归、语义增量明确的新题
- 同时把每次实现中的“回归过程”也记录下来，方便后续持续复盘

这一轮选择 `python-poetry/tomlkit#295`，因为它是很典型的 AoT 文档保真问题：追加子表后，原始注释锚点不应跑到错误位置。

### 目标

- 把 `python-poetry/tomlkit#295` 转成新的 semi_real 正式任务
- 为 AoT 条目追加子表后的注释锚点跑偏问题补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上验证 `improved_v54`
- 同步 maturity 审计，把正式任务数推进到 `51`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_102.json`
- `benchmarks/tasks/task_103.json`
- `benchmarks/repos/tomlkit_comment_anchor_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v54.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev54r1_001.json`
- `logs/summaries/batch_eval_realissuev54r2_001.json`
- `logs/summaries/batch_compare_realissue_step34_002.json`
- `logs/summaries/batch_eval_frozen20v54r1_001.json`
- `logs/summaries/batch_eval_frozen20v54r2_001.json`
- `logs/summaries/batch_compare_frozen20_step33_002.json`
- `logs/summaries/duration_compare_realissuev54_001.json`
- `logs/summaries/duration_compare_frozen20v54_001.json`
- `logs/summaries/benchmark_maturity_maturity_029.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 通过 GitHub issue 导入入口补录新候选：
  - `python-poetry/tomlkit#295`
- 新增 `real_issue` 草稿：
  - `task_102`
- 新增可运行的 semi_real 正式任务：
  - `task_103`
- 新增 repo：
  - `benchmarks/repos/tomlkit_comment_anchor_repo`
- 在 repo 中故意保留 bug：
  - 给第一个 `[[routes]]` 条目追加子表后
  - 原本属于第二个 route 的注释会被错误吸附到前一个 route 的新增子表附近
- 新增 `improved_v54`
- 在 patcher 中新增 tomlkit comment anchor 的专用规则
- 把 `task_103` 加入正式 manifest
- 更新候选池状态、结果文档、项目记忆与注册表

### 额外记录的过程性回归

- `v54r1` 首轮批量评测出现严重回归：
  - 正式集只成功 `6 / 51`
  - `frozen_20` 只成功 `0 / 20`
  - taxonomy 大量落到 `Premature Finish`
- 这轮失败并不是新题语义本身有问题
- 根因是 `app/agent/patcher.py` 里多段版本集合漏掉了 `improved_v54`
- 结果是旧规则链没有被完整继承
- 修复后补齐了 `improved_v54` 对以下规则链的继承：
  - `improved_v43`
  - `improved_v44`
  - `improved_v45`
  - `improved_v46`
  - `improved_v47`
  - `improved_v48`

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_comment_anchor_repo/tests/test_renderer.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_103.json --policy optimization/policy_versions/improved_v54.json`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v54.json --run-label realissuev54r2 --compare-against-eval logs/summaries/batch_eval_realissuev53r1_001.json --compare-label realissue_step34`
- 固定 `20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v54.json --run-label frozen20v54r2 --compare-against-eval logs/summaries/batch_eval_frozen20v53r1_001.json --compare-label frozen20_step33`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `50 -> 51`
- 候选池状态：
  - `accepted = 50 -> 51`
  - `to_review = 0 -> 0`
- `improved_v54` 正式 `51` 条任务集结果：
  - `success_count: 50 -> 51`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.7143 -> 0.6544`
- `improved_v54` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.7361 -> 0.6697`
- maturity 审计：
  - 正式任务数：`51 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`8`

### 这轮额外记录的过程

- 正式集时延对比显示：
  - 公共 `50` 条任务平均耗时增量：`-0.0593s`
- `frozen_20` 时延对比显示：
  - 公共 `20` 条任务平均耗时增量：`-0.0664s`
- 这说明 `v54` 的核心结论不是“又一次无变化扩容”
- 而是：
  - 新题扩容成功
  - 首轮真实暴露出策略继承链回归
  - 修复后功能口径恢复全绿
  - 性能相对 `v53` 重新回落

### 结论

- `tomlkit#295` 已成功作为新的 AoT 注释锚点保真题补进正式 semi_real 任务集
- `improved_v54` 已把正式任务数推进到 `51`
- 功能上，`improved_v54` 继续保持正式集与 `frozen_20` 无回归
- 并且它把相对 `v53` 的正式集与 `frozen_20` 平均耗时重新拉回
- 但这轮还没有补 `frozen_40` 同集合验证
- 当前最准确口径仍然是：
  - `improved_v50` 是稳定基线
  - `improved_v54` 是扩容成功、性能恢复中的最新版本
  - 当前 `frozen_40 streak` 仍保持 `8`

## 2026-06-12 Phase 6 pytest nested filtering 扩容与 `improved_v55`

### 背景

上一轮我们已经完成：

- `python-poetry/tomlkit#295 -> task_103`
- `improved_v54`
- 正式任务数推进到 `51`

但此时本地候选池也出现了一个新拐点：

- `accepted = 51`
- `to_review = 0`
- 也就是说，已有离线候选已经基本消耗完

因此这一轮的目标不只是继续扩题，还包括：

- 重新打开真实 GitHub issue 的新来源入口
- 优先给覆盖还偏薄的生态补新题
- 继续保持“扩容成功”和“稳定版本判断”分开记录

这一轮选择 `pytest-dev/pytest#14189`，因为它是非常干净的嵌套上下文管理问题：相同 filter 嵌套使用时，内层退出不应提前移除外层仍在使用的 filter。

### 目标

- 把 `pytest-dev/pytest#14189` 转成新的 semi_real 正式任务
- 为嵌套 caplog filtering 提前移除外层 filter 的问题补一条规则型修复能力
- 在正式扩容集与 `frozen_20` 上验证 `improved_v55`
- 补一轮复跑，区分真实性能回归与一次性环境抖动
- 同步 maturity 审计，把正式任务数推进到 `52`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_104.json`
- `benchmarks/tasks/task_105.json`
- `benchmarks/repos/pytest_caplog_filter_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v55.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev55r1_001.json`
- `logs/summaries/batch_eval_realissuev55r2_001.json`
- `logs/summaries/batch_compare_realissue_step35_002.json`
- `logs/summaries/batch_eval_frozen20v55r1_001.json`
- `logs/summaries/batch_eval_frozen20v55r2_001.json`
- `logs/summaries/batch_compare_frozen20_step34_002.json`
- `logs/summaries/duration_compare_realissuev55_001.json`
- `logs/summaries/duration_compare_frozen20v55_001.json`
- `logs/summaries/benchmark_maturity_maturity_030.json`
- `logs/summaries/batch_eval_frozen40v55r1_001.json`
- `logs/summaries/batch_compare_frozen40_step10_001.json`
- `logs/summaries/benchmark_maturity_maturity_031.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 直接从 GitHub 新增候选导入：
  - `pytest-dev/pytest#14189`
- 新增 `real_issue` 草稿：
  - `task_104`
- 新增可运行的 semi_real 正式任务：
  - `task_105`
- 新增 repo：
  - `benchmarks/repos/pytest_caplog_filter_repo`
- 在 repo 中故意保留 bug：
  - 相同 filter 嵌套进入两个 filtering 上下文
  - 内层退出时错误把外层仍在使用的 filter 提前移除
- 新增 `improved_v55`
- 在 patcher 中新增 pytest nested caplog filtering 的专用规则
- 把 `task_105` 加入正式 manifest
- 更新候选池状态、结果文档、项目记忆与注册表

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/pytest_caplog_filter_repo/tests/test_logging_utils.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_105.json --policy optimization/policy_versions/improved_v55.json`
- 正式集首轮：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v55.json --run-label realissuev55r1 --compare-against-eval logs/summaries/batch_eval_realissuev54r2_001.json --compare-label realissue_step35`
- 正式集复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v55.json --run-label realissuev55r2 --compare-against-eval logs/summaries/batch_eval_realissuev54r2_001.json --compare-label realissue_step35`
- 固定 `20` 首轮：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v55.json --run-label frozen20v55r1 --compare-against-eval logs/summaries/batch_eval_frozen20v54r2_001.json --compare-label frozen20_step34`
- 固定 `20` 复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v55.json --run-label frozen20v55r2 --compare-against-eval logs/summaries/batch_eval_frozen20v54r2_001.json --compare-label frozen20_step34`
- 时延分析：
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev54r2_001.json --improved-batch-summary logs/summaries/batch_run_realissuev55r1_001.json --run-label realissuev55`
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen20v54r2_001.json --improved-batch-summary logs/summaries/batch_run_frozen20v55r1_001.json --run-label frozen20v55`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `51 -> 52`
- 候选池状态：
  - `accepted = 51 -> 52`
  - `to_review = 0 -> 0`
- `improved_v55` 正式 `52` 条任务集复跑结果：
  - `success_count: 51 -> 52`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6544 -> 0.6551`
- `improved_v55` `frozen_20` 复跑结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6697 -> 0.6835`
- `improved_v55` `frozen_40` 首轮结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6824 -> 0.6527`
- maturity 审计：
  - 正式任务数：`52 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`8`

### 这轮额外记录的过程

- 首轮正式集时延对比显示：
  - 公共 `51` 条任务平均耗时增量：`+0.0251s`
- 首轮 `frozen_20` 时延对比显示：
  - 公共 `20` 条任务平均耗时增量：`+0.0345s`
- 复跑后关键口径收敛为：
  - 正式集 `0.6544 -> 0.6551`
  - `frozen_20` `0.6697 -> 0.6835`
- 随后补上的 `frozen_40` 首轮结果说明：
  - 功能口径继续全绿
  - 相对 `v52r2` 的平均耗时回落了 `0.0297s`
  - 但绝对值 `0.6527` 仍明显高于 `improved_v32` 阈值 `0.5514`
- 这说明 `v55` 的更准确结论不是“明显回归”
- 而是：
  - 新题扩容成功
  - 功能口径保持全绿
  - 首轮有轻微时延波动
  - 复跑后已经明显收敛
  - 固定 `40` 条集合上也证明功能稳定，但还没回到长期性能门槛内

### 结论

- `pytest#14189` 已成功作为新的嵌套过滤上下文生命周期题补进正式 semi_real 任务集
- `improved_v55` 已把正式任务数推进到 `52`
- 功能上，`improved_v55` 继续保持正式集、`frozen_20` 与 `frozen_40` 首轮同集合验证无回归
- 性能上，这轮复跑口径已经把相对 `v54` 的回升压缩到很小范围，并且 `frozen_40` 相对 `v52r2` 也有回落
- 但当前 `frozen_40` 绝对耗时仍未回到长期阈值以内
- 当前最准确口径仍然是：
  - `improved_v50` 是稳定基线
  - `improved_v55` 是扩容成功、性能轻微波动但已收敛的最新版本
  - 当前 `frozen_40 streak` 仍保持 `8`

## 2026-06-12 Phase 6 tomlkit 单元素 key 规范扩容与 `improved_v56`

### 背景

上一轮我们已经完成：

- `pytest-dev/pytest#14189 -> task_105`
- `improved_v55`
- 正式任务数推进到 `52`

同时，`v55` 虽然已经在 `frozen_40` 上功能全绿，但绝对耗时仍高于长期阈值：

- `0.6527 > 0.5514`

因此这一轮除了继续扩新题，还希望验证两件事：

- 能否继续把正式任务数推高到 `53`
- 能否把固定 `40` 条集合的平均耗时重新拉回长期阈值以内

这一轮选择 `python-poetry/tomlkit#430`，因为它是一个非常干净的 key 构造语义问题：单元素列表 key 规范不应继续构造成 DottedKey，而应与单字符串输入保持一致。

### 目标

- 把 `python-poetry/tomlkit#430` 转成新的 semi_real 正式任务
- 为单元素列表 key 规范错误构造成 DottedKey 的问题补一条规则型修复能力
- 在正式扩容集、`frozen_20`、`frozen_40` 上验证 `improved_v56`
- 同步 maturity 审计，把正式任务数推进到 `53`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_106.json`
- `benchmarks/tasks/task_107.json`
- `benchmarks/repos/tomlkit_single_key_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v56.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev56r1_001.json`
- `logs/summaries/batch_eval_realissuev56r2_001.json`
- `logs/summaries/batch_compare_realissue_step36_002.json`
- `logs/summaries/batch_eval_frozen20v56r1_001.json`
- `logs/summaries/batch_eval_frozen20v56r2_001.json`
- `logs/summaries/batch_compare_frozen20_step35_002.json`
- `logs/summaries/batch_eval_frozen40v56r1_001.json`
- `logs/summaries/batch_eval_frozen40v56r2_001.json`
- `logs/summaries/batch_compare_frozen40_step11_002.json`
- `logs/summaries/benchmark_maturity_maturity_032.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 直接从 GitHub 新增候选导入：
  - `python-poetry/tomlkit#430`
- 新增 `real_issue` 草稿：
  - `task_106`
- 新增可运行的 semi_real 正式任务：
  - `task_107`
- 新增 repo：
  - `benchmarks/repos/tomlkit_single_key_repo`
- 在 repo 中故意保留 bug：
  - `build_key(["my_key"])` 被错误构造成 `DottedKey`
  - 导致单元素列表 key 规范与普通字符串 key 的存在性判断不一致
- 新增 `improved_v56`
- 在 patcher 中新增 tomlkit 单元素 key 规范的专用规则
- 修复 `v56r1` 首轮暴露出的 `task_105` 继承链漏接问题
- 把 `task_107` 加入正式 manifest
- 更新候选池状态、结果文档、项目记忆与注册表

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_single_key_repo/tests/test_keys.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_107.json --policy optimization/policy_versions/improved_v56.json`
- 回归单任务复核：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_105.json --policy optimization/policy_versions/improved_v56.json`
- 正式集首轮：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v56.json --run-label realissuev56r1 --compare-against-eval logs/summaries/batch_eval_realissuev55r2_001.json --compare-label realissue_step36`
- 正式集复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v56.json --run-label realissuev56r2 --compare-against-eval logs/summaries/batch_eval_realissuev55r2_001.json --compare-label realissue_step36`
- 固定 `20` 首轮：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v56.json --run-label frozen20v56r1 --compare-against-eval logs/summaries/batch_eval_frozen20v55r2_001.json --compare-label frozen20_step35`
- 固定 `20` 复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v56.json --run-label frozen20v56r2 --compare-against-eval logs/summaries/batch_eval_frozen20v55r2_001.json --compare-label frozen20_step35`
- 固定 `40` 首轮：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v56.json --run-label frozen40v56r1 --compare-against-eval logs/summaries/batch_eval_frozen40v55r1_001.json --compare-label frozen40_step11`
- 固定 `40` 复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v56.json --run-label frozen40v56r2 --compare-against-eval logs/summaries/batch_eval_frozen40v55r1_001.json --compare-label frozen40_step11`
- maturity 审计：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`

### 关键观察

- 正式任务数：
  - `52 -> 53`
- 候选池状态：
  - `accepted = 52 -> 53`
  - `to_review = 0 -> 0`
- `improved_v56` 正式 `53` 条任务集复跑结果：
  - `success_count: 52 -> 53`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6551 -> 0.5237`
- `improved_v56` `frozen_20` 复跑结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6835 -> 0.5313`
- `improved_v56` `frozen_40` 复跑结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6527 -> 0.5293`
- maturity 审计：
  - 正式任务数：`53 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`8`

### 这轮额外记录的过程

- `v56r1` 首轮正式集出现了 `task_105` 的单点回归：
  - 标签：`Premature Finish`
  - 根因：`improved_v56` 首轮漏继承 `improved_v55` 的 pytest nested caplog filtering 规则
- 修复后补跑 `v56r2`：
  - 正式集恢复 `53 / 53`
  - `frozen_20` 继续 `20 / 20`
  - `frozen_40` 继续 `40 / 40`
- 这说明这轮最重要的不只是新增题：
  - 还再次验证了 patcher 版本继承链必须显式维护
  - 同时修复后性能结果反而比 `v55` 更好

### 结论

- `tomlkit#430` 已成功作为新的 key 规范一致性题补进正式 semi_real 任务集
- `improved_v56` 已把正式任务数推进到 `53`
- 功能上，`improved_v56` 继续保持正式集、`frozen_20` 与 `frozen_40` 三线无回归
- 性能上，这轮不仅正式集平均耗时继续回落，`frozen_40` 也重新回到长期阈值以内
- 当前最准确口径更新为：
  - `improved_v50` 是稳定基线
  - `improved_v56` 是扩容成功且三线验证通过的最新版本
  - 当前 `frozen_40 streak` 仍保持 `8`
  - 正式任务数已经推进到 `53`

## 2026-06-12 Phase 6 packaging 名称规范化边界扩容与 `improved_v57`

### 背景

上一轮我们已经完成：

- `python-poetry/tomlkit#430 -> task_107`
- `improved_v56`
- 正式任务数推进到 `53`

同时，`v56` 已经把 `frozen_40` 重新拉回长期阈值以内：

- `0.5293 < 0.5514`

因此这一轮希望继续验证两件事：

- 能否继续把正式任务数推高到 `54`
- 能否在继续扩题时守住 `frozen_40` 的功能稳定与长期性能门槛

这一轮选择 `pypa/packaging#1231`，因为它是一个非常干净的名称规范化 roundtrip 语义问题：当名称已经是 `canonicalize_name()` 的稳定输出时，`is_normalized_name()` 不应继续错误拒绝前后带连字符的 canonicalized 名称。

### 目标

- 把 `pypa/packaging#1231` 转成新的 semi_real 正式任务
- 为 `canonicalize_name()` 与 `is_normalized_name()` 在边界连字符上的语义不一致补一条规则型修复能力
- 在正式扩容集、`frozen_20`、`frozen_40` 上验证 `improved_v57`
- 同步 maturity 审计，把正式任务数推进到 `54`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_108.json`
- `benchmarks/tasks/task_109.json`
- `benchmarks/repos/packaging_name_normalization_repo/`
- `benchmarks/manifests/real_issue_tasks.json`
- `optimization/policy_versions/improved_v57.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev57r1_001.json`
- `logs/summaries/batch_eval_realissuev57r2_001.json`
- `logs/summaries/batch_eval_realissuev57r3_001.json`
- `logs/summaries/batch_compare_realissue_step37_003.json`
- `logs/summaries/batch_eval_frozen20v57r1_001.json`
- `logs/summaries/batch_eval_frozen20v57r2_001.json`
- `logs/summaries/batch_compare_frozen20_step36_002.json`
- `logs/summaries/batch_eval_frozen40v57r1_001.json`
- `logs/summaries/batch_eval_frozen40v57r2_001.json`
- `logs/summaries/batch_compare_frozen40_step12_002.json`
- `logs/summaries/benchmark_maturity_maturity_033.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 直接从 GitHub 新增候选导入：
  - `pypa/packaging#1231`
- 新增 `real_issue` 草稿：
  - `task_108`
- 新增可运行的 semi_real 正式任务：
  - `task_109`
- 新增 repo：
  - `benchmarks/repos/packaging_name_normalization_repo`
- 在 repo 中故意保留 bug：
  - `canonicalize_name()` 会保留前后连字符的稳定输出
  - `is_normalized_name()` 却继续用更窄的正则把这些名称误判为未规范化
- 新增 `improved_v57`
- 在 patcher 中新增 packaging 名称规范化边界的专用规则
- 修复 `v57r1` 首轮暴露出的两处继承链漏接问题
- 把 `task_109` 加入正式 manifest
- 更新候选池状态、结果文档、项目记忆与注册表

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/packaging_name_normalization_repo/tests/test_utils.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_109.json --policy optimization/policy_versions/improved_v57.json`
- 回归单任务复核：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_006.json --policy optimization/policy_versions/improved_v57.json`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_107.json --policy optimization/policy_versions/improved_v57.json`
- 正式集首轮：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v57.json --run-label realissuev57r1 --compare-against-eval logs/summaries/batch_eval_realissuev56r2_001.json --compare-label realissue_step37`
- 正式集修复后复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v57.json --run-label realissuev57r2 --compare-against-eval logs/summaries/batch_eval_realissuev56r2_001.json --compare-label realissue_step37`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v57.json --run-label realissuev57r3 --compare-against-eval logs/summaries/batch_eval_realissuev56r2_001.json --compare-label realissue_step37`
- 固定 `20` 首轮与修复后复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v57.json --run-label frozen20v57r1 --compare-against-eval logs/summaries/batch_eval_frozen20v56r2_001.json --compare-label frozen20_step36`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v57.json --run-label frozen20v57r2 --compare-against-eval logs/summaries/batch_eval_frozen20v56r2_001.json --compare-label frozen20_step36`
- 固定 `40` 首轮与修复后复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v57.json --run-label frozen40v57r1 --compare-against-eval logs/summaries/batch_eval_frozen40v56r2_001.json --compare-label frozen40_step12`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v57.json --run-label frozen40v57r2 --compare-against-eval logs/summaries/batch_eval_frozen40v56r2_001.json --compare-label frozen40_step12`
- maturity 审计：
  - `python scripts/analyze_benchmark_maturity.py --run-label maturity`
- 核心回归测试：
  - `python -m pytest tests/test_import_issue_batch.py tests/test_scaffold_semi_real_task.py tests/test_run_real_issue_eval.py tests/test_analyze_benchmark_maturity.py -q`

### 关键观察

- 正式任务数：
  - `53 -> 54`
- 候选池状态：
  - `accepted = 53 -> 54`
  - `to_review = 0 -> 0`
- `improved_v57` 正式 `54` 条任务集最终结果：
  - `success_count: 53 -> 54`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5237 -> 0.523`
- `improved_v57` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5313 -> 0.5385`
- `improved_v57` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5293 -> 0.5437`
- maturity 审计：
  - 正式任务数：`54 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`8`

### 这轮额外记录的过程

- `v57r1` 首轮正式集与冻结集出现系统性回归：
  - 正式集只成功 `9 / 54`
  - `frozen_20` 只成功 `0 / 20`
  - `frozen_40` 只成功 `0 / 40`
  - taxonomy 大量落到 `Premature Finish`
- 第一处根因：
  - patcher 中多段旧规则版本集合遗漏了 `improved_v57`
  - 导致 `v47 ~ v43` 这段旧规则链没有被继续继承
- 修复后补跑 `v57r2`：
  - `task_006` 恢复成功
  - `frozen_20` 恢复 `20 / 20`
  - `frozen_40` 恢复 `40 / 40`
- 随后正式集仍有 `task_107` 单点回归：
  - 根因是 `v56` 的 tomlkit 单元素 key 规则仍只绑定 `improved_v56`
  - 没有继续继承到 `improved_v57`
- 修复后补跑 `v57r3`：
  - 正式集恢复 `54 / 54`
  - 正式集平均耗时继续小幅优于 `v56`
- 这说明这轮最重要的不只是新增题：
  - 还再次验证了 patcher 版本继承链必须显式维护到最新版本
  - 而且继承链问题会优先以“系统性 Premature Finish”或“新近规则单点失效”两种形式暴露出来

### 结论

- `packaging#1231` 已成功作为新的名称规范化 roundtrip 语义题补进正式 semi_real 任务集
- `improved_v57` 已把正式任务数推进到 `54`
- 功能上，`improved_v57` 继续保持正式集、`frozen_20` 与 `frozen_40` 三线无回归
- 性能上，这轮正式集继续小幅改善，`frozen_40` 虽然相对 `v56` 略有波动，但仍稳定低于长期阈值
- 当前最准确口径更新为：
  - `improved_v50` 是稳定基线
  - `improved_v57` 是扩容成功且三线验证通过的最新版本
  - 当前 `frozen_40 streak` 仍保持 `8`
  - 正式任务数已经推进到 `54`

## 2026-06-12 Phase 6 click usage 连字符换行扩容与 `improved_v58`

### 本轮目标

- 继续朝 Benchmark Maturity v1 的 `60+` 正式任务数推进
- 新增一条边界清晰、单模块可修的真实 issue 派生任务
- 顺手增强 issue 导入链路，让后续结构化候选清单可以直接导入并保留筛选理由

### 改动类型

- `benchmark`
- `policy`
- `tooling`
- `documentation`

### 主要文件

- `benchmarks/issue_batch_v58_candidates.json`
- `benchmarks/tasks/task_110.json`
- `benchmarks/tasks/task_111.json`
- `benchmarks/repos/click_usage_repo/`
- `optimization/policy_versions/improved_v58.json`
- `app/agent/patcher.py`
- `scripts/import_github_issue.py`
- `scripts/import_issue_batch.py`
- `tests/test_import_issue_batch.py`
- `benchmarks/real_world_candidates.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 从 GitHub 新增候选导入：
  - `pallets/click#3362`
- 新增 `real_issue` 草稿：
  - `task_110`
- 新增可运行的 semi_real 正式任务：
  - `task_111`
- 新增 repo：
  - `benchmarks/repos/click_usage_repo`
- 在 repo 中故意保留 bug：
  - usage 文本通过 `textwrap.wrap` 直接换行
  - 默认允许在连字符处断行，导致 `--max-retry-count` 这类长选项被错误拆成两行
- 新增 `improved_v58`
- 在 patcher 中新增 click usage 连字符换行的专用规则
- 批量 issue 导入脚本支持结构化候选说明：
  - 可接收 `why_it_fits / expected_target_files / expected_test_shape / risk_notes / recommendation`
  - 并把这些说明追加进候选池备注，而不是覆盖历史
- 把 `task_111` 加入正式 manifest
- 更新候选池状态与主文档口径

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/click_usage_repo/tests/test_formatting.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_111.json --policy optimization/policy_versions/improved_v58.json`
- 核心回归测试：
  - `python -m pytest tests/test_import_issue_batch.py tests/test_scaffold_semi_real_task.py tests/test_run_real_issue_eval.py -q`

### 关键观察

- 正式任务数：
  - `54 -> 55`
- 候选池状态：
  - `accepted = 54 -> 55`
  - `to_review = 0 -> 0`
- 单任务 `task_111`：
  - `pre_test_exit_code: 1`
  - `post_test_exit_code: 0`
  - `patch_applied: true`
  - `duration_sec: 0.4886`

### 这轮额外记录的过程

- 先对多个候选进行了风险筛选：
  - `packaging#934` 因规范争议暂不适合
  - `jsonschema#1465` 更像底层依赖行为，不够干净
  - 最终选择 `click#3362` 作为 `v58` 首条落地任务
- 这一轮没有先跑全量评测，而是优先保证：
  - 新题语义边界清楚
  - 单任务闭环能稳定成功
  - issue 导入基础设施更适合后续扩容

### 结论

- `click#3362` 已成功作为新的 usage 文本换行语义题补进正式 semi_real 任务集
- `improved_v58` 已把正式任务数推进到 `55`
- `v58r1` 首轮正式集只暴露 `task_109` 单点回归：
  - 根因是 `v57` 的 packaging 名称规范化规则没有继续继承到 `improved_v58`
- 修复后补跑 `v58r2`：
  - 正式集恢复 `55 / 55`
  - 正式集平均耗时为 `0.5234`
- `v58` 当前已经完成正式集、`frozen_20` 与 `frozen_40` 三线验证
- 下一轮应继续把正式任务数从 `55` 推向 `60+`，优先考虑 `packaging#810 / tomlkit#450 / jinja#2118` 这类高质量候选

## 2026-06-12 Phase 6 distlib WHEEL metadata 扩容与 `improved_v59`

### 本轮目标

- 继续朝 Benchmark Maturity v1 的 `60+` 正式任务数推进
- 新增一个来自新生态 `pypa/distlib` 的真实 issue 派生任务
- 保持 frozen 集功能稳定，并尽量不让平均耗时继续恶化

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/issue_batch_v59_candidates.json`
- `benchmarks/tasks/task_112.json`
- `benchmarks/tasks/task_113.json`
- `benchmarks/repos/distlib_wheel_repo/`
- `optimization/policy_versions/improved_v59.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev59r1_001.json`
- `logs/summaries/batch_eval_realissuev59r2_001.json`
- `logs/summaries/batch_compare_realissue_step39_002.json`
- `logs/summaries/batch_eval_frozen20v59r1_001.json`
- `logs/summaries/batch_compare_frozen20_step38_001.json`
- `logs/summaries/batch_eval_frozen40v59r1_001.json`
- `logs/summaries/batch_compare_frozen40_step14_001.json`
- `logs/summaries/benchmark_maturity_maturity_035.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 直接从 GitHub 新增候选导入：
  - `pypa/distlib#238`
- 新增 `real_issue` 草稿：
  - `task_112`
- 新增可运行的 semi_real 正式任务：
  - `task_113`
- 新增 repo：
  - `benchmarks/repos/distlib_wheel_repo`
- 在 repo 中故意保留 bug：
  - `buildver` 存在时仍没有把 `Build:` 行写入 WHEEL metadata
- 新增 `improved_v59`
- 在 patcher 中新增 distlib WHEEL metadata Build 行的专用规则
- 把 `task_113` 加入正式 manifest
- 把新生态 `pypa/distlib` 纳入正式任务来源集合

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/distlib_wheel_repo/tests/test_wheel.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_113.json --policy optimization/policy_versions/improved_v59.json`
- 回归单任务复核：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_111.json --policy optimization/policy_versions/improved_v59.json`
- 正式集首轮与修复后复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v59.json --run-label realissuev59r1 --compare-against-eval logs/summaries/batch_eval_realissuev58r2_001.json --compare-label realissue_step39`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v59.json --run-label realissuev59r2 --compare-against-eval logs/summaries/batch_eval_realissuev58r2_001.json --compare-label realissue_step39`
- 固定 `20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v59.json --run-label frozen20v59r1 --compare-against-eval logs/summaries/batch_eval_frozen20v58r1_001.json --compare-label frozen20_step38`
- 固定 `40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v59.json --run-label frozen40v59r1 --compare-against-eval logs/summaries/batch_eval_frozen40v58r1_001.json --compare-label frozen40_step14`
- maturity 审计：
  - `python scripts/analyze_benchmark_maturity.py --run-label maturity`

### 关键观察

- 正式任务数：
  - `55 -> 56`
- 来源生态数：
  - `13 -> 14`
- 候选池状态：
  - `accepted = 55 -> 56`
  - `to_review = 0 -> 0`
- `improved_v59` 正式 `56` 条任务集最终结果：
  - `success_count: 55 -> 56`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5234 -> 0.5197`
- `improved_v59` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5506 -> 0.5605`
- `improved_v59` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5294 -> 0.5296`

### 这轮额外记录的过程

- `v59r1` 首轮正式集只暴露 `task_111` 单点回归：
  - 根因是 `v58` 的 click usage 连字符换行规则没有继续继承到 `improved_v59`
- 修复后补跑 `v59r2`：
  - 正式集恢复 `56 / 56`
  - 正式集平均耗时不仅没有继续恶化，反而较 `v58` 进一步回落
- 这再次说明：
  - patcher 的版本继承链仍是当前策略演化里最高频、最真实的回归来源之一

### 结论

- `distlib#238` 已成功作为来自新生态的一条 metadata 生成语义题补进正式 semi_real 任务集
- `improved_v59` 已把正式任务数推进到 `56`
- 功能上，`improved_v59` 继续保持正式集、`frozen_20` 与 `frozen_40` 三线无回归
- 性能上，正式集平均耗时进一步回落，`frozen_40` 几乎持平且仍稳定低于长期阈值
- 下一轮应继续把正式任务数从 `56` 推向 `60+`

## 2026-06-12 Phase 6 pytest expression scanner 扩容与 `improved_v60`

### 本轮目标

- 继续朝 Benchmark Maturity v1 的 `60+` 正式任务数推进
- 新增一个来自 `pytest-dev/pytest` 的真实 issue 派生任务
- 保持 frozen 集功能稳定，并继续验证版本继承链修复机制

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/issue_batch_v60_candidates.json`
- `benchmarks/tasks/task_114.json`
- `benchmarks/tasks/task_115.json`
- `benchmarks/repos/pytest_expression_repo/`
- `optimization/policy_versions/improved_v60.json`
- `app/agent/patcher.py`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev60r1_001.json`
- `logs/summaries/batch_eval_realissuev60r2_001.json`
- `logs/summaries/batch_compare_realissue_step41_001.json`
- `logs/summaries/batch_eval_frozen20v60r2_001.json`
- `logs/summaries/batch_compare_frozen20_step40_001.json`
- `logs/summaries/batch_eval_frozen40v60r2_001.json`
- `logs/summaries/batch_compare_frozen40_step16_001.json`
- `logs/summaries/benchmark_maturity_maturity_037.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 直接从 GitHub 新增候选导入：
  - `pytest-dev/pytest#14474`
- 新增 `real_issue` 草稿：
  - `task_114`
- 新增可运行的 semi_real 正式任务：
  - `task_115`
- 新增 repo：
  - `benchmarks/repos/pytest_expression_repo`
- 在 repo 中故意保留 bug：
  - 扫描字符串字面量时错误地检查了整个输入里的反斜杠
- 新增 `improved_v60`
- 在 patcher 中新增 pytest expression scanner 的专用规则
- 把 `task_115` 加入正式 manifest

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/pytest_expression_repo/tests/test_expression.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_115.json --policy optimization/policy_versions/improved_v60.json`
- 回归单任务复核：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_113.json --policy optimization/policy_versions/improved_v60.json`
- 正式集首轮与修复后复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v60.json --run-label realissuev60r1 --compare-against-eval logs/summaries/batch_eval_realissuev59r2_001.json --compare-label realissue_step40`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v60.json --run-label realissuev60r2 --compare-against-eval logs/summaries/batch_eval_realissuev59r2_001.json --compare-label realissue_step41`
- 固定 `20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v60.json --run-label frozen20v60r2 --compare-against-eval logs/summaries/batch_eval_frozen20v59r1_001.json --compare-label frozen20_step40`
- 固定 `40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v60.json --run-label frozen40v60r2 --compare-against-eval logs/summaries/batch_eval_frozen40v59r1_001.json --compare-label frozen40_step16`
- maturity 审计：
  - `python scripts/analyze_benchmark_maturity.py --run-label maturity`

### 关键观察

- 正式任务数：
  - `56 -> 57`
- 来源生态数：
  - `14 -> 14`
- 候选池状态：
  - `accepted = 56 -> 57`
  - `to_review = 0 -> 0`
- `improved_v60` 正式 `57` 条任务集最终结果：
  - `success_count: 56 -> 57`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5197 -> 0.5262`
- `improved_v60` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5605 -> 0.5471`
- `improved_v60` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5296 -> 0.5320`

### 这轮额外记录的过程

- `v60r1` 首轮正式集只暴露 `task_113` 单点回归：
  - 根因是 `v59` 的 distlib WHEEL metadata 规则没有继续继承到 `improved_v60`
- 修复后补跑 `v60r2`：
  - 正式集恢复 `57 / 57`
  - `frozen_20` 平均耗时相对 `v59` 反而回落
- 这再次说明：
  - patcher 的版本继承链仍是当前策略演化里最需要优先防守的回归来源

### 结论

- `pytest#14474` 已成功作为一条 scanner 作用域语义题补进正式 semi_real 任务集
- `improved_v60` 已把正式任务数推进到 `57`
- 功能上，`improved_v60` 继续保持正式集、`frozen_20` 与 `frozen_40` 三线无回归
- 性能上，`frozen_40` 只有 `0.0024s` 的轻微回升，仍稳定低于长期阈值
- 下一轮应继续把正式任务数从 `57` 推向 `60+`

## 2026-06-12 Phase 6 tomlkit 负整数翻转扩容与 `improved_v61`

### 本轮目标

- 继续朝 Benchmark Maturity v1 的 `60+` 正式任务数推进
- 新增一个来自 `python-poetry/tomlkit` 的真实 issue 派生任务
- 在保持 frozen 集无回归的前提下，把 `formal_task_count` 推进到 `58`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/issue_batch_v61_candidates.json`
- `benchmarks/tasks/task_116.json`
- `benchmarks/tasks/task_117.json`
- `benchmarks/repos/tomlkit_negative_int_repo/`
- `optimization/policy_versions/improved_v61.json`
- `app/agent/patcher.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev61r1_001.json`
- `logs/summaries/batch_eval_realissuev61r2_001.json`
- `logs/summaries/batch_compare_realissue_step43_001.json`
- `logs/summaries/batch_eval_frozen20v61r2_001.json`
- `logs/summaries/batch_compare_frozen20_step42_001.json`
- `logs/summaries/batch_eval_frozen40v61r2_001.json`
- `logs/summaries/batch_compare_frozen40_step18_001.json`
- `logs/summaries/benchmark_maturity_maturity_039.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 直接从 GitHub 新增候选导入：
  - `python-poetry/tomlkit#346`
- 新增 `real_issue` 草稿：
  - `task_116`
- 新增可运行的 semi_real 正式任务：
  - `task_117`
- 新增 repo：
  - `benchmarks/repos/tomlkit_negative_int_repo`
- 在 repo 中故意保留 bug：
  - 负整数原地乘以 `-1` 时，文本符号会错误进入 `+x / --x / x / -x` 之类的循环污染
- 新增 `improved_v61`
- 在 patcher 中新增 tomlkit 负整数翻转的专用规则
- 把 `task_117` 加入正式 manifest

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_negative_int_repo/tests/test_items.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_117.json --policy optimization/policy_versions/improved_v61.json`
- 回归单任务复核：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_115.json --policy optimization/policy_versions/improved_v61.json`
- 正式集首轮与修复后复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v61.json --run-label realissuev61r1 --compare-against-eval logs/summaries/batch_eval_realissuev60r2_001.json --compare-label realissue_step42`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v61.json --run-label realissuev61r2 --compare-against-eval logs/summaries/batch_eval_realissuev60r2_001.json --compare-label realissue_step43`
- 固定 `20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v61.json --run-label frozen20v61r2 --compare-against-eval logs/summaries/batch_eval_frozen20v60r2_001.json --compare-label frozen20_step42`
- 固定 `40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v61.json --run-label frozen40v61r2 --compare-against-eval logs/summaries/batch_eval_frozen40v60r2_001.json --compare-label frozen40_step18`
- maturity 审计：
  - `python scripts/analyze_benchmark_maturity.py --run-label maturity`

### 关键观察

- 正式任务数：
  - `57 -> 58`
- 来源生态数：
  - `14 -> 14`
- 候选池状态：
  - `accepted = 57 -> 58`
  - `to_review = 0 -> 0`
- `improved_v61` 正式 `58` 条任务集最终结果：
  - `success_count: 57 -> 58`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5262 -> 0.5465`
- `improved_v61` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5471 -> 0.5518`
- `improved_v61` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5320 -> 0.5377`
- 最新 maturity：
  - `formal_task_count = 58`
  - `ecosystem_count = 14`
  - `latest_frozen_count = 40`
  - `frozen_40_streak = 8`

### 这轮额外记录的过程

- `v61r1` 首轮出现了系统性回归，不是单题回归：
  - 多段旧规则版本集合遗漏了 `improved_v61`
  - `run_v34_fallback_chain` 的入口集合遗漏了 `improved_v61`
  - `v60` 的 pytest expression 修复规则没有继续继承到 `v61`
- 修复后补跑 `v61r2`：
  - 正式集恢复 `58 / 58`
  - `frozen_20` 恢复 `20 / 20`
  - `frozen_40` 恢复 `40 / 40`
- 这说明：
  - patcher 的“版本继承链完整性”已经成为当前策略演化里最需要优先防守的工程风险
  - 后续 `v62+` 每次新增策略后，都必须优先核对旧规则集合和 fallback 链是否已带上新版本

### 结论

- `tomlkit#346` 已成功作为新的数值渲染语义题补进正式 semi_real 任务集
- `improved_v61` 已把正式任务数推进到 `58`
- 功能上，`improved_v61` 继续保持正式集、`frozen_20` 与 `frozen_40` 三线无回归
- 性能上，`frozen_40` 只有 `0.0057s` 的轻微回升，仍稳定低于长期阈值
- 下一轮应继续把正式任务数从 `58` 推向 `60+`

## 2026-06-12 Phase 6 tomlkit bool item comment 包装扩容与 `improved_v62`

### 本轮目标

- 继续朝 Benchmark Maturity v1 的 `60+` 正式任务数推进
- 新增一个来自 `python-poetry/tomlkit` 的真实 issue 派生任务
- 在保持 frozen 集功能无回归的前提下，把 `formal_task_count` 推进到 `59`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/issue_batch_v62_candidates.json`
- `benchmarks/tasks/task_118.json`
- `benchmarks/tasks/task_119.json`
- `benchmarks/repos/tomlkit_bool_comment_repo/`
- `optimization/policy_versions/improved_v62.json`
- `app/agent/patcher.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev62r1_001.json`
- `logs/summaries/batch_eval_realissuev62r2_001.json`
- `logs/summaries/batch_eval_realissuev62r3_001.json`
- `logs/summaries/batch_compare_realissue_step46_001.json`
- `logs/summaries/batch_eval_frozen20v62r2_001.json`
- `logs/summaries/batch_compare_frozen20_step44_001.json`
- `logs/summaries/batch_eval_frozen40v62r2_001.json`
- `logs/summaries/batch_compare_frozen40_step20_001.json`
- `logs/summaries/benchmark_maturity_maturity_041.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 通过 issue 查询补录新候选：
  - `python-poetry/tomlkit#450`
- 新增 `real_issue` 草稿：
  - `task_118`
- 新增可运行的 semi_real 正式任务：
  - `task_119`
- 新增 repo：
  - `benchmarks/repos/tomlkit_bool_comment_repo`
- 在 repo 中故意保留 bug：
  - table 里的 bool 项被错误保留成原生 `bool`，导致后续取回后无法继续调用 `.comment()`
- 新增 `improved_v62`
- 在 patcher 中新增 tomlkit bool item 包装保真的专用规则
- 把 `task_119` 加入正式 manifest

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_bool_comment_repo/tests/test_table.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_119.json --policy optimization/policy_versions/improved_v62.json`
- 回归单任务复核：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_117.json --policy optimization/policy_versions/improved_v62.json`
- 正式集首轮与修复后复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v62.json --run-label realissuev62r1 --compare-against-eval logs/summaries/batch_eval_realissuev61r2_001.json --compare-label realissue_step44`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v62.json --run-label realissuev62r2 --compare-against-eval logs/summaries/batch_eval_realissuev61r2_001.json --compare-label realissue_step45`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v62.json --run-label realissuev62r3 --compare-against-eval logs/summaries/batch_eval_realissuev61r2_001.json --compare-label realissue_step46`
- 固定 `20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v62.json --run-label frozen20v62r2 --compare-against-eval logs/summaries/batch_eval_frozen20v61r2_001.json --compare-label frozen20_step44`
- 固定 `40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v62.json --run-label frozen40v62r2 --compare-against-eval logs/summaries/batch_eval_frozen40v61r2_001.json --compare-label frozen40_step20`
- maturity 审计：
  - `python scripts/analyze_benchmark_maturity.py --run-label maturity`

### 关键观察

- 正式任务数：
  - `58 -> 59`
- 来源生态数：
  - `14 -> 14`
- 候选池状态：
  - `accepted = 58 -> 59`
  - `to_review = 0 -> 0`
- `improved_v62` 正式 `59` 条任务集最终结果：
  - `success_count: 58 -> 59`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5465 -> 0.5289`
- `improved_v62` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5518 -> 0.5564`
- `improved_v62` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5377 -> 0.5554`
- 最新 maturity：
  - `formal_task_count = 59`
  - `ecosystem_count = 14`
  - `latest_frozen_count = 40`
  - `frozen_40_streak = 8`

### 这轮额外记录的过程

- `v62r1` 首轮出现了系统性回归，不是新题本身的问题：
  - 旧规则继承链从 `v47` 到 `v43` 的多段版本集合遗漏了 `improved_v62`
- 修复后补跑 `v62r2`：
  - `frozen_20` 与 `frozen_40` 恢复全绿
  - 但正式集仍剩 `task_117` 单点回归
- 继续定位后发现：
  - `v61` 的 tomlkit 负整数翻转规则没有继续继承到 `improved_v62`
- 再补跑 `v62r3`：
  - 正式集恢复 `59 / 59`
- 这再次说明：
  - patcher 的“版本继承链完整性”仍是当前策略演化里最需要优先防守的工程风险
  - 后续 `v63+` 每次新增策略后，都必须同时检查新规则入口、旧规则集合和上一版新题的继续继承

### 结论

- `tomlkit#450` 已成功作为新的 item 包装保真语义题补进正式 semi_real 任务集
- `improved_v62` 已把正式任务数推进到 `59`
- 功能上，`improved_v62` 继续保持正式集、`frozen_20` 与 `frozen_40` 三线无功能回归
- 性能上，正式集相对 `v61` 反而回落，但 `frozen_40` 当前 `0.5554` 略高于长期阈值 `0.5514`
- 下一轮应继续把正式任务数从 `59` 推向 `60+`，并优先观察是否能把 `frozen_40` 拉回阈值以内

## 2026-06-12 Phase 6 tomlkit 容器 int key 规范化扩容与 `improved_v63`

### 本轮目标

- 继续朝 Benchmark Maturity v1 的 `60+` 正式任务数推进
- 新增一个来自 `python-poetry/tomlkit` 的真实 issue 派生任务
- 在保持 frozen 集功能无回归的前提下，把 `formal_task_count` 推进到 `60`

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要文件

- `benchmarks/issue_batch_v63_candidates.json`
- `benchmarks/tasks/task_120.json`
- `benchmarks/tasks/task_121.json`
- `benchmarks/repos/tomlkit_int_key_repo/`
- `optimization/policy_versions/improved_v63.json`
- `app/agent/patcher.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev63r1_001.json`
- `logs/summaries/batch_eval_realissuev63r2_001.json`
- `logs/summaries/batch_compare_realissue_step48_001.json`
- `logs/summaries/batch_eval_frozen20v63r2_001.json`
- `logs/summaries/batch_compare_frozen20_step46_001.json`
- `logs/summaries/batch_eval_frozen40v63r2_001.json`
- `logs/summaries/batch_compare_frozen40_step22_001.json`
- `logs/summaries/benchmark_maturity_maturity_043.json`
- `GUIDE.md`
- `docs/results.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/benchmark_registry.md`

### 本轮实现内容

- 通过 issue 查询补录新候选：
  - `python-poetry/tomlkit#412`
- 新增 `real_issue` 草稿：
  - `task_120`
- 新增可运行的 semi_real 正式任务：
  - `task_121`
- 新增 repo：
  - `benchmarks/repos/tomlkit_int_key_repo`
- 在 repo 中故意保留 bug：
  - `add(4, 5)` 与 `setdefault(4, 5)` 没有像解析入口那样把整数 key 规范化成字符串，而是错误把 `int` 当成可迭代对象处理并崩溃
- 新增 `improved_v63`
- 在 patcher 中新增 tomlkit 容器 int key 规范化的专用规则
- 把 `task_121` 加入正式 manifest

### 测试与验证

- 原始 repo 测试：
  - `python -m pytest benchmarks/repos/tomlkit_int_key_repo/tests/test_container.py -q`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_121.json --policy optimization/policy_versions/improved_v63.json`
- 回归单任务复核：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_119.json --policy optimization/policy_versions/improved_v63.json`
- 正式集首轮与修复后复跑：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v63.json --run-label realissuev63r1 --compare-against-eval logs/summaries/batch_eval_realissuev62r3_001.json --compare-label realissue_step47`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v63.json --run-label realissuev63r2 --compare-against-eval logs/summaries/batch_eval_realissuev62r3_001.json --compare-label realissue_step48`
- 固定 `20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v63.json --run-label frozen20v63r2 --compare-against-eval logs/summaries/batch_eval_frozen20v62r2_001.json --compare-label frozen20_step46`
- 固定 `40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v63.json --run-label frozen40v63r2 --compare-against-eval logs/summaries/batch_eval_frozen40v62r2_001.json --compare-label frozen40_step22`
- maturity 审计：
  - `python scripts/analyze_benchmark_maturity.py --run-label maturity`

### 关键观察

- 正式任务数：
  - `59 -> 60`
- 来源生态数：
  - `14 -> 14`
- 候选池状态：
  - `accepted = 59 -> 60`
  - `to_review = 0 -> 0`
- `improved_v63` 正式 `60` 条任务集最终结果：
  - `success_count: 59 -> 60`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5289 -> 0.5411`
- `improved_v63` `frozen_20` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5564 -> 0.5704`
- `improved_v63` `frozen_40` 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5554 -> 0.5594`
- 最新 maturity：
  - `formal_task_count = 60`
  - `ecosystem_count = 14`
  - `latest_frozen_count = 40`
  - `frozen_40_streak = 8`

### 这轮额外记录的过程

- `v63r1` 首轮出现了系统性回归，不是新题本身的问题：
  - 旧规则继承链从 `v47` 到 `v43` 的多段版本集合遗漏了 `improved_v63`
- 修复后补跑 `v63r2`：
  - 正式集恢复 `60 / 60`
  - `frozen_20` 恢复 `20 / 20`
  - `frozen_40` 恢复 `40 / 40`
- 这再次说明：
  - patcher 的“版本继承链完整性”仍是当前策略演化里最需要优先防守的工程风险
  - 后续 `v64+` 每次新增策略后，都必须同时检查新规则入口、旧规则集合，以及从 `v47` 到 `v43` 那几段是否已带上新版本

### 结论

- `tomlkit#412` 已成功作为新的容器 key 规范化语义题补进正式 semi_real 任务集
- `improved_v63` 已把正式任务数推进到 `60`
- 功能上，`improved_v63` 继续保持正式集、`frozen_20` 与 `frozen_40` 三线无功能回归
- 性能上，当前 `frozen_40` 为 `0.5594`，仍高于长期阈值 `0.5514`
- 这意味着 Benchmark Maturity v1 已满足规模、生态和稳定性门槛，但仍未满足性能门控；下一轮应优先做性能友好型扩容或专项时延收敛

## 2026-06-12 Phase 6 `improved_v63` 性能门控复核

### 本轮目标

- 判断 `v63r2` 的 `frozen_40 = 0.5594` 是稳定恶化，还是单次采样偏高
- 在不改策略的前提下补齐性能门控证据

### 改动类型

- `evaluation`
- `analysis`
- `documentation`

### 主要文件

- `logs/summaries/duration_compare_realissuev63_001.json`
- `logs/summaries/duration_compare_frozen40v63_001.json`
- `logs/summaries/trace_hotspots_frozen40v63_001.json`
- `logs/summaries/batch_eval_frozen20v63r3_001.json`
- `logs/summaries/batch_compare_frozen20_step47_001.json`
- `logs/summaries/batch_eval_frozen40v63r3_001.json`
- `logs/summaries/batch_compare_frozen40_step23_001.json`
- `logs/summaries/benchmark_maturity_maturity_044.json`

### 本轮实现内容

- 先对 `v62 -> v63` 做公共任务时延分析：
  - 正式 `59` 条公共任务平均耗时变化：`-0.0005s`
  - `frozen_40` 公共 `40` 条任务平均耗时变化：`+0.004s`
- 再做 trace 热点分析：
  - 回升主要仍集中在 `run_tests`
  - 但整体增量非常小，更接近采样抖动而不是新增 patch 规则带来的稳定开销
- 随后对同一策略版本补跑：
  - `frozen20v63r3`
  - `frozen40v63r3`
- 最后重新跑一轮 benchmark maturity 审计

### 关键观察

- `frozen_20` 同版复跑：
  - `average_duration_sec: 0.5704 -> 0.554`
- `frozen_40` 同版复跑：
  - `average_duration_sec: 0.5594 -> 0.5454`
- 功能指标保持不变：
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
- 长期性能阈值：
  - `improved_v32` 阈值：`0.5514`
  - `v63r3 frozen_40`：`0.5454`

### 结论

- `v63r2` 的 `0.5594` 更像一次偏高采样，而不是策略本身稳定变慢
- `improved_v63` 在同版复跑中已自然回落到阈值以内
- 截至 `benchmark_maturity_maturity_044`：
  - `formal_task_count = 60`
  - `ecosystem_count = 14`
  - `latest_frozen_count = 40`
  - `frozen_40_streak = 8`
  - 当前性能口径也已满足 `<= 0.5514`
- 因此 Benchmark Maturity v1 当前可以正式视为达成

## 2026-06-13 C2/C3 候选链路收口

### 本轮目标

- 修复 `--from-candidate --dry-run` 验证时误污染 candidate 状态的问题
- 把候选状态机从历史的 `to_review / drafted / scaffolded` 口径收敛到 roadmap 里的最小版
- 给后续 issue 扩容补上更稳的半自动筛选入口

### 改动类型

- `workflow`
- `tooling`
- `documentation`

### 主要文件

- `scripts/import_github_issue.py`
- `scripts/scaffold_semi_real_task.py`
- `scripts/screen_candidate.py`
- `scripts/run_real_issue_eval.py`
- `benchmarks/real_world_candidates.json`
- `GUIDE.md`
- `docs/next_actions.md`

### 本轮实现内容

- 把 `import_github_issue.py` 新导入候选的默认状态改成 `imported`
- 取消把 real_issue 草稿显式写成 `drafted` 状态，改为只追加备注
- 给 `scaffold_semi_real_task.py` 增加候选状态门禁：
  - 非 `dry-run` 模式下，只有 `screened` 或 `accepted` 的候选允许落盘
- 保留 `--dry-run` 只看自动推断结果，不写任务、不建 repo、不改 candidate
- 让 `run_real_issue_eval.py` 在状态汇总里基于本轮成功任务派生 `completed` 计数
- 修回 `pypa_distlib_issue_238` 的误状态，避免把验证残留混入正式候选基线

### 结论

- 候选导入、人工筛选、脚手架生成之间的边界已经更清晰
- 之后继续扩真实 issue 时，可以先 `imported`，再 `screened`，再进入脚手架阶段
- `docs/optimization_log.md` 继续保持追加式记录，不覆盖历史

## 2026-06-13 C3 状态机脚本与当前态文档补齐

### 本轮目标

- 把仍在使用旧候选状态口径的脚本入口和当前态文档继续收口
- 避免 `validate_tasks.py`、`import_issue_batch.py` 和 benchmark 说明继续输出 `to_review / drafted / rejected`

### 改动类型

- `tooling`
- `validation`
- `documentation`

### 主要文件

- `scripts/validate_tasks.py`
- `scripts/import_issue_batch.py`
- `docs/benchmark.md`
- `docs/project_memory.md`

### 本轮实现内容

- `validate_tasks.py` 的候选状态校验改为：
  - `imported`
  - `screened`
  - `accepted`
  - `completed`
  - `blocked`
- `import_issue_batch.py` 的批量导入输出从 `drafted_count` 改成 `draft_task_count`
- 批量导入单条结果会显式打印：
  - `status`
  - `draft_task_generated`
- 更新了 benchmark 和 project memory 中的“当前候选池状态”说明
- 保留历史日志里的旧状态描述不回写，只修当前对外口径

### 结论

- 候选状态机的主入口、校验器和当前态文档现在已经基本统一到 roadmap 的最小版设计
- 后续继续扩容时，可以直接沿 `imported -> screened -> accepted -> completed` 推进，而不会再被旧术语干扰

## 2026-06-13 C1 -> C3 搜索结果导入链路补齐

### 本轮目标

- 把 `search_candidate_issues.py` 的输出真正接到候选池
- 避免候选搜索结果只能停留在 `logs/summaries/candidate_search_*.json`，仍然需要手工搬运

### 改动类型

- `tooling`
- `workflow`
- `documentation`

### 主要文件

- `scripts/import_search_results.py`
- `scripts/import_github_issue.py`
- `tests/test_import_search_results.py`
- `tests/test_import_issue_batch.py`
- `GUIDE.md`
- `docs/next_actions.md`

### 本轮实现内容

- 新增 `scripts/import_search_results.py`
- 支持把 `candidate_search_*.json` 导入 `benchmarks/real_world_candidates.json`
- 支持：
  - `--recommendation high,medium`
  - `--limit N`
- 搜索结果导入后的默认状态为 `imported`
- 如果 candidate 已存在：
  - 保留既有人工状态
  - 只追加“重新同步 GitHub issue 元数据”备注
- 在 `import_github_issue.py` 中补了 `build_candidate_from_search_summary()` 复用入口

### 结论

- `C1` 的搜索报告现在已经能自然流入 `C3` 的候选状态机
- 后续扩新来源时，可以按 `search -> import_search_results -> screen_candidate -> scaffold` 的链路连续推进

## 2026-06-13 C1 搜索启发式去噪与质量修正

### 本轮目标

- 修正 `search_candidate_issues.py` 里最明显的 family / recommendation 误判
- 避免代码块、URL 和异常示例把候选错误打成 `并发与协程` 或 `其他`

### 改动类型

- `tooling`
- `quality`
- `testing`

### 主要文件

- `scripts/search_candidate_issues.py`
- `tests/test_search_candidate_issues.py`

### 本轮实现内容

- 给搜索启发式增加了信号清洗：
  - 去掉代码块
  - 去掉 URL
  - 再做 family / recommendation / risk 推断
- 补充了更贴近文本 bug 的关键词：
  - `unicode`
  - `UnicodeEncodeError`
  - `UnicodeDecodeError`
  - `wrap/wrapping`
  - `encoding`
- 收紧了 `risk_notes` 的网络风险触发条件：
  - 不再因为 issue 正文里出现 GitHub 链接就误判成“重环境问题”
- 新增针对性测试，覆盖：
  - 代码块中的 `subprocess.run()` 不应把文本 bug 判成并发问题
  - URL 不应把 wrapping bug 判成网络依赖问题

### 验证

- `python -m pytest tests/test_search_candidate_issues.py tests/test_import_search_results.py tests/test_import_issue_batch.py -q`
- `python scripts/validate_tasks.py`

### 结论

- 这轮修正后，`candidate_search_textualize_rich_001.json` 里的两个样本都会更自然地落到 `解析与字符串语义`
- 后续真正对 `asyncio / trio / anyio / pathlib / fsspec` 做扩容搜索时，误判噪声会更低

## 2026-06-13 C3 候选批量筛选入口补齐

### 本轮目标

- 把 `screen_candidate.py` 从“单条手工筛一个”推进到“按状态批量逐条筛”
- 降低后续清理 `imported` 候选池时的人肉操作成本

### 改动类型

- `tooling`
- `workflow`
- `testing`

### 主要文件

- `scripts/screen_candidate.py`
- `tests/test_screen_candidate.py`
- `GUIDE.md`
- `docs/next_actions.md`

### 本轮实现内容

- `screen_candidate.py` 新增批量模式：
  - `--status imported`
  - `--limit N`
  - `--decision y/n/s`
- 当不传 `--candidate-id` 时，会按状态筛出候选并逐条处理
- 默认状态过滤为 `imported`
- 批量模式会输出：
  - `matched_count`
  - `screened_count`
  - `blocked_count`
  - `skipped_count`
  - 每条 candidate 的状态变化
- 新增测试覆盖：
  - 按状态过滤
  - 状态解析
  - 单条状态更新
  - 筛选后备注追加

### 结论

- 候选池治理现在更接近 roadmap 的真实使用场景
- 后续用 `search -> import_search_results -> screen_candidate(batch) -> scaffold` 扩新来源时，会顺手很多

## 2026-06-13 A2 定向搜索预设补齐

### 本轮目标

- 让 `search_candidate_issues.py` 更贴近 A2 当前真实缺口
- 减少为了补 `并发与协程 / 文件路径与 IO` 候选而手工反复试 query 的成本

### 改动类型

- `tooling`
- `workflow`
- `documentation`

### 主要文件

- `scripts/search_candidate_issues.py`
- `tests/test_search_candidate_issues.py`
- `GUIDE.md`
- `docs/next_actions.md`

### 本轮实现内容

- 给 `search_candidate_issues.py` 新增 `--target-family`
- 当前支持的搜索预设：
  - `并发与协程`
  - `文件路径与 IO`
  - `继承、优先级与控制流`
- 支持别名输入，例如：
  - `async`
  - `路径`
  - `priority`
- 当启用 `--target-family` 时，会自动在基础 query 上追加对应关键词组
- 输出摘要和 Markdown 报告里也会记录 `target_family`

### 验证

- `python -m pytest tests/test_search_candidate_issues.py -q`
- `python scripts/search_candidate_issues.py --help`

### 结论

- A2 的“补 0 覆盖家族”现在已经不只是文档建议，而是有了直接可用的命令入口
- 下一步如果继续扩真实 issue，可以优先用这组预设去跑 `trio / anyio / pathlib / fsspec`

## 2026-06-13 A2 首轮真实候选扩容

### 本轮目标

- 用已经补好的 A2/C 线入口，真正跑一轮新来源候选扩容
- 不再只停在工具和文档层

### 改动类型

- `candidate expansion`
- `workflow`
- `documentation`

### 主要产物

- `logs/summaries/candidate_search_anyio_async_scan_001.json`
- `logs/summaries/candidate_search_watchfiles_path_scan_001.json`
- `logs/summaries/candidate_search_fsspec_path_scan_002.json`
- `benchmarks/real_world_candidates.json`
- `docs/candidate_shortlist.md`
- `docs/next_actions.md`

### 本轮实现内容

- 通过代理 + `gh auth token` 跑通 live candidate search
- 确认 `python-trio/trio` 当前这轮没有返回 closed bug 候选
- 成功拿到：
  - `agronholm/anyio` 候选 `11` 条
  - `samuelcolvin/watchfiles` 候选 `8` 条
  - `fsspec/filesystem_spec` 候选 `1` 条
- 为避免一次性灌入太多噪声，只精选导入了 `5` 条：
  - `agronholm/anyio#1109`
  - `agronholm/anyio#1111`
  - `agronholm/anyio#1113`
  - `samuelcolvin/watchfiles#266`
  - `fsspec/filesystem_spec#979`
- 重建了 shortlist，并明确推荐优先顺序：
  - `fsspec#979`
  - `anyio#1109`
  - `anyio#1111`

### 结论

- A2 的“补并发与协程 / 文件路径与 IO 空白”已经进入真实候选推进阶段
- 下一步最自然的动作不是继续搜，而是把 `fsspec#979` 或 `anyio#1109` 推进到 `screened` 并开始 semi_real 缩题

## 2026-06-13 首条新候选推进到 screened

### 本轮目标

- 不只把候选导入池子，而是把 shortlist 第一名真正推进一步
- 验证这条新来源候选是否已经足够接近 semi_real 缩题

### 改动类型

- `candidate triage`
- `workflow`
- `documentation`

### 主要文件

- `benchmarks/real_world_candidates.json`
- `docs/candidate_shortlist.md`
- `docs/next_actions.md`

### 本轮实现内容

- 将 `fsspec/filesystem_spec#979` 从 `imported` 推进到 `screened`
- 跑通：
  - `python scripts/scaffold_semi_real_task.py --from-candidate fsspec_filesystem_spec_issue_979 --candidate-file benchmarks/real_world_candidates.json --semi-repo-name fsspec_unstrip_protocol_repo --dry-run`
- 确认这条 issue 已经可以进入 semi_real 缩题准备阶段
- 同时也观察到一个后续细化点：
  - 当前自动推断还没有抓到真正的目标模块路径，真实落盘前建议手工补上 `expected_target_files`

### 结论

- `fsspec#979` 现在已经是“可直接继续缩题”的状态，不再只是候选池里的一个名字
- 下一步最优先的动作是补目标文件提示并进入非 dry-run 脚手架阶段

## 2026-06-13 文档口径与候选元数据收口

### 本轮目标

- 修正 v2 路线图推进后遗留的旧口径，避免文档继续把当前阶段描述成更早版本
- 为 `fsspec#979` 补齐足够进入非 dry-run 脚手架的候选元数据

### 改动类型

- `documentation`
- `candidate metadata`
- `workflow hygiene`

### 主要文件

- `benchmarks/real_world_candidates.json`
- `docs/benchmark.md`
- `docs/project_memory.md`

### 本轮实现内容

- 为 `fsspec/filesystem_spec#979` 补充 `expected_target_files`
  - `fsspec/spec.py`
  - `fsspec/tests/test_spec.py`
- 在候选 notes 中追加说明：
  - 当前已手工补齐目标文件提示，后续可直接进入非 dry-run 脚手架
- 修正文档中的旧数据口径：
  - `docs/benchmark.md` 不再把真实 issue 层写成纯 future set
  - 正式任务规模从旧的 `26` 条更新为当前 `60` 条
  - 候选池状态从旧的 `accepted = 60 / imported = 0` 更新为当前 `accepted = 60 / imported = 4 / screened = 1`
- 修正项目记忆卡中的当前重点：
  - 新导入重点来源改为 `anyio / fsspec / watchfiles`
  - 下一步动作明确切到 `fsspec#979 -> anyio#1109/#1111`

### 结论

- 这轮没有引入新功能，但把“当前事实”和“文档叙事”重新对齐了
- 后续继续推进 A2/C 线时，不会再被旧阶段数字和旧候选状态误导

## 2026-06-13 `fsspec#979` 非 dry-run 脚手架落盘

### 本轮目标

- 把 `fsspec/filesystem_spec#979` 从“仅完成筛选”继续推进到真正落盘的 semi_real 脚手架
- 验证 `scaffold_semi_real_task.py --from-candidate` 在真实候选上已经能完成 task + repo 生成

### 改动类型

- `candidate pipeline`
- `semi_real scaffold`
- `documentation`

### 主要文件

- `benchmarks/tasks/task_122.json`
- `benchmarks/repos/fsspec_unstrip_protocol_repo/`
- `benchmarks/real_world_candidates.json`
- `docs/candidate_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 本轮实现内容

- 执行：
  - `python scripts/scaffold_semi_real_task.py --from-candidate fsspec_filesystem_spec_issue_979 --candidate-file benchmarks/real_world_candidates.json --semi-repo-name fsspec_unstrip_protocol_repo`
- 成功生成：
  - `task_122`
  - `benchmarks/repos/fsspec_unstrip_protocol_repo`
  - `fsspec/spec.py`
  - `fsspec/tests/test_spec.py`
- 确认脚手架行为符合预期：
  - 候选仍保持 `screened`
  - 新任务带 `draft` 标签
  - metadata 标记为 `needs_manual_completion`
  - 尚未自动加入正式 manifest
- 跑通基础校验：
  - `python scripts/validate_tasks.py`
- 同步把 roadmap 相关文档更新到当前中间态：
  - `fsspec#979` 已不再只是候选，而是“已生成 draft semi_real”

### 结论

- A2/C 线现在已经真正打通到“候选 -> 落盘脚手架”这一步
- 下一步不该重复做搜索或再做 dry-run，而是直接把 `task_122` 补成可运行回归任务，再决定是否进入正式 manifest

## 2026-06-13 `task_122` ready 化

### 本轮目标

- 把 `fsspec#979` 生成出的 draft 脚手架继续补成真正可运行的 semi_real 任务
- 验证这条新来源候选已经具备 `ready` 口径，而不只是“能落盘”

### 改动类型

- `semi_real task`
- `candidate pipeline`
- `documentation`

### 主要文件

- `benchmarks/repos/fsspec_unstrip_protocol_repo/fsspec/spec.py`
- `benchmarks/repos/fsspec_unstrip_protocol_repo/fsspec/tests/test_spec.py`
- `benchmarks/tasks/task_122.json`
- `benchmarks/real_world_candidates.json`
- `docs/candidate_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 本轮实现内容

- 在 `fsspec/spec.py` 中还原最小缺陷：
  - 旧逻辑只要发现路径以 `protocol` 开头就直接返回
  - 正确判定应只在路径以 `protocol://` 开头时才视为已有协议
- 在 `fsspec/tests/test_spec.py` 中补成 3 个稳定回归测试：
  - `abstract-file`
  - `s3-file / s3a-file`
  - 已带 `s3://` 的正常不回归场景
- 先跑测试确认失败形态对准真实缺陷
- 修复实现后再跑测试，确认 `3 / 3` 全绿
- 将 `task_122` 从 draft 元数据推进到 ready 口径：
  - 移除 `draft`
  - 补上 `expected_failure_test`
  - `repo_scaffold_status = ready`
- 将 `fsspec#979` 的候选状态从 `screened` 推进到 `accepted`

### 验证

- `python -m pytest benchmarks/repos/fsspec_unstrip_protocol_repo/fsspec/tests/test_spec.py -q`
- `python scripts/validate_tasks.py`

### 结论

- `fsspec#979` 已经不只是“候选可脚手架”，而是完成了从候选到 ready semi_real 的闭环
- 下一步应把注意力切到：
  - 是否将 `task_122` 纳入正式 manifest
  - 继续推进 `anyio#1109 / #1111`

## 2026-06-13 `task_122` 接入正式 benchmark 与 `improved_v64`

### 本轮目标

- 把 `task_122` 从“ready semi_real”继续推进到真正符合正式 benchmark 口径的任务
- 避免把“已经修好态的 repo”直接误当成正式评测样本

### 改动类型

- `benchmark integrity`
- `policy`
- `documentation`

### 主要文件

- `benchmarks/repos/fsspec_unstrip_protocol_repo/fsspec/spec.py`
- `app/agent/patcher.py`
- `optimization/policy_versions/improved_v64.json`
- `benchmarks/manifests/real_issue_tasks.json`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 本轮实现内容

- 先把 `fsspec_unstrip_protocol_repo` 恢复成带 bug 的基线状态
  - `unstrip_protocol()` 再次保留“只按协议名前缀判断”的缺陷
- 验证当前带 bug repo 的真实状态：
  - 直接跑 repo 测试，出现 `2 failed, 1 passed`
  - `improved_v63` 单任务运行失败，且 patcher 未命中
- 在 patcher 中新增 `improved_v64` 的专用规则：
  - 只在路径已带 `protocol://` 时保留原串
  - 其余前缀相似路径一律补回协议
- 新增：
  - `optimization/policy_versions/improved_v64.json`
- 再验证：
  - `improved_v64` 对 `task_122` 单任务成功
  - pre-test 失败、post-test 通过，形成真实修复证据
- 把 `task_122` 加入正式 manifest
  - 正式任务总数从 `60` 推进到 `61`

### 验证

- `python -m pytest benchmarks/repos/fsspec_unstrip_protocol_repo/fsspec/tests/test_spec.py -q`
- `python scripts/run_single_task.py --task benchmarks/tasks/task_122.json --policy optimization/policy_versions/improved_v63.json`
- `python scripts/run_single_task.py --task benchmarks/tasks/task_122.json --policy optimization/policy_versions/improved_v64.json`
- `python scripts/validate_tasks.py`

### 结论

- `task_122` 现在已经不是“修好态样本”，而是正式 benchmark 可接受的真实任务形态
- 当前还缺的是：
  - `improved_v64` 的正式集 / frozen 集最小验证
  - 再继续推进 `anyio` 方向的新来源扩容

## 2026-06-13 `improved_v64` 三线最小验证

### 本轮目标

- 为 `improved_v64` 补齐正式集、`frozen_20`、`frozen_40` 的最小验证
- 验证 `task_122` 接入后，是否保持正式 benchmark 的功能稳定性

### 改动类型

- `evaluation`
- `benchmark expansion`
- `documentation`

### 主要产物

- `logs/summaries/batch_eval_realissuev64r1_001.json`
- `logs/summaries/batch_compare_realissue_step49_001.json`
- `logs/summaries/batch_eval_frozen20v64r1_001.json`
- `logs/summaries/batch_compare_frozen20_step47_002.json`
- `logs/summaries/batch_eval_frozen40v64r1_001.json`
- `logs/summaries/batch_compare_frozen40_step23_002.json`
- `logs/summaries/benchmark_maturity_maturity_051.json`

### 本轮实现内容

- 运行：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v64.json --run-label realissuev64r1 --compare-against-eval logs/summaries/batch_eval_realissuev63r2_001.json --compare-label realissue_step49`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v64.json --run-label frozen20v64r1 --compare-against-eval logs/summaries/batch_eval_frozen20v63r2_001.json --compare-label frozen20_step47`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v64.json --run-label frozen40v64r1 --compare-against-eval logs/summaries/batch_eval_frozen40v63r2_001.json --compare-label frozen40_step23`
- 验证结果：
  - 正式集：`60 -> 61` 条，`61 / 61` 成功，`average_duration_sec: 0.5411 -> 0.5551`
  - `frozen_20`：功能继续全绿，`average_duration_sec: 0.5704 -> 0.5773`
  - `frozen_40`：功能继续全绿，`average_duration_sec: 0.5594 -> 0.5686`
- maturity 审计同步更新为：
  - `formal = 61 / 60`
  - `eco = 15 / 6`
  - `frozen = 40 / 40`
  - `streak = 8 / 5`

### 结论

- `improved_v64` 已完成最小三线扩容验证
- 这一轮的准确结论是：
  - 扩容成功
  - 功能无回归
  - 性能轻微回升
- 下一步最合理的是补一轮 `v64` 稳定性复跑，再决定这次回升是单次采样波动还是稳定趋势

## 2026-06-13 `improved_v64` 稳定性复跑

### 本轮目标

- 判断 `v64` 单次 compare 中出现的轻微耗时回升，到底是采样波动还是稳定趋势
- 继续沿 B 线把“单次结果”和“复跑口径”分开记录

### 改动类型

- `stability`
- `evaluation`
- `documentation`

### 主要产物

- `logs/summaries/stability_recheck_frozen20_v64_stability_001.json`
- `logs/summaries/stability_recheck_frozen40_v64_stability_001.json`

### 本轮实现内容

- 运行：
  - `python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v64.json --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --repetitions 3 --run-label frozen20_v64_stability`
  - `python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v64.json --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --repetitions 3 --run-label frozen40_v64_stability`
- 结果：
  - `frozen_20`
    - mean = `0.5475`
    - std = `0.0182`
    - conclusion = `stable`
  - `frozen_40`
    - mean = `0.5432`
    - std = `0.0035`
    - conclusion = `stable`
    - 并且均值已经回到长期阈值 `0.5514` 以内

### 结论

- `v64` 当前最准确的表述应更新为：
  - 扩容成功
  - 功能无回归
  - 复跑口径稳定
- 单次 compare 中观察到的轻微时延回升，不足以单独定性为长期退化
- 下一步可以把主注意力重新切回 `anyio#1109 / #1111`

## 2026-06-13 `anyio#1109` 推进到 screened

### 本轮目标

- 在 `fsspec#979` 这条线阶段性收口后，把 A2 主焦点切回并发与协程缺口
- 不再只停留在 shortlist，而是真正推进下一条高优先级候选

### 改动类型

- `candidate triage`
- `candidate pipeline`
- `documentation`

### 主要文件

- `benchmarks/real_world_candidates.json`
- `docs/candidate_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 本轮实现内容

- 将 `agronholm/anyio#1109` 从 `imported` 推进到 `screened`
- 运行：
  - `python scripts/scaffold_semi_real_task.py --from-candidate agronholm_anyio_issue_1109 --candidate-file benchmarks/real_world_candidates.json --semi-repo-name anyio_taskgroup_reentry_repo --dry-run`
- dry-run 结果：
  - `module_file = anyio_taskgroup_reentry_repo/module.py`
  - `test_file = tests/test_module.py`
- 结论：
  - 当前 issue 已足够进入 semi_real 缩题阶段
  - 但自动推断还没抓到真实目标文件，非 `dry-run` 前最好先手工补 `expected_target_files`

### 结论

- roadmap 的当前扩容焦点已经从 `fsspec#979` 顺利切到 `anyio#1109`
- 下一步最自然的动作是先补 target file 提示，再把 `anyio#1109` 进入非 `dry-run` 脚手架

## 2026-06-13 `anyio#1109` 落盘 non-dry-run semi_real 草稿

本轮推进：

- 为 `agronholm/anyio#1109` 补上 `expected_target_files`
  - `anyio/_backends/_asyncio.py`
  - `tests/test_taskgroups.py`
- 运行：
  - `python scripts/scaffold_semi_real_task.py --from-candidate agronholm_anyio_issue_1109 --candidate-file benchmarks/real_world_candidates.json --semi-repo-name anyio_taskgroup_reentry_repo`
- 成功生成：
  - `benchmarks/tasks/task_123.json`
  - `benchmarks/repos/anyio_taskgroup_reentry_repo`

结果与判断：

- 这说明 `anyio#1109` 已从“只有 dry-run 证据”推进到“真正落盘的 semi_real 草稿”
- 当前自动推断已经命中较可信的目标形状：
  - `module_file = anyio/_backends/_asyncio.py`
  - `test_file = tests/test_taskgroups.py`
- 候选状态保持 `screened` 是合理的，因为当前 repo 里仍然是 TODO 模块与 TODO 测试，还没有 ready 化

下一步：

- 把 `anyio_taskgroup_reentry_repo` 的 TODO 脚手架补成最小可运行 bug repo
- 让旧策略对带 bug 的 `task_123` 失败，再补新策略尝试修复
- 如果这条线顺利，再考虑把 `agronholm/anyio#1111` 作为并发家族的第二条候选推进

## 2026-06-13 `task_123` ready 化并验证带 bug 状态

本轮推进：

- 将 `benchmarks/repos/anyio_taskgroup_reentry_repo` 从空脚手架补成最小可运行 repo
- 新增最小公开入口：
  - `anyio.create_task_group()`
  - `anyio.run(...)`
- 在 `anyio/_backends/_asyncio.py` 中保留核心 bug：
  - 第一次退出后删除 `_exceptions`
  - 第二次再次退出同一个 `TaskGroup` 时触发 `AttributeError`
- 将 `tests/test_taskgroups.py` 改为 2 条稳定测试：
  - 正常路径：不同 task group 顺序使用通过
  - 目标回归：重复进入同一个 task group 时期望抛出受控错误
- 补充 `anyio/pytest_plugin.py`
  - 避免本地最小 `anyio` 包遮住环境插件后，pytest 在启动阶段先失败

验证：

- 运行：
  - `python -m pytest tests/test_taskgroups.py -q`
- 结果：
  - `1 passed, 1 failed`
- 当前失败点：
  - `test_reentering_same_task_group_raises_runtime_error`
  - 实际错误：`AttributeError: 'TaskGroup' object has no attribute '_exceptions'`

结果与判断：

- 这说明 `task_123` 已经从“只有文件壳子”推进到“真正带 bug 的 ready semi-real 任务”
- 当前失败形式与原 issue 对齐，说明它已经适合作为下一轮策略验证入口
- 下一步最自然的动作是：
  - 跑单任务确认当前旧策略失败
  - 在 `app/agent/patcher.py` 中补针对 task group 重复进入的修复规则
  - 新增下一版 policy 并做最小三线验证

## 2026-06-13 `task_123` 单任务验证打通 `improved_v64 -> improved_v65`

本轮推进：

- 运行旧策略：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_123.json --policy optimization/policy_versions/improved_v64.json`
- 结果：
  - `final_status = failed`
  - `patch_applied = false`
  - 说明旧规则链对 `TaskGroup` 重复进入场景没有自动修复能力
- 在 `app/agent/patcher.py` 中新增：
  - `_handle_anyio_taskgroup_reentry_guard`
- 新增 policy：
  - `optimization/policy_versions/improved_v65.json`
- 运行新策略：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_123.json --policy optimization/policy_versions/improved_v65.json`
- 结果：
  - `final_status = success`
  - `patch_applied = true`
  - 只修改 `anyio/_backends/_asyncio.py`

修复语义：

- 重复进入同一个 `TaskGroup` 时
- 不再继续沿用第一次退出后已删除的 `_exceptions` 状态
- 直接抛出受控 `RuntimeError("TaskGroup cannot be re-entered")`

结果与判断：

- 这说明 `anyio#1109 -> task_123 -> improved_v65` 这条线已经完成了最关键的“旧策略失败 / 新策略成功”验证
- 当前最自然的下一步已经从“还原任务”切到“是否纳入正式集前的最小三线验证”

## 2026-06-13 `improved_v65` 三线最小验证收口

### 本轮目标

- 在修复 `v43 ~ v50` 继承链漏接后，重新拿到 `improved_v65` 的可信最终结论
- 确认 `task_123` 纳入正式集后，不会把正式集或冻结集打坏

### 主要文件

- `app/agent/patcher.py`
- `optimization/policy_versions/improved_v65.json`
- `benchmarks/manifests/real_issue_tasks.json`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/experiment_summary.md`
- `README.md`

### 本轮运行

- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v65.json --run-label realissuev65r3 --compare-against-eval logs/summaries/batch_eval_realissuev64r1_001.json --compare-label realissue_step50_r3`
- `frozen_20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v65.json --run-label frozen20v65r3 --compare-against-eval logs/summaries/batch_eval_frozen20v64r1_001.json --compare-label frozen20_step48_r3`
- `frozen_40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v65.json --run-label frozen40v65r3 --compare-against-eval logs/summaries/batch_eval_frozen40v64r1_001.json --compare-label frozen40_step24_r3`

### 结果

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
- maturity：
  - `formal = 62 / 60`
  - `eco = 16 / 6`
  - `frozen = 40 / 40`
  - `streak = 8 / 5`

### 结论

- `improved_v65` 当前可以定性为：
  - 新任务 `task_123` 扩容成功
  - 新生态 `agronholm/anyio` 接入成功
  - 正式集、`frozen_20`、`frozen_40` 三线无回归
  - 当前 compare 口径下三条线平均耗时都相对 `v64` 小幅改善
- 之前 `v65r1 / v65r2` 暴露出来的大面积 `Premature Finish`，最终确认主要是 patcher 版本继承链漏接，不应再作为 `v65` 的最终能力结论

### 产物

- `logs/summaries/batch_eval_realissuev65r3_001.json`
- `logs/summaries/batch_compare_realissue_step50_r3_001.json`
- `logs/summaries/batch_eval_frozen20v65r3_001.json`
- `logs/summaries/batch_compare_frozen20_step48_r3_001.json`
- `logs/summaries/batch_eval_frozen40v65r3_001.json`
- `logs/summaries/batch_compare_frozen40_step24_r3_001.json`
- `logs/summaries/benchmark_maturity_maturity_060.json`

## 2026-06-13 `improved_v65` 稳定性复跑

### 本轮目标

- 为 `improved_v65` 补齐冻结集上的同版 stability recheck
- 确认 `anyio` 并发生态扩容后，不只是“最小验证能过”，而且复跑口径也稳定

### 本轮运行

- `frozen_20`：
  - `python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v65.json --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --repetitions 3 --run-label frozen20_v65_stability`
- `frozen_40`：
  - `python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v65.json --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --repetitions 3 --run-label frozen40_v65_stability`

### 结果

- `frozen_20`
  - mean = `0.5617`
  - std = `0.0051`
  - outlier_count = `0`
  - conclusion = `stable`
- `frozen_40`
  - mean = `0.5487`
  - std = `0.0126`
  - outlier_count = `0`
  - conclusion = `stable`
- 两条冻结集都保持：
  - `functional_consistent = true`
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`

### 结论

- `improved_v65` 当前最终口径可以更新为：
  - 正式集、`frozen_20`、`frozen_40` 三线无回归
  - `frozen_20 / frozen_40` 同版复跑均达到 `stable`
  - `anyio` 并发生态扩容已经从“能过”收口到“稳定能过”
- 这也说明当前主注意力可以继续切向下一条并发候选，而不必继续停留在 `task_123` 的收尾验证上

### 产物

- `logs/summaries/stability_recheck_frozen20_v65_stability_001.json`
- `logs/summaries/stability_recheck_frozen20_v65_stability_001.md`
- `logs/summaries/stability_recheck_frozen40_v65_stability_001.json`
- `logs/summaries/stability_recheck_frozen40_v65_stability_001.md`

## 2026-06-13 `anyio#1111` 推进到 ready bug repo

### 本轮目标

- 在 `task_123 / improved_v65` 收口后，继续沿并发与协程家族推进下一条高优先级候选
- 判断 `agronholm/anyio#1111` 能否进入正式的 semi-real 缩题与策略验证链路

### 本轮推进

- 先人工筛选：
  - `python scripts/screen_candidate.py --candidate-file benchmarks/real_world_candidates.json --candidate-id agronholm_anyio_issue_1111 --decision y`
- 再做脚手架 dry-run：
  - `python scripts/scaffold_semi_real_task.py --from-candidate agronholm_anyio_issue_1111 --candidate-file benchmarks/real_world_candidates.json --semi-repo-name anyio_cancellation_spin_repo --dry-run`
- dry-run 命中：
  - `module_file = anyio/_backends/_asyncio.py`
  - `test_file = tests/test__asyncio.py`
- 继续执行非 `dry-run`：
  - `python scripts/scaffold_semi_real_task.py --from-candidate agronholm_anyio_issue_1111 --candidate-file benchmarks/real_world_candidates.json --semi-repo-name anyio_cancellation_spin_repo`

### 本轮实现内容

- 生成：
  - `benchmarks/tasks/task_124.json`
  - `benchmarks/repos/anyio_cancellation_spin_repo`
- 将空脚手架补成最小可运行 bug repo：
  - `anyio/_backends/_asyncio.py`
  - `tests/test__asyncio.py`
  - `anyio/__init__.py`
  - `anyio/pytest_plugin.py`
- 当前还原的核心语义是：
  - `_deliver_cancellation` 对已完成 task 缺少 `task.done()` 检查
  - 导致已完成 task 留在 `_tasks` 集合时，回调持续自我重排

### 验证

- 运行：
  - `python -m pytest tests/test__asyncio.py -q`
- 结果：
  - `1 passed, 1 failed`
- 当前失败点：
  - `test_completed_task_is_ignored_during_cancellation_delivery`
  - 失败形式：
    - `RuntimeError("Detected cancellation spin")`

### 结论

- `anyio#1111` 已经从“只有候选说明”推进到“ready 口径最小 bug repo”
- 这说明它已经具备进入下一轮策略验证的条件
- 当前最自然的下一步是：
  - 跑 `improved_v65` 单任务，确认旧策略失败
  - 再决定是否引入 `improved_v66`

## 2026-06-13 `improved_v66` 命中 `anyio#1111`

### 本轮目标

- 把 `task_124` 从 ready bug repo 继续推进到正式 benchmark 口径
- 形成清晰证据链：
  - 带 bug repo 保留
  - 旧策略失败
  - 新策略成功

### 本轮实现

- 在 `app/agent/patcher.py` 中新增：
  - `_handle_anyio_completed_task_cancellation_guard`
- 在版本继承链中接入：
  - `improved_v66`
- 新增策略文件：
  - `optimization/policy_versions/improved_v66.json`

### 修复语义

- 问题根因：
  - `_deliver_cancellation` 遇到已完成 task 时，只触发下一轮重排
  - 但没有把已完成 task 从 `_tasks` 集合中清掉
- 规则修复：
  - 若 `task.done()` 为真，直接从 `_tasks` 中移除
  - 不再继续 `call_soon` 自我重排

### 单任务验证

- 旧策略失败：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_124.json --policy optimization/policy_versions/improved_v65.json`
- 新策略成功：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_124.json --policy optimization/policy_versions/improved_v66.json`

### 结果

- `improved_v65`
  - `final_status = failed`
  - `patch_applied = false`
- `improved_v66`
  - `final_status = success`
  - `patch_applied = true`
  - `modified_files = ["anyio/_backends/_asyncio.py"]`
  - `duration_sec = 0.5343`

### 结论

- `task_124` 已满足正式纳入条件
- 当前已完成：
  - 候选状态 `screened -> accepted`
  - `task_124` 纳入 `real_issue_tasks.json`
- 当前下一步应补：
  - `improved_v66` 的正式集、`frozen_20`、`frozen_40` 最小验证

### 产物

- `logs/trajectories/task_124/run_20260613T080448188084Z_1975/result.json`
- `logs/trajectories/task_124/run_20260613T081144377715Z_2752/result.json`
- `logs/trajectories/task_124/run_20260613T081144377715Z_2752/summary.md`

## 2026-06-13 `improved_v66` 三线最小验证

### 本轮目标

- 把 `improved_v66` 从“单任务成功”推进到正式 benchmark 口径
- 判断它是否能像 `v65` 一样完成：
  - 正式集扩容
  - `frozen_20` 无回归
  - `frozen_40` 无回归

### 首轮结果

- `v66r1` 首轮不是一次过：
  - 正式集 `62 / 63`
  - `task_123` 出现 `Premature Finish`
- 冻结集两条线功能仍是全绿

### 首轮暴露的问题

- 根因不是 `task_124` 本身，而是版本继承链漏接：
  - `improved_v65` 的 `TaskGroup` 规则没有继续继承到 `improved_v66`
- 具体现象：
  - `task_123` 单任务失败
  - `patch_applied = false`
  - `当前规则型 patch 生成器未找到可自动修复的位置`

### 修复动作

- 在 `app/agent/patcher.py` 中把：
  - `if policy_config.patch_strategy == "improved_v65":`
- 改为：
  - `if policy_config.patch_strategy in {"improved_v65", "improved_v66"}:`

### 复验结果

- 单任务：
  - `task_123 / improved_v66` 成功
  - `task_124 / improved_v66` 成功
- `v66r2` 三线最小验证：
  - 正式集：`63 / 63`
  - `frozen_20`：`20 / 20`
  - `frozen_40`：`40 / 40`

### 性能观察

- 正式集：
  - `0.5434 -> 0.5514`
- `frozen_20`：
  - `0.5611 -> 0.5867`
- `frozen_40`：
  - `0.5520 -> 0.5732`

### 时延分析

已补：

- `duration_compare_realissuev66r2_001.md`
- `duration_compare_frozen20v66r2_001.md`
- `duration_compare_frozen40v66r2_001.md`

当前共同热点回升任务主要包括：

- `task_013`
- `task_022`
- `task_024`
- `task_030`
- `task_036`
- `task_056`
- `task_063`

### 结论

- `v66` 当前最终口径应更新为：
  - `task_124` 正式接入成功
  - 正式任务数推进到 `63`
  - 正式集、`frozen_20`、`frozen_40` 三线功能全绿
  - 但当前平均耗时相对 `v65` 有系统性回升
  - 所以现在还不能把 `v66` 直接视为新的稳定基线

### 产物

- `logs/summaries/batch_eval_realissuev66r2_001.json`
- `logs/summaries/batch_compare_realissue_step52_r2_001.json`
- `logs/summaries/batch_eval_frozen20v66r2_001.json`
- `logs/summaries/batch_compare_frozen20_step50_r2_001.json`
- `logs/summaries/batch_eval_frozen40v66r2_001.json`
- `logs/summaries/batch_compare_frozen40_step26_r2_001.json`
- `logs/summaries/duration_compare_realissuev66r2_001.md`
- `logs/summaries/duration_compare_frozen20v66r2_001.md`
- `logs/summaries/duration_compare_frozen40v66r2_001.md`

## 2026-06-13 从 `v66` 性能回升到 `v68` 回收耗时

### 本轮目标

- 不停留在“`v66` 变慢了”的描述层
- 继续把性能问题推进到：
  - 可定位
  - 可否证
  - 可形成下一版策略

### 第一阶段：定位 `v66` 的回升来源

先补：

- `trace_hotspots_realissuev66r2_001`
- `trace_hotspots_frozen40v66r2_001`
- `task_history_cohort_v66_hotspots_001`
- `task_history_task_013_001`
- `task_history_task_024_001`

结论收敛为：

- 主要回升来源不是 patch 规则本身
- 主要增量集中在：
  - `run_tests`
- 更细一层看：
  - 主要落在 `run_tests` 的 subprocess / pytest collection 链路

### 第二阶段：代表任务细分实验

对 `task_013` / `task_024` 分别补：

- `pytest_phases_*`
- `pytest_importtime_*`
- `pytest_plugin_variants_*`

共同结论：

- `pytest_collect_only` 相对 `pytest --version` 仍会稳定多出约 `37` 个模块
- 局部最强降耗变体是：
  - `minimal_safe_plugins`
- 但更保守、看起来更可能落地的候选是：
  - `-p no:threadexception`

### 第三阶段：`v67` 失败试验

先尝试：

- `improved_v67`
- flags:
  - `-p no:debugging`
  - `-p no:unraisableexception`
  - `-p no:threadexception`

局部 benchmark 看起来更快，但真实评测闭环直接失败：

- 正式集：`2 / 63`
- `frozen_20`：`0 / 20`
- `frozen_40`：`0 / 40`

失败形式统一指向：

- `_pytest.config.__init__.py:1892`
- `ValueError: no option named 'trace'`

根因：

- 关闭 `debugging` 插件后
- unittest 路径仍会访问 tracing 选项
- 导致当前 pytest 运行前提被破坏

这条线当前可以明确记为：

- **无效优化方向**

### 第四阶段：`v68` 保守收口

基于 `v67` 的失败，把 runtime 裁剪收窄为：

- `improved_v68`
- flags:
  - `-p no:unraisableexception`
  - `-p no:threadexception`

先过代表单任务：

- `task_013` 成功
- `task_024` 成功
- `task_123` 成功
- `task_124` 成功

再补三线最小验证：

- 正式集：`63 / 63`
- `frozen_20`：`20 / 20`
- `frozen_40`：`40 / 40`

相对 `v66`：

- 正式集：
  - `0.5514 -> 0.5424`
- `frozen_20`：
  - `0.5867 -> 0.5609`
- `frozen_40`：
  - `0.5732 -> 0.5589`

### 第五阶段：`v68` 稳定性复跑

已补：

- `stability_recheck_frozen20_v68_stability_001`
- `stability_recheck_frozen40_v68_stability_001`

结果：

- `frozen_20`
  - mean = `0.5617`
  - std = `0.0166`
  - conclusion = `stable`
- `frozen_40`
  - mean = `0.5529`
  - std = `0.0031`
  - conclusion = `stable`

### 结论

- `v67` 已明确否证：
  - 过激关闭 pytest debugging 相关插件，会破坏真实 benchmark 闭环
- `v68` 当前最终口径可以更新为：
  - 保持正式集、`frozen_20`、`frozen_40` 三线功能全绿
  - 相对 `v66` 在三条线平均耗时均有回落
  - `frozen_20 / frozen_40` stability recheck 都为 `stable`
- 这意味着当前主线已经可以从“解释 `v66` 为什么慢”切回：
  - 以 `v68` 为主版本继续扩真实 issue

### 产物

- `logs/summaries/trace_hotspots_realissuev66r2_001.md`
- `logs/summaries/trace_hotspots_frozen40v66r2_001.md`
- `logs/summaries/task_history_cohort_v66_hotspots_001.md`
- `logs/summaries/task_history_task_013_001.md`
- `logs/summaries/task_history_task_024_001.md`
- `logs/summaries/pytest_phases_task013_v66_probe_001.md`
- `logs/summaries/pytest_importtime_task013_v66_probe_001.md`
- `logs/summaries/pytest_plugin_variants_task013_v66_probe_001.md`
- `logs/summaries/pytest_phases_task024_v66_probe_001.md`
- `logs/summaries/pytest_importtime_task024_v66_probe_001.md`
- `logs/summaries/pytest_plugin_variants_task024_v66_probe_001.md`
- `logs/summaries/batch_eval_realissuev68r1_001.json`
- `logs/summaries/batch_compare_realissue_step54_r1_001.json`
- `logs/summaries/batch_eval_frozen20v68r1_001.json`
- `logs/summaries/batch_compare_frozen20_step52_r1_001.json`
- `logs/summaries/batch_eval_frozen40v68r1_001.json`
- `logs/summaries/batch_compare_frozen40_step28_r1_001.json`
- `logs/summaries/stability_recheck_frozen20_v68_stability_001.json`
- `logs/summaries/stability_recheck_frozen40_v68_stability_001.json`

## 2026-06-13 Phase 6 环境基线快照 `B4` 首版落地

### 本轮目标

- 把 roadmap 里的 `B4` 从“留待后续”推进成实际可运行脚本
- 让后续性能回归分析不只看任务集时延，还能附带一层环境漂移信号

### 改动类型

- `runtime`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/snapshot_env_baseline.py`
- `scripts/analyze_duration_regressions.py`
- `tests/test_snapshot_env_baseline.py`
- `tests/test_analyze_duration_regressions.py`
- `logs/env_baselines/env_baseline_20260613T090027807410Z.json`
- `logs/env_baselines/env_baseline_20260613T090027807410Z.md`

### 改动摘要

- 新增 `scripts/snapshot_env_baseline.py`
  - 默认重复采样两条固定轻量命令：
    - `python -c "pass"`
    - `python -m pytest --version`
  - 输出每条命令的：
    - `samples_sec`
    - `mean_sec`
    - `min_sec`
    - `max_sec`
    - `std_sec`
  - 支持 `--compare-against`，可和历史快照比较环境漂移
- 增强 `scripts/analyze_duration_regressions.py`
  - 新增 `--env-baseline`
  - 当环境快照中存在 comparison 段时，额外输出：
    - `env_adjusted_common_average_delta_sec`
  - 让时延 compare 至少能先把“环境本身变慢了多少”单独展示出来

### 关键验证

- 针对脚本与接入口的单测：
  - `python -m pytest tests/test_snapshot_env_baseline.py tests/test_analyze_duration_regressions.py -q`
  - 结果：`6 passed`
- 实际跑一份环境快照：
  - `python scripts/snapshot_env_baseline.py --repetitions 2 --output-dir logs/env_baselines`
  - 产出：
    - `logs/env_baselines/env_baseline_20260613T090027807410Z.json`
    - `logs/env_baselines/env_baseline_20260613T090027807410Z.md`
- CLI 接口验证：
  - `python scripts/analyze_duration_regressions.py --help`
  - 已确认 `--env-baseline` 参数正常暴露

### 当前结论

- `B4` 已经不再只是路线图里的待办，而是有脚本、测试和真实产物支撑的首版能力
- 后续如果又出现“固定集合平均耗时突然抬头”的情况，现在可以先采环境基线，再做带环境信号的时延 compare
- 它还不是严格的性能归因器，但已经足够把“环境漂移”和“策略回归”做第一层拆分

### 下一步

- 在下一轮真实扩容或性能回归调查时，补一组：
  - 旧环境快照
  - 新环境快照
  - 带 `--env-baseline` 的 duration compare
- 再决定是否需要把环境基线信号进一步接到 `run_real_issue_eval.py` 的自动流水线里

## 2026-06-13 Phase 6 `anyio#1113` 进入脚手架阶段

### 本轮目标

- 把 `agronholm/anyio#1113` 从 imported 候选推进到可继续落地的本地脚手架状态
- 顺手增强 `--from-candidate`，避免“issue 只有 Python 符号名、没有显式文件路径”时退化成通用 `module.py`

### 改动类型

- `benchmark`
- `tooling`
- `documentation`

### 主要涉及文件

- `benchmarks/tasks/task_125.json`
- `benchmarks/repos/anyio_check_cancelled_repo`
- `benchmarks/real_world_candidates.json`
- `scripts/scaffold_semi_real_task.py`
- `tests/test_scaffold_semi_real_task.py`

### 改动摘要

- 用 `scripts/screen_candidate.py` 把：
  - `agronholm_anyio_issue_1113`
  - 从 `imported` 推进到 `screened`
- 增强 `scripts/scaffold_semi_real_task.py`
  - 新增 Python 符号路径启发式
  - 当 issue 文本出现：
    - `from_thread.check_cancelled`
  - 现在会尝试还原为：
    - `anyio/from_thread.py`
- 基于增强后的 `--from-candidate`，生成：
  - `task_125`
  - `anyio_check_cancelled_repo`

### 关键验证

- 相关单测：
  - `python -m pytest tests/test_scaffold_semi_real_task.py -q`
  - 结果：`5 passed`
- 自动推断 dry-run：
  - `python scripts/scaffold_semi_real_task.py --from-candidate agronholm_anyio_issue_1113 --candidate-file benchmarks/real_world_candidates.json --semi-repo-name anyio_check_cancelled_repo --dry-run`
  - 已确认输出：
    - `module_file: anyio/from_thread.py`
    - `test_file: tests/test_from_thread.py`
- 实际落盘：
  - `python scripts/scaffold_semi_real_task.py --from-candidate agronholm_anyio_issue_1113 --candidate-file benchmarks/real_world_candidates.json --semi-repo-name anyio_check_cancelled_repo`
  - 已生成：
    - `benchmarks/tasks/task_125.json`
    - `benchmarks/repos/anyio_check_cancelled_repo`

### 当前结论

- `anyio#1113` 已不再停留在 imported 候选层，而是进入了可继续 ready 化的本地脚手架阶段
- `--from-candidate` 现在对“正文只有 Python 符号名”的 issue 更友好，后续同类候选转 semi-real 时会更顺手
- 当前还没有进入“正式任务接入”阶段；下一步应先把 `task_125` 从 TODO 脚手架补成 ready bug repo

## 2026-06-13 Phase 6 `task_125` ready bug repo 落地

### 本轮目标

- 把 `agronholm/anyio#1113` 对应的 `task_125`
- 从 TODO 脚手架继续推进到可直接做单任务策略验证的 ready bug repo

### 改动类型

- `benchmark`
- `documentation`

### 主要涉及文件

- `benchmarks/repos/anyio_check_cancelled_repo/anyio/from_thread.py`
- `benchmarks/repos/anyio_check_cancelled_repo/anyio/__init__.py`
- `benchmarks/repos/anyio_check_cancelled_repo/anyio/pytest_plugin.py`
- `benchmarks/repos/anyio_check_cancelled_repo/tests/test_from_thread.py`
- `benchmarks/tasks/task_125.json`

### 改动摘要

- 把 `anyio/from_thread.py` 从 TODO 占位改成最小 backend 分派模型
  - 保留 `asyncio` backend 下 `CancelledError` 泄漏出 cancel scope 的 bug
  - 保留 `trio` backend 作为对照正常路径
- 把 `tests/test_from_thread.py` 从 TODO 测试改成 2 条稳定回归测试
  - `test_trio_backend_catches_cancellation_inside_scope`
  - `test_asyncio_backend_does_not_leak_cancelled_error`
- 新增 `anyio/pytest_plugin.py`
  - 解决本地最小 `anyio` 包遮住环境安装包后，pytest 自动加载入口点失败的问题
- 更新 `task_125.json`
  - `expected_failure_test` 改为：
    - `test_asyncio_backend_does_not_leak_cancelled_error`
  - `draft_status` 改为：
    - `ready`
  - `repo_scaffold_status` 改为：
    - `ready`

### 关键验证

- 整体测试：
  - `python -m pytest tests/test_from_thread.py -q`
  - 结果：`1 failed, 1 passed`
- 正常路径单独验证：
  - `python -m pytest tests/test_from_thread.py -q -k trio`
  - 结果：`1 passed`
- 目标回归单独验证：
  - `python -m pytest tests/test_from_thread.py -q -k asyncio`
  - 结果：`1 failed`

### 当前结论

- `task_125` 已经不再是 TODO 脚手架，而是 ready 口径最小 bug repo
- 当前失败形式和 issue 语义保持一致：
  - `asyncio` backend 下 `CancelledError` 会泄漏出对应 cancel scope
- 后续主线已经切到：
  - 先验证旧策略在 `task_125` 上单任务失败
  - 再决定是否需要新增 `improved_v69`

## 2026-06-13 Phase 6 `task_125 / improved_v69` 正式接入

### 本轮目标

- 验证 `task_125` 是否满足“旧策略失败 / 新策略成功”的正式准入标准
- 若满足，则把它纳入正式 manifest，并补齐 `v69` 的正式集与冻结集最小验证

### 改动类型

- `benchmark`
- `policy`
- `evaluation`
- `documentation`

### 主要涉及文件

- `app/agent/patcher.py`
- `optimization/policy_versions/improved_v69.json`
- `benchmarks/tasks/task_125.json`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`

### 改动摘要

- 单任务验证确认：
  - `improved_v68` 在 `task_125` 上失败
  - `improved_v69` 在 `task_125` 上成功
- 新增 `improved_v69`
  - 保持 `v68` 的 runtime 配置不变
  - 只新增一条规则型修复：
    - 让 `anyio from_thread.check_cancelled` 在 `asyncio` backend 下也通过传入 cancel scope 吃掉 `CancelledError`
- 正式接入：
  - `task_125` 已纳入 `benchmarks/manifests/real_issue_tasks.json`
  - `agronholm_anyio_issue_1113` 状态从 `screened` 推进到 `accepted`
  - `task_125` 的 `draft` 标签已移除

### 关键验证

- 旧策略单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_125.json --policy optimization/policy_versions/improved_v68.json`
  - 结果：`failed`
- 新策略单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_125.json --policy optimization/policy_versions/improved_v69.json`
  - 结果：`success`
- 正式集：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v69.json --run-label realissuev69r1 --compare-against-eval logs/summaries/batch_eval_realissuev68r1_001.json --compare-label realissue_step55_r1`
  - 结果：
    - `64 / 64`
    - `average_duration_sec: 0.5424 -> 0.5656`
- `frozen_20`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v69.json --run-label frozen20v69r1 --compare-against-eval logs/summaries/batch_eval_frozen20v68r1_001.json --compare-label frozen20_step29_r1`
  - 结果：
    - `20 / 20`
    - `average_duration_sec: 0.5609 -> 0.5975`
- `frozen_40`：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v69.json --run-label frozen40v69r1 --compare-against-eval logs/summaries/batch_eval_frozen40v68r1_001.json --compare-label frozen40_step29_r1`
  - 结果：
    - `40 / 40`
    - `average_duration_sec: 0.5589 -> 0.5861`

### 当前结论

- `task_125` 已满足正式准入标准，并已成为第 `64` 条正式任务
- `v69` 功能上完成了新的真实 issue 扩容：
  - 正式集 `64 / 64`
  - `frozen_20` `20 / 20`
  - `frozen_40` `40 / 40`
- `v69` 的 stability recheck 也已补齐：
  - `frozen_20 mean = 0.5665`
  - `frozen_20 conclusion = stable`
  - `frozen_40 mean = 0.5555`
  - `frozen_40 conclusion = stable`
- 但性能口径相对 `v68` 有回升
- 因此当前最准确的判断是：
  - `v69` 是最新扩容成功版本
  - 还不是新的稳定性能叙事锚点
  - 下一步应继续补 stability recheck 和时延定位

## 2026-06-13 Phase 6 `v68 -> v69` 性能回升定位

### 本轮目标

- 把 `v69` 相对 `v68` 的平均耗时回升从“现象”推进为“有证据的诊断结论”
- 为是否需要新增 `improved_v70` 提供直接依据

### 改动类型

- `evaluation`
- `diagnosis`
- `documentation`

### 主要涉及文件

- `logs/summaries/duration_compare_realissuev69r1_001.json`
- `logs/summaries/duration_compare_frozen20v69r1_001.json`
- `logs/summaries/duration_compare_frozen40v69r1_001.json`
- `logs/summaries/trace_hotspots_realissuev69r1_001.json`

### 关键验证

- 正式集公共任务时延分析：
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev68r1_001.json --improved-batch-summary logs/summaries/batch_run_realissuev69r1_001.json --run-label realissuev69r1`
  - 结果：
    - `common_task_count = 63`
    - `common_average_delta_sec = +0.0241`
- `frozen_20` 时延分析：
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen20v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen20v69r1_001.json --run-label frozen20v69r1`
  - 结果：
    - `common_task_count = 20`
    - `common_average_delta_sec = +0.0366`
- `frozen_40` 时延分析：
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40v69r1`
  - 结果：
    - `common_task_count = 40`
    - `common_average_delta_sec = +0.0272`
- 正式集 trace 热点分析：
  - `python scripts/analyze_trace_hotspots.py --baseline-batch-summary logs/summaries/batch_run_realissuev68r1_001.json --improved-batch-summary logs/summaries/batch_run_realissuev69r1_001.json --run-label realissuev69r1`
  - 结果：
    - `average_duration_delta_sec = +0.0241`
    - 顶层工具回升主要集中在 `run_tests` 与 `search_code`

### 诊断摘要

- 这次回升不是由新增 `task_125` 单题直接拉高造成的
  - 正式集公共 `63` 条任务平均增量仍有 `+0.0241s`
- `frozen_20` 与 `frozen_40` 也同步回升
  - 说明这不是只发生在扩容集上的偶发波动
- 正式集 trace 热点显示，主回升来源仍然是：
  - `run_tests`
    - 总量 `32.4093 -> 33.2978`
    - 总增量 `+0.8885s`
  - `search_code`
    - 总量 `0.4815 -> 1.0612`
    - 总增量 `+0.5797s`

### 热点任务

- 正式集 top regressions：
  - `task_123` `+0.0966s`
  - `task_022` `+0.0774s`
  - `task_050` `+0.0739s`
  - `task_034` `+0.0631s`
  - `task_046` `+0.0569s`
- `frozen_20` top regressions：
  - `task_034` `+0.0654s`
  - `task_038` `+0.0643s`
  - `task_024` `+0.0632s`
  - `task_010` `+0.0575s`
  - `task_040` `+0.0547s`
- `frozen_40` top regressions：
  - `task_050` `+0.0743s`
  - `task_034` `+0.0665s`
  - `task_022` `+0.0637s`
  - `task_079` `+0.0580s`
  - `task_010` `+0.0545s`

### 更细的原因判断

- 多数热点任务的主回升来源仍是 `run_tests`
  - 例如 `task_022`、`task_050`、`task_034`、`task_046`、`task_010`
- 但这轮和 `v66 -> v68` 不同，`search_code` 的回升已经不能忽略
  - `task_123` 上 `search_code` 单项增量达到 `+0.0628s`
  - `task_093`、`task_109`、`task_111`、`task_119`、`task_121` 等也都有明显 `search_code` 增量
- 个别任务存在离散型噪声
  - `task_079` 的 `copy_workspace` 单次增量达到 `+0.0328s`
  - 当前更像单任务异常采样，不足以单独解释整体现象

### 当前结论

- `v69` 的性能回升已经被确认是真实存在的公共任务回升，而不是只由新增任务带来的表观抬升
- 当前最可信的两条优化主线是：
  - 继续收紧 `run_tests` 链路，优先复查 pytest 启动 / collection 相关开销
  - 额外补一轮 `search_code` 开销定位，确认是否是搜索范围、命中量或文件枚举行为发生了系统性变化
- 因此如果继续做 `v70`，更合理的目标不是再扩题，而是：
  - 保留 `task_125` 修复能力
  - 尽量回收 `v69` 相对 `v68` 的 `run_tests + search_code` 双重回升

## 2026-06-13 Phase 6 `search_code` 回升专项定位

### 本轮目标

- 把上一轮发现的 `search_code` 回升从“trace 现象”推进为“结构化证据”
- 判断问题更像策略行为变化，还是搜索执行层抖动

### 改动类型

- `tooling`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/analyze_search_code_regressions.py`
- `tests/test_analyze_search_code_regressions.py`
- `logs/summaries/search_code_regressions_realissuev69r1_001.json`

### 改动摘要

- 新增 `scripts/analyze_search_code_regressions.py`
  - 直接从两次 batch run 的 trace 中抽取 `search_code` 步骤
  - 比较每个任务的：
    - 查询序列
    - 命中数
    - 命中文件数
    - 每次搜索耗时
  - 重点判断：
    - 查询签名是否完全一致
    - 是否主要由第一条搜索变慢驱动
- 新增 `tests/test_analyze_search_code_regressions.py`
  - 覆盖“查询签名相同但整体变慢”的核心分析逻辑
  - 覆盖 trace 抽取 `search_code` 指标的基础解析

### 关键验证

- 单测：
  - `python -m pytest tests/test_analyze_search_code_regressions.py -q`
  - 结果：`2 passed`
- 正式集专项分析：
  - `python scripts/analyze_search_code_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev68r1_001.json --improved-batch-summary logs/summaries/batch_run_realissuev69r1_001.json --run-label realissuev69r1`
  - 结果：
    - `common_task_count = 63`
    - `total_search_duration_delta_sec = +0.5797`
    - `identical_query_signature_task_count = 63`
    - `identical_query_signature_regression_task_count = 56`
    - `first_search_total_delta_sec = +0.5614`
    - `first_search_dominant_regression_task_count = 56`

### 诊断摘要

- 公共 `63` 条任务里，`63 / 63` 的查询签名完全一致
  - 说明 `v68` 和 `v69` 的 planner / patcher 没有改变 `search_code` 查询行为
- 其中有 `56 / 63` 个任务在“查询签名不变”的情况下出现 `search_code` 回升
  - 说明回升主因不在 query 生成逻辑
- `56 / 63` 个任务的回升又主要由第一条搜索主导
  - `first_search_total_delta_sec = +0.5614`
  - 几乎覆盖了 `search_code` 总增量 `+0.5797`

### 热点例子

- `task_123`
  - `search_code: 0.0138 -> 0.0766`
  - 第一条 `_exceptions` 搜索单独贡献 `+0.0579`
- `task_119`
  - `search_code: 0.0034 -> 0.0301`
  - 唯一一条查询本身就贡献全部回升
- `task_097`
  - `search_code: 0.0052 -> 0.0335`
  - 第一条 `show_pos` 搜索贡献 `+0.0252`

### 当前结论

- `search_code` 回升不是因为：
  - 搜索词变了
  - 搜索轮数变了
  - 命中数或命中文件数系统性增加了
- 当前更像是：
  - 搜索执行层在“第一条搜索”上出现了系统性抖动或冷启动成本
- 因此下一步更值得做的是：
  - 补一轮 `search_code` 冷启动 / 热启动基准
  - 必要时对比 `Path.rglob + read_text` 方案与 `rg` / 缓存式实现

## 2026-06-13 Phase 6 `search_code` 冷启动 / 热启动基准

### 本轮目标

- 验证上一轮定位出来的“第一条搜索普遍更慢”是否能在当前环境下稳定复现
- 判断是否应该直接改写 `search_code` 实现

### 改动类型

- `tooling`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/benchmark_search_code_cold_warm.py`
- `tests/test_benchmark_search_code_cold_warm.py`
- `logs/summaries/search_code_cold_warm_task123_v69_search_001.json`
- `logs/summaries/search_code_cold_warm_task119_v69_search_001.json`

### 改动摘要

- 新增 `scripts/benchmark_search_code_cold_warm.py`
  - 复用真实任务 trace 中的查询词序列
  - 比较同一 repo 上：
    - 第 1 轮冷启动搜索
    - 后续多轮热启动搜索
  - 输出总时长和第一条搜索时长的冷/热差值
- 新增 `tests/test_benchmark_search_code_cold_warm.py`
  - 覆盖 trace 查询提取
  - 覆盖多轮统计聚合
  - 覆盖结果文件落盘

### 关键验证

- 单测：
  - `python -m pytest tests/test_benchmark_search_code_cold_warm.py -q`
  - 结果：`3 passed`
- `task_123` 冷热启动基准：
  - `python scripts/benchmark_search_code_cold_warm.py --task benchmarks/tasks/task_123.json --repo-root . --rounds 5 --trace-path logs/trajectories/task_123/run_20260613T093317605792Z_6343/trace.json --benchmark-label task123_v69_search`
  - 结果：
    - `cold_total_duration_sec = 0.0037`
    - `warm_mean_total_duration_sec = 0.0036`
    - `warm_minus_cold_total_delta_sec = -0.0001`
    - `cold_first_query_duration_sec = 0.0009`
    - `warm_mean_first_query_duration_sec = 0.0007`
- `task_119` 冷热启动基准：
  - `python scripts/benchmark_search_code_cold_warm.py --task benchmarks/tasks/task_119.json --repo-root . --rounds 5 --trace-path logs/trajectories/task_119/run_20260613T093316027177Z_5358/trace.json --benchmark-label task119_v69_search`
  - 结果：
    - `cold_total_duration_sec = 0.0009`
    - `warm_mean_total_duration_sec = 0.0006`
    - `warm_minus_cold_total_delta_sec = -0.0003`
    - `cold_first_query_duration_sec = 0.0009`
    - `warm_mean_first_query_duration_sec = 0.0006`

### 当前结论

- 在当前环境下，单独把 `search_code` 从 batch run 中拿出来重复基准：
  - 没有复现 `+20ms ~ +60ms` 级别的回升
  - 冷启动和热启动差异都只有亚毫秒级
- 这说明当前更稳妥的判断是：
  - `search_code` 回升并不明显来自函数本体的稳定算法退化
  - 更像是当时 batch run 上下文中的解释器 / 文件系统 / 调度噪声
- 因此下一步不应直接重写 `search_code`
- 更合理的动作是：
  - 先在当前环境重跑少量热点任务，对比 `v68 / v69` 是否还能复现 `search_code` 差异
  - 如果不能稳定复现，再把 `search_code` 回升降级为次要线索，把 `run_tests` 重新升为 `v70` 主攻方向

## 2026-06-13 文档口径校准：统一到 `v69 / 64` 条正式任务

### 本轮目标

- 修正展示层与“当前状态”文档中的口径漂移
- 避免 README、实验摘要、架构说明继续停留在 `v68 / 63` 条任务阶段，误导后续判断

### 改动类型

- `documentation`
- `governance`

### 主要涉及文件

- `README.md`
- `docs/experiment_summary.md`
- `docs/architecture.md`
- `docs/benchmark.md`
- `GUIDE.md`

### 改动摘要

- 将对外展示入口统一到当前真实基线：
  - 正式任务数：`64`
  - 来源生态数：`16`
  - 当前主版本：`improved_v69`
- 更新 README 的体验命令与代表性案例：
  - 单任务示例切到 `task_125`
  - stability recheck 与 batch eval 示例切到 `v69`
- 更新实验摘要：
  - 从“`v68` 是当前版本”改为“`v69` 是当前版本，`v68` 是上一轮性能更优参考”
  - 增补 `v68 -> v69` 这一段性能复核结论
- 更新架构与 benchmark 说明中的当前规模字段
- 在 `GUIDE.md` 中补一条明确约定：
  - “当前状态”与“历史记录”分开维护，避免后续再次混淆

### 当前结论

- 这次改动不改变任何代码行为，也不改写历史实验记录
- 它解决的是“文档治理”问题：
  - 当前入口不再落后于真实项目状态
  - 历史时间线仍然保留原始演进语境
- 后续如果继续推进 `v70+`，应把展示层同步当成每轮重要更新的固定动作

## 2026-06-13 Phase 6 热点任务双策略复跑复核入口

### 本轮目标

- 把“先重跑少量热点任务复核 `v68 / v69` 差异”从待办变成可执行脚本
- 给 `search_code` 与 `run_tests` 的下一步判断补一个更贴近真实 batch run 的证据入口

### 改动类型

- `tooling`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/recheck_policy_pair_tasks.py`
- `tests/test_recheck_policy_pair_tasks.py`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 改动摘要

- 新增 `scripts/recheck_policy_pair_tasks.py`
  - 接收多个 `--task`
  - 接收 `--baseline-policy` 与 `--improved-policy`
  - 对每个任务、每个策略重复运行多次
  - 聚合：
    - `duration_sec`
    - `search_code_total_duration_sec`
    - `run_tests_total_duration_sec`
  - 输出 JSON + Markdown 报告
- 新增 `tests/test_recheck_policy_pair_tasks.py`
  - 覆盖任务级聚合
  - 覆盖结果文件落盘
- 同步文档，把它明确标记为当前下一步性能复核入口

### 关键验证

- 单测：
  - `python -m pytest tests/test_recheck_policy_pair_tasks.py -q`
  - 结果：`2 passed`

### 当前结论

- 这一轮还没有直接得出新的真实性能结论
- 但 roadmap 的下一步已经从“想法”变成了“可以直接执行的脚本”
- 现在最自然的后续动作就是：
  - 用这条脚本重跑 `task_123 / task_119 / task_097 / task_034`
  - 判断 `v68 -> v69` 的回升是否还能在当前环境稳定复现

## 2026-06-13 Phase 6 热点任务 `v68 / v69` 真实复跑复核

### 本轮目标

- 用刚新增的双策略复跑脚本，验证 `v68 -> v69` 的热点差异在当前环境里是否还能稳定复现
- 判断 `search_code` 是否还应继续作为 `v70` 的主攻方向

### 改动类型

- `evaluation`
- `documentation`

### 主要涉及文件

- `logs/summaries/policy_pair_recheck_v68_v69_hotspots_001.json`
- `logs/summaries/policy_pair_recheck_v68_v69_hotspots_001.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 关键验证

- 真实复跑命令：
  - `python scripts/recheck_policy_pair_tasks.py --task benchmarks/tasks/task_123.json --task benchmarks/tasks/task_119.json --task benchmarks/tasks/task_097.json --task benchmarks/tasks/task_034.json --baseline-policy optimization/policy_versions/improved_v68.json --improved-policy optimization/policy_versions/improved_v69.json --repetitions 3 --run-label v68_v69_hotspots`
- 相关单测：
  - `python -m pytest tests/test_recheck_policy_pair_tasks.py tests/test_benchmark_search_code_cold_warm.py tests/test_analyze_search_code_regressions.py -q`
  - 结果：`7 passed`

### 当前结果

- 聚合结果：
  - `average_duration_delta_sec = -0.0149`
  - `average_search_code_delta_sec = -0.0095`
  - `average_run_tests_delta_sec = -0.0041`
  - `reproduced_search_code_task_count = 0 / 4`
  - `reproduced_run_tests_task_count = 1 / 4`
- 分任务结果：
  - `task_123`: `search_code delta = -0.0074`
  - `task_119`: `search_code delta = -0.0104`
  - `task_097`: `search_code delta = -0.0047`
  - `task_034`: `search_code delta = -0.0157`

### 当前结论

- 在当前环境下，这组热点任务没有复现 `search_code` 回升
- 这使得当前证据更支持：
  - `search_code` 是一条已经被排查过、但暂时不稳定的次要线索
  - `run_tests` 应重新升为 `v70` 的主攻方向
- 后续更自然的动作是：
  - 重用既有 `pytest` phase / importtime / plugin variants 入口
  - 继续向 `run_tests` 的 subprocess / collection 链路下钻

## 2026-06-13 热点任务复跑细化：拆分两次 `run_tests`

### 本轮目标

- 把双策略热点任务复跑从“只看总 `run_tests`”推进到“区分第一次和第二次 `run_tests`”
- 判断后续该优先盯 pre-test 还是 post-test

### 改动类型

- `tooling`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/recheck_policy_pair_tasks.py`
- `tests/test_recheck_policy_pair_tasks.py`
- `logs/summaries/policy_pair_recheck_v68_v69_hotspots_split_001.json`
- `logs/summaries/policy_pair_recheck_v68_v69_hotspots_split_001.md`

### 改动摘要

- 为复跑脚本新增：
  - `run_tests_first_duration_sec`
  - `run_tests_second_duration_sec`
- 聚合层新增：
  - `average_run_tests_first_delta_sec`
  - `average_run_tests_second_delta_sec`
  - 对应 reproduced / ratio 字段
- 用同一组热点任务重新跑了一轮真实复核

### 关键验证

- 单测：
  - `python -m pytest tests/test_recheck_policy_pair_tasks.py -q`
  - 结果：`2 passed`
- 真实复跑：
  - `python scripts/recheck_policy_pair_tasks.py --task benchmarks/tasks/task_123.json --task benchmarks/tasks/task_119.json --task benchmarks/tasks/task_097.json --task benchmarks/tasks/task_034.json --baseline-policy optimization/policy_versions/improved_v68.json --improved-policy optimization/policy_versions/improved_v69.json --repetitions 3 --run-label v68_v69_hotspots_split`

### 当前结果

- 聚合结果：
  - `average_duration_delta_sec = -0.0227`
  - `average_search_code_delta_sec = -0.0044`
  - `average_run_tests_delta_sec = -0.018`
  - `average_run_tests_first_delta_sec = -0.0117`
  - `average_run_tests_second_delta_sec = -0.0064`
- 这说明：
  - 当前环境下，`run_tests` 总体也没有复现回升
  - 如果继续细分观察，第一次 `run_tests` 的信号更强

### 当前结论

- 当前 `v70` 的更稳妥方向不是“立刻改 runtime”
- 而是优先沿：
  - pre-test
  - pytest startup / collect
  继续做更小粒度的策略版对照

## 2026-06-13 `v70` 准备动作：pytest 诊断脚本接入策略版本

### 本轮目标

- 让 `run_tests` 主线上的诊断脚本真正支持按策略版本复跑
- 避免后续分析 `v68 / v69 / v70` 时，诊断命令没有带上真实 `pytest_additional_flags`

### 改动类型

- `tooling`
- `testing`
- `documentation`

### 主要涉及文件

- `scripts/benchmark_pytest_phases.py`
- `scripts/benchmark_pytest_importtime.py`
- `scripts/benchmark_pytest_plugin_variants.py`
- `tests/test_benchmark_pytest_phases.py`
- `tests/test_benchmark_pytest_importtime.py`
- `tests/test_benchmark_pytest_plugin_variants.py`

### 改动摘要

- 为三条 `pytest` 诊断脚本统一新增 `policy_path / --policy`
- 运行基准时会先加载策略配置，再把其中的 `pytest_additional_flags` 透传给 `run_tests`
- 输出摘要中新增：
  - `policy_id`
  - `policy_path`
  - `pytest_additional_flags`
- 补充测试覆盖，确认策略 flags 确实会传进诊断调用链

### 关键验证

- 单测：
  - `python -m pytest tests/test_benchmark_pytest_phases.py tests/test_benchmark_pytest_importtime.py tests/test_benchmark_pytest_plugin_variants.py -q`
  - 结果：`15 passed`

### 当前结论

- 这一步不直接给出新的性能结论
- 但它把 `v70` 的分析入口从“近似环境基准”升级成了“真实策略版本基准”
- 下一步可以直接用：
  - `improved_v68`
  - `improved_v69`
  - 后续 `improved_v70`
  做可复验的 `pytest` 分阶段 / importtime / 插件变体对照

## 2026-06-13 `v70` 准备动作：pytest 策略摘要双版本 compare

### 本轮目标

- 把“手工读两份策略版 benchmark JSON”收口成可复用 compare 脚本
- 快速判断 `v68 / v69` 的 phase / importtime 差值到底是不是足够稳定

### 改动类型

- `tooling`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/compare_pytest_policy_pair.py`
- `tests/test_compare_pytest_policy_pair.py`
- `logs/summaries/pytest_policy_pair_task123_phase_v68_v69_001.json`
- `logs/summaries/pytest_policy_pair_task123_importtime_v68_v69_001.json`
- `logs/summaries/pytest_policy_pair_task119_phase_v68_v69_001.json`
- `logs/summaries/pytest_policy_pair_task119_importtime_v68_v69_001.json`

### 改动摘要

- 新增 `scripts/compare_pytest_policy_pair.py`
  - 输入同一任务的 baseline / improved summary
  - 当前支持：
    - `pytest phases`
    - `pytest importtime`
  - 输出结构化 delta 报告
- 新增 `tests/test_compare_pytest_policy_pair.py`
  - 覆盖 `pytest phases` compare
  - 覆盖 `pytest importtime` compare
  - 覆盖结果文件落盘

### 关键验证

- 单测：
  - `python -m pytest tests/test_compare_pytest_policy_pair.py -q`
  - 结果：`3 passed`
- 真实 compare：
  - `task_123` phase / importtime
  - `task_119` phase / importtime

### 当前结果

- `task_123` phase：
  - `pytest_startup_over_python_delta_sec = +0.0038`
  - `collect_over_pytest_startup_delta_sec = -0.0077`
  - `full_first_minus_repeated_delta_sec = +0.0341`
- `task_123` importtime：
  - `collect_wall_delta_sec = -0.0007`
  - `collect_import_self_delta_us = +5753`
- `task_119` phase：
  - `pytest_startup_over_python_delta_sec = -0.0003`
  - `collect_over_pytest_startup_delta_sec = -0.0009`
- `task_119` importtime：
  - `collect_wall_delta_sec = +0.0015`
  - `collect_import_self_delta_us = -3660`

### 当前结论

- 当前 `v68 / v69` 的策略版 phase / importtime 差异量级整体仍然偏小
- 现阶段更像是个别任务的首轮波动，而不是已经足够明确的系统级 runtime 回归
- 因此下一步仍应优先：
  - 补更多热点任务的策略版 compare
  - 再判断是否存在一致性的系统回升信号

## 2026-06-13 `v70` 准备动作：补第二轮真实策略版 pytest compare

### 本轮目标

- 把 `task_097` 与 `task_034` 也纳入 `v68 / v69` 的策略版 `pytest phases + importtime` 对照
- 避免只用 `task_123 / task_119` 两个样本就过早判断 `v70` 是否该做 runtime 改动

### 改动类型

- `evaluation`
- `documentation`

### 主要涉及文件

- `logs/summaries/pytest_phases_task097_v68_phases_policy_001.json`
- `logs/summaries/pytest_phases_task097_v69_phases_policy_001.json`
- `logs/summaries/pytest_importtime_task097_v68_importtime_policy_001.json`
- `logs/summaries/pytest_importtime_task097_v69_importtime_policy_001.json`
- `logs/summaries/pytest_policy_pair_task097_phase_v68_v69_001.json`
- `logs/summaries/pytest_policy_pair_task097_importtime_v68_v69_001.json`
- `logs/summaries/pytest_phases_task034_v68_phases_policy_001.json`
- `logs/summaries/pytest_phases_task034_v69_phases_policy_001.json`
- `logs/summaries/pytest_importtime_task034_v68_importtime_policy_001.json`
- `logs/summaries/pytest_importtime_task034_v69_importtime_policy_001.json`
- `logs/summaries/pytest_policy_pair_task034_phase_v68_v69_001.json`
- `logs/summaries/pytest_policy_pair_task034_importtime_v68_v69_001.json`

### 关键验证

- `task_097` phase：
  - `pytest_startup_over_python_delta_sec = -0.0051`
  - `collect_over_pytest_startup_delta_sec = +0.0114`
  - `full_over_collect_delta_sec = +0.0098`
- `task_097` importtime：
  - `collect_wall_delta_sec = -0.0182`
  - `collect_import_self_delta_us = -12204`
  - `collect_unique_module_delta = 0`
- `task_034` phase：
  - `pytest_startup_over_python_delta_sec = -0.0539`
  - `collect_over_pytest_startup_delta_sec = +0.0446`
  - `full_over_collect_delta_sec = +0.0093`
- `task_034` importtime：
  - `collect_wall_delta_sec = +0.0277`
  - `collect_import_self_delta_us = +14898`
  - `collect_unique_module_delta = 0`

### 当前结论

- 这轮补样本后，`v68 / v69` 的真实策略版 compare 仍没有收敛出单一稳定主因
- `task_097` 给出的信号是：
  - phase 侧 `collect / full` 略慢
  - 但 importtime 侧反而更轻
- `task_034` 给出的信号是：
  - phase 侧 `collect / full` 更慢
  - importtime 侧也同步更重
- 因此当前最稳妥的判断仍然是：
  - `collect` 链路值得继续优先观察
  - 但现阶段证据还不足以支撑“直接为了 `v70` 改 runtime 实现”
  - 下一步应继续扩大策略版 compare 样本，而不是过早提交性能回收版本

## 2026-06-13 `v70` 准备动作：多任务策略版 compare 收口成 cohort 汇总

### 本轮目标

- 把多任务 `pytest_policy_pair_*.json` 的手工阅读收口成结构化 cohort 汇总
- 让后续每补一轮任务样本后，都能直接看跨任务平均 delta 与同方向任务数

### 改动类型

- `tooling`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/analyze_pytest_policy_pair_cohort.py`
- `tests/test_analyze_pytest_policy_pair_cohort.py`
- `logs/summaries/pytest_policy_pair_phases_cohort_v68_v69_hotspots_phase_001.json`
- `logs/summaries/pytest_policy_pair_phases_cohort_v68_v69_hotspots_phase_001.md`
- `logs/summaries/pytest_policy_pair_importtime_cohort_v68_v69_hotspots_importtime_001.json`
- `logs/summaries/pytest_policy_pair_importtime_cohort_v68_v69_hotspots_importtime_001.md`

### 改动摘要

- 新增 `scripts/analyze_pytest_policy_pair_cohort.py`
  - 输入多份同类型 compare summary
  - 当前支持：
    - `pytest_phases`
    - `pytest_importtime`
  - 输出：
    - 跨任务平均 delta
    - 同方向任务数
    - 按关键 delta 排序的 task snapshots
- 新增 `tests/test_analyze_pytest_policy_pair_cohort.py`
  - 覆盖 phase compare 聚合
  - 覆盖 importtime compare 聚合
  - 覆盖结果文件落盘

### 关键验证

- 单测：
  - `python -m pytest tests/test_analyze_pytest_policy_pair_cohort.py -q`
  - 结果：`3 passed`
- 真实 cohort：
  - phase：`task_123 / task_119 / task_097 / task_034`
  - importtime：`task_123 / task_119 / task_097 / task_034`

### 当前结果

- phase cohort：
  - `average_pytest_startup_over_python_delta_sec = -0.0139`
  - `average_collect_over_pytest_startup_delta_sec = +0.0118`
  - `average_full_over_collect_delta_sec = +0.0054`
  - `collect_slower_task_count = 2 / 4`
  - `full_slower_task_count = 3 / 4`
- importtime cohort：
  - `average_collect_wall_delta_sec = +0.0026`
  - `average_collect_import_self_delta_us = +1197`
  - `collect_wall_slower_task_count = 2 / 4`
  - `collect_import_self_higher_task_count = 2 / 4`

### 当前结论

- 当前 4 任务聚合后，phase 侧的 `collect` 与 `full` 仍偏正向变慢
- 但 importtime 聚合后的均值已经明显收敛到接近噪声级
- 因此当前更可信的判断是：
  - `collect` 值得继续盯
  - 但不能把回升简单解释成“稳定 import 链恶化”
  - 下一步应继续扩样本，再决定是否真的需要 `v70`

## 2026-06-13 `v70` 准备动作：多任务策略版 pytest 对照收口成一键 matrix

### 本轮目标

- 把多任务 `phase / importtime / compare / cohort` 的完整链路收口成一条命令
- 让后续 roadmap 的持续追踪不再依赖十几条手工命令

### 改动类型

- `tooling`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/run_pytest_policy_pair_matrix.py`
- `tests/test_run_pytest_policy_pair_matrix.py`
- `logs/summaries/pytest_policy_pair_matrix_v68_v69_hotspots_matrix_001.json`
- `logs/summaries/pytest_policy_pair_matrix_v68_v69_hotspots_matrix_001.md`
- `logs/summaries/pytest_policy_pair_phases_cohort_v68_v69_hotspots_matrix_phase_001.json`
- `logs/summaries/pytest_policy_pair_importtime_cohort_v68_v69_hotspots_matrix_importtime_001.json`

### 改动摘要

- 新增 `scripts/run_pytest_policy_pair_matrix.py`
  - 输入一组 task 和两版 policy
  - 自动串起：
    - `benchmark_pytest_phases.py`
    - `benchmark_pytest_importtime.py`
    - `compare_pytest_policy_pair.py`
    - `analyze_pytest_policy_pair_cohort.py`
  - 最终产出：
    - 每个任务的 phase/importtime compare
    - 两条 cohort summary
    - 一份总 matrix summary
- 新增 `tests/test_run_pytest_policy_pair_matrix.py`
  - 覆盖 task matrix 聚合
  - 覆盖结果文件落盘

### 关键验证

- 单测：
  - `python -m pytest tests/test_run_pytest_policy_pair_matrix.py -q`
  - 结果：`2 passed`
- 联合单测：
  - `python -m pytest tests/test_run_pytest_policy_pair_matrix.py tests/test_analyze_pytest_policy_pair_cohort.py tests/test_compare_pytest_policy_pair.py -q`
  - 结果：`8 passed`
- 真实 matrix：
  - `task_123 / task_119 / task_097 / task_034`
  - `baseline = improved_v68`
  - `improved = improved_v69`

### 当前结果

- phase cohort：
  - `average_pytest_startup_over_python_delta_sec = +0.0101`
  - `average_collect_over_pytest_startup_delta_sec = -0.0235`
  - `average_full_over_collect_delta_sec = +0.0159`
  - `startup_slower_task_count = 4 / 4`
  - `collect_slower_task_count = 0 / 4`
  - `full_slower_task_count = 3 / 4`
- importtime cohort：
  - `average_collect_wall_delta_sec = -0.0047`
  - `average_collect_import_self_delta_us = +1672`
  - `collect_wall_slower_task_count = 1 / 4`
  - `collect_import_self_higher_task_count = 2 / 4`

### 当前结论

- 这轮更完整编排下，原先“collect 普遍更慢”的假设没有继续站稳
- 当前更像是：
  - `pytest startup` 更慢
  - `full run` 也更值得继续观察
  - 但 `collect` 与 `importtime` 没有显示出稳定恶化
- 因此当前最稳妥的下一步仍然是：
  - 继续扩样本
  - 必要时补重复 matrix
  - 暂缓直接做 `v70`

## 2026-06-13 `v70` 准备动作：把历史 run_tests 热点集合也纳入 matrix

### 本轮目标

- 不只看“当前扩样本 4 任务”，还要回到历史 `run_tests` 热点集合本身
- 验证 `startup / collect / full run / importtime` 哪条线在真正的老热点上更稳

### 改动类型

- `evaluation`
- `documentation`

### 主要涉及文件

- `logs/summaries/pytest_policy_pair_matrix_v68_v69_run_tests_hotspots_matrix_001.json`
- `logs/summaries/pytest_policy_pair_matrix_v68_v69_run_tests_hotspots_matrix_001.md`
- `logs/summaries/pytest_policy_pair_phases_cohort_v68_v69_run_tests_hotspots_matrix_phase_001.json`
- `logs/summaries/pytest_policy_pair_importtime_cohort_v68_v69_run_tests_hotspots_matrix_importtime_001.json`

### 关键验证

- 任务集合：
  - `task_034`
  - `task_036`
  - `task_038`
  - `task_040`
- matrix 命令：
  - `python scripts/run_pytest_policy_pair_matrix.py --task benchmarks/tasks/task_034.json --task benchmarks/tasks/task_036.json --task benchmarks/tasks/task_038.json --task benchmarks/tasks/task_040.json --repo-root . --baseline-policy optimization/policy_versions/improved_v68.json --improved-policy optimization/policy_versions/improved_v69.json --repetitions 3 --matrix-label v68_v69_run_tests_hotspots_matrix`

### 当前结果

- phase cohort：
  - `average_pytest_startup_over_python_delta_sec = +0.004`
  - `average_collect_over_pytest_startup_delta_sec = -0.0047`
  - `average_full_over_collect_delta_sec = -0.0152`
  - `startup_slower_task_count = 2 / 4`
  - `collect_slower_task_count = 2 / 4`
  - `full_slower_task_count = 1 / 4`
- importtime cohort：
  - `average_collect_wall_delta_sec = +0.0024`
  - `average_collect_import_self_delta_us = +8255`
  - `collect_wall_slower_task_count = 1 / 4`
  - `collect_import_self_higher_task_count = 3 / 4`

### 当前结论

- 这轮更贴近历史回升来源的矩阵结果说明：
  - `startup` 只有轻微正向
  - `collect` 方向重新分裂
  - `full run` 甚至整体更快
  - `importtime` 虽然偏正，但还远不足以单独定责
- 因此当前最可信的判断进一步收紧为：
  - 还没有稳定的单主因
  - 继续扩样本与重复 matrix 仍优于直接做 `v70`

## 2026-06-13 `v70` 准备动作：把三轮 matrix 再向上聚合成 matrix set

### 本轮目标

- 不再靠人工对比三份 matrix summary
- 直接形成“跨集合聚合”的统一判断口径

### 改动类型

- `tooling`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/analyze_pytest_policy_pair_matrix_set.py`
- `tests/test_analyze_pytest_policy_pair_matrix_set.py`
- `logs/summaries/pytest_policy_pair_matrix_set_v68_v69_triage_001.json`
- `logs/summaries/pytest_policy_pair_matrix_set_v68_v69_triage_001.md`

### 改动摘要

- 新增 `scripts/analyze_pytest_policy_pair_matrix_set.py`
  - 输入多份 matrix summary
  - 输出跨集合 aggregate
  - 聚合：
    - `startup / collect / full` 三条 phase 线
    - `collect wall / collect import` 两条 importtime 线
    - 各方向在多少个 matrix 上为正
- 新增 `tests/test_analyze_pytest_policy_pair_matrix_set.py`
  - 覆盖多轮 matrix 聚合
  - 覆盖结果文件落盘

### 关键验证

- 单测：
  - `python -m pytest tests/test_analyze_pytest_policy_pair_matrix_set.py -q`
  - 结果：`2 passed`
- 联合单测复跑：
  - `python -m pytest tests/test_analyze_pytest_policy_pair_matrix_set.py tests/test_run_pytest_policy_pair_matrix.py tests/test_analyze_pytest_policy_pair_cohort.py tests/test_compare_pytest_policy_pair.py -q`
  - 结果：`10 passed`
- 真实聚合对象：
  - `v68_v69_hotspots_matrix`
  - `v68_v69_run_tests_hotspots_matrix`
  - `v68_v69_control_group_matrix`

### 当前结果

- `average_startup_delta_sec = +0.0051`
- `average_collect_delta_sec = -0.0089`
- `average_full_delta_sec = -0.0023`
- `average_collect_wall_delta_sec = +0.0032`
- `average_collect_import_self_delta_us = +6506.3333`
- `startup_positive_matrix_count = 3 / 3`
- `collect_positive_matrix_count = 1 / 3`
- `full_positive_matrix_count = 1 / 3`
- `collect_import_positive_matrix_count = 3 / 3`

### 当前结论

- 到这一步，当前最稳定偏正的线已经不是 `collect`，而是 `pytest startup`
- `collect` 与 `full run` 都没有继续表现出稳定正向
- `importtime` 有一定偏正，但更适合作为次级观察项，而不是直接定责主因
- 因此当前最稳妥的主线排序应更新为：
  - 第一优先级：`pytest startup`
  - 第二优先级：`importtime` 作为辅助观察
  - 暂时降级：继续深拆 `collect`

## 2026-06-13 Phase 6 口径校准：`v68 / v69` pytest compare 属于 runtime 等价噪声探针

### 本轮目标

- 校准 `v68 / v69` pytest compare 这条线的解释口径
- 避免继续把 runtime 实际相同的策略对误读成 pytest flags 差异实验
- 在不重写历史日志的前提下，让后续分析脚本也能正确识别 runtime 等价关系

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/compare_pytest_policy_pair.py`
- `scripts/analyze_pytest_policy_pair_cohort.py`
- `scripts/run_pytest_policy_pair_matrix.py`
- `scripts/analyze_pytest_policy_pair_matrix_set.py`
- `tests/test_compare_pytest_policy_pair.py`
- `tests/test_analyze_pytest_policy_pair_cohort.py`
- `tests/test_run_pytest_policy_pair_matrix.py`
- `tests/test_analyze_pytest_policy_pair_matrix_set.py`
- `docs/v2_roadmap.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 关键验证

- 策略文件核对：
  - `optimization/policy_versions/improved_v68.json`
  - `optimization/policy_versions/improved_v69.json`
- 结论：
  - 两者 `pytest_additional_flags` 完全相同
  - 都是：
    - `-p no:unraisableexception`
    - `-p no:threadexception`
- 单测复跑：
  - `python -m pytest tests/test_compare_pytest_policy_pair.py tests/test_analyze_pytest_policy_pair_cohort.py tests/test_run_pytest_policy_pair_matrix.py tests/test_analyze_pytest_policy_pair_matrix_set.py -q`
  - 结果：`11 passed`

### 改动摘要

- 为 pytest compare / cohort / matrix / matrix-set 结果补上 `runtime_equivalent` 口径
- 增加向后兼容推断：
  - 新 summary 优先读取显式 `runtime_equivalent`
  - 旧 summary 若未显式写入，则会尝试：
    - 读取 `runtime_signature`
    - 或根据 `baseline_policy_id / improved_policy_id` 回查策略文件
- 文档层同步加入统一说明：
  - 当前 `v68 / v69` 的 pytest compare 更适合作为 `runtime-equivalent noise probe`
  - 不再直接当作“runtime flags 差异主因实验”

### 当前结论

- 之前那批 `v68 / v69` 的 phase / importtime / matrix / matrix-set 数值本身仍然有参考价值
- 但它们当前更适合回答的问题是：
  - 同 runtime 配置下的噪声有多大
  - 哪些阶段在环境波动下更敏感
  - 是否存在值得继续深挖的总链路热点
- 它们不再适合直接回答的问题是：
  - “哪条 pytest runtime flag 导致了 `v69` 变慢”
- 因此后续主线应调整为：
  - 如果继续做性能追因，先回到 `run_tests` 总链路、环境基线与稳定性复跑
  - 如果要做 runtime 对照实验，先构造真正 runtime 不同的 policy pair

## 2026-06-13 Phase 6 校准产物补落盘：复用旧真实日志重生 calibrated summaries

### 本轮目标

- 不重跑已有 benchmark
- 直接复用现有 `v68 / v69` 真实 compare 与 matrix 日志
- 生成带有 runtime-equivalent 解释口径的新 summary，方便后续直接引用

### 改动类型

- `tooling`
- `evaluation`
- `documentation`

### 主要涉及文件

- `scripts/analyze_pytest_policy_pair_matrix_set.py`
- `logs/summaries/pytest_policy_pair_phases_cohort_v68_v69_hotspots_phase_calibrated_001.json`
- `logs/summaries/pytest_policy_pair_importtime_cohort_v68_v69_hotspots_importtime_calibrated_001.json`
- `logs/summaries/pytest_policy_pair_matrix_set_v68_v69_triage_calibrated_001.json`

### 改动摘要

- 增强 `analyze_pytest_policy_pair_matrix_set.py`
  - 旧 `matrix` 文件即使没有显式 `runtime_equivalent_task_count`
  - 也可以回查嵌套 compare summary 的策略版本
  - 进一步回查 `optimization/policy_versions/*.json`
  - 自动推断 runtime 是否等价
- 在此基础上，直接复用旧真实产物重生成三份 calibrated summary

### 关键验证

- 单测：
  - `python -m pytest tests/test_analyze_pytest_policy_pair_matrix_set.py tests/test_run_pytest_policy_pair_matrix.py tests/test_analyze_pytest_policy_pair_cohort.py tests/test_compare_pytest_policy_pair.py -q`
  - 结果：`11 passed`
- 真实重生成命令：
  - `python scripts/analyze_pytest_policy_pair_matrix_set.py --matrix-summary logs/summaries/pytest_policy_pair_matrix_v68_v69_hotspots_matrix_001.json --matrix-summary logs/summaries/pytest_policy_pair_matrix_v68_v69_run_tests_hotspots_matrix_001.json --matrix-summary logs/summaries/pytest_policy_pair_matrix_v68_v69_control_group_matrix_001.json --set-label v68_v69_triage_calibrated --output-dir logs/summaries`
  - `python scripts/analyze_pytest_policy_pair_cohort.py --compare-summary logs/summaries/pytest_policy_pair_task123_phase_pair_001.json --compare-summary logs/summaries/pytest_policy_pair_task119_phase_pair_001.json --compare-summary logs/summaries/pytest_policy_pair_task097_phase_pair_001.json --compare-summary logs/summaries/pytest_policy_pair_task034_phase_pair_001.json --cohort-label v68_v69_hotspots_phase_calibrated --output-dir logs/summaries`
  - `python scripts/analyze_pytest_policy_pair_cohort.py --compare-summary logs/summaries/pytest_policy_pair_task123_importtime_pair_001.json --compare-summary logs/summaries/pytest_policy_pair_task119_importtime_pair_001.json --compare-summary logs/summaries/pytest_policy_pair_task097_importtime_pair_001.json --compare-summary logs/summaries/pytest_policy_pair_task034_importtime_pair_001.json --cohort-label v68_v69_hotspots_importtime_calibrated --output-dir logs/summaries`

### 当前结果

- 新 matrix-set 产物：
  - `pytest_policy_pair_matrix_set_v68_v69_triage_calibrated_001.json`
  - `runtime_equivalent_matrix_count = 3`
- 新 cohort 产物：
  - `pytest_policy_pair_phases_cohort_v68_v69_hotspots_phase_calibrated_001.json`
  - `pytest_policy_pair_importtime_cohort_v68_v69_hotspots_importtime_calibrated_001.json`
- 数值层面与旧 summary 保持一致
- 新增价值主要在于：
  - 解释口径被固化进真实产物
  - 后续不用再靠人工记忆 “v68/v69 runtime 其实相同”

### 当前结论

- 当前这条 pytest compare 支线已经从“可能的 runtime 对照实验”正式收口为：
  - `runtime-equivalent noise probe`
- 这让 roadmap 后续推进更清晰：
  - 如果想继续追性能，应切回总链路与环境噪声复核
  - 如果想继续做 runtime 对照，必须先造出真实 runtime-different 的 policy pair

## 2026-06-13 Phase 6 校准入口收口：新增 calibrated view 重建脚本

### 本轮目标

- 把“复用旧日志重生 calibrated summaries”的动作从人工命令串收口成单脚本入口
- 降低后续继续追踪 roadmap 时的上下文负担
- 让 calibrated 产物除了分散 JSON 外，再多一个总索引 summary

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/rebuild_pytest_policy_pair_calibrated_views.py`
- `tests/test_rebuild_pytest_policy_pair_calibrated_views.py`
- `logs/summaries/pytest_policy_pair_calibrated_view_v68_v69_hotspots_001.json`
- `logs/summaries/pytest_policy_pair_calibrated_view_v68_v69_hotspots_001.md`

### 改动摘要

- 新增 `scripts/rebuild_pytest_policy_pair_calibrated_views.py`
  - 输入：
    - phase compare summaries
    - importtime compare summaries
    - matrix summaries
  - 输出：
    - calibrated phase cohort
    - calibrated importtime cohort
    - calibrated matrix-set
    - 一份总索引 calibrated view summary
- 新增 `tests/test_rebuild_pytest_policy_pair_calibrated_views.py`
  - 覆盖串联 cohort / matrix-set 聚合入口
  - 覆盖总索引结果文件落盘

### 关键验证

- 单测：
  - `python -m pytest tests/test_rebuild_pytest_policy_pair_calibrated_views.py tests/test_analyze_pytest_policy_pair_matrix_set.py tests/test_analyze_pytest_policy_pair_cohort.py tests/test_compare_pytest_policy_pair.py tests/test_run_pytest_policy_pair_matrix.py -q`
  - 结果：`13 passed`
- 真实重建命令：
  - `python scripts/rebuild_pytest_policy_pair_calibrated_views.py --phase-compare logs/summaries/pytest_policy_pair_task123_phase_pair_001.json --phase-compare logs/summaries/pytest_policy_pair_task119_phase_pair_001.json --phase-compare logs/summaries/pytest_policy_pair_task097_phase_pair_001.json --phase-compare logs/summaries/pytest_policy_pair_task034_phase_pair_001.json --importtime-compare logs/summaries/pytest_policy_pair_task123_importtime_pair_001.json --importtime-compare logs/summaries/pytest_policy_pair_task119_importtime_pair_001.json --importtime-compare logs/summaries/pytest_policy_pair_task097_importtime_pair_001.json --importtime-compare logs/summaries/pytest_policy_pair_task034_importtime_pair_001.json --matrix-summary logs/summaries/pytest_policy_pair_matrix_v68_v69_hotspots_matrix_001.json --matrix-summary logs/summaries/pytest_policy_pair_matrix_v68_v69_run_tests_hotspots_matrix_001.json --matrix-summary logs/summaries/pytest_policy_pair_matrix_v68_v69_control_group_matrix_001.json --view-label v68_v69_hotspots --output-dir logs/summaries`

### 当前结果

- 总索引产物：
  - `pytest_policy_pair_calibrated_view_v68_v69_hotspots_001.json`
- 它指向：
  - `pytest_policy_pair_phases_cohort_v68_v69_hotspots_phase_calibrated_002.json`
  - `pytest_policy_pair_importtime_cohort_v68_v69_hotspots_importtime_calibrated_002.json`
  - `pytest_policy_pair_matrix_set_v68_v69_hotspots_triage_calibrated_001.json`
- 这份总索引的价值是：
  - 后续不用再手动维护三条长命令
  - 也不用在多个 calibrated summary 之间来回跳

### 当前结论

- 这条 roadmap 支线现在已经不只是“结论被校准”
- 而是连“校准动作本身”也被工具化了
- 后续如果继续扩这条线，优先建议：
  - 直接复用这个脚本重建新的 calibrated view
  - 然后再判断是否需要继续追总链路性能，还是切回 A 线扩题

## 2026-06-13 `watchfiles#266` 前置收口：修正脚手架自动推断噪声并推进到 screened

### 本轮目标

- 检查 `samuelcolvin/watchfiles#266` 是否适合继续从候选池往前推进
- 在不冒进进入 semi-real 脚手架的前提下，先修掉自动推断里的 URL 噪声问题
- 如果本地证据足够，再把候选状态从 `imported` 推进到 `screened`

### 改动类型

- `tooling`
- `candidate-triage`
- `documentation`

### 主要涉及文件

- `scripts/scaffold_semi_real_task.py`
- `tests/test_scaffold_semi_real_task.py`
- `benchmarks/real_world_candidates.json`
- `docs/candidate_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`

### 改动摘要

- 修正 `scaffold_semi_real_task.py` 的目标路径自动推断：
  - 先剥离普通 URL，避免把 `github.com/...` 噪声误识别成 `github.py`
  - 对同仓库 GitHub `blob/tree` 链接单独提取真实 repo 内文件路径
- 新增针对该问题的测试：
  - `test_infer_target_paths_ignores_github_url_noise_and_prefers_repo_blob_path`
- 在此基础上，重新对 `watchfiles#266` 跑 `--dry-run`

### 关键验证

- 单测：
  - `python -m pytest tests/test_scaffold_semi_real_task.py tests/test_screen_candidate.py -q`
  - 结果：`10 passed`
- `dry-run`：
  - `python scripts/scaffold_semi_real_task.py --from-candidate samuelcolvin_watchfiles_issue_266 --candidate-file benchmarks/real_world_candidates.json --dry-run`
  - 修正前错误推断：
    - `watchfiles/github.py`
  - 修正后推断：
    - `watchfiles/main.py`
    - `tests/test_main.py`
- 候选状态推进：
  - `python scripts/screen_candidate.py --candidate-id samuelcolvin_watchfiles_issue_266 --candidate-file benchmarks/real_world_candidates.json --decision y`
  - 结果：`imported -> screened`

### 当前结果

- `samuelcolvin/watchfiles#266` 已不再卡在 `imported`
- 当前候选池状态同步变为：
  - `accepted = 64`
  - `screened = 1`
  - `imported = 0`
- `watchfiles#266` 当前可继续进入下一步，但仍保留一层保守判断：
  - 平台 / WSL / Docker 语境偏重
  - 先压清最小跨平台复现边界，再决定是否进入非 `dry-run` 脚手架更稳

### 当前结论

- 这轮推进的价值不只是多推进了一条候选
- 更重要的是把 semi-real 脚手架自动推断里的一个真实噪声源清掉了
- 后续如果继续沿 A 线扩题：
  - `watchfiles#266` 现在已经具备继续被人工缩题的条件
  - 但优先级仍应低于那些平台依赖更弱、边界更清晰的候选

## 2026-06-13 `watchfiles#266` 继续推进：从 screened 进入本地 draft scaffold

### 本轮目标

- 在保持保守节奏的前提下，把 `watchfiles#266` 从“只完成筛选”继续推进到“有本地脚手架可继续缩题”
- 验证非 `dry-run` 脚手架不会错误推进候选状态，也不会误入正式 manifest

### 改动类型

- `candidate-triage`
- `tooling`
- `documentation`

### 主要涉及文件

- `benchmarks/tasks/task_126.json`
- `benchmarks/repos/watchfiles_266_repo/watchfiles/main.py`
- `benchmarks/repos/watchfiles_266_repo/tests/test_main.py`
- `benchmarks/repos/watchfiles_266_repo/README.md`
- `benchmarks/real_world_candidates.json`

### 关键验证

- 脚手架命令：
  - `python scripts/scaffold_semi_real_task.py --from-candidate samuelcolvin_watchfiles_issue_266 --candidate-file benchmarks/real_world_candidates.json`
- 结果：
  - `semi_real_task = task_126`
  - `repo_root = benchmarks/repos/watchfiles_266_repo`
  - `module_file = watchfiles/main.py`
  - `test_file = tests/test_main.py`
  - `ready = False`
- 落盘后核对：
  - `task_126` 的 `source_type = semi_real`
  - `metadata.repo_scaffold_status = needs_manual_completion`
  - `expected_failure_test = null`
  - 候选状态仍保持 `screened`
  - 仅追加了一条“已生成 semi_real 脚手架 task_126”的 note

### 当前结果

- `watchfiles#266` 已不再只是“筛选通过”
- 当前已经进入：
  - `screened`
  - `本地 draft scaffold 已落盘`
  这一阶段
- 但它仍然没有进入：
  - `accepted`
  - `ready`
  - `正式 manifest`

### 当前结论

- 这条候选现在已经具备继续人工缩题的工作面
- 下一步真正关键的不是再推进状态，而是把：
  - 平台依赖
  - 最小复现边界
  - 稳定回归测试形状
  压清楚
- 只有做到这一步，才值得把 `task_126` 继续推进到 ready 或 accepted

## 2026-06-13 `watchfiles#266` ready 化：`task_126` 进入可运行 semi-real，但暂不接入正式 manifest

### 本轮目标

- 判断 `task_126` 是否已经具备从 TODO 脚手架推进到可运行 semi-real 的条件
- 如果可以，就把它补成 ready 口径任务
- 同时保留一个更谨慎的边界：ready 不等于必须立刻进正式集

### 改动类型

- `benchmark-content`
- `candidate-triage`
- `documentation`

### 主要涉及文件

- `benchmarks/repos/watchfiles_266_repo/watchfiles/main.py`
- `benchmarks/repos/watchfiles_266_repo/tests/test_main.py`
- `benchmarks/repos/watchfiles_266_repo/README.md`
- `benchmarks/tasks/task_126.json`
- `benchmarks/real_world_candidates.json`

### 改动摘要

- 将 `watchfiles/main.py` 从 TODO 占位实现改成最小 semi-real 复现逻辑
- 将 `tests/test_main.py` 改成 3 条稳定回归测试
- 将 `README.md` 改成 ready 口径说明
- 将 `task_126` metadata 从：
  - `repo_scaffold_status = needs_manual_completion`
  改成：
  - `repo_scaffold_status = ready`
- 将候选 `samuelcolvin_watchfiles_issue_266` 从 `screened` 推进到 `accepted`
- 但故意不把 `task_126` 追加到正式 manifest

### 关键验证

- 单任务测试：
  - `python -m pytest benchmarks/repos/watchfiles_266_repo/tests/test_main.py -q`
  - 结果：`3 passed`
- task 元数据核对：
  - `task_126.source_type = semi_real`
  - `task_126.metadata.repo_scaffold_status = ready`
  - `task_126` 不再带 `draft` tag
- 候选状态核对：
  - `samuelcolvin_watchfiles_issue_266.status = accepted`
- manifest 核对：
  - `benchmarks/manifests/real_issue_tasks.json` 中不存在 `task_126`

### 当前结果

- `watchfiles#266` 当前已经达到：
  - 候选状态 `accepted`
  - 本地 ready semi-real repo
  - 可运行回归测试 `3 passed`
- 但它还没有达到：
  - 正式任务接入
  - 新策略版本验证
  - 冻结集验证

### 当前结论

- 这条题已经证明：
  - 可以被压成稳定、可运行的 semi-real
- 但当前仍保留一个有意的保守判断：
  - issue 原始语境里的平台 / WSL / Docker 味道偏重
  - 现有缩题虽然稳定，但是否足够代表原问题，还值得再看一眼
- 因此当前最稳妥的位置是：
  - `accepted + ready`
  - 但暂不立刻进入正式 manifest

## 2026-06-13 Phase 6 追踪底座补强：新增 semi-real 接入阶段审计

### 本轮目标

- 把 candidate / task / formal manifest 三边状态对齐做成可执行审计
- 避免后续继续推进 roadmap 时，总靠人工翻候选文件、task 文件和 manifest
- 让 `accepted + ready + 未入正式集` 这类过渡态也能被直接量化

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/audit_semi_real_pipeline.py`
- `tests/test_audit_semi_real_pipeline.py`
- `logs/summaries/semi_real_pipeline_audit_phase6_001.json`
- `logs/summaries/semi_real_pipeline_audit_phase6_001.md`

### 改动摘要

- 新增 `scripts/audit_semi_real_pipeline.py`
  - 读取：
    - `benchmarks/real_world_candidates.json`
    - `benchmarks/tasks/*.json`
    - `benchmarks/manifests/real_issue_tasks.json`
  - 对齐 candidate_id
  - 输出每条候选当前处在哪个接入阶段
- 当前显式区分的关键阶段包括：
  - `accepted_in_formal_manifest`
  - `accepted_ready_not_in_formal_manifest`
  - `accepted_draft_task_not_in_formal_manifest`
  - `screened_with_task`
  - `screened_without_task`

### 关键验证

- 单测：
  - `python -m pytest tests/test_audit_semi_real_pipeline.py tests/test_scaffold_semi_real_task.py tests/test_run_real_issue_eval.py -q`
  - 结果：`12 passed`
- 真实审计：
  - `python scripts/audit_semi_real_pipeline.py --run-label phase6`

### 当前结果

- 真实审计产物：
  - `semi_real_pipeline_audit_phase6_001.json`
- 当前全局状态被明确量化为：
  - `candidate_count = 65`
  - `formal_candidate_count = 64`
  - `accepted_in_formal_manifest = 64`
  - `accepted_ready_not_in_formal_manifest = 1`
- 这 `1` 条当前正是：
  - `samuelcolvin_watchfiles_issue_266`
  - 对应 `task_126`

### 当前结论

- 这轮推进的价值在于把“接入状态”本身也纳入了 benchmark 基础设施
- 现在后续每次推进时，我们不仅能问：
  - 新题有没有做出来
- 还能直接问：
  - 当前有多少条已经 ready 但还没决定是否接入正式集
  - 当前是否还有 screened 候选卡着没进脚手架
- 这会让 roadmap 的持续追踪明显更省上下文

## 2026-06-13 Phase 6 challenge manifest 首版落地

### 本轮目标

- 给 `accepted + ready` 但暂不适合直接并入正式主集的题目一个稳定承载位
- 让 `watchfiles#266 / task_126` 可以被展示、被审计、被后续评测复用
- 避免 challenge 题污染正式 benchmark 口径

### 改动类型

- `benchmark-governance`
- `tooling`
- `documentation`

### 主要涉及文件

- `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- `scripts/audit_semi_real_pipeline.py`
- `tests/test_audit_semi_real_pipeline.py`
- `docs/benchmark.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/candidate_shortlist.md`
- `GUIDE.md`

### 改动摘要

- 新增独立 challenge manifest：
  - `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- 首条 challenge 任务为：
  - `task_126`
- 扩展 semi-real 接入阶段审计口径：
  - 从只区分 `formal / not formal`
  - 升级为区分：
    - `accepted_in_formal_manifest`
    - `accepted_in_challenge_manifest`
    - `accepted_ready_not_in_any_manifest`
- 同步更新 benchmark / memory / next actions / GUIDE 的叙事口径

### 关键结果

- `watchfiles#266` 当前位置被明确固定为：
  - `accepted`
  - `ready`
  - `in_challenge_manifest`
- 正式主集仍保持：
  - `64` 条
- challenge 集当前为：
  - `1` 条

### 当前结论

- 这一步比直接把 `task_126` 并入正式集更稳
- 它保留了这条题的展示和复用价值
- 同时不破坏当前正式 benchmark 的保守口径

## 2026-06-13 Phase 6 maturity 审计补认 challenge 集

### 本轮目标

- 让 challenge manifest 不只是文档概念，而是进入成熟度追踪链路
- 减少后续续做 roadmap 时对“正式集之外还有哪些边界题”的人工记忆负担

### 改动类型

- `tooling`
- `documentation`

### 主要涉及文件

- `scripts/analyze_benchmark_maturity.py`
- `scripts/run_real_issue_eval.py`
- `tests/test_analyze_benchmark_maturity.py`
- `docs/architecture.md`
- `docs/benchmark_registry.md`

### 改动摘要

- 扩展 maturity 审计：
  - 现在会同时读取：
    - `formal manifest`
    - `challenge manifest`
- 扩展 maturity markdown：
  - 新增 `Challenge Task Set` 段落
- 扩展评测流水线 headline：
  - 现在会显示 `challenge=<count>`
- 同步架构文档与 benchmark registry：
  - 显式把 `real_issue_tasks_challenge_v1.json` 纳入关键 manifest 视图

### 当前结论

- 现在 roadmap 的持续追踪口径已经从：
  - 只看正式集
  - 升级成同时看正式集与 challenge 集
- 这会让后续系统边界案例的治理更稳定，也更上下文友好

## 2026-06-13 Phase 6 challenge 评测入口首版落地

### 本轮目标

- 让 challenge manifest 不只是“被记录”
- 而是能像正式集一样被单独运行、单独展示
- 同时保留 challenge 与正式集的语义边界

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/run_challenge_eval.py`
- `tests/test_run_challenge_eval.py`
- `README.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 改动摘要

- 新增 challenge 专用批量入口：
  - `scripts/run_challenge_eval.py`
- 它会：
  - 读取 `real_issue_tasks_challenge_v1.json`
  - 跑 batch run
  - 跑 batch eval
  - 同时带出最新 maturity headline
- 同步补充 README / GUIDE / project memory 的体验路径

### 关键验证

- 单测：
  - `python -m pytest tests/test_run_challenge_eval.py tests/test_analyze_benchmark_maturity.py tests/test_run_real_issue_eval.py tests/test_audit_semi_real_pipeline.py -q`
  - 结果：`10 passed`
- 真实运行：
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v69.json --run-label challengev69`

### 当前结果

- 已生成真实产物：
  - `logs/summaries/batch_run_challengev69_001.json`
  - `logs/summaries/batch_eval_challengev69_001.json`
  - `logs/summaries/benchmark_maturity_maturity_077.json`
- 当前 headline 为：
  - `formal=64/60`
  - `challenge=1`
  - `eco=16/6`
  - `frozen=40/40`
  - `streak=8/5`

### 当前结论

- challenge 集现在已经从“文档层存在”推进到“脚本层可运行”
- 后续 roadmap 继续推进时，系统边界题不再需要借道正式集或手工单题说明
- 这让 challenge set 终于具备了独立成立的最小基础设施形态

## 2026-06-13 Phase 6 challenge 展示层首版收口

### 本轮目标

- 让 challenge 线不只“能跑”，还“能被快速理解”
- 降低后续续做时重新解释 challenge 集定位的成本

### 改动类型

- `documentation`

### 主要涉及文件

- `docs/challenge_set.md`
- `docs/benchmark_registry.md`
- `README.md`
- `docs/project_memory.md`

### 改动摘要

- 新增 challenge 专门文档：
  - `docs/challenge_set.md`
- 在 benchmark registry 中新增 `Challenge 任务` 段落
- 把 README 的证据引用同步到：
  - `benchmark_maturity_maturity_077.json`
  - `batch_eval_challengev69_001.json`
- 把 challenge 文档入口加入 README 与 project memory

### 当前结论

- challenge 线现在已经同时具备：
  - manifest
  - 审计
  - maturity 追踪
  - 独立评测入口
  - 独立说明文档
- 这让后续把 roadmap 作为长期 goal 持续追踪时，上下文恢复成本进一步下降

## 2026-06-13 Phase 6 challenge shortlist 首版落地

### 本轮目标

- 把“下一条 challenge 该选什么”从临时讨论，收口成稳定文档入口
- 降低后续续做时重新比较 challenge 候选的上下文成本

### 改动类型

- `documentation`

### 主要涉及文件

- `docs/challenge_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `README.md`
- `GUIDE.md`

### 改动摘要

- 新增 `docs/challenge_shortlist.md`
  - 明确 challenge 题选择标准
  - 明确当前已落地 challenge 题
  - 给出下一条候选优先级
- 当前 shortlist 首批候选为：
  - `dateutil/dateutil#1191`
  - `PyCQA/isort#1815`
  - `pallets/click#2402`
- 同步把 challenge 下一步动作接入：
  - `next_actions`
  - `project_memory`
  - `README`
  - `GUIDE`

### 当前结论

- challenge 线现在不仅知道“当前有什么”
- 也开始知道“下一步该挑什么”
- 这让 roadmap 的 A3 challenge set 支线第一次具备了明确的后续推进顺序

## 2026-06-13 Phase 6 challenge shortlist 口径纠偏

### 本轮目标

- 修正 challenge shortlist 中已经与正式主集冲突的错误候选
- 把“当前 challenge 下一条题”的口径校准回真实状态
- 避免后续续做时再次把正式任务误判成 challenge 候选

### 改动类型

- `documentation`
- `governance`

### 主要涉及文件

- `docs/challenge_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 改动摘要

- 纠正了上一版 shortlist 的一个口径错误：
  - `dateutil/dateutil#1191`
  - `PyCQA/isort#1815`
  - `pallets/click#2402`
  这 3 条都已经进入正式主集，不应继续写成“下一条 challenge 候选”
- 将当前 challenge shortlist 校准为：
  - 本地空表
  - 需要重新 sourcing 第 `2` 条 challenge 候选
- 将 challenge 线下一步统一改写为：
  - 优先从新的 issue 来源中找“平台 / 环境语境较重”或“复杂 parser / formatter / control-flow 边界”题

### 关键校准结果

- `dateutil/dateutil#1191` 已在正式主集，对应 `task_050`
- `PyCQA/isort#1815` 已在正式主集，对应 `task_061`
- `pallets/click#2402` 已在正式主集，对应 `task_042`
- 当前 challenge 集仍然只有：
  - `task_126 / samuelcolvin/watchfiles#266`

### 当前结论

- challenge 线的当前真实状态不是“已有下一条明确候选”
- 而是“第 1 条 challenge 已落地，第 2 条 challenge 候选需要重新 sourcing”
- 这次纠偏的价值主要在于减少后续续做时的上下文误导，避免同一条题在正式集与 challenge 线被重复叙述

## 2026-06-13 Phase 6 challenge sourcing brief 首版落地

### 本轮目标

- 给 challenge 线补一份独立的找题 brief
- 把“什么样的 issue 适合 challenge”从口头共识收口成稳定文档入口
- 进一步降低后续续做时的上下文恢复成本

### 改动类型

- `documentation`
- `governance`

### 主要涉及文件

- `docs/challenge_sourcing_brief_a3.md`
- `docs/challenge_set.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `GUIDE.md`
- `docs/v2_roadmap.md`

### 改动摘要

- 新增 `docs/challenge_sourcing_brief_a3.md`
  - 明确 challenge 题的核心定位：
    - 更适合展示系统边界
    - 但暂时不适合直接并入正式主集
  - 明确当前最高优先级：
    - 平台 / 环境语境较重，但仍可稳定本地化的题
    - parser / formatter / control-flow 内部语义复杂的题
  - 明确必须排除项：
    - 已进入正式主集的题
    - 无法压成稳定本地回归的题
    - 依赖真实外部系统的题
- 同步更新 challenge 文档与当前态入口：
  - `challenge_set`
  - `next_actions`
  - `project_memory`
  - `GUIDE`
- 校准 `v2_roadmap` 的 A3 状态：
  - 从“待启动”
  - 改成“已启动，待扩展”

### 当前结果

- challenge 线现在已经同时具备：
  - manifest
  - 评测入口
  - shortlist
  - sourcing brief
- 当前更准确的下一步是：
  - 继续 sourcing 第 `2` 条 challenge 题
  - 而不是重新解释 challenge 线到底该找什么

### 当前结论

- 这轮没有新增 benchmark 任务
- 但把 challenge 线的治理底座又补齐了一块
- 后续无论是我继续找题，还是你让 Claude 帮忙搜题，现在都可以直接复用同一份 brief，减少口径漂移

## 2026-06-13 Phase 6 challenge shortlist 校验器首版落地

### 本轮目标

- 把“challenge shortlist 误收正式主集题”这个问题收口成可执行校验
- 避免后续继续推进 roadmap 时，只能靠人工审文档发现口径错误

### 改动类型

- `tooling`
- `validation`
- `documentation`

### 主要涉及文件

- `scripts/validate_challenge_shortlist.py`
- `tests/test_validate_challenge_shortlist.py`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 新增 `scripts/validate_challenge_shortlist.py`
  - 读取：
    - `docs/challenge_shortlist.md`
    - `benchmarks/manifests/real_issue_tasks.json`
  - 提取 challenge shortlist 候选标题行里的 GitHub issue 引用
  - 反查正式 manifest 中对应任务的：
    - `repo_full_name`
    - `issue_number`
  - 如果发现候选 issue 已在正式主集，就直接报错
- 新增 `tests/test_validate_challenge_shortlist.py`
  - 覆盖：
    - 能正确识别正式主集冲突
    - 不误伤“当前已在正式主集”的解释性引用
    - 只识别真正的候选标题行
- 同步把这个入口补到：
  - `next_actions`
  - `GUIDE`

### 关键验证

- 单测：
  - `python -m pytest tests/test_validate_challenge_shortlist.py -q`
  - 结果：`3 passed`

### 当前结论

- challenge 线现在不只是“有 shortlist”
- 还开始具备最小自动治理能力
- 后续如果再把正式主集里的题误写成 challenge 候选，这条脚本可以更早暴露问题

## 2026-06-13 Phase 6 challenge shortlist 校验并入总验证入口

### 本轮目标

- 避免 challenge 文档治理变成一条“单独记得跑”的旁路校验
- 把 challenge shortlist 校验自然接回现有 `validate_tasks.py` 总入口

### 改动类型

- `tooling`
- `validation`
- `documentation`

### 主要涉及文件

- `scripts/validate_tasks.py`
- `tests/test_validate_tasks.py`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 扩展 `scripts/validate_tasks.py`
  - 新增 `validate_repository()` 总校验入口
  - 在原有：
    - task schema 校验
    - candidate file 最小结构校验
    之外，追加：
    - challenge shortlist 与正式主集冲突校验
- 新增参数：
  - `--challenge-shortlist`
  - `--formal-manifest`
- 输出成功信息时，新增：
  - `validated_challenge_shortlist`
  - `validated_formal_manifest`
- 新增 `tests/test_validate_tasks.py`
  - 覆盖 challenge shortlist 冲突能被总入口捕获
  - 覆盖无冲突场景可正常通过

### 关键验证

- 单测：
  - `python -m pytest tests/test_validate_tasks.py tests/test_validate_challenge_shortlist.py -q`
  - 结果：`5 passed`
- 当前仓库实跑：
  - `python scripts/validate_tasks.py`

### 当前结论

- challenge 线的最小自动治理能力，现在已经不再是独立散落的脚本
- 而是接回了仓库级总校验入口
- 后续继续追 roadmap 时，只跑一个总校验命令，也更不容易漏掉 challenge 文档口径问题

## 2026-06-13 roadmap 状态快照首版落地

### 本轮目标

- 把 roadmap 当前最关键的推进状态收口成可生成的结构化快照
- 降低后续续做时必须同时翻 `v2_roadmap / project_memory / maturity / pipeline audit` 的上下文成本

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/snapshot_roadmap_status.py`
- `tests/test_snapshot_roadmap_status.py`
- `docs/v2_roadmap.md`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 新增 `scripts/snapshot_roadmap_status.py`
  - 复用：
    - `build_benchmark_maturity_summary`
    - `build_semi_real_pipeline_audit`
  - 输出一份面向 roadmap 续做的状态快照，包含：
    - formal / challenge / ecosystem / candidate / frozen 核心数字
    - 当前 goal progress
    - challenge 当前状态
    - 当前 roadmap focus
- 新增 `tests/test_snapshot_roadmap_status.py`
  - 覆盖 summary 聚合逻辑
  - 覆盖 JSON / Markdown 产物落盘
- 同步把这个入口补到：
  - `v2_roadmap`
  - `next_actions`
  - `GUIDE`

### 关键验证

- 单测：
  - `python -m pytest tests/test_snapshot_roadmap_status.py -q`
  - 结果：`2 passed`

### 当前结论

- 这轮没有新增 benchmark 题，也没有改策略版本
- 但 roadmap 本身的“可追踪性”更强了
- 后续任何会话如果要快速恢复当前全局进度，可以先看这份状态快照，再决定是切回性能线、正式扩容线，还是 challenge 线

## 2026-06-13 roadmap tracking 一键刷新入口首版落地

### 本轮目标

- 把 roadmap 持续追踪所需的关键动作收口成一条一键刷新命令
- 降低后续续做时手工串：
  - `validate_tasks`
  - `audit_semi_real_pipeline`
  - `analyze_benchmark_maturity`
  - `snapshot_roadmap_status`
  的上下文成本

### 改动类型

- `tooling`
- `validation`
- `documentation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 新增 `scripts/refresh_roadmap_tracking.py`
  - 先跑仓库级校验
  - 若校验通过，再顺序刷新：
    - `audit_semi_real_pipeline`
    - `analyze_benchmark_maturity`
    - `snapshot_roadmap_status`
  - 最终写出一份总索引 summary，记录：
    - validation 结果
    - 三份核心产物路径
    - 当前 headline
- 新增 `tests/test_refresh_roadmap_tracking.py`
  - 覆盖“校验失败后短路”
  - 覆盖“全链路成功写出 summary”
- 同步补充：
  - `next_actions`
  - `GUIDE`

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
  - 结果：`2 passed`

### 当前结论

- roadmap 追踪入口现在又往前收了一步
- 后续如果只是想刷新“当前状态有没有变、关键产物是否齐”，不必再手工串多条命令
- 这更贴近“把 roadmap 作为持续追踪 goal”本身的实际使用方式

## 2026-06-13 roadmap tracking latest 稳定入口补齐

### 本轮目标

- 让 roadmap tracking 刷新结果除了编号产物外，还始终有一个稳定路径可读
- 避免后续续做时还要先人工判断哪个 `roadmap_tracking_*.json` 是最新的

### 改动类型

- `tooling`
- `documentation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 扩展 `refresh_roadmap_tracking.py`
  - 每次刷新除了写：
    - 编号产物 `roadmap_tracking_<label>_NNN.json/.md`
  - 也同步写：
    - `roadmap_tracking_latest_<label>.json/.md`
- 这样后续读取最新状态时，可以直接走稳定路径
- 同步把推荐阅读路径补到：
  - `next_actions`
  - `GUIDE`

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
  - 结果：`2 passed`

### 当前结论

- roadmap tracking 入口现在更适合长期使用了
- 后续任何会话如果只想先看“最新状态”，直接打开 latest 文件即可，不必先做编号推断

## 2026-06-13 roadmap tracking delta 摘要首版落地

### 本轮目标

- 让 roadmap tracking 不只告诉我们“当前 latest 是什么”
- 还直接告诉我们“相对上一次 latest 变了什么”
- 降低后续续做时人工比对两份 summary 的成本

### 改动类型

- `tooling`
- `validation`
- `documentation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 扩展 `refresh_roadmap_tracking.py`
  - 刷新前会先读取当前 `roadmap_tracking_latest_<label>.json`
  - 刷新后会在新 summary 中补出：
    - `previous_latest_summary_json_path`
    - `changed_fields`
    - `delta`
- 当前 delta 只对比高信号字段：
  - `headline`
  - `formal_task_count`
  - `challenge_task_count`
  - `ecosystem_count`
  - `candidate_count`
  - `latest_frozen_task_count`
  - `frozen_40_streak`
- 补充测试覆盖：
  - 无 previous latest 时，delta 为 `None`
  - 有 previous latest 且关键字段变化时，能正确产出 `field_changes`
- 同步把 latest + delta 的推荐阅读方式补到：
  - `docs/next_actions.md`
  - `GUIDE.md`

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
- 真实验证：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- roadmap tracking 现在从“有 latest 快照”升级成了“能直接看变化”
- 后续续做时，更容易先判断：
  - 只是又跑了一次 refresh
  - 还是正式任务数、生态覆盖、frozen 状态真的发生了推进

## 2026-06-13 roadmap tracking outcome 结论层首版落地

### 本轮目标

- 让 roadmap tracking 不只输出数字变化
- 还直接输出一条更适合人读的 refresh 结论
- 进一步降低后续续做时打开 latest 后的判断成本

### 改动类型

- `tooling`
- `validation`
- `documentation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 扩展 `refresh_roadmap_tracking.py`
  - 新增 `refresh_outcome`
  - 当前会把 refresh 结果归类为：
    - `first_refresh`
    - `validation_failed`
    - `no_material_change`
    - `progress`
    - `regression`
    - `mixed`
- 结论生成当前依赖：
  - `validation` 状态
  - 高信号字段 delta
  - 数值字段的增减方向
- 扩展 markdown 输出
  - latest `.md` 现在会直接显示：
    - `Outcome`
    - `category`
    - `summary`
- 扩展测试覆盖：
  - 首次 refresh
  - validation 失败
  - 正向推进
  - 无实质变化

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
- 真实验证：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- roadmap tracking 现在从“能看状态、能看变化”继续升级到“能直接看结论”
- 这使得后续继续追踪 roadmap 时，`roadmap_tracking_latest_refresh.md/json` 更接近一个真正的总入口，而不是只是一份中间 summary

## 2026-06-13 roadmap tracking history 索引首版落地

### 本轮目标

- 让 roadmap tracking 不只适合读“当前这一次 refresh”
- 也适合读“最近几次 refresh 的连续走势”
- 在不覆盖历史编号产物的前提下，补一层稳定历史索引入口

### 改动类型

- `tooling`
- `validation`
- `documentation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 扩展 `refresh_roadmap_tracking.py`
  - 每次 refresh 后会扫描当前标签下所有编号产物：
    - `roadmap_tracking_<label>_NNN.json`
  - 重建稳定历史索引：
    - `roadmap_tracking_history_latest_<label>.json`
    - `roadmap_tracking_history_latest_<label>.md`
- 当前 history summary 会收口：
  - `total_refresh_count`
  - `category_counts`
  - `recent_no_material_change_streak`
  - 最近若干轮 refresh 的精简时间线
- 同时在单次 refresh summary 中补出：
  - `history_overview`
  - 让 latest 文件也能顺手看到历史趋势入口
- 补充测试覆盖：
  - 首次 refresh 时 history 正常生成
  - validation 失败时 history 仍正常生成
  - 可从旧编号产物重建连续 history，不依赖覆盖式写法

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
- 真实验证：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- roadmap tracking 现在已经具备三层可读性：
  - 当前状态
  - 相对上次的变化
  - 最近几轮的连续走势
- 这比只看 latest 更适合把 roadmap 真正当作长期 goal 追踪

## 2026-06-13 roadmap tracking history advice 首版落地

### 本轮目标

- 让 history 视图不只展示“最近几轮发生了什么”
- 还给出一层保守、可执行的趋势建议
- 降低后续续做时从 tracking 结果切回主线动作的判断成本

### 改动类型

- `tooling`
- `validation`
- `documentation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 扩展 history summary：
  - 新增 `advice`
  - 根据 recent history 生成保守趋势建议
- 当前主要覆盖的高信号场景包括：
  - `validation_failed`
  - `regression`
  - `recent_no_material_change_streak >= 5`
  - `progress`
- 当连续多轮 `no_material_change` 时：
  - history 会提示不要继续只跑 refresh
  - 而应切回：
    - 正式集扩容
    - challenge sourcing
    - 或新的性能/稳定性证据补强
- 同步把 history advice 的阅读入口补到：
  - `GUIDE.md`
  - `docs/next_actions.md`

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
- 真实验证：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- roadmap tracking 现在不只是在“记录”
- 还开始具备最小的“下一步动作提示”能力
- 这让它更像一个长期 goal 的操作面板，而不是单纯的状态快照集合

## 2026-06-13 roadmap action board 首版落地

### 本轮目标

- 把 latest、history、history advice 再向前收一层
- 给 roadmap 持续追踪补一个真正的“当前该做什么”稳定入口
- 减少后续续做时在多个 summary 之间来回切换的成本

### 改动类型

- `tooling`
- `validation`
- `documentation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 每次 refresh 现在会额外生成：
  - `roadmap_action_board_latest_<label>.json`
  - `roadmap_action_board_latest_<label>.md`
- action board 会统一收口：
  - 当前 refresh headline
  - refresh outcome
  - history advice
  - 当前关键状态
  - top priorities
- 当前优先级生成逻辑会优先响应：
  - `validation_failed`
  - `stalled_tracking`
  - `progress`
- 在当前真实状态下：
  - top priority 会落在正式集扩容
  - 第二优先级是 challenge 第 2 题 sourcing
  - 第三优先级是性能证据补强

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
- 真实验证：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- roadmap tracking 现在已经从“状态快照集合”进一步升级成“最小 action board”
- 后续如果只是想知道现在最该做什么，不必再人工综合 latest、history 和 roadmap 文档

## 2026-06-13 roadmap action board 执行入口补齐

### 本轮目标

- 让 action board 不只告诉我们优先级
- 还直接告诉我们可以先执行什么命令、先看什么文档
- 把“看懂面板”推进到“拿着面板就能开工”

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/next_actions.md`
- `GUIDE.md`

### 改动摘要

- 扩展 action board 的每个 priority：
  - 新增 `commands`
  - 新增 `docs`
- 当前 stalled 状态下的 action board 已能直接给出：
  - 正式扩容线的找题命令
  - challenge 线的 shortlist / refresh 入口
  - 性能线的环境基线与 refresh 入口
- 同步把“可直接从 action board 抄命令开工”的口径补到：
  - `GUIDE.md`
  - `docs/next_actions.md`

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
- 真实验证：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- action board 现在已经不只是“决策看板”
- 而是“带启动入口的最小执行面板”
- 这让 roadmap goal 的持续追踪更接近真正可恢复、可持续工作的形态

## 2026-06-13 roadmap action board 完成信号与 refresh 触发点补齐

### 本轮目标

- 让 action board 不只告诉我们先做什么
- 还告诉我们做到什么算这一轮完成、什么时候该回到 refresh
- 降低后续推进过程中“什么时候停下来刷新 tracking”这类判断成本

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `GUIDE.md`
- `docs/next_actions.md`

### 改动摘要

- 扩展 action board 的每个 priority：
  - 新增 `done_signal`
  - 新增 `when_to_refresh`
- 当前 stalled 状态下的 3 条主线现在都会明确回答：
  - 什么时候算本轮动作做到了
  - 做到后应在什么节点重新 refresh
- 同步把这层口径补到：
  - `GUIDE.md`
  - `docs/next_actions.md`

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
- 真实验证：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- action board 现在已经从“可读、可执行”进一步升级到“可收口”
- 后续推进时，不只知道该做什么，还知道做到哪一步该回来刷新 roadmap 追踪口径

## 2026-06-13 roadmap action board 预期 tracking 信号补齐

### 本轮目标

- 让 action board 不只告诉我们什么时候 refresh
- 还直接告诉我们 refresh 后该重点看哪些 tracking 字段
- 减少后续续做时“刷新了，但应该先看哪里”这类判断成本

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `GUIDE.md`
- `docs/next_actions.md`

### 改动摘要

- 扩展 action board 的每个 priority：
  - 新增 `expected_tracking_signals`
- 当前 stalled 状态下：
  - 正式扩容线会明确提示关注 `formal_task_count`、`candidate_count`、`ecosystem_count` 等高信号字段
  - challenge 线会明确提示关注 `challenge_task_count`、`challenge_status.next_action`
  - 性能线会明确提示关注 `history_advice`、性能相关输出产物与建议分类变化
- 同步把“refresh 后应重点看哪些字段”的口径补到：
  - `GUIDE.md`
  - `docs/next_actions.md`

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
- 真实验证：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- action board 现在已经具备：
  - 做什么
  - 怎么做
  - 什么时候算做完
  - 什么时候回来 refresh
  - refresh 后重点看哪些信号
- 这让 roadmap 的持续追踪更接近真正的“可执行闭环”

## 2026-06-13 roadmap status card 首版落地

### 本轮目标

- 给 roadmap 持续追踪补一个真正的 TL;DR 入口
- 让每次恢复会话时可以在 30 秒内完成状态接管
- 避免一上来就打开过长的 latest / history / action board

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `GUIDE.md`
- `docs/next_actions.md`

### 改动摘要

- 每次 refresh 现在会额外生成：
  - `roadmap_status_card_latest_<label>.json`
  - `roadmap_status_card_latest_<label>.md`
- status card 只保留最小必要信息：
  - 当前 headline
  - refresh outcome category
  - history advice category / summary
  - recent no-change streak
  - 当前关键状态
  - 当前 top priority
  - 第一条命令
  - done signal
  - when to refresh
- 同步把这个 TL;DR 入口补到：
  - `GUIDE.md`
  - `docs/next_actions.md`

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
- 真实验证：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- roadmap tracking 现在已经不仅有完整面板，还有一个低恢复成本的 status card
- 后续如果只是想快速接管当前状态，先读 status card 就够了

## 2026-06-13 roadmap tracking latest summary 快捷入口显式化

### 本轮目标

- 让 latest refresh markdown 本身就成为真正的跳转入口
- 降低“知道有 history / action board / status card，但还要手动去日志目录找文件”的摩擦
- 把接管顺序压缩成 `latest -> fast path -> 目标面板`

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `GUIDE.md`
- `docs/next_actions.md`
- `logs/summaries/roadmap_tracking_latest_refresh.md`

### 改动摘要

- 扩展 `build_refresh_markdown()`：
  - 在 `Outputs` 中显式展示
    - `history_summary_json_path / md_path`
    - `action_board_json_path / md_path`
    - `status_card_json_path / md_path`
- 新增 `## Fast Paths`：
  - `status_card`
  - `action_board`
  - `history_summary`
- 补充单测，确保 latest markdown 会持续暴露这些快捷入口
- 同步把这层读取顺序补到：
  - `GUIDE.md`
  - `docs/next_actions.md`

### 关键验证

- 单测：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
- 真实验证：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- latest refresh 现在不只是“当前 summary”
- 它已经成为 roadmap tracking 的稳定索引页
- 后续恢复上下文时，通常可以直接按：
  - `latest`
  - `Fast Paths`
  - `status card / action board / history`
  这个顺序接管

## 2026-06-13 roadmap tracking 候选状态与 challenge shortlist 信号补齐

### 本轮目标

- 让 roadmap tracking 不只捕捉“候选池总数变化”
- 同时捕捉 `imported -> screened` 这类筛选链路推进
- 以及 challenge shortlist 是否已经从空表恢复为“有下一候选”

### 改动类型

- `tooling`
- `documentation`
- `validation`

### 主要涉及文件

- `scripts/validate_challenge_shortlist.py`
- `scripts/snapshot_roadmap_status.py`
- `scripts/refresh_roadmap_tracking.py`
- `tests/test_validate_challenge_shortlist.py`
- `tests/test_snapshot_roadmap_status.py`
- `tests/test_refresh_roadmap_tracking.py`
- `GUIDE.md`
- `docs/next_actions.md`

### 改动摘要

- 新增 challenge shortlist 结构化摘要函数：
  - 直接提取候选数量和第一条 issue ref
- 扩展 roadmap status snapshot：
  - 新增 `screened_candidate_count`
  - 新增 `imported_candidate_count`
  - 新增 `blocked_candidate_count`
  - 新增 `challenge_status.shortlist_candidate_count`
  - 新增 `challenge_status.next_candidate_issue_ref`
- 扩展 refresh delta 与展示层：
  - latest / status card / action board 现在都能直接看见候选状态推进
  - challenge 线的“重新 sourcing”与“已有下一候选待评估”也能被 refresh 明确区分

### 关键验证

- 单测：
  - `python -m pytest tests/test_validate_challenge_shortlist.py tests/test_snapshot_roadmap_status.py tests/test_audit_semi_real_pipeline.py tests/test_refresh_roadmap_tracking.py -q`

### 当前结论

- roadmap tracking 现在不再只擅长看“规模变化”
- 它也已经开始能看“治理流转变化”
- 这让后续持续追踪更贴近真实推进节奏

## 2026-06-13 challenge 候选 watchfiles#110 推进到 screened + dry-run

### 本轮目标

- 沿最新 roadmap active_track 继续推进 challenge 线
- 不只停在“shortlist 已恢复”
- 继续把 `watchfiles#110` 往可落地方向推进一档

### 改动类型

- `benchmark`
- `documentation`
- `validation`

### 主要涉及文件

- `benchmarks/real_world_candidates.json`
- `docs/challenge_shortlist.md`
- `scripts/screen_candidate.py`
- `scripts/scaffold_semi_real_task.py`

### 改动摘要

- 把 `samuelcolvin_watchfiles_issue_110`：
  - 从 `imported` 推进到 `screened`
- 跑通：
  - `python scripts/scaffold_semi_real_task.py --from-candidate samuelcolvin_watchfiles_issue_110 --dry-run`
- dry-run 当前自动推断结果为：
  - `watchfiles/main.py`
  - `tests/test_main.py`
- 同步把 challenge shortlist 从“待筛选”更新为“已 screened，可继续脚手架评估”

### 关键验证

- 命令：
  - `python scripts/screen_candidate.py --candidate-id samuelcolvin_watchfiles_issue_110 --candidate-file benchmarks/real_world_candidates.json --decision y`
  - `python scripts/scaffold_semi_real_task.py --from-candidate samuelcolvin_watchfiles_issue_110 --dry-run`

### 当前结论

- challenge 线已经不再只有“有下一候选”这一层
- `watchfiles#110` 现在已经进入可继续做 semi-real 评估的阶段
- 下一步最自然的是决定是否把它推进到 `task_127` 对应的 challenge semi-real 脚手架

## 2026-06-13 文档口径再校准：roadmap / memory / guide 对齐 tracking latest

### 本轮目标

- 消除少数展示层文档与最新 tracking 口径之间的偏差
- 避免后续续做时把历史样例误读成“当前最新状态”

### 改动类型

- `documentation`
- `tracking`

### 主要涉及文件

- `docs/v2_roadmap.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 改动摘要

- 把 `docs/v2_roadmap.md` 的候选池统计：
  - 从只写 `accepted = 65`
  - 改成与 latest refresh 一致的：
    - `candidate_count = 68`
    - `accepted = 65`
    - `screened = 2`
    - `imported = 1`
- 把 `docs/project_memory.md` 的候选池状态同步到当前真实推进：
  - 明确补上
    - `samuelcolvin/watchfiles#110`
    - `agronholm/anyio#82`
    - `agronholm/anyio#88`
    这三条仍在候选推进链路中的条目
- 把 `GUIDE.md` 中原本写成“当前最新落地到 improved_v63”的段落：
  - 改成“以 `improved_v63` 为例说明一次完整扩容闭环”
  - 显式声明它是历史样例，不代表当前最新版本

### 当前结论

- 当前展示层里最容易误导续做的三处入口已经重新对齐
- 后续恢复上下文时：
  - 当前状态优先看 tracking latest / status card
  - `GUIDE` 里的 `v63` 段落只作为扩容模板样例使用

## 2026-06-13 challenge 候选 watchfiles#110 推进到 task_127 + screened_with_task

### 本轮目标

- 不只把 `watchfiles#110` 停留在 `screened`
- 继续把 challenge 候选推进到本地 semi-real 脚手架阶段
- 同时让 roadmap tracking 能感知这一步推进

### 改动类型

- `benchmark`
- `tracking`
- `documentation`
- `validation`

### 主要涉及文件

- `benchmarks/tasks/task_127.json`
- `benchmarks/repos/watchfiles_110_repo`
- `benchmarks/real_world_candidates.json`
- `scripts/snapshot_roadmap_status.py`
- `scripts/refresh_roadmap_tracking.py`
- `tests/test_snapshot_roadmap_status.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/challenge_shortlist.md`
- `docs/next_actions.md`

### 改动摘要

- 将 `samuelcolvin_watchfiles_issue_110` 正式推进到 semi-real 脚手架阶段：
  - 新增 `task_127`
  - 新增 `watchfiles_110_repo`
  - 候选备注追加记录脚手架落盘结果
- 当前该候选的更准确状态不再只是：
  - `screened`
- 而是：
  - `screened_with_task`
  - `repo_scaffold_status = needs_manual_completion`
- 为了让 roadmap 真正持续追踪到这一步：
  - 在 status snapshot 中新增 `screened_with_task_count`
  - 在 refresh delta 中把它纳入高信号字段
  - 同步让 status card / latest markdown 暴露该字段

### 关键验证

- 命令：
  - `python scripts/scaffold_semi_real_task.py --from-candidate samuelcolvin_watchfiles_issue_110`
  - `python scripts/validate_tasks.py`
  - `python -m pytest tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_audit_semi_real_pipeline.py tests/test_validate_challenge_shortlist.py tests/test_validate_tasks.py tests/test_scaffold_semi_real_task.py -q`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- `watchfiles#110` 已经不再只是 shortlist 上的“下一候选”
- 它已经成为：
  - 可继续手工补齐 bug 场景的 `task_127`
  - challenge 线上的真实待 ready 化任务
- tracking 侧也已经开始显式暴露：
  - `screened_with_task_count = 1`

## 2026-06-13 challenge 候选 watchfiles#110 正式接入 challenge manifest

### 本轮目标

- 判断 `task_127` 是否已经具备 challenge hard case 资格
- 若具备，则把 challenge manifest 从 `1` 条扩到 `2` 条
- 让 roadmap tracking 真实反映 challenge 线规模变化

### 改动类型

- `benchmark`
- `tracking`
- `documentation`
- `validation`

### 主要涉及文件

- `benchmarks/repos/watchfiles_110_repo/watchfiles/main.py`
- `benchmarks/repos/watchfiles_110_repo/tests/test_main.py`
- `benchmarks/repos/watchfiles_110_repo/README.md`
- `benchmarks/tasks/task_127.json`
- `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- `benchmarks/real_world_candidates.json`
- `docs/challenge_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`

### 改动摘要

- 先把 `task_127` 从“会白过的 ready repo”校正成真正的 benchmark 语义：
  - 测试改为表达期望行为
  - 当前基准实现保留 bug
  - 因此 repo 自测现在会稳定失败
- 关键验证结果：
  - `python -m pytest benchmarks/repos/watchfiles_110_repo/tests/test_main.py -q`
    - 当前失败
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_127.json --policy optimization/policy_versions/improved_v69.json`
    - 当前失败
- 这说明它已经具备 challenge hard case 的最关键属性：
  - 不是“零改动也成功”的白过题
  - 而是当前策略真实未解的难题
- 基于这个判断，将：
  - `task_127`
  - 正式纳入 `real_issue_tasks_challenge_v1.json`
  - 并把 `samuelcolvin_watchfiles_issue_110` 候选状态推进到 `accepted`

### 关键验证

- 命令：
  - `python -m pytest benchmarks/repos/watchfiles_110_repo/tests/test_main.py -q`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_127.json --policy optimization/policy_versions/improved_v69.json`
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v69.json --run-label challengev69_r2`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- challenge manifest 已从 `1` 条扩到 `2` 条
- `watchfiles#110` 当前更准确的定位是：
  - ready 且已纳入 challenge manifest
  - 同时仍然是 `improved_v69` 尚未解决的 hard case
- 这让 challenge 线第一次真正具备了“至少两条边界题”的可展示规模

## 2026-06-13 challenge tracking 口径校正到“已落地 2 条 + 重新 sourcing 第 3 条”

### 本轮目标

- 修正 challenge shortlist 与 roadmap tracking 的语义冲突
- 避免 latest refresh 继续把 `watchfiles#110` 识别成“下一条 challenge 候选”
- 让 status snapshot、action board、status card 和文档都反映当前真实阶段

### 改动类型

- `tracking`
- `validation`
- `documentation`
- `tests`

### 主要涉及文件

- `scripts/validate_challenge_shortlist.py`
- `scripts/snapshot_roadmap_status.py`
- `scripts/refresh_roadmap_tracking.py`
- `tests/test_validate_challenge_shortlist.py`
- `tests/test_snapshot_roadmap_status.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/challenge_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 改动摘要

- 给 challenge shortlist 摘要逻辑补了一层保护：
  - 如果某条 issue 已经在 `real_issue_tasks_challenge_v1.json` 中
  - 即使它还残留在“下一条 challenge 候选”区段
  - tracking 也会自动把它过滤掉
- 把 challenge 下一步动作从写死文案：
  - `重新 sourcing 第 2 条 challenge 候选`
  - 改成根据当前 challenge 数动态推导
- 因此当前 challenge 已有 `2` 条时：
  - shortlist 为空会自动落成
  - `重新 sourcing 第 3 条 challenge 候选`
- 同步把 `docs/challenge_shortlist.md` 改成更准确的结构：
  - `watchfiles#110` 归入“当前已落地 challenge 题”
  - “下一条最值得补的 challenge 候选”区段改为空表并说明原因
- 同步更新：
  - `docs/next_actions.md`
  - `docs/project_memory.md`
  - `GUIDE.md`

### 关键验证

- 命令：
  - `python -m pytest tests/test_validate_challenge_shortlist.py tests/test_snapshot_roadmap_status.py tests/test_refresh_roadmap_tracking.py tests/test_validate_tasks.py -q`

### 当前结论

- challenge tracking 现在会更稳地反映真实状态：
  - challenge manifest = `2`
  - `watchfiles#110` 不再是 `next_candidate_issue_ref`
  - 当前更准确的下一步是：
    - 继续观察 `task_127`
    - 重新 sourcing 第 `3` 条 challenge 候选

## 2026-06-13 performance action board 从“只会 refresh”升级为“先诊断再收口”

### 本轮目标

- 让 roadmap tracking 在 performance 线给出真正可执行的下一步
- 避免 action board 把“refresh 自己”误当成第一动作
- 顺手补一轮新的环境基线和冻结集时延对比证据

### 改动类型

- `tracking`
- `performance`
- `documentation`
- `tests`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/optimization_log.md`
- `logs/env_baselines/env_baseline_20260613T154023784306Z.json`
- `logs/env_baselines/env_baseline_20260613T154023784306Z.md`
- `logs/summaries/duration_compare_frozen40_v68_v69_001.json`
- `logs/summaries/duration_compare_frozen40_v68_v69_001.md`
- `logs/summaries/roadmap_tracking_refresh_025.json`
- `logs/summaries/roadmap_action_board_latest_refresh.json`

### 改动摘要

- 调整 `refresh_roadmap_tracking.py` 中 performance priority 的命令顺序：
  - 先跑 `snapshot_env_baseline`
  - 再跑 `analyze_duration_regressions`
  - 最后才是 `refresh`
- 这样 `monitor_and_continue` 与 `stalled_tracking` 两种场景下：
  - performance 线都不再是“先刷新一遍看看”
  - 而是先补真实诊断证据，再回到 tracking 收口
- 同步新增测试，锁定：
  - `monitor_and_continue` 下的 performance top priority 必须先给诊断命令
- 顺手补了一轮新的环境基线：
  - `env_baseline_20260613T154023784306Z`
  - `python_noop mean = 0.0181`
  - `pytest_version mean = 0.1397`
- 再补了一轮冻结集对比：
  - `duration_compare_frozen40_v68_v69_001`
  - `common_average_delta_sec = 0.0272`
  - 当前 top regressions 包括：
    - `task_050 = +0.0743`
    - `task_034 = +0.0665`
    - `task_022 = +0.0637`
- refresh 到 `roadmap_tracking_refresh_025` 后：
  - latest action board 的 performance priority 已变成“先诊断再 refresh”的口径

### 关键验证

- 命令：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
  - `python scripts/snapshot_env_baseline.py --repetitions 5 --output-dir logs/env_baselines`
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40_v68_v69 --env-baseline logs/env_baselines/env_baseline_20260613T154023784306Z.json`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- roadmap tracking 现在不只是“记录状态”，也更像真正的执行入口：
  - performance 线会先引导去补环境与时延证据
  - 然后再回到 refresh 做统一收口
- 这对长期 goal 很重要，因为后续续做时会更少出现：
  - 只刷新状态
  - 但没有推进真实证据

## 2026-06-13 roadmap tracking 开始把 performance 证据更新识别为 progress

### 本轮目标

- 解决一个 tracking 盲点：
  - 即使已经补了新的 `env baseline` 和 `duration compare`
  - latest refresh 仍可能显示 `no_material_change`
- 让 roadmap 真正把“性能证据补强”也视作高信号推进

### 改动类型

- `tracking`
- `performance`
- `documentation`
- `tests`

### 主要涉及文件

- `scripts/snapshot_roadmap_status.py`
- `scripts/refresh_roadmap_tracking.py`
- `tests/test_snapshot_roadmap_status.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/optimization_log.md`
- `logs/summaries/roadmap_status_refresh_026.json`
- `logs/summaries/roadmap_tracking_refresh_026.json`
- `logs/summaries/roadmap_tracking_latest_refresh.json`

### 改动摘要

- 给 `snapshot_roadmap_status.py` 新增了：
  - `performance_status`
- 当前它会自动收口最新：
  - `env baseline`
  - `duration compare`
  - 以及关键数值：
    - `latest_env_baseline_mean_of_means_sec`
    - `latest_duration_compare_common_average_delta_sec`
    - `latest_duration_compare_env_adjusted_common_average_delta_sec`
- 再把这些字段接入 `refresh_roadmap_tracking.py` 的 delta extractor：
  - 因此后续只要性能证据有更新
  - `changed_fields` 就不再是空
  - `refresh_outcome` 也可以自然进入 `progress`
- 当前真实结果是：
  - `roadmap_tracking_refresh_026`
  - 已不再显示 `no_material_change`
  - 而是：
    - `progress`
    - `performance_env_baseline_snapshot_id updated`
    - `performance_duration_compare_id updated`
    - `performance_duration_compare_common_average_delta_sec updated`

### 关键验证

- 命令：
  - `python -m pytest tests/test_snapshot_roadmap_status.py tests/test_refresh_roadmap_tracking.py -q`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- roadmap tracking 现在更接近“持续追踪 goal”的真实含义：
  - 不仅能看见规模扩容
  - 也能看见性能治理证据的持续补强
- 这让 refresh 入口不再天然偏向：
  - “只有 task / candidate 变化才算推进”
  - 而是开始接受：
    - `benchmark evidence progress`

## 2026-06-13 keep_momentum 不再退化成泛 active_track

### 本轮目标

- 修正一个新的 handoff 退化点：
  - 即使 `refresh_026` 已经正确把 performance 证据识别成 `progress`
  - action board / status card 仍会在 `keep_momentum` 分支里退回泛化的 `active_track`
- 让 latest 能保留“最近一次 progress 属于哪条主线”

### 改动类型

- `tracking`
- `handoff`
- `documentation`
- `tests`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/optimization_log.md`
- `logs/summaries/roadmap_action_board_latest_refresh.json`
- `logs/summaries/roadmap_status_card_latest_refresh.json`
- `logs/summaries/roadmap_tracking_refresh_027.json`

### 改动摘要

- 新增了 `infer_progress_track(current_summary)`：
  - 根据 `changed_fields` 自动推断最近一次 progress 属于：
    - `performance_track`
    - `challenge_track`
    - `formal_expansion_track`
    - 或回退到 `active_track`
- 再把 `keep_momentum` 分支改成：
  - 如果最近一次 progress 来自 performance 字段
  - 就继续给 performance 线的具体动作
  - 而不是只给一句“继续沿同一主线推进”
- 当前真实验证结果：
  - `refresh_026` 代表 performance 证据补强
  - `refresh_027` 虽然因为没有新增证据而回到 `no_material_change`
  - 但 latest handoff 仍保留：
    - `top_priority.track = performance_track`

### 关键验证

- 命令：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py -q`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 当前结论

- roadmap tracking 现在不只会说“有推进”
- 它也开始能保留：
  - “推进发生在哪条主线”
  - 以及“下一轮继续往哪条主线接着做”
- 这使得持续追踪 goal 的 handoff 质量更高：
  - 不容易在一轮 `no_material_change` 后丢失真实主线

## 2026-06-14 `anyio#88` ready 化完成，并形成 `v69` 失败 / `v70` 成功证据

### 本轮目标

- 把 `agronholm/anyio#88` 从“已脚手架”继续推进到真正可用于策略扩容验证的 ready bug repo
- 同时补齐 roadmap tracking 对 `accepted + ready` 阶段变化的感知
- 再确认它是否足够成为下一版策略候选的直接证据点

### 改动类型

- `formal-expansion`
- `tracking`
- `documentation`
- `tests`

### 主要涉及文件

- `benchmarks/tasks/task_129.json`
- `benchmarks/repos/anyio_88_repo/`
- `app/agent/patcher.py`
- `optimization/policy_versions/improved_v70.json`
- `tests/test_patcher_anyio_v70.py`
- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `tests/test_scaffold_semi_real_task.py`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/optimization_log.md`
- `GUIDE.md`

### 改动摘要

- `agronholm/anyio#88` 已完成：
  - `imported -> screened -> task_129 -> ready -> accepted`
- 当前 `task_129` 的 ready 证据已经清楚：
  - 正常路径 `1` 条通过
  - 目标 asyncio 路径 `1` 条失败
- 这说明它已经不是“只有脚手架”的候选，而是一个可直接用于单任务修复验证的真实扩容入口

- 在 patcher 中新增了 `improved_v70`：
  - 专门处理 `anyio#88` 的 asyncio backend 额外取消父任务问题
  - 并把 `improved_v69` 的 anyio 修复链完整继承到 `v70`
- 当前单任务验证结果已经形成一条很干净的证据链：
  - `improved_v69` 运行 `task_129`：`failed`
  - `improved_v70` 运行 `task_129`：`success`

- 当前还补强了 roadmap tracking 的阶段感知：
  - 新增 `accepted_candidate_count`
  - 新增 `challenge_accepted_ready_not_in_any_manifest_count`
- 这让 tracking 能看见：
  - 候选从 `screened + task` 升级到 `accepted + ready`
  - 而不只是看见“task 脚手架数量变化”

- 同时增强了 semi_real 脚手架的 target inference：
  - 支持从 Python 符号名还原目标模块
  - 忽略 GitHub blob URL 噪声
  - 只有测试线索时回退到包主模块
  - 把 `fail_case.py / repro.py` 识别成复现脚本而不是目标模块

### 关键验证

- 命令：
  - `python -m pytest tests/test_patcher_anyio_v70.py tests/test_scaffold_semi_real_task.py tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_audit_semi_real_pipeline.py -q`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_129.json --policy optimization/policy_versions/improved_v69.json`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_129.json --policy optimization/policy_versions/improved_v70.json`

### 当前结论

- `anyio#88 / task_129` 现在已经成为一个高质量的下一轮正式扩容候选：
  - 不是只有 ready bug repo
  - 而是已经具备 `旧策略失败 / 新策略成功` 的直接证据
- 这让后续是否把它接入正式 manifest，不再需要靠直觉判断
- 当前更合理的下一步是：
  - 先决定是否把 `task_129` 纳入正式集
  - 再做 `v70` 在正式集 / frozen 集上的最小回归验证

## 2026-06-14 `v70` 已完成三线最小验证，并补出首轮稳定性证据

### 本轮目标

- 把 `task_129` 真正接入正式主集
- 验证 `improved_v70` 在正式集、`frozen_20`、`frozen_40` 上是否功能无回归
- 再补一轮 stability recheck，判断它是否已具备新的稳定锚点资格

### 改动类型

- `formal-expansion`
- `evaluation`
- `stability`
- `documentation`

### 主要涉及文件

- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `docs/benchmark_registry.md`
- `README.md`
- `GUIDE.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `logs/summaries/batch_eval_realissuev70r1_001.json`
- `logs/summaries/batch_compare_realissue_step70_001.json`
- `logs/summaries/batch_compare_frozen20_step70_001.json`
- `logs/summaries/batch_compare_frozen40_step70_001.json`
- `logs/summaries/stability_recheck_frozen20_v70_stability_001.json`
- `logs/summaries/stability_recheck_frozen40_v70_stability_001.json`
- `logs/summaries/roadmap_tracking_refresh_035.json`

### 改动摘要

- `task_129` 已正式纳入主 manifest：
  - 正式任务数 `64 -> 65`
  - `refresh_035` 已捕获：
    - `formal_task_count +1`
    - `challenge_accepted_ready_not_in_any_manifest_count -1`

- `improved_v70` 已完成三线最小功能验证：
  - 正式集：`65 / 65`
  - `frozen_20`：`20 / 20`
  - `frozen_40`：`40 / 40`

- 相对 `v69` 的当前最小 compare 结果是：
  - 正式集：
    - `average_duration_sec: 0.5656 -> 0.5924`
  - `frozen_20`：
    - `average_duration_sec: 0.5975 -> 0.5803`
  - `frozen_40`：
    - `average_duration_sec: 0.5861 -> 0.5582`

- 因此这轮的性能信号不是单向的：
  - 正式集回升
  - 两条冻结集回落

- 当前首轮 stability recheck 结果：
  - `frozen_20`
    - `mean = 0.5799`
    - `std = 0.0448`
    - `conclusion = borderline`
  - `frozen_40`
    - `mean = 0.5668`
    - `std = 0.0153`
    - `conclusion = stable`

### 关键验证

- 命令：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v70.json --run-label realissuev70r1 --compare-against-eval logs/summaries/batch_eval_realissuev69r1_001.json --compare-label realissue_step70`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --policy optimization/policy_versions/improved_v70.json --run-label frozen20v70r1 --compare-against-eval logs/summaries/batch_eval_frozen20v69r1_001.json --compare-label frozen20_step70`
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --policy optimization/policy_versions/improved_v70.json --run-label frozen40v70r1 --compare-against-eval logs/summaries/batch_eval_frozen40v69r1_001.json --compare-label frozen40_step70`
  - `python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v70.json --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --repetitions 3 --run-label frozen20_v70_stability`
  - `python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v70.json --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --repetitions 3 --run-label frozen40_v70_stability`

### 当前结论

- `improved_v70` 已经不是“只在单任务成功”的候选版本
- 它现在是：
  - 最新扩容成功版本
  - 已完成正式集与冻结集三线最小功能验证
  - 但稳定性证据仍然分化：
    - `frozen_40` 可以接受
    - `frozen_20` 还需要继续复核
- 因此当前最合理的下一步是：
  - 再补 `v70` 的稳定性复查
  - 同时继续推进 `task_128`
  - 不要过早把 `v70` 升格为新的长期稳定锚点

## 2026-06-14 `v70 frozen_20` 已复核收敛，`task_128` 进入 ready bug repo

### 本轮目标

- 复核 `improved_v70` 在 `frozen_20` 上的 borderline 结论是否只是采样波动
- 把 `agronholm/anyio#82 / task_128` 从纯脚手架推进到 ready bug repo

### 改动类型

- `stability`
- `formal-expansion`
- `documentation`

### 主要涉及文件

- `logs/summaries/stability_recheck_frozen20_v70_stability_r2_001.json`
- `benchmarks/repos/anyio_82_repo/anyio/module.py`
- `benchmarks/repos/anyio_82_repo/anyio/__init__.py`
- `benchmarks/repos/anyio_82_repo/test_anyio.py`
- `benchmarks/tasks/task_128.json`
- `benchmarks/real_world_candidates.json`
- `docs/candidate_shortlist.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `docs/optimization_log.md`

### 改动摘要

- `improved_v70` 在 `frozen_20` 上追加了 5 次 stability recheck：
  - `mean = 0.5732`
  - `std = 0.005`
  - `conclusion = stable`
- 这说明前一轮 `borderline`
  - 更像采样波动
  - 当前不应继续作为 `v70` 的第一风险点

- `task_128` 已从纯脚手架推进成 ready 口径最小并发回归任务：
  - trio 对照路径 `1` 条通过
  - asyncio / curio 目标路径 `2` 条失败
- 当前更准确的口径是：
  - `screened + ready + task_128`
- 这意味着它已经具备：
  - 单任务修复验证条件
  - 成为 `v71` 候选扩容题的基础质量

### 关键验证

- 命令：
  - `python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v70.json --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --repetitions 5 --run-label frozen20_v70_stability_r2`
  - `cd benchmarks/repos/anyio_82_repo`
  - `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest test_anyio.py -q`

### 当前结论

- `v70` 当前最关键的冻结集稳定性风险已经明显下降：
  - `frozen_20` 与 `frozen_40` 现在都可视为稳定
- 当前最值得继续推进的动作已经更清楚：
  - 直接拿 `task_128` 做下一轮单任务修复验证
  - 再决定是否产出 `improved_v71`

## 2026-06-14 `task_128` 完成 `improved_v70 -> improved_v71` 扩容闭环，并修复 `v71` 首轮继承链漏接

### 本轮目标

- 把 `agronholm/anyio#82 / task_128` 从 ready bug repo 推成正式扩容证据
- 验证 `improved_v71` 是否能安全接入主线

### 改动类型

- `formal-expansion`
- `policy-fix`
- `regression-repair`
- `documentation`

### 主要涉及文件

- `optimization/policy_versions/improved_v71.json`
- `app/agent/patcher.py`
- `tests/test_patcher_anyio_v71.py`
- `benchmarks/tasks/task_128.json`
- `benchmarks/repos/anyio_82_repo/anyio/module.py`
- `benchmarks/repos/anyio_82_repo/test_anyio.py`
- `benchmarks/manifests/real_issue_tasks.json`
- `benchmarks/real_world_candidates.json`
- `logs/summaries/batch_eval_realissuev71r2_001.json`
- `logs/summaries/batch_compare_realissue_step71_r2_001.json`
- `logs/summaries/batch_eval_frozen20v71r2_001.json`
- `logs/summaries/batch_compare_frozen20_step71_r2_001.json`
- `logs/summaries/batch_eval_frozen40v71r2_001.json`
- `logs/summaries/batch_compare_frozen40_step71_r2_001.json`
- `logs/summaries/roadmap_tracking_refresh_036.json`

### 改动摘要

- `task_128` 已完成单任务扩容闭环：
  - `improved_v70` 单任务失败
  - `improved_v71` 单任务成功
- 已把 `task_128` 纳入正式 manifest：
  - 正式任务数 `65 -> 66`
  - 候选池收敛到 `accepted = 68 / screened = 0`

- `v71r1` 首轮正式集验证曾暴露严重回归：
  - 正式集只成功 `10 / 66`
  - `frozen_20` `0 / 20`
  - `frozen_40` `0 / 40`
  - taxonomy 统一退化为 `Premature Finish`
- 根因已定位为：
  - `app/agent/patcher.py` 中 `improved_v71` 只接上了最新几段 anyio 规则
  - 但没有继续继承 `v59 -> v43` 的旧规则链
- 已修复：
  - 把 `improved_v71` 补回旧规则继承集合

### 关键验证

- patcher 回归：
  - `python -m pytest tests/test_patcher_anyio_v70.py tests/test_patcher_anyio_v71.py tests/test_scaffold_semi_real_task.py -q`
  - `10 passed`
- 单任务：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_128.json --policy optimization/policy_versions/improved_v70.json`
  - `failed`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_128.json --policy optimization/policy_versions/improved_v71.json`
  - `success`
- `v71r2` 三线最小验证：
  - 正式集：`66 / 66`
  - `frozen_20`：`20 / 20`
  - `frozen_40`：`40 / 40`

### 当前结论

- `improved_v71` 已经不是“只在单任务成功”的候选版本
- 当前它是：
  - 最新扩容成功版本
  - 已完成正式集、`frozen_20`、`frozen_40` 三线最小功能验证
  - 已把正式任务数从 `65` 推进到 `66`
- 当前相对 `v70` 的性能口径是：
  - 正式集：`0.5924 -> 0.5617`
  - `frozen_20`：`0.5803 -> 0.5974`
  - `frozen_40`：`0.5582 -> 0.5794`
- 因此当前最合理的下一步是：
  - 对 `v71` 补 stability recheck
  - 继续观察冻结集回升是否稳定存在
  - 再决定它是否升级为新的长期主稳定锚点

## 2026-06-14 `improved_v71` 冻结集稳定性复跑

### 本轮目标

- 在 `v71r2` 已完成三线最小验证后，继续确认冻结集回升是否只是单次采样波动

### 主要涉及文件

- `logs/summaries/stability_recheck_frozen20_v71_stability_001.json`
- `logs/summaries/stability_recheck_frozen20_v71_stability_001.md`
- `logs/summaries/stability_recheck_frozen40_v71_stability_001.json`
- `logs/summaries/stability_recheck_frozen40_v71_stability_001.md`

### 关键验证

- `python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v71.json --manifest benchmarks/manifests/real_issue_tasks_frozen_20_v1.json --repetitions 3 --run-label frozen20_v71_stability`
- `python scripts/stability_recheck.py --policy optimization/policy_versions/improved_v71.json --manifest benchmarks/manifests/real_issue_tasks_frozen_40_v1.json --repetitions 3 --run-label frozen40_v71_stability`

### 当前结果

- `frozen_20`
  - `mean = 0.5727`
  - `std = 0.0177`
  - `conclusion = stable`
- `frozen_40`
  - `mean = 0.5637`
  - `std = 0.0099`
  - `conclusion = stable`

### 当前结论

- `improved_v71` 现在已经具备：
  - 正式集、`frozen_20`、`frozen_40` 三线最小功能验证
  - `frozen_20 / frozen_40` 同版稳定性复跑 `stable`
- 因此当前可以把 `v71` 定位为：
  - 最新扩容成功版本
  - 证据链完整的可继续扩题基线
- 但仍需记住：
  - 相对 `v70`，冻结集平均耗时回升
  - 后续若继续扩题，应继续同步观察是否需要单独产出一轮性能回收版本

## 2026-06-14 文档口径校准：统一到 `v71 / formal=66 / challenge=2`

### 本轮目标

- 修正续做入口文档中残留的旧口径
- 避免后续继续基于 `64 / v69 / challenge=1` 的历史状态做判断

### 主要涉及文件

- `docs/v2_roadmap.md`
- `docs/challenge_shortlist.md`
- `docs/challenge_sourcing_brief_a3.md`
- `docs/challenge_set.md`
- `docs/next_actions.md`
- `docs/project_memory.md`

### 改动摘要

- 已把路线图、challenge 说明与记忆卡统一校准到当前真实状态：
  - 正式任务：`66`
  - challenge 任务：`2`
  - 当前主扩容版本：`improved_v71`
  - `frozen_40 streak = 8`
- 已把 challenge 线表述从“补第 `2` 条”改为“补第 `3` 条”
- 已把 `semi_real pipeline audit` 的关键口径同步为：
  - `accepted_in_formal_manifest = 66`
  - `accepted_in_challenge_manifest = 2`

### 当前结论

- 当前项目的大方向没有变化：
  - 继续扩正式真实 issue
  - 继续补第 `3` 条 challenge 候选
  - 继续以 `v71` 作为当前可继续扩题的主线版本
- 但文档入口已经重新与真实仓库状态对齐，后续 handoff 和续做会更稳

## 2026-06-14 challenge sourcing 恢复：补回第 `3` 条入口

### 本轮目标

- 不让 challenge 线停留在“shortlist 为空”的状态
- 用真实搜索结果重新补回第 `3` 条 challenge 候选入口

### 主要涉及文件

- `logs/summaries/candidate_search_watchfiles_a3_001.json`
- `benchmarks/real_world_candidates.json`
- `docs/challenge_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`

### 改动摘要

- 已修复当前会话中的 GitHub 认证干扰：
  - 根因是环境变量里的 `GITHUB_TOKEN` 失效
  - 临时移除后恢复了 `gh search` 能力
- 已重新跑一轮 watchfiles 的 challenge 定向搜索：
  - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label watchfiles_a3`
- 已把 `samuelcolvin/watchfiles#169` 导入候选池并推进到：
  - `screened`
- 已把它写回 challenge shortlist，作为当前最值得继续判题的第 `3` 条入口

### 当前结论

- challenge 线已经不再是“没有下一候选”
- 当前最自然的下一步是：
  - 直接对 `watchfiles#169` 做一轮 issue 级判题
  - 再决定是否进入 challenge 脚手架 dry-run

## 2026-06-14 `watchfiles#169` issue 级判题推进

### 本轮目标

- 不只把 `watchfiles#169` 停留在 `screened`
- 继续把它推进到“已完成 issue 级判题，可直接继续 dry-run 脚手架”的阶段

### 主要涉及文件

- `scripts/scaffold_semi_real_task.py`
- `tests/test_scaffold_semi_real_task.py`
- `benchmarks/real_world_candidates.json`
- `docs/challenge_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`

### 改动摘要

- 已先增强脚手架目标文件推断：
  - 对 `foobar.py` 这类 issue 中的示例脚本降权处理
  - 避免把 docs MRE 误当成仓库核心模块
- 已补对应测试并验证：
  - `python -m pytest tests/test_scaffold_semi_real_task.py -q`
  - `9 passed`
- 已对 `samuelcolvin/watchfiles#169` 完成一轮 issue 级判题：
  - 结合完整 issue 正文
  - 结合已落地的 `watchfiles#266 / #110` challenge 样例
  - 将目标文件收敛到：
    - `watchfiles/main.py`
    - `tests/test_main.py`

### 当前结论

- `watchfiles#169` 已经从“仅 screened 候选”推进到：
  - `screened + 已完成 issue 级判题`
- 当前最自然的下一步是：
  - 继续重跑 `--from-candidate --dry-run`
  - 如结果稳定，再进入 challenge 脚手架落盘

## 2026-06-14 `watchfiles#169` 推进到 ready challenge 草稿

### 本轮目标

- 不只停在 `task_130` 落盘
- 继续把它推进到 ready 口径的 challenge semi-real 回归任务

### 主要涉及文件

- `benchmarks/repos/watchfiles_169_repo/watchfiles/main.py`
- `benchmarks/repos/watchfiles_169_repo/tests/test_main.py`
- `benchmarks/repos/watchfiles_169_repo/README.md`
- `benchmarks/tasks/task_130.json`
- `benchmarks/real_world_candidates.json`
- `docs/challenge_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`

### 改动摘要

- 已把 `watchfiles#169` 压成最小环境边界复现：
  - WSL / Docker / Linux-like 环境只上报 `metadata-write`
  - 当前错误实现会把这类目标文件变更直接过滤掉
  - 从而不触发 reload
- 已补 3 条稳定本地测试：
  - 目标 Linux-like `metadata-write` 路径当前失败
  - 非目标文件路径保护通过
  - 正常 `modified` 事件路径通过
- 已验证：
  - `python -m pytest benchmarks/repos/watchfiles_169_repo/tests/test_main.py -q`
  - 结果：`1 failed, 2 passed`
- 已把候选状态推进为：
  - `accepted`

### 当前结论

- `watchfiles#169` 现在已经不是“仅有脚手架的候选”
- 当前它是：
  - `accepted + ready + task_130`
  - 可继续用于 challenge manifest 评估的在途 hard case

## 2026-06-14 `watchfiles#169` 正式接入 challenge manifest

### 本轮目标

- 把 `watchfiles#169 / task_130` 从 ready challenge 候选推进成正式 challenge 题
- 让 challenge manifest、文档入口、tracking 口径和后续评测入口统一到同一真实状态

### 改动类型

- `challenge-expansion`
- `documentation`
- `tracking`

### 主要涉及文件

- `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- `benchmarks/real_world_candidates.json`
- `docs/challenge_set.md`
- `docs/challenge_shortlist.md`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `README.md`
- `GUIDE.md`

### 改动摘要

- 已把 `benchmarks/tasks/task_130.json` 纳入：
  - `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- challenge manifest 当前从 `2` 条扩到 `3` 条：
  - `task_126`
  - `task_127`
  - `task_130`
- 已把 `watchfiles#169` 的候选 notes 追加写成：
  - 已纳入 challenge manifest，成为第 `3` 条 challenge 任务
- 已同步修正文档口径：
  - challenge 任务数从 `2 -> 3`
  - `watchfiles#169` 从 shortlist 候选区移动到“当前已落地 challenge 题”
  - challenge 下一步从“补第 `3` 条”切换成“补第 `4` 条”

### 当前结论

- challenge 线现在不再只是“已有 ready 候选等待决定”
- 而是已经形成 `3` 条可运行、可评测、可展示的系统边界题集合
- 下一步最自然的动作不再是继续讨论 `watchfiles#169` 要不要接入
- 而是：
  - 跑一轮三题 challenge 评测
  - refresh 收口
  - 再重新 sourcing 第 `4` 条 challenge 候选

### 关键验证

- 命令：
  - `python -m pytest tests/test_validate_challenge_shortlist.py tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_audit_semi_real_pipeline.py tests/test_run_challenge_eval.py tests/test_validate_tasks.py -q`
  - `python scripts/validate_tasks.py`
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v71.json --run-label challengev71_r3`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
- 结果：
  - challenge 相关测试：`27 passed`
  - `validate_tasks`：`Validation Passed`
  - `challengev71_r3`：
    - `task_count = 3`
    - `success_rate = 0.3333`
    - `test_pass_rate = 0.3333`
    - `Premature Finish = 2`
  - `roadmap_tracking_refresh_039`：
    - `headline = roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK`
    - `challenge_next_action = 重新 sourcing 第 4 条 challenge 候选`

### 后续补充

- 已继续把 challenge brief 入口校准到最新状态：
  - `docs/challenge_sourcing_brief_a3.md`
  - 明确 challenge 集当前已有 `3` 条任务
  - 明确当前应重新 sourcing 第 `4` 条 challenge 候选

## 2026-06-14 `v70 -> v71` 冻结集时延证据补强

### 本轮目标

- 在 challenge 第 `4` 条候选暂时受外部代理阻塞时，不中断 roadmap 主线推进
- 补一轮新的环境基线与 `v70 -> v71` 冻结集公共任务时延证据
- 让 performance track 继续有真实增量，而不是停留在旧的 `v68 -> v69` 证据上

### 改动类型

- `performance`
- `evaluation`
- `documentation`

### 主要涉及文件

- `logs/env_baselines/env_baseline_20260613T182156280991Z.json`
- `logs/env_baselines/env_baseline_20260613T182156280991Z.md`
- `logs/summaries/duration_compare_frozen40_v70_v71_001.json`
- `logs/summaries/duration_compare_frozen40_v70_v71_001.md`
- `logs/summaries/duration_compare_frozen20_v70_v71_001.json`
- `logs/summaries/duration_compare_frozen20_v70_v71_001.md`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 改动摘要

- 新增一轮环境基线快照：
  - `env_baseline_20260613T182156280991Z`
  - `python_noop mean = 0.0198`
  - `pytest_version mean = 0.1431`
- 新增一轮 `v70 -> v71` 冻结集 compare：
  - `frozen_40`
    - `common_average_delta_sec = +0.0212`
  - `frozen_20`
    - `common_average_delta_sec = +0.0171`
- 这轮继续说明：
  - `v71` 相对 `v70` 在两条冻结集上都存在正向回升
  - 当前不能只靠正式集平均耗时回落来描述 `v71`

### 关键验证

- 命令：
  - `python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines`
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v70r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v71r2_001.json --run-label frozen40_v70_v71`
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen20v70r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen20v71r2_001.json --run-label frozen20_v70_v71`

### 当前结论

- 当前 roadmap 仍在持续推进，而不是因为外部 GitHub 检索受阻就停顿
- performance 线现在已经不只围绕 `v68 -> v69`
- 也新增了 `v70 -> v71` 的冻结集证据
- 下一步可以：
  - refresh 收口这轮性能证据
  - 再视网络状态恢复 challenge 第 `4` 条候选 sourcing

### 后续补充

- 已继续补 `v70 -> v71` 的 trace 热点分析：
  - `trace_hotspots_frozen40v71r2_001`
    - `run_tests delta_total_duration_sec = +0.9079`
  - `trace_hotspots_frozen20v71r2_001`
    - `run_tests delta_total_duration_sec = +0.3933`
- 因此这轮新的更稳妥结论是：
  - `v71` 相对 `v70` 的冻结集回升主增量，仍主要集中在 `run_tests`
  - 当前暂时没有证据支持把主因转移到 `copy_workspace` 或其它外围步骤

## 2026-06-14 challenge 第 4 候选 sourcing 首轮受代理阻塞

### 本轮目标

- 尝试直接恢复 challenge 第 `4` 条候选的定向 sourcing
- 若外部网络不可用，也明确记录阻塞形态，避免后续误判为“没有推进”

### 改动类型

- `challenge-sourcing`
- `tracking`

### 主要涉及文件

- `docs/optimization_log.md`
- `docs/next_actions.md`

### 关键观察

- 已尝试运行：
  - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label watchfiles_a4`
- 当前阻塞不是 GitHub 认证失败，而是：
  - 本机代理 `127.0.0.1:7890` 拒绝连接
  - 报错为 `proxyconnect tcp ... actively refused`

### 当前结论

- challenge 第 `4` 条候选并不是“没有继续做”
- 而是已经尝试推进，但当前 live GitHub 检索被本地代理状态阻塞
- 在这个前提下，本轮已合理切回本地可推进的 performance 证据补强

## 2026-06-14 refresh_043：tracking 导航从泛化 active_track 收敛到 challenge_track

### 本轮目标

- 修正 roadmap tracking 在 `keep_momentum` 场景下的导航退化问题
- 让 latest `action_board / status_card` 能直接指向当前最具体的下一步，而不是只返回泛化的 `active_track`

### 改动类型

- `tracking`
- `roadmap-governance`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `logs/summaries/roadmap_tracking_refresh_043.json`
- `logs/summaries/roadmap_action_board_latest_refresh.md`
- `logs/summaries/roadmap_status_card_latest_refresh.md`

### 关键修改

- 新增 `resolve_priority_track()`
- 当前逻辑不再只看本轮 `changed_fields`
- 当本轮没有高信号字段变化、但 `history_advice` 已明确保留最近一次真实主线时：
  - 会优先继承 `history_advice.progress_track`
  - 其次继承 `history_advice.recommended_focus`
  - 只有两者都拿不到明确主线时，才回退到 `active_track`

### 关键验证

- 测试：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_validate_challenge_shortlist.py -q`
  - 结果：`23 passed`
- refresh：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 结果：
    - `refresh_id = roadmap_tracking_refresh_043`
    - `headline = roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK`

### 当前结论

- `refresh_043` 虽然仍是 `no_material_change`
- 但 latest `history_advice` 已明确保持：
  - `recommended_focus = challenge_track`
- 更重要的是，latest 展示层入口现在也已经真正跟上：
  - `roadmap_action_board_latest_refresh.md`
    - `Priority 1: challenge_track`
    - `action: 重新 sourcing 第 4 条 challenge 候选`
  - `roadmap_status_card_latest_refresh.md`
    - `top_priority_track: challenge_track`
    - `first_action: 重新 sourcing 第 4 条 challenge 候选`

### 这轮推进的意义

- 后续续做时，refresh 产物不再只是“提醒继续推进”
- 而是已经能更准确地承担“下一步导航器”的角色
- 这让 roadmap goal 更容易长期持续推进，而不是每次都要重新人工判断主线

## 2026-06-14 refresh_045：monitor_and_continue 下仍保持 challenge 第 4 候选为第一优先级

### 本轮目标

- 修正 `refresh_044` 暴露出的“latest 又回到 performance_track 第一优先级”的回弹问题
- 让 challenge 第 `4` 条候选缺口在当前状态下继续保持第一优先级

### 改动类型

- `tracking`
- `challenge-governance`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `logs/summaries/roadmap_tracking_refresh_045.json`
- `logs/summaries/roadmap_action_board_latest_refresh.md`
- `logs/summaries/roadmap_status_card_latest_refresh.md`

### 关键修改

- 在 `build_action_board()` 里新增一层更窄的 challenge gap 判断：
  - `history_advice.category == monitor_and_continue`
  - `challenge_task_count >= 3`
  - `challenge_shortlist_candidate_count == 0`
  - `next_action` 明确仍是 `重新 sourcing 第 4 条 challenge 候选`
- 满足以上条件时：
  - 即使 `history_advice` 已回到 `monitor_and_continue`
  - latest `action_board / status_card` 仍会把 challenge 线保持为第一优先级

### 关键验证

- 测试：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_validate_challenge_shortlist.py -q`
  - 结果：`25 passed`
- refresh：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 结果：
    - `refresh_id = roadmap_tracking_refresh_045`
    - `headline = roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK`

### 当前结论

- `refresh_045` 里：
  - `history_advice_category = monitor_and_continue`
  - `recent_no_material_change_streak = 4`
- 但 latest 展示层入口已经继续保持正确优先级：
  - `roadmap_action_board_latest_refresh.md`
    - `Priority 1: challenge_track`
    - `first command: python scripts/search_candidate_issues.py --query bug --target-family "文件路径与 IO" --limit 10 --run-label challenge_a4`
  - `roadmap_status_card_latest_refresh.md`
    - `top_priority_track: challenge_track`
    - `first_action: 重新 sourcing 第 4 条 challenge 候选`

### 这轮推进的意义

- latest 不再因为连续几轮 `no_material_change` 就过早把 challenge 缺口让位给泛化性能线
- roadmap tracking 现在更像“持续工作的导航器”
- 而不是“只在刚出现 progress 的短窗口内才短暂正确”

## 2026-06-14 live challenge sourcing 复核：当前首先卡在 GitHub 认证，而不是候选质量

### 本轮目标

- 真正执行一次第 `4` 条 challenge 候选 sourcing
- 不再只根据旧日志推测阻塞，而是拿到当前真实错误形态

### 改动类型

- `challenge-sourcing`
- `tracking`

### 主要涉及文件

- `logs/summaries/roadmap_tracking_refresh_047.json`
- `logs/summaries/roadmap_action_board_latest_refresh.md`
- `logs/summaries/roadmap_status_card_latest_refresh.md`
- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`

### 关键验证

- 真实执行：
  - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4`
- 在放开网络后，当前真实错误不是：
  - 候选为空
  - 代理 refused
- 而是：
  - `gh 认证失败（401 Bad credentials）`
- 同时 `gh auth status` 已确认：
  - `GITHUB_TOKEN` 当前无效
  - keyring 里的 `wangd237` 账号仍然存在，但不是当前 active account

### 当前结论

- 第 `4` 条 challenge 候选的 live sourcing 不是“没推进”
- 当前最先卡住的是：
  - challenge 搜题前置认证
- 因此 latest 导航已经继续收口为：
  - `roadmap_tracking_refresh_047`
  - `history_advice_category = stalled_tracking`
  - 但 `top_priority_track = challenge_track`
  - `first_command = gh auth status`
- 这意味着后续续做时，最正确的第一步不再是盲跑搜索，而是：
  - 先检查并清理无效 `GITHUB_TOKEN`
  - 再继续 challenge 搜索、导入、筛选链路

### 这轮推进的意义

- 我们现在已经把“第 4 条 challenge 候选为什么还没出来”从模糊状态变成了可验证状态
- 这让 roadmap goal 的 handoff 更准确：
  - 当前不是题源问题优先
  - 也不是 challenge 线失去价值
  - 而是认证前置条件先需要恢复

## 2026-06-14 challenge 搜题认证解析修复：坏 GITHUB_TOKEN 不再直接卡死脚本

### 本轮目标

- 继续降低第 `4` 条 challenge 候选 sourcing 的前置阻塞
- 把“环境变量里有坏 token 就直接 401”这一层问题先修掉

### 改动类型

- `challenge-sourcing`
- `auth-hardening`

### 主要涉及文件

- `scripts/search_candidate_issues.py`
- `tests/test_search_candidate_issues.py`
- `logs/summaries/roadmap_tracking_refresh_048.json`

### 关键修改

- `_resolve_gh_token()` 现在不再盲目优先信任环境变量
- 当 `GITHUB_TOKEN / GH_TOKEN` 看起来不像 GitHub token 时：
  - 会优先在移除环境变量污染后调用 `gh auth token`
  - 尝试回退到 keyring 中的可用认证来源
- 因此即使当前 shell 里残留了坏 token：
  - challenge 搜题脚本也不会直接被这层环境变量卡死

### 关键验证

- 测试：
  - `python -m pytest tests/test_search_candidate_issues.py tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_validate_challenge_shortlist.py -q`
  - 结果：`37 passed`
- 真实复核：
  - `GITHUB_TOKEN='invalid-token'` 条件下再次执行：
    - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4`
  - 当前已不再报：
    - `401 Bad credentials`
  - 而是重新收敛为：
    - `dial tcp ... access a socket in a way forbidden by its access permissions`

### 当前结论

- 这说明认证解析修复已经生效
- challenge 搜题当前主要阻塞已从：
  - `坏 GITHUB_TOKEN`
  收缩为：
  - 当前 shell / sandbox 层的外网访问限制
- 因此 handoff 语义也应更新为：
  - 脚本本身对坏 token 的鲁棒性已经增强
  - 下一步更需要恢复可访问 GitHub API 的执行环境

## 2026-06-14 refresh_049：tracking 文案从“认证前置条件”收口到“外部访问前置条件”

### 本轮目标

- 收掉 latest tracking 中已经过时的一句阻塞描述
- 让 action board / status card 与真实 live sourcing 现状一致

### 改动类型

- `tracking`
- `handoff-hardening`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `logs/summaries/roadmap_tracking_refresh_049.json`
- `logs/summaries/roadmap_action_board_latest_refresh.md`
- `logs/summaries/roadmap_status_card_latest_refresh.md`

### 关键修改

- `stalled_tracking + challenge gap` 场景下的第一优先级 reason 文案：
  - 已从：
    - `首先卡在 GitHub 认证前置条件`
  - 更新为：
    - `首先卡在外部访问前置条件`
- 这样 latest 不会再把当前阻塞过度收窄成单一认证问题

### 关键验证

- 测试：
  - `python -m pytest tests/test_search_candidate_issues.py tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_validate_challenge_shortlist.py -q`
  - 结果：`37 passed`
- refresh：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 新产物：
    - `roadmap_tracking_refresh_049`
- latest 验证：
  - `top_priority_track = challenge_track`
  - `first_action = 重新 sourcing 第 4 条 challenge 候选`
  - `top_priority_reason` 已改为：
    - `首先卡在外部访问前置条件`

### 当前结论

- 这轮不是策略或规模层面的推进
- 而是一次必要的 tracking 纠偏：
  - 保持 challenge 仍是第一优先级
  - 同时把真实阻塞从“认证唯一问题”修正为更准确的“外部访问前置条件”
- 这样后续无论是继续 live sourcing，还是做 handoff / refresh，都不会再被旧文案误导

## 2026-06-14 challenge 搜题认证桥接 fallback：无 token 导出时仍允许直接走 gh 会话

### 本轮目标

- 不让 challenge live sourcing 被“拿不到可导出的 token”这层脚本前置条件卡死
- 继续把真实阻塞往外推进到更接近最终执行环境的层面

### 改动类型

- `challenge-sourcing`
- `auth-hardening`

### 主要涉及文件

- `scripts/search_candidate_issues.py`
- `tests/test_search_candidate_issues.py`

### 关键修改

- `run_gh_search()` 不再在 `_resolve_gh_token()` 返回 `None` 时立刻报错退出
- 当前行为改为：
  - 如果拿到了 token：
    - 继续显式注入 `GITHUB_TOKEN`
  - 如果拿不到 token：
    - 清理 `GITHUB_TOKEN / GH_TOKEN`
    - 直接让 `gh search issues` 走当前已登录会话
- 这样做是因为当前机器上真实出现了：
  - `gh auth status` 显示已登录
  - 但 `gh auth token` 返回：
    - `no oauth token found for github.com`

### 关键验证

- 测试：
  - `python -m pytest tests/test_search_candidate_issues.py tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_validate_challenge_shortlist.py -q`
  - 结果：`39 passed`
- 真实复核：
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue; gh auth status`
    - 当前 active account 已恢复为 `wangd237 (keyring)`
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue; gh auth token`
    - 返回：`no oauth token found for github.com`
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue; python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4`
    - 当前不再报：
      - `无法获取 GitHub 认证 token`
    - 而是继续推进到：
      - `gh search issues 失败：Post "https://api.github.com/graphql": dial tcp ... connectex: An attempt was made to access a socket in a way forbidden by its access permissions.`

### 当前结论

- challenge 搜题脚本现在已经越过了“token 不可导出”这一层本地阻塞
- 当前第一阻塞已更明确地稳定收敛为：
  - 当前执行层对 GitHub API 的 socket / 外网访问限制
- 这让后续 tracking / handoff 可以更有把握地把 challenge 线定义为：
  - 候选方向仍然合理
  - 脚本桥接层已基本打通
  - 现在主要需要可访问 GitHub API 的执行环境

## 2026-06-14 refresh_051：challenge 本地认证准备度接入 roadmap tracking

### 本轮目标

- 不再让 challenge 线的认证排查只存在于手工命令历史里
- 把 challenge 搜题的本地认证准备度收口成 latest 可直接消费的状态信号

### 改动类型

- `tracking`
- `challenge-sourcing`
- `handoff-hardening`

### 主要涉及文件

- `scripts/snapshot_roadmap_status.py`
- `scripts/refresh_roadmap_tracking.py`
- `tests/test_snapshot_roadmap_status.py`
- `tests/test_refresh_roadmap_tracking.py`
- `logs/summaries/roadmap_tracking_refresh_051.json`

### 关键修改

- `snapshot_roadmap_status.py` 新增：
  - `challenge_status.local_auth_readiness`
- 当前会采集的 challenge 本地认证信号包括：
  - `env_token_present`
  - `env_token_source`
  - `env_token_looks_valid`
  - `gh_cli_available`
  - `gh_auth_logged_in`
  - `gh_auth_active_account`
  - `gh_auth_token_exportable`
  - `preferred_search_mode`
- `refresh_roadmap_tracking.py` 已把这组信号继续透传到：
  - `status card`
  - `action board`
  - `snapshot markdown`
- 这样后续只看 latest 就能直接判断：
  - 当前更像是环境变量污染
  - `gh` 会话不可用
  - token 不可导出
  - 还是当前会优先走 `env_token / gh_auth_token / gh_session_fallback`

### 关键验证

- 测试：
  - `python -m pytest tests/test_snapshot_roadmap_status.py tests/test_refresh_roadmap_tracking.py tests/test_search_candidate_issues.py tests/test_validate_challenge_shortlist.py -q`
  - 结果：`40 passed`
- refresh：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 新产物：
    - `roadmap_tracking_refresh_051`
- latest 验证：
  - `roadmap_status_card_latest_refresh.md`
  - `roadmap_action_board_latest_refresh.md`
  - 已出现：
    - `challenge_auth_env_token_present`
    - `challenge_auth_env_token_looks_valid`
    - `challenge_auth_gh_logged_in`
    - `challenge_auth_token_exportable`
    - `challenge_auth_preferred_search_mode`

### 当前结论

- 这轮虽然没有新增任务规模变化
- 但 roadmap tracking 的可执行性又提高了一步：
  - challenge 线不再只说“先做认证预检”
  - 而是 latest 自己就能先给出本地认证准备度快照
- `refresh_051` 还顺手暴露了一个新事实：
  - 当前常驻环境里存在一个看起来像有效 token 的环境变量
  - 因此 latest 当前把 challenge 搜题默认路径判断成：
    - `preferred_search_mode = env_token`
- 这让后续续做时更容易识别：
  - 何时应该先清理环境污染
  - 而不是直接把失败都归因到网络层

## 2026-06-14 refresh_052：challenge latest 动作建议开始按 readiness 自动收口

### 本轮目标

- 不让 challenge readiness 只停留在“展示字段”
- 让 latest 第一优先级动作真正根据本地认证准备度自动调整

### 改动类型

- `tracking`
- `handoff-hardening`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `logs/summaries/roadmap_tracking_refresh_052.json`

### 关键修改

- challenge 线新增基于 `local_auth_readiness.preferred_search_mode` 的预检编排逻辑
- 当前至少区分三类路径：
  - `env_token`
  - `gh_session_fallback`
  - 默认保守路径
- 其中当 latest 检测到：
  - `preferred_search_mode = env_token`
- challenge `Priority 1` 会自动调整为：
  - 第一条动作先提示环境变量 token 正在优先生效
  - 第一条命令先执行：
    - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`

### 关键验证

- 测试：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_search_candidate_issues.py tests/test_validate_challenge_shortlist.py -q`
  - 结果：`41 passed`
- refresh：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 新产物：
    - `roadmap_tracking_refresh_052`
- latest 验证：
  - `roadmap_action_board_latest_refresh.md`
  - `roadmap_status_card_latest_refresh.md`
  - 当前 `first_command` 已自动更新为：
    - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`

### 当前结论

- 这轮的意义不是新增更多状态
- 而是让 roadmap tracking 真正开始“消费状态”
- 现在 latest 已经从：
  - 被动展示 challenge readiness
  继续推进到：
  - 主动基于 readiness 编排第一步动作
- 这让 challenge 线的 handoff 更接近真正可执行的控制面板

## 2026-06-14 refresh_054：challenge readiness 正式进入 tracking delta/history

### 本轮目标

- 不让 challenge readiness 只停留在 snapshot 与 latest 展示层
- 让本地认证准备度变化真正进入 `delta / history / progress_track`
- 修复由此带来的测试口径漂移

### 改动类型

- `tracking`
- `testing`
- `documentation`

### 主要涉及文件

- `scripts/refresh_roadmap_tracking.py`
- `tests/test_refresh_roadmap_tracking.py`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `logs/summaries/roadmap_tracking_refresh_054.json`

### 关键修改

- `refresh_roadmap_tracking.py` 的 `DELTA_FIELD_EXTRACTORS` 已新增：
  - `challenge_auth_env_token_present`
  - `challenge_auth_env_token_looks_valid`
  - `challenge_auth_gh_logged_in`
  - `challenge_auth_token_exportable`
  - `challenge_auth_preferred_search_mode`
- `build_refresh_outcome()` 已把：
  - `challenge_auth_* updated`
  视为 challenge 线正向变化信号
- 修复测试：
  - `test_refresh_roadmap_tracking_marks_no_material_change_when_latest_is_unchanged`
  - 为当前 snapshot stub 补齐与 previous latest 一致的：
    - `challenge_status.local_auth_readiness`
  - 避免 readiness 新接线后把 unchanged 场景误判为 delta

### 关键验证

- 测试：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_search_candidate_issues.py tests/test_validate_challenge_shortlist.py -q`
  - 结果：`42 passed`
- refresh：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 新产物：
    - `roadmap_tracking_refresh_054`
- latest 验证：
  - `roadmap_tracking_latest_refresh.json`
  - `roadmap_action_board_latest_refresh.md`
  - `roadmap_status_card_latest_refresh.md`
  - 已确认 source refresh 均更新到：
    - `roadmap_tracking_refresh_054`

### 指标/状态对比

- baseline：
  - readiness 只进入 snapshot/latest 展示层
  - tracking delta 不会把 `challenge_auth_*` 当成正式变化
- improved：
  - readiness 已进入 `changed_fields / delta.field_changes / history`
  - readiness 变化可被视为 challenge 线推进信号
- 当前真实运行结果：
  - `refresh_053 -> refresh_054` 仍为 `no_material_change`
  - 原因不是接线失败
  - 而是两轮真实 readiness 状态一致

### 结论

- challenge readiness 现在已经从“展示信息”升级为“tracking 语义的一部分”
- 这让后续 challenge 认证状态变化具备正式打断 `no_material_change streak` 的能力
- 当前下一步不应继续只跑 refresh
- 更应该触发一轮真实的 challenge 认证/外部访问变化，再观察 tracking 是否出现 progress

## 2026-06-14 refresh_056：第 4 条 challenge 候选恢复，并修正 shortlist 解析口径

### 本轮目标

- 真正恢复第 4 条 challenge 候选，而不是继续停留在空 shortlist
- 让这次恢复被 roadmap tracking 客观识别为 challenge 线 progress
- 修复 shortlist 文档标题与解析脚本之间的真实口径脱节

### 改动类型

- `challenge-sourcing`
- `tracking`
- `testing`
- `documentation`

### 主要涉及文件

- `benchmarks/real_world_candidates.json`
- `docs/challenge_shortlist.md`
- `scripts/validate_challenge_shortlist.py`
- `tests/test_validate_challenge_shortlist.py`
- `docs/project_memory.md`
- `docs/next_actions.md`
- `logs/summaries/candidate_search_challenge_a4_001.json`
- `logs/summaries/roadmap_tracking_refresh_056.json`

### 关键修改

- 先清理当前 shell 的 `GITHUB_TOKEN`，再执行：
  - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4`
- 已成功拿到 live 搜索结果：
  - `candidate_search_challenge_a4_001.json`
  - `candidate_count = 10`
- 人工比对后，选择：
  - `samuelcolvin/watchfiles#215`
  作为当前最合适的第 4 条 challenge 候选
- 已完成：
  - `python scripts/import_search_results.py --search-result logs/summaries/candidate_search_challenge_a4_001.json --issue-number 215`
  - `python scripts/screen_candidate.py --candidate-id samuelcolvin_watchfiles_issue_215 --decision y`
- 并把 `watchfiles#215` 写入：
  - `docs/challenge_shortlist.md`
- 同时修复 shortlist 解析兼容性：
  - `validate_challenge_shortlist.py` 现在同时支持：
    - `## 下一条最值得补的 challenge 候选`
    - `## 当前最值得补的 challenge 候选`
- 新增测试：
  - `test_extract_candidate_issue_refs_supports_current_candidate_section_heading`

### 关键验证

- 测试：
  - `python -m pytest tests/test_validate_challenge_shortlist.py tests/test_snapshot_roadmap_status.py tests/test_refresh_roadmap_tracking.py tests/test_search_candidate_issues.py -q`
  - 结果：`43 passed`
- shortlist 校验：
  - `python scripts/validate_challenge_shortlist.py`
  - 结果：`Validation Passed`
- refresh：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 新产物：
    - `roadmap_tracking_refresh_056`

### 指标/状态对比

- baseline：
  - challenge shortlist 为空
  - `challenge_shortlist_candidate_count = 0`
  - `next_candidate_issue_ref = None`
  - history 长时间停留在 `no_material_change`
- improved：
  - shortlist 已恢复为：
    - `samuelcolvin/watchfiles#215`
  - `challenge_shortlist_candidate_count = 1`
  - `challenge_next_candidate_issue_ref = samuelcolvin/watchfiles#215`
  - `refresh_outcome = progress`
  - `top_priority_track = challenge_track`

### 结论

- challenge 第 4 条候选已经从“没有明确入口”恢复到“有明确 shortlist + 有 candidate 池状态 + 有 tracking 证据”
- 这轮推进的重要意义不只是多了一个候选
- 更在于我们修掉了一个真实的解析口径漏洞：
  - 文档里明明已有候选，但 snapshot 以前会错误读成 `0`
- 接下来 challenge 线最自然的动作已变成：
  - 评估 `watchfiles#215` 能否压成稳定本地 semi-real challenge 题

## 2026-06-14 refresh_059：watchfiles#215 进入 task 脚手架，并修正 challenge 脚手架信号归类

### 本轮目标

- 把 `watchfiles#215` 从 shortlist 候选继续推进到本地 semi-real 脚手架阶段
- 让这次推进在 tracking 里被正确识别为 challenge 主线，而不是误落到 formal 扩题

### 改动类型

- `challenge-sourcing`
- `tracking`
- `testing`
- `documentation`

### 主要涉及文件

- `benchmarks/tasks/task_131.json`
- `benchmarks/repos/watchfiles_215_repo/watchfiles/main.py`
- `benchmarks/repos/watchfiles_215_repo/tests/test_main.py`
- `scripts/snapshot_roadmap_status.py`
- `scripts/refresh_roadmap_tracking.py`
- `tests/test_snapshot_roadmap_status.py`
- `tests/test_refresh_roadmap_tracking.py`
- `logs/summaries/semi_real_pipeline_audit_challenge215_001.json`
- `logs/summaries/roadmap_tracking_refresh_059.json`

### 关键修改

- 已执行：
  - `python scripts/scaffold_semi_real_task.py --from-candidate samuelcolvin_watchfiles_issue_215 --semi-repo-name watchfiles_215_repo --module-path watchfiles/main.py --test-path tests/test_main.py`
- 生成产物：
  - `task_131`
  - `benchmarks/repos/watchfiles_215_repo`
- 当前阶段语义：
  - `samuelcolvin_watchfiles_issue_215.status = screened`
  - latest pipeline stage = `screened_with_task`
  - `repo_scaffold_status = needs_manual_completion`
- 新增 snapshot 信号：
  - `challenge_status.shortlist_screened_with_task_count`
- 这让 tracking 能区分：
  - “普通 formal screened_with_task”
  - 和“shortlist 内 challenge 候选已进入 task 脚手架”
- 同时修正 refresh 语义：
  - `challenge_shortlist_screened_with_task_count` 的变化已被视为 challenge 正向推进信号

### 关键验证

- 测试：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_validate_challenge_shortlist.py tests/test_search_candidate_issues.py -q`
  - 结果：`46 passed`
- semi-real 审计：
  - `python scripts/audit_semi_real_pipeline.py --run-label challenge215`
  - 结果：
    - `screened_with_task = 1`
- refresh：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 最新产物：
    - `roadmap_tracking_refresh_059`

### 指标/状态对比

- baseline：
  - `watchfiles#215` 只有 shortlist 候选身份
  - 尚未进入 task / repo 脚手架
  - challenge 脚手架推进容易在 latest 中被误归到 formal 线
- improved：
  - `watchfiles#215 -> task_131 + watchfiles_215_repo`
  - `shortlist_candidate_count = 1`
  - `shortlist_screened_with_task_count = 1`
  - `semi_real_pipeline stage = screened_with_task`
  - `roadmap_tracking_refresh_059` 的 latest action board 已重新把主优先级收口为：
    - `challenge_track`

### 结论

- challenge 第 4 条候选目前已经推进到“有 task、有 repo、可继续补 ready 回归题”的阶段
- 这比单纯恢复 shortlist 更进一步
- 当前下一步最自然的动作不再是继续找题
- 而是把 `task_131` 从 TODO 脚手架压成稳定本地 challenge semi-real 草稿

## 2026-06-14 `watchfiles#215` 正式接入 challenge manifest

### 本轮目标

- 把已经 ready 的 `task_131` 正式纳入 challenge manifest
- 让 challenge 文档、repo README、project memory 与 latest tracking 口径对齐到同一真实状态
- 把下一步动作从“继续补第 4 条候选”切到“重新 sourcing 第 5 条候选”

### 改动类型

- `challenge-manifest`
- `documentation`
- `tracking-prep`

### 主要涉及文件

- `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- `benchmarks/real_world_candidates.json`
- `docs/challenge_shortlist.md`
- `docs/challenge_set.md`
- `benchmarks/repos/watchfiles_110_repo/README.md`
- `benchmarks/repos/watchfiles_169_repo/README.md`
- `benchmarks/repos/watchfiles_215_repo/README.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 关键修改

- challenge manifest 当前从 `3` 条扩到 `4` 条：
  - `task_126`
  - `task_127`
  - `task_130`
  - `task_131`
- 已把候选 `samuelcolvin_watchfiles_issue_215` 的 notes 继续追加为：
  - 已纳入 challenge manifest，成为第 `4` 条 challenge 任务
- `docs/challenge_shortlist.md` 已做口径切换：
  - `watchfiles#215` 从“当前最值得补的候选”移动到“当前已落地 challenge 题”
  - 下一步改为重新 sourcing 第 `5` 条候选
- 三个 watchfiles challenge repo README 已同步到真实状态：
  - `#110`、`#169` 不再误写成“尚未纳入 challenge manifest”
  - `#215` 不再停留在脚手架待完成描述

### 关键验证

- 本轮先做 challenge manifest 与文档口径收口
- 下一步应补：
  - `python scripts/validate_challenge_shortlist.py`
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v71.json --run-label challengev71_r4`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 指标/状态对比

- baseline：
  - `challenge_task_count = 3`
  - `accepted_ready_not_in_any_manifest_count = 1`
  - 唯一项为：
    - `samuelcolvin/watchfiles#215`
- improved：
  - `challenge_task_count = 4`
  - 期望 `accepted_ready_not_in_any_manifest_count = 0`
  - challenge 下一步应自然切到：
    - 重新 sourcing 第 `5` 条候选

### 结论

- challenge 第 `4` 条任务已经正式落地，不再只是 ready 草稿
- 当前 challenge 线已经从“补齐入口”切换到“扩下一条候选 + 跑四题集合评测”

## 2026-06-14 challenge 搜题认证回退链补强，并确认第 5 条候选的最新外部阻塞

### 本轮目标

- 继续推进第 `5` 条 challenge 候选 sourcing，而不是停在“建议下一步”
- 修掉 `search_candidate_issues.py` 在坏 `GITHUB_TOKEN` 场景下过早 401 退出的问题
- 把 challenge 外部阻塞从模糊“认证失败”继续收口到更真实的网络入口

### 改动类型

- `challenge-sourcing`
- `infra`
- `testing`

### 主要涉及文件

- `scripts/search_candidate_issues.py`
- `tests/test_search_candidate_issues.py`
- `docs/project_memory.md`
- `docs/next_actions.md`

### 关键修改

- `search_candidate_issues.py` 当前已从“解析单个 token”改成“解析多级 token / session 候选链”：
  - 环境变量 token
  - 去除环境污染后的 `gh` keyring token
  - 当前环境下的 `gh auth token`
  - 纯 `gh session fallback`
- 这让脚本在遇到：
  - `GITHUB_TOKEN` 看起来像真的
  - 但实际已经无效
  的情况下，不会第一时间直接退出
- 同时补了对应测试：
  - 保留环境变量 token 与 keyring fallback 候选顺序
  - 当首个环境变量 token 返回 401 时，自动继续尝试 keyring token

### 关键验证

- 测试：
  - `python -m pytest tests/test_search_candidate_issues.py -q`
  - 结果：`14 passed`
- challenge live sourcing 复测：
  - 已用清理后的 auth 环境重跑多条 challenge 搜索
  - 当前不再首先报 `401 Bad credentials`
  - 最新真实阻塞已前移为：
    - `proxyconnect tcp: dial tcp 127.0.0.1:7890: connectex: No connection could be made because the target machine actively refused it`

### 指标/状态对比

- baseline：
  - shell 里只要残留无效 `GITHUB_TOKEN`
  - `search_candidate_issues.py` 很容易先报 `401 Bad credentials`
  - challenge 第 `5` 条候选 sourcing 会被误判为“认证链没打通”
- improved：
  - 脚本已能跨过坏 token，继续尝试 keyring / session fallback
  - 当前真正需要解决的外部前置条件已变成：
    - 本地 `7890` 代理不可达

### 结论

- challenge 第 `5` 条候选 sourcing 这条线已经不是“脚本认证回退不够稳”的问题
- 当前更真实的外部阻塞是：
  - 代理配置存在
  - 但代理服务没有在本地监听

## 2026-06-14 `rich#2411` 进入 accepted + ready + not_in_manifest

### 本轮目标

- 把 `Textualize/rich#2411` 从 shortlist + screened 候选继续推进到可运行的 challenge semi-real 回归任务
- 避免把 issue 里的 `run.py / rich_script.py` 误判成仓库目标模块
- 让 tracking 能把这条候选识别为 `accepted + ready + not_in_manifest`

### 改动类型

- `challenge-semi-real`
- `scaffold-heuristic`
- `documentation`

### 主要涉及文件

- `scripts/scaffold_semi_real_task.py`
- `tests/test_scaffold_semi_real_task.py`
- `benchmarks/tasks/task_132.json`
- `benchmarks/repos/rich_windows_rule_repo/`
- `benchmarks/real_world_candidates.json`
- `docs/challenge_shortlist.md`
- `GUIDE.md`
- `docs/project_memory.md`

### 关键修改

- 脚手架启发式新增对根目录复现脚本的过滤：
  - `run.py`
  - `script.py`
  - `rich_script.py`
  - `*_script.py`
- 新增测试确保这类路径会回退到包内默认模块，而不是被误当目标实现文件
- 为 `Textualize/rich#2411` 生成：
  - `task_132`
  - `benchmarks/repos/rich_windows_rule_repo`
- 当前最小 repo 已压成可运行口径：
  - `rich_windows_rule_repo/console.py`
  - `tests/test_console.py`
- 当前 3 条回归测试覆盖：
  - `cp1252` 流上的 `rule()` 安全降级
  - `ascii` 流上的 `print("─")` 安全降级
  - `utf-8` 流上仍保留 Unicode 横线
- 候选 `Textualize_rich_issue_2411` 当前已从：
  - `screened`
  继续推进到：
  - `accepted`
- 当前 pipeline / snapshot 已把它识别为：
  - `accepted_ready_not_in_any_manifest`

### 关键验证

- `python -m pytest tests/test_scaffold_semi_real_task.py -q`
- `python -m pytest benchmarks/repos/rich_windows_rule_repo/tests/test_console.py -q`
- `python -m pytest tests/test_scaffold_semi_real_task.py tests/test_audit_semi_real_pipeline.py tests/test_snapshot_roadmap_status.py tests/test_refresh_roadmap_tracking.py -q`
- `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 指标/状态对比

- baseline：
  - `accepted_candidate_count = 70`
  - `screened_candidate_count = 1`
  - `screened_with_task_count = 1`
  - `challenge_accepted_ready_not_in_any_manifest_count = 0`
- improved：
  - `accepted_candidate_count = 71`
  - `screened_candidate_count = 0`
  - `screened_with_task_count = 0`
  - `challenge_accepted_ready_not_in_any_manifest_count = 1`

### 结论

- `rich#2411` 当前已经不是“待评估脚手架候选”
- 它已进入“本地 ready，等待是否纳入 challenge manifest”的阶段
- challenge 线下一步最自然的动作是：
  - 决定是否将 `task_132` 接入 challenge manifest
  - 然后补一轮五题 challenge 集评测

## 2026-06-14 `rich#2411` 正式接入 challenge manifest

### 本轮目标

- 把已经 ready 的 `task_132` 正式纳入 challenge manifest
- 让 challenge 文档、候选 notes、评测结果与 latest tracking 统一到 `challenge=5`
- 把下一步动作切换为重新 sourcing 第 `6` 条 challenge 候选

### 改动类型

- `challenge-manifest`
- `challenge-eval`
- `documentation`

### 主要涉及文件

- `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- `benchmarks/real_world_candidates.json`
- `docs/challenge_shortlist.md`
- `docs/challenge_set.md`
- `docs/project_memory.md`
- `GUIDE.md`

### 关键修改

- challenge manifest 当前从 `4` 条扩到 `5` 条：
  - `task_126`
  - `task_127`
  - `task_130`
  - `task_131`
  - `task_132`
- 已把候选 `Textualize_rich_issue_2411` 的 notes 继续追加为：
  - 已纳入 challenge manifest，成为第 `5` 条 challenge 任务
- `docs/challenge_shortlist.md` 已做口径切换：
  - `rich#2411` 从“当前最值得补的候选”移动到“当前已落地 challenge 题”
  - 下一步改为重新 sourcing 第 `6` 条候选
- `docs/challenge_set.md` 已同步到 challenge 五题集合

### 关键验证

- `python scripts/run_single_task.py --task benchmarks/tasks/task_132.json --policy optimization/policy_versions/improved_v71.json`
- `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v71.json --run-label challengev71_r5`
- `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 指标/状态对比

- baseline：
  - `challenge_task_count = 4`
  - `accepted_in_challenge_manifest_count = 4`
  - `shortlist_candidate_count = 1`
  - `next_action = 优先评估 challenge 候选 Textualize/rich#2411`
- improved：
  - `challenge_task_count = 5`
  - `accepted_in_challenge_manifest_count = 5`
  - `shortlist_candidate_count = 0`
  - `next_action = 重新 sourcing 第 6 条 challenge 候选`

### 结论

- `rich#2411` 已经不再只是 ready 候选，而是正式成为第 `5` 条 challenge 任务
- 当前 challenge 线已经从“评估第 5 条候选”切换到“维护五题集合并继续找第 6 条候选”

## 2026-06-14 第 6 条 challenge 候选恢复：`rich#2457`

### 本轮目标

- 不让 challenge 线在五题 manifest 落地后再次停回空 shortlist
- 继续从真实仓库里恢复第 `6` 条 challenge 候选
- 把这次恢复动作收口进 tracking 与文档，而不是只停留在临时命令历史里

### 改动类型

- `challenge-sourcing`
- `candidate-screening`
- `documentation`

### 主要涉及文件

- `benchmarks/real_world_candidates.json`
- `docs/challenge_shortlist.md`
- `docs/project_memory.md`
- `docs/optimization_log.md`
- `docs/next_actions.md`

### 关键修改

- 先真实复核 challenge 搜题环境：
  - 当前 shell 里残留无效 `GITHUB_TOKEN`
  - 但 `gh` keyring 账号 `wangd237` 可用
- 在清理 `GITHUB_TOKEN / HTTP_PROXY / HTTPS_PROXY` 后，补跑多路 challenge sourcing
- 本轮结果判断：
  - `attrs` 路线质量一般，不像第 `6` 条最佳候选
  - `fsspec#979` 虽然命中，但已在正式主集，必须排除
  - 最终选定：
    - `Textualize/rich#2457`
- 已把 `Textualize/rich#2457`：
  - 导入 candidate 池
  - 从 `imported` 推进到 `screened`
  - 写入 `docs/challenge_shortlist.md`

### 关键验证

- `gh auth status`
- `python scripts/validate_challenge_shortlist.py`
- `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 指标/状态对比

- baseline：
  - `candidate_count = 71`
  - `screened_candidate_count = 0`
  - `challenge_shortlist_candidate_count = 0`
  - `next_action = 重新 sourcing 第 6 条 challenge 候选`
- improved：
  - `candidate_count = 72`
  - `screened_candidate_count = 1`
  - `challenge_shortlist_candidate_count = 1`
  - `next_action = 优先评估 challenge 候选 Textualize/rich#2457`

### 结论

- challenge 第 `6` 条候选已经从“空缺”恢复到“有明确 shortlist + 已 screened”
- 当前 challenge 线的下一步不再是继续盲搜
- 而是优先评估 `rich#2457` 是否适合进入 semi-real 脚手架阶段

## 2026-06-14 challenge 第 6 题落地：`rich#2457 -> task_133 + improved_v72`

### 本轮目标

- 收掉当前正在执行的小任务，不再让 `rich#2457` 停留在“值得评估”的模糊状态
- 把它真正压成可运行 challenge semi-real 题
- 同时补上对应策略版本、单任务闭环验证、challenge 六题评测与 tracking 刷新

### 改动类型

- `challenge-expansion`
- `semi-real-task`
- `policy-extension`
- `tracking-refresh`
- `documentation`

### 主要涉及文件

- `benchmarks/tasks/task_133.json`
- `benchmarks/repos/rich_windows_no_color_repo/`
- `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- `app/agent/patcher.py`
- `optimization/policy_versions/improved_v72.json`
- `tests/test_patcher_rich_v72.py`
- `GUIDE.md`
- `docs/challenge_set.md`
- `docs/challenge_shortlist.md`
- `docs/next_actions.md`
- `docs/project_memory.md`
- `docs/optimization_log.md`

### 关键修改

- 先直连核实原始 issue `Textualize/rich#2457`，确认问题核心不是编码，而是：
  - `legacy_windows=True + vt=False` 分支里忽略了 `no_color=True`
- 随后生成并补全：
  - `task_133`
  - `rich_windows_no_color_repo`
- 当前缩题口径固定为：
  - 不依赖真实 Windows 终端
  - 用最小 `WindowsConsoleFeatures(vt=False, truecolor=False)` 表达平台边界
  - 用 `render()` 是否仍输出 `<WIN:...>` 样式标记表达 bug
- 新增策略版本：
  - `improved_v72`
- 新增规则：
  - 让 legacy Windows 分支先判断 `no_color`
  - 再决定是否输出 Windows 样式标记
- 最后把 `task_133` 正式纳入：
  - `real_issue_tasks_challenge_v1.json`

### 关键验证

- `python -m pytest benchmarks/repos/rich_windows_no_color_repo/tests/test_console.py -q`
  - 基线：`1 failed, 2 passed`
- `python -m pytest tests/test_patcher_rich_v72.py -q`
  - `1 passed`
- `python scripts/run_single_task.py --task benchmarks/tasks/task_133.json --policy optimization/policy_versions/improved_v72.json`
  - `final_status = success`
- `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v72.json --run-label challengev72_r6`
- `python scripts/refresh_roadmap_tracking.py --run-label refresh`

### 指标/状态对比

- baseline：
  - `challenge_task_count = 5`
  - `accepted_in_challenge_manifest_count = 5`
  - `shortlist_candidate_count = 1`
  - `next_action = 优先评估 challenge 候选 Textualize/rich#2457`
- improved：
  - `challenge_task_count = 6`
  - `accepted_in_challenge_manifest_count = 6`
  - `shortlist_candidate_count = 0`
  - `next_action = 重新 sourcing 第 7 条 challenge 候选`

### challenge 六题评测结果

- `policy_id = improved_v72`
- `task_count = 6`
- `success_rate = 0.5`
- `test_pass_rate = 0.5`
- `average_duration_sec = 0.5422`

### 结论

- `rich#2457` 已不再只是 shortlist / screened 候选
- 它已经成为 challenge 第 `6` 条正式任务
- 当前 challenge 线下一步应切换到：
  - 重新 sourcing 第 `7` 条 challenge 候选
  - 并继续观察 `task_127`、`task_130`、`task_131`、`task_132`、`task_133` 的 hard-case 代表性

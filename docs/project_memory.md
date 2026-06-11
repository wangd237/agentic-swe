# 项目记忆卡

本文件用于在新会话或长间隔续做时，快速恢复项目上下文。

目标不是替代完整文档，而是提供一个高密度、低冗余的冷启动入口。

## 当前阶段

- 当前阶段：`Phase 6 - 优化系统`
- 当前最新策略：`improved_v33`
- 当前主分支最近重要能力：
  - 已完成 `30` 条真实 issue 派生 `semi_real` 正式任务
  - 已在 `frozen_20` 上补齐一轮 `improved_v32 -> improved_v33` 无回归验证
  - 已在正式 `30` 条真实任务集上补齐 `improved_v32 -> improved_v33` 全量验证
  - 已把当前高优先级 `to_review` 候选池清零
  - 已新增批量 issue 导入入口 `scripts/import_issue_batch.py`
  - 已新增时延回归分析入口 `scripts/analyze_duration_regressions.py`
  - 已新增 trace 热点分析入口 `scripts/analyze_trace_hotspots.py`
  - 已新增单任务历史时延分析入口 `scripts/analyze_task_history.py`
  - 已新增热点任务集合历史分析入口 `scripts/analyze_task_history_cohort.py`
  - 已新增 `run_tests` 模式基准入口 `scripts/benchmark_run_tests_modes.py`
  - 已新增 `run_tests` 模式 cohort 汇总入口 `scripts/analyze_run_tests_mode_cohort.py`
  - 已新增 `pytest` 分阶段基准入口 `scripts/benchmark_pytest_phases.py`
  - 已新增 `pytest` 分阶段 cohort 汇总入口 `scripts/analyze_pytest_phase_cohort.py`
  - 已新增 `pytest importtime` 基准入口 `scripts/benchmark_pytest_importtime.py`
  - 已新增 `pytest importtime` cohort 汇总入口 `scripts/analyze_pytest_importtime_cohort.py`
  - 已新增 `pytest` 插件变体基准入口 `scripts/benchmark_pytest_plugin_variants.py`
  - 已新增 `pytest` 插件变体 cohort 汇总入口 `scripts/analyze_pytest_plugin_variant_cohort.py`
  - 已让新 trace 记录显式步骤耗时
  - 已形成追加式优化记录、候选池维护和 GitHub 推送节奏

## 当前核心链路

项目当前已经稳定具备这条主线：

`Task -> Agent Run -> Logging -> Evaluation -> Optimization -> Re-run`

对应入口：

- 单任务运行：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_001.json`
- 批量运行：
  - `python scripts/run_batch.py`
- 真实 issue 任务集流水线：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v33.json --run-label realissuev33`
- 候选批量导入：
  - `python scripts/import_issue_batch.py --input benchmarks/example_issue_batch.txt`
- 时延回归分析：
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev31_001.json --improved-batch-summary logs/summaries/batch_run_realissuev32_001.json --run-label realissuev32`
- trace 热点分析：
  - `python scripts/analyze_trace_hotspots.py --baseline-batch-summary logs/summaries/batch_run_realissuev31_001.json --improved-batch-summary logs/summaries/batch_run_realissuev32_001.json --run-label realissuev32`
- 单任务历史时延分析：
  - `python scripts/analyze_task_history.py --task-dir logs/trajectories/task_040 --output-dir logs/summaries`
- 热点任务集合历史分析：
  - `python scripts/analyze_task_history_cohort.py --task-id task_034 --task-id task_036 --task-id task_038 --task-id task_040 --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

## 当前正式任务规模

- 正式 `semi_real` 真实 issue 任务数：`30`
- 当前正式任务来源生态数：`13`
- 当前正式 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`
- 当前冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`
- 当前最大 frozen 集合：`20`

## 当前候选池状态

- `accepted = 30`
- `drafted = 0`
- `to_review = 0`
- 当前 accepted 候选已基本全部转成正式任务，下一阶段扩容主要依赖新增候选来源

候选来源文件：

- `benchmarks/real_world_candidates.json`

## 最新评测结论

### 1. 最新扩容对比

- 对比：`improved_v31 -> improved_v32`
- 任务集：`29 -> 30` 条
- 结果：
  - `success_count: 29 -> 30`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_steps: 9.3448 -> 9.3`
  - `average_duration_sec: 0.6115 -> 0.6778`

说明：

- 这组结果证明我们已经把正式真实任务集稳定扩容到 `30` 条
- 扩容后依旧保持 `100%` 成功率和 `100%` 测试通过率
- 这一组仍属于扩容对比，步数继续改善，但耗时继续回升，已经值得单独跟踪

### 2. 当前最新冻结同集合证据

- 对比：`improved_v32 -> improved_v33`
- 任务集：固定 `20` 条
- 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_steps: 9.25 -> 10.25`
  - `average_duration_sec: 0.6774 -> 0.5379`

说明：

- 这是当前最新的一轮 `frozen_20` 无回归验证
- 说明新增 `pytest_additional_flags` 注入口和 `-p no:unraisableexception` 没有破坏已有 `20` 条固定任务
- 这一轮不仅无回归，而且平均耗时出现了显著回落

### 3. 当前最新正式集证据

- 对比：`improved_v32 -> improved_v33`
- 任务集：固定正式 `30` 条
- 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_steps: 9.3 -> 10.3`
  - `average_duration_sec: 0.6778 -> 0.5423`

说明：

- 这说明 `improved_v33` 的收益并没有停留在热点样本或 `frozen_20`
- 在正式 `30` 条真实任务集上，它同样保持了 `100%` 成功率和 `100%` 测试通过率
- 因此它已经可以作为后续扩容到 `60+` 与构建 `frozen_40` 的候选基线

### 4. 最新时延分析结论

- 扩容集分析：
  - `logs/summaries/duration_compare_realissuev32_001.json`
  - 公共 `29` 条任务平均耗时：`0.6115 -> 0.6767`
  - 平均差值：`+0.0652s`
- `frozen_20` 分析：
  - `logs/summaries/duration_compare_frozen20v33_001.json`
  - 公共 `20` 条任务平均耗时：`0.6774 -> 0.5379`
  - 平均差值：`-0.1395s`
- 正式 `30` 条任务集分析：
  - `logs/summaries/duration_compare_realissuev33_001.json`
  - 公共 `30` 条任务平均耗时：`0.6778 -> 0.5423`
  - 平均差值：`-0.1355s`
- trace 热点分析：
  - `logs/summaries/trace_hotspots_realissuev32_001.json`
  - `logs/summaries/trace_hotspots_frozen20v33_001.json`
  - `logs/summaries/trace_hotspots_realissuev33_001.json`
  - 三组分析都指向 `run_tests` 是最主要的时延杠杆点
  - 扩容集上的 `run_tests` 总耗时增量约 `+1.5149s`
  - `frozen_20` 上 `improved_v32 -> improved_v33` 的 `run_tests` 总耗时变化约 `-2.5941s`
  - 正式 `30` 条任务集上 `improved_v32 -> improved_v33` 的 `run_tests` 总耗时变化约 `-3.6001s`
- 单任务历史分析：
  - `logs/summaries/task_history_task_040_003.json`
  - `task_040` 在 `improved_v31 -> improved_v32` 的历史平均耗时：`0.6213 -> 0.8171`
  - 平均增量：`+0.1958s`
  - 其中 `run_tests` 平均增量：`+0.2032s`
  - `improved_v32` 的已观测 `run_tests_subprocess` 平均值是 `0.5296`
  - 由于旧 trace 没有该字段，当前不能直接计算跨版本 `run_tests_subprocess` delta
- 热点任务集合历史分析：
  - `logs/summaries/task_history_cohort_run_tests_hotspots_v32_001.json`
  - 覆盖任务：`task_034 / task_036 / task_038 / task_040`
  - 平均历史耗时增量：`+0.1732s`
  - 平均 `run_tests` 历史耗时增量：`+0.1665s`
  - `4 / 4` 个热点任务都呈现正向回升
- `run_tests` 模式基准分析：
  - `logs/summaries/run_tests_modes_cohort_run_tests_hotspots_v32_001.json`
  - `average_persistent_run_tests_delta_sec = -0.0068`
  - `average_fresh_run_tests_delta_sec = -0.0091`
  - `average_persistent_combined_delta_sec = -0.0059`
  - `average_fresh_combined_delta_sec = -0.0068`
  - `average_fresh_copy_duration_sec = 0.0023`
  - `fresh_slower_than_source_task_count = 2`
  - `persistent_slower_than_source_task_count = 2`
- `pytest` 分阶段基准分析：
  - `logs/summaries/pytest_phases_cohort_run_tests_hotspots_v32_001.json`
  - `average_pytest_startup_over_python_sec = 0.1322`
  - `average_collect_over_pytest_startup_sec = 0.0797`
  - `average_full_over_collect_sec = 0.0159`
  - `average_collect_first_minus_repeated_sec = 0.0132`
  - `average_full_first_minus_repeated_sec = -0.0065`
- `pytest importtime` 基准分析：
  - `logs/summaries/pytest_importtime_cohort_run_tests_hotspots_v32_002.json`
  - `average_collect_wall_delta_sec = 0.0697`
  - `average_collect_import_self_delta_us = 20898`
  - `average_collect_unique_module_delta = 37`
  - 高频新增模块：`_ctypes`、`pyexpat`、`xml.etree.ElementTree`、`_pytest.skipping`、`ctypes.wintypes`
- `pytest` 插件变体基准分析：
  - `logs/summaries/pytest_plugin_variants_cohort_run_tests_hotspots_v32_004.json`
  - `unraisableexception_only`：`avg_wall_delta = -0.0282`
  - `debugging_only`：`avg_wall_delta = -0.0104`
  - `threadexception_only`：`avg_wall_delta = 0.0059`
  - `debug_exception_plugins`：`avg_wall_delta = -0.0346`
  - `minimal_safe_plugins`：`avg_wall_delta = -0.0496`
  - `minimal_safe_plugins`：`avg_import_delta_us = -17930`
  - `minimal_safe_plugins`：`avg_module_delta = -22`
  - `_001` 样本已确认受命令拼接 bug 污染，后续应以 `_002 / _003` 为准
- `pytest importtime` 分组分析：
  - `logs/summaries/pytest_import_groups_run_tests_hotspots_v32_002.json`
  - `pytest_optional_plugins`：`avg_self_us = 6181`
  - `windows_ctypes`：`avg_self_us = 5103`
  - `xml_stack`：`avg_self_us = 4026`
  - `terminal_chain`：`avg_self_us = 3653`
  - `debugging_chain`：`avg_self_us = 2094`
  - `other` 已经压到 `0`

说明：

- 这说明最近一轮时延回升并不只是 `task_061` 新增导致
- 当前更像是公共任务执行路径本身整体变慢
- 时延回升最明显的任务集中在：`task_040`、`task_038`、`task_036`、`task_034`
- workspace copy 的额外成本只有毫秒级，且三种运行模式没有呈现稳定的“workspace 更慢”趋势
- 当前最可信的方向已经进一步收窄到 pytest 命令执行链本身，而不是工作副本复制
- 在 pytest 命令执行链内部，主要耗时又进一步集中在启动与 collection，而不是 full run 本体
- 在 collection 内部，又已经能看到稳定新增的 import 链与模块集合，不再只是笼统的“collection 变慢”
- 新增的插件变体实验给出了一个很有价值的负结论：
  - `unraisableexception_only` 单独就能稳定减少约 `28.2ms`
  - `debugging_only` 只有小到中等收益
  - `threadexception_only` 基本没有帮助，甚至轻微变慢
  - `minimal_safe_plugins` 整体能稳定减少约 `49.6ms` 和 `22` 个模块
  - 当前最该继续下钻的是 `unraisableexception` 与剩余轻量 optional plugins 的组合边界
- runtime 已新增 policy 级 `pytest_additional_flags` 注入口：
  - `app/agent/policy.py`
  - `app/tools/run_tests.py`
  - `app/runtime/task_runner.py`
  - 已新增 `improved_v33`，先用 `-p no:unraisableexception` 做低风险 runtime 验证
- `improved_v33` 小集合验证：
  - `logs/summaries/duration_compare_hotspotsv33_001.json`
  - 热点 `4` 任务公共平均耗时：`0.5589 -> 0.5569`
  - `common_average_delta_sec = -0.002`
- `improved_v33` `frozen_20` 验证：
  - `logs/summaries/batch_eval_frozen20v33_001.json`
  - `logs/summaries/batch_compare_frozen20_step12_001.json`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6774 -> 0.5379`
  - `run_tests` 总耗时下降：`-2.5941s`
- `improved_v33` 正式 `30` 条任务集验证：
  - `logs/summaries/batch_eval_realissuev33_001.json`
  - `logs/summaries/batch_compare_realissue_step13_002.json`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.6778 -> 0.5423`
  - `run_tests` 总耗时下降：`-3.6001s`
- maturity 审计结果：
  - `logs/summaries/benchmark_maturity_maturity_002.json`
  - 正式任务数：`30 / 60`
  - 来源生态数：`13 / 6`
  - frozen 集合：`20 / 40`
  - `frozen_40` 连续版本：`0 / 5`
- 新增的 import 分组分析又进一步说明：
  - 这些新增模块几乎都能归到明确链路，不再存在一大块难以解释的 `other`
  - 当前更值得优先切分的是 `pytest_optional_plugins`、`windows_ctypes`、`xml_stack` 和 `terminal_chain`
  - 其中 `pytest_optional_plugins` 已经和新的 plugin variants `_002` 结果形成互相印证

## 最新新增任务

- `task_043`
  - 类型：`real_issue`
  - 来源：`dateutil/dateutil#384`
- `task_044`
  - 类型：`semi_real`
  - repo：`dateutil_month_year_repo`
  - 首个通过版本：`improved_v21`
  - 缺陷类型：`MM.YYYY` 月年格式解析
- `task_045`
  - 类型：`real_issue`
  - 来源：`python-jsonschema/jsonschema#1162`
- `task_046`
  - 类型：`semi_real`
  - repo：`jsonschema_single_label_hostname_repo`
  - 首个通过版本：`improved_v22`
  - 缺陷类型：single-label hostname 合法性判定
- `task_047`
  - 类型：`real_issue`
  - 来源：`pypa/packaging#810`
- `task_048`
  - 类型：`semi_real`
  - repo：`packaging_specifier_repo`
  - 首个通过版本：`improved_v23`
  - 缺陷类型：`Specifier >` 在 `dev+local` 场景下的版本比较
- `task_049`
  - 类型：`real_issue`
  - 来源：`dateutil/dateutil#1191`
- `task_050`
  - 类型：`semi_real`
  - repo：`dateutil_attached_comma_repo`
  - 首个通过版本：`improved_v24`
  - 缺陷类型：年份前紧贴逗号时的 parser token 识别
- `task_051`
  - 类型：`real_issue`
  - 来源：`python-jsonschema/jsonschema#1328`
- `task_052`
  - 类型：`semi_real`
  - repo：`jsonschema_error_tree_repo`
  - 首个通过版本：`improved_v25`
  - 缺陷类型：访问缺失索引时的 ErrorTree 状态污染
- `task_053`
  - 类型：`real_issue`
  - 来源：`python-jsonschema/jsonschema#1125`
- `task_054`
  - 类型：`semi_real`
  - repo：`jsonschema_extend_repo`
  - 首个通过版本：`improved_v26`
  - 缺陷类型：`extend()` 丢失 `applicable_validators` 语义
- `task_055`
  - 类型：`real_issue`
  - 来源：`simonw/sqlite-utils#159`
- `task_056`
  - 类型：`semi_real`
  - repo：`sqlite_delete_repo`
  - 首个通过版本：`improved_v27`
  - 缺陷类型：`delete_where()` 删除后未提交事务
- `task_057`
  - 类型：`semi_real`
  - repo：`pydantic_inheritance_repo`
  - 首个通过版本：`improved_v28`
  - 缺陷类型：子类 `model_validator` 覆盖父类校验链
- `task_058`
  - 类型：`semi_real`
  - repo：`attrs_alias_repo`
  - 首个通过版本：`improved_v29`
  - 缺陷类型：`field_transformer` 阶段默认 alias 不可见
- `task_059`
  - 类型：`semi_real`
  - repo：`sqlite_transform_repo`
  - 首个通过版本：`improved_v30`
  - 缺陷类型：数值列转换时空字符串未回落为 `None`
- `task_060`
  - 类型：`semi_real`
  - repo：`sqlite_extract_repo`
  - 首个通过版本：`improved_v31`
  - 缺陷类型：extract 时错误为 `None` 生成维表记录
- `task_061`
  - 类型：`semi_real`
  - repo：`isort_profile_repo`
  - 首个通过版本：`improved_v32`
  - 缺陷类型：tuple 格式化分支未继承 profile 布局策略

## 最近三轮优化结论

### `improved_v26`

- 覆盖场景：`extend()` 保留 legacy validator 的 `applicable_validators`
- 新增任务：`task_054`
- 在 `frozen_20` 上补齐一轮无回归验证

### `improved_v27`

- 覆盖场景：`delete_where()` 删除后自动提交事务
- 新增任务：`task_056`
- 在 `frozen_20` 上补齐一轮无回归验证

### `improved_v28`

- 覆盖场景：子类 `model_validator` 继续追加执行父类 validator
- 新增任务：`task_057`
- 在 `frozen_20` 上补齐一轮无回归验证

### `improved_v29`

- 覆盖场景：`field_transformer` 定义阶段默认 alias 提前可见
- 新增任务：`task_058`
- 在 `frozen_20` 上补齐一轮无回归验证

### `improved_v30`

- 覆盖场景：数值列转换时空字符串回落为 `None`
- 新增任务：`task_059`
- 在 `frozen_20` 上补齐一轮无回归验证

### `improved_v31`

- 覆盖场景：extract 时跳过 `None` 维表提取
- 新增任务：`task_060`
- 在 `frozen_20` 上补齐一轮无回归验证

### `improved_v32`

- 覆盖场景：tuple 格式化分支继承 profile 布局策略
- 新增任务：`task_061`
- 在 `frozen_20` 上补齐一轮无回归验证

## 接下来最值得做的事

- 围绕 `frozen_20` 继续积累后续版本的同集合对比证据
- 当前高优先级 `to_review` 已清零，下一步应通过批量导入入口扩新来源，并继续定位近期耗时回升原因
- 当前性能定位已经收窄到 `run_tests` 链路，下一步应优先检查测试执行环境和子进程开销
- 对热点任务集合的历史聚合已经证明 `task_034 / task_036 / task_038 / task_040` 都在 `improved_v32` 上稳定回升
- `run_tests` 模式基准已经证明 workspace copy 不是主因
- `pytest` 分阶段基准已经证明主要开销位于启动与 collection，下一步应优先拆 import/collection 内部差异和解释器抖动
- `pytest importtime` 基准已经证明 collection 的额外耗时伴随稳定新增 import 链，下一步应优先验证这些模块是否与平台或 pytest 默认插件链有关
- `pytest` 插件变体基准已经推进到 `_004`：当前最值得直接产品化验证的项是 `-p no:unraisableexception`
- `pytest importtime` 分组分析已经进一步证明：新增 import 开销主要由 `pytest_optional_plugins / windows_ctypes / xml_stack / terminal_chain` 构成，下一步应通过更细命令形态验证哪些组可以真正削减
- `improved_v33` 已把 benchmark 结论接入 runtime，并已同时通过热点集、`frozen_20` 与正式 `30` 条任务集验证
- 当前主线应从 `v33` 验证切换到更高层目标：继续扩充真实任务到 `60+`、构建 `frozen_40`，并开始累计连续 `5` 轮无回归证据
- 当前已经确认：来源广泛度不是瓶颈，真正缺口集中在正式任务规模和 `frozen_40` 稳定性证据
- 持续把“扩容对比”和“冻结同集合对比”成对保留

## 建议冷启动顺序

如果后续由新的会话继续推进，建议先读：

1. `docs/project_memory.md`
2. `docs/next_actions.md`
3. `docs/candidate_shortlist.md`
4. `docs/benchmark_registry.md`
5. `docs/results.md`
6. `docs/optimization_log.md`

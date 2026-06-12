# 项目记忆卡

本文件用于在新会话或长间隔续做时，快速恢复项目上下文。

目标不是替代完整文档，而是提供一个高密度、低冗余的冷启动入口。

## 当前阶段

- 当前阶段：`Phase 6 - 优化系统`
- 当前稳定基线策略：`improved_v50`
- 当前最新扩容策略：`improved_v52`
- 当前主分支最近重要能力：
  - 已完成 `49` 条真实 issue 派生 `semi_real` 正式任务
  - 已正式建立 `benchmarks/manifests/real_issue_tasks_frozen_40_v1.json`
  - 已补齐 `frozen_40` 上的 `improved_v32` 基线评测
  - 已在 `frozen_20` 上补齐一轮 `improved_v49 -> improved_v50` 无回归验证
  - 已在正式 `47` 条真实任务集上补齐 `improved_v49 -> improved_v50` 全量验证
  - 已在 `frozen_40` 上补齐一轮 `improved_v49 -> improved_v50` 无回归验证
  - 已把 `pallets/click#3125` 从新来源候选推进为正式任务 `task_095`
  - 已把 `pallets/click#3571` 从新来源候选推进为正式任务 `task_097`
  - 已把 `pallets/jinja#2108` 从新来源候选推进为正式任务 `task_099`
  - 已落地 `improved_v52` 的 jinja macro include without context 修复规则
  - 已完成 `v52` 的正式集、`frozen_20`、`frozen_40` 三线功能验证
  - 已确认 `v52` 相对 `v51` 在正式集与 `frozen_20` 上出现时延回落，但 `frozen_40` 仍未回到长期阈值
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
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v50.json --run-label realissuev50`
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

- 正式 `semi_real` 真实 issue 任务数：`49`
- 当前正式任务来源生态数：`13`
- 当前正式 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`
- 当前冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_40_v1.json`
- 当前最大 frozen 集合：`40`

## 当前候选池状态

- `accepted = 49`
- `drafted = 0`
- `to_review = 0`
- 当前 accepted 候选已全部转成正式任务，下一阶段扩容主要依赖新增候选来源

候选来源文件：

- `benchmarks/real_world_candidates.json`
- 当前新导入但尚未落地的重点候选主要来自：
  - `pypa/packaging`
  - `python-poetry/tomlkit`
  - `pallets/jinja`

## 最新评测结论

### 1. 当前最新扩容对比

- 对比：`improved_v51 -> improved_v52`
- 任务集：`48 -> 49` 条
- 结果：
  - `success_count: 48 -> 49`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - 正式集 compare 口径 `average_duration_sec: 0.6987 -> 0.6707`

说明：

- 这说明 `improved_v52` 已成功把正式真实任务集从 `48` 条推进到 `49` 条
- 新增任务是 `task_099`，来源于 `pallets/jinja#2108`
- 功能上这一轮仍然保持 `100%` 成功率与 `100%` 测试通过率
- 同时它还把 `v51` 的正式集平均耗时拉回了 `0.028s`
- 但当前还不能把 `v52` 直接视为新的稳定 streak 版本

### 2. 当前最新冻结集观察

- `improved_v52` `frozen_20` compare：
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `average_duration_sec: 0.7361 -> 0.6912`
- `improved_v52` `frozen_40` compare：
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `average_duration_sec: 0.6616 -> 0.6824`
- 当前稳定 streak：
  - 仍为 `8`

说明：

- `v52` 在固定集合上没有功能回归
- 它在 `frozen_20` 上已经明显优于 `v51`
- 但 `frozen_40` 仍然没有回到长期阈值
- 因此 `frozen_40 streak` 仍然停留在 `v50` 时的 `8`

### 3. 最新环境级诊断结论

- 同环境 `improved_v50` `frozen_40` 复跑对比：
  - `logs/summaries/batch_compare_frozen40_envcheck_v50_001.json`
  - `average_duration_sec: 0.5410 -> 0.6616`
- 正式集 `v51 -> v52` 时延对比：
  - `logs/summaries/duration_compare_realissuev52_001.json`
  - 公共 `48` 条任务平均耗时增量：`-0.0357s`
- `frozen_20` `v51 -> v52` 时延对比：
  - `logs/summaries/duration_compare_frozen20v52_001.json`
  - 公共 `20` 条任务平均耗时增量：`-0.0629s`
- `frozen_40` 环境基线对比：
  - `logs/summaries/batch_compare_frozen40_step09_001.json`
  - `average_duration_sec: 0.6616 -> 0.6824`

说明：

- `v52` 不是继续恶化的版本，它已经把 `v51` 上的大部分回升拉回来了
- 但当前最强证据仍然表明：系统还处在环境级漂移后的恢复阶段，而不是已经完全恢复到长期阈值内
- 后续文档与结论仍然必须把“扩题成功”和“稳定性门控通过”分开记录

### 4. 上一轮稳定扩容对比

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

- 对比：`improved_v49 -> improved_v50`
- 任务集：固定 `20` 条
- 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_steps: 10.25 -> 10.25`
  - `average_duration_sec: 0.5972 -> 0.5672`

说明：

- 这是当前最新的一轮 `frozen_20` 无回归验证
- 说明新增 click version_option package_name 规则没有破坏已有 `20` 条固定任务
- 这一轮固定集平均耗时回落了 `0.03s`

### 3. 当前最新正式集证据

- 对比：`improved_v49 -> improved_v50`
- 任务集：扩容到正式 `47` 条
- 结果：
  - `success_count: 46 -> 47`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5869 -> 0.5583`

说明：

- 这说明 `improved_v50` 不只是保住了 `v49` 的已有能力
- 它还把正式真实任务集从 `46` 条稳定扩到 `47` 条，并继续保持 `100%` 成功率和 `100%` 测试通过率
- 同时它让 `frozen_40` 连续无回归版本从 `7` 推进到 `8`
- 因此当前主线基线已经从 `v49 / 46 条 + streak 7` 前进到 `v50 / 47 条 + streak 8`

### 4. 最新时延分析结论

- 扩容集分析：
  - `logs/summaries/duration_compare_realissuev50_001.json`
  - 公共 `46` 条任务平均耗时差值：`-0.0287s`
- `frozen_20` 分析：
  - `logs/summaries/duration_compare_frozen20v50_001.json`
  - 公共 `20` 条任务平均耗时差值：`-0.03s`
- trace 热点分析：
  - `logs/summaries/trace_hotspots_realissuev50_001.json`
- 当前结果说明 `v50` 在继续扩容后仍保持功能稳定，而且这轮正式集与 `frozen_20` 耗时都有回落
- 正式扩容集公共 `46` 条任务平均耗时差值约 `-0.0287s`
- `frozen_20` 公共 `20` 条任务平均耗时差值约 `-0.03s`
- 相比 `improved_v32` 基线，当前 `frozen_40` 复跑口径 `batch_eval_frozen40v50_002.json` 仍保持在长期约束内
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
- `improved_v37` `frozen_20` 验证：
  - `logs/summaries/batch_eval_frozen20v37_001.json`
  - `logs/summaries/batch_compare_frozen20_step16_001.json`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5386 -> 0.5687`
- `improved_v37` 正式 `34` 条任务集验证：
  - `logs/summaries/batch_eval_realissuev37_001.json`
  - `logs/summaries/batch_compare_realissue_step17_002.json`
  - `success_count: 33 -> 34`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_duration_sec: 0.5312 -> 0.6038`
- maturity 审计结果：
  - `logs/summaries/benchmark_maturity_maturity_008.json`
  - 正式任务数：`34 / 60`
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
- `task_062`
  - 类型：`real_issue`
  - 来源：`pypa/packaging#638`
- `task_063`
  - 类型：`semi_real`
  - repo：`packaging_marker_repo`
  - 首个通过版本：`improved_v34`
  - 缺陷类型：`Marker.evaluate(extra=None)` 错误对 `None` 调用 `.lower()`
- `task_064`
  - 类型：`real_issue`
  - 来源：`pypa/packaging#788`
- `task_065`
  - 类型：`semi_real`
  - repo：`packaging_prerelease_repo`
  - 首个通过版本：`improved_v35`
  - 缺陷类型：`< prerelease` 比较错误排除了更早的合法 prerelease
- `task_066`
  - 类型：`real_issue`
  - 来源：`pypa/packaging#909`
- `task_067`
  - 类型：`semi_real`
  - repo：`packaging_tag_order_repo`
  - 首个通过版本：`improved_v36`
  - 缺陷类型：wheel compressed tag set 未排序时仍被错误接受

## 最近三轮优化结论

### `improved_v50`

- 覆盖场景：`version_option(package_name=...)` 显式包名优先级
- 新增任务：`task_095`
- 这是当前稳定基线，正式任务数推进到 `47`，`frozen_40 streak` 推进到 `8`

### `improved_v51`

- 覆盖场景：`click.progressbar` 在 `show_pos=True` 时结束态完整位置显示
- 新增任务：`task_097`
- 功能上完成 `48` 条正式任务扩容，但当前先记为“扩容成功、性能门控待过”的版本

### `improved_v52`

- 覆盖场景：macro 内部 `include without context` 不应输出 generator repr
- 新增任务：`task_099`
- 功能上完成 `49` 条正式任务扩容，并且相对 `v51` 在正式集与 `frozen_20` 上出现时延回落，但 `frozen_40` 仍未回到长期阈值

## 接下来最值得做的事

- 围绕 `frozen_40` 继续积累后续稳定版本的同集合对比证据，但不要把 `v51 / v52` 直接算入 streak
- 当前高优先级 `to_review` 已清零，下一步应通过批量导入入口扩新来源，把正式任务数从 `49` 继续推向 `60+`
- 当前性能定位已经收窄到 `run_tests` 链路，下一步应优先把 `frozen_40` 从 `0.68s` 级别继续拉回
- 对热点任务集合的历史聚合已经证明 `task_034 / task_036 / task_038 / task_040` 都在 `improved_v32` 上稳定回升
- `run_tests` 模式基准已经证明 workspace copy 不是主因
- `pytest` 分阶段基准已经证明主要开销位于启动与 collection，下一步应优先拆 import/collection 内部差异和解释器抖动
- `pytest importtime` 基准已经证明 collection 的额外耗时伴随稳定新增 import 链，下一步应优先验证这些模块是否与平台或 pytest 默认插件链有关
- `pytest` 插件变体基准已经推进到 `_004`：当前最值得直接产品化验证的项是 `-p no:unraisableexception`
- `pytest importtime` 分组分析已经进一步证明：新增 import 开销主要由 `pytest_optional_plugins / windows_ctypes / xml_stack / terminal_chain` 构成，下一步应通过更细命令形态验证哪些组可以真正削减
- `improved_v33` 已把 benchmark 结论接入 runtime，并已同时通过热点集、`frozen_20` 与正式 `30` 条任务集验证
- 当前主线应从 `v33` 验证切换到更高层目标：继续扩充真实任务到 `60+`、构建 `frozen_40`，并开始累计连续 `5` 轮无回归证据
- 当前已经确认：来源广泛度不是瓶颈，真正缺口集中在正式任务规模和 `frozen_40` 稳定性证据
- 当前最新状态是：规模侧已经推进到 `49 / 60`，稳定性侧 `frozen_40 streak = 8` 已满足长期目标，但需要继续守住；新的实际缺口是继续扩容并把 `frozen_40` 性能重新拉回长期阈值
- 持续把“扩容对比”和“冻结同集合对比”成对保留

## 建议冷启动顺序

如果后续由新的会话继续推进，建议先读：

1. `docs/project_memory.md`
2. `docs/next_actions.md`
3. `docs/candidate_shortlist.md`
4. `docs/benchmark_registry.md`
5. `docs/results.md`
6. `docs/optimization_log.md`

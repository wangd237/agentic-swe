# 项目记忆卡

本文件用于在新会话或长间隔续做时，快速恢复项目上下文。

目标不是替代完整文档，而是提供一个高密度、低冗余的冷启动入口。

## 当前阶段

- 当前阶段：`Phase 6 - 优化系统`
- 当前主版本策略：`improved_v71`
- 当前长期对比锚点：`improved_v50`
- 当前性能主线校准：
  - `improved_v68` 与 `improved_v69` 的 `pytest_additional_flags` 完全相同
- 当前 `v68 / v69` 的 pytest compare 结果应视为 `runtime-equivalent noise probe`
- 当前 roadmap action board 已进一步把 performance 线收口成更可执行的入口：
  - 先跑环境基线：
    - `python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines`
  - 再跑冻结集公共任务时延对比：
    - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_frozen40v68r1_001.json --improved-batch-summary logs/summaries/batch_run_frozen40v69r1_001.json --run-label frozen40_v68_v69`
  - 最后再 refresh 收口
- 当前新增环境基线快照：
  - `logs/env_baselines/env_baseline_20260613T154023784306Z.json`
  - `python_noop mean = 0.0181`
  - `pytest_version mean = 0.1397`
- 当前又新增一轮环境基线快照：
  - `logs/env_baselines/env_baseline_20260613T182156280991Z.json`
  - `python_noop mean = 0.0198`
  - `pytest_version mean = 0.1431`
- 当前新增冻结集对比产物：
  - `logs/summaries/duration_compare_frozen40_v68_v69_001.json`
  - `common_average_delta_sec = 0.0272`
  - 当前 top regressions 前几项包括：
    - `task_050 = +0.0743`
    - `task_034 = +0.0665`
    - `task_022 = +0.0637`
- 当前又补了一轮 `v70 -> v71` 冻结集时延对比：
  - `logs/summaries/duration_compare_frozen40_v70_v71_001.json`
    - `common_average_delta_sec = +0.0212`
    - 当前 top regressions 前几项包括：
      - `task_056 = +0.0881`
      - `task_006 = +0.082`
      - `task_008 = +0.0566`
  - `logs/summaries/duration_compare_frozen20_v70_v71_001.json`
    - `common_average_delta_sec = +0.0171`
    - 当前 top regressions 前几项包括：
      - `task_038 = +0.0611`
      - `task_030 = +0.0469`
      - `task_008 = +0.0452`
- 当前又补了一轮 `v70 -> v71` trace 热点分析：
  - `logs/summaries/trace_hotspots_frozen40v71r2_001.json`
    - `average_duration_delta_sec = +0.0212`
    - `top_tool_regressions` 里主增量为：
      - `run_tests = +0.9079s`
  - `logs/summaries/trace_hotspots_frozen20v71r2_001.json`
    - `average_duration_delta_sec = +0.0171`
    - `top_tool_regressions` 里主增量为：
      - `run_tests = +0.3933s`
- 因此当前更稳妥的性能结论又收窄了一步：
  - `v70 -> v71` 的冻结集回升主要仍集中在 `run_tests`
  - 不像是 `copy_workspace` 这类外围开销主导
- 当前 roadmap snapshot / refresh 已开始把 performance 证据也视为高信号变化：
  - `snapshot_summary.performance_status`
  - `changed_fields` 现在会显式包含：
    - `performance_env_baseline_snapshot_id`
    - `performance_duration_compare_id`
    - 以及对应的关键数值字段
- 因此 `refresh_026` 已不再是 `no_material_change`
  - 而是被正确识别为：
    - `progress`
- 当前 handoff 层也已补上“主线记忆”：
  - 即使下一轮 refresh 因为没有新增证据而回到 `no_material_change`
  - `action_board / status_card` 也不会退化成泛化的 `active_track`
  - 而会保留最近一次 progress 所属的主线
  - 当前真实保留的是：
    - `performance_track`
- 当前 history advice 也已补上“短暂停顿记忆”：
  - 如果最近一轮是 `no_material_change`
  - 但距离最近一次 `progress` 仍很近
  - 则 `history_advice` 不会立刻退回 `monitor_and_continue`
  - 而会继续返回：
    - `keep_momentum`
    - 并继承最近一次 `progress_track`
  - 当前这层能力已由 `tests/test_refresh_roadmap_tracking.py` 覆盖
  - 但要注意真实 latest 已推进到：
    - `roadmap_tracking_refresh_029`
    - 当前 `recent_no_material_change_streak = 3`
  - 因此 latest history advice 现已合理回到：
    - `monitor_and_continue`
  - 这不是回归，而是短暂停顿窗口已结束后的正常行为
  - 在没有新的 runtime-different policy pair 之前，不应把这条线继续当作 runtime flags 主因证据
  - 已复用旧真实日志重生校准产物：
    - `pytest_policy_pair_phases_cohort_v68_v69_hotspots_phase_calibrated_001.json`
    - `pytest_policy_pair_importtime_cohort_v68_v69_hotspots_importtime_calibrated_001.json`
    - `pytest_policy_pair_matrix_set_v68_v69_triage_calibrated_001.json`
  - 已新增单脚本重建入口：
    - `scripts/rebuild_pytest_policy_pair_calibrated_views.py`
  - 当前推荐直接看的总索引产物：
    - `pytest_policy_pair_calibrated_view_v68_v69_hotspots_001.json`
  - 当前最关键的校准证据是：
    - `runtime_equivalent_matrix_count = 3`
- 当前 semi-real 接入阶段审计：
  - 已新增 `scripts/audit_semi_real_pipeline.py`
  - 最新真实审计产物：
    - `semi_real_pipeline_audit_phase6_001.json`
  - 当前最关键的阶段信号：
    - `accepted_in_formal_manifest = 66`
    - `accepted_in_challenge_manifest = 3`
    - challenge 第 `3` 条入口已完成接入：
      - `samuelcolvin/watchfiles#169`
      - 当前状态：`accepted`
      - 当前 issue 级判题结论：
        - 目标文件优先落在 `watchfiles/main.py`
        - 测试入口优先落在 `tests/test_main.py`
      - 当前已进一步生成：
        - `benchmarks/tasks/task_130.json`
        - `benchmarks/repos/watchfiles_169_repo`
      - 当前测试口径：
        - 目标 WSL-like `metadata-write` 路径 `1` 条失败
        - 相邻保护路径 `2` 条通过
      - 当前已纳入：
        - `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- 当前主分支最近重要能力：
  - 已完成 `66` 条真实 issue 派生 `semi_real` 正式任务
  - 已正式建立 `benchmarks/manifests/real_issue_tasks_frozen_40_v1.json`
  - 已补齐 `frozen_40` 上的 `improved_v32` 基线评测
  - 已在 `frozen_20` 上补齐一轮 `improved_v49 -> improved_v50` 无回归验证
  - 已在正式 `47` 条真实任务集上补齐 `improved_v49 -> improved_v50` 全量验证
  - 已在 `frozen_40` 上补齐一轮 `improved_v49 -> improved_v50` 无回归验证
  - 已把 `pallets/click#3125` 从新来源候选推进为正式任务 `task_095`
  - 已把 `pallets/click#3571` 从新来源候选推进为正式任务 `task_097`
  - 已把 `pallets/jinja#2108` 从新来源候选推进为正式任务 `task_099`
  - 已把 `python-poetry/tomlkit#505` 从新来源候选推进为正式任务 `task_101`
  - 已把 `python-poetry/tomlkit#295` 从新来源候选推进为正式任务 `task_103`
  - 已把 `pytest-dev/pytest#14189` 从新来源候选推进为正式任务 `task_105`
  - 已把 `python-poetry/tomlkit#430` 从新来源候选推进为正式任务 `task_107`
  - 已把 `pypa/packaging#1231` 从新来源候选推进为正式任务 `task_109`
  - 已把 `pallets/click#3362` 从新来源候选推进为正式任务 `task_111`
  - 已把 `pypa/distlib#238` 从新来源候选推进为正式任务 `task_113`
  - 已把 `pytest-dev/pytest#14474` 从新来源候选推进为正式任务 `task_115`
  - 已把 `python-poetry/tomlkit#346` 从新来源候选推进为正式任务 `task_117`
  - 已把 `python-poetry/tomlkit#450` 从新来源候选推进为正式任务 `task_119`
  - 已把 `python-poetry/tomlkit#412` 从新来源候选推进为正式任务 `task_121`
  - 已落地 `improved_v57` 的 packaging 名称规范化边界修复规则
  - 已落地 `improved_v58` 的 click usage 连字符换行修复规则
  - 已落地 `improved_v59` 的 distlib WHEEL metadata Build 行修复规则
  - 已落地 `improved_v60` 的 pytest expression 反斜杠检查作用域修复规则
  - 已落地 `improved_v61` 的 tomlkit 负整数翻转规范渲染修复规则
  - 已落地 `improved_v62` 的 tomlkit bool item 包装保真修复规则
  - 已落地 `improved_v63` 的 tomlkit 容器 int key 规范化修复规则
  - 已落地 `improved_v64` 的 fsspec protocol 前缀保护修复规则
  - 已落地 `improved_v65` 的 anyio TaskGroup 重入保护修复规则
  - 已落地 `improved_v66` 的 anyio completed task cancellation spin 修复规则
  - 已落地 `improved_v68` 的更保守 pytest runtime 裁剪策略（在保留 `-p no:unraisableexception` 的基础上追加 `-p no:threadexception`）
  - 已落地 `improved_v69` 的 anyio `from_thread.check_cancelled()` 取消语义修复规则
  - 已完成 `v57` 的正式集、`frozen_20`、`frozen_40` 功能验证及复跑
  - 已确认 `v57` 相对 `v56` 在功能上继续全绿，并继续把 `frozen_40` 保持在长期阈值以内
  - 已完成 `v58` 的正式集、`frozen_20`、`frozen_40` 验证
  - 已确认 `v58r1` 首轮只暴露 `task_109` 的继承链漏接，`v58r2` 修复后已恢复正式集 `55 / 55`
  - 已完成 `v59` 的正式集、`frozen_20`、`frozen_40` 验证
  - 已确认 `v59r1` 首轮只暴露 `task_111` 的继承链漏接，`v59r2` 修复后已恢复正式集 `56 / 56`
  - 已完成 `v60` 的正式集、`frozen_20`、`frozen_40` 验证
  - 已确认 `v60r1` 首轮只暴露 `task_113` 的继承链漏接，`v60r2` 修复后已恢复正式集 `57 / 57`
  - 已完成 `v61` 的正式集、`frozen_20`、`frozen_40` 验证
  - 已确认 `v61r1` 首轮出现多段旧规则集合与 fallback 链漏接，`v61r2` 修复后已恢复正式集 `58 / 58`
  - 已完成 `v62` 的正式集、`frozen_20`、`frozen_40` 验证
  - 已确认 `v62r1 / v62r2` 首轮先后暴露旧规则集合漏接与 `v61` 新规则未继续继承的问题，`v62r3` 修复后已恢复正式集 `59 / 59`
  - 已完成 `v63` 的正式集、`frozen_20`、`frozen_40` 验证
  - 已确认 `v63r1` 首轮再次暴露从 `v47` 到 `v43` 的旧规则集合漏接，`v63r2` 修复后已恢复正式集 `60 / 60`
  - 已完成 `v64` 的正式集、`frozen_20`、`frozen_40` 最小验证与稳定性复跑
  - 已确认 `v64` 在扩到 `61` 条正式任务后继续保持功能全绿，且 `frozen_20 / frozen_40` 复跑都达到 `stable`
  - 已完成 `v65` 的正式集、`frozen_20`、`frozen_40` 最小验证
  - 已完成 `v65` 的 `frozen_20 / frozen_40` stability recheck
  - 已确认 `v65` 在扩到 `62` 条正式任务后继续保持三线全绿，且冻结集复跑结论为 `stable`，正式集、`frozen_20`、`frozen_40` 平均耗时都相对 `v64` 小幅改善
  - 已确认 issue 导入脚本支持结构化候选说明追加写入
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
  - 已把上述三条 `pytest` 诊断脚本都补成支持 `policy + pytest_additional_flags`
  - 已新增同任务双策略摘要 compare 入口 `scripts/compare_pytest_policy_pair.py`
  - 已新增双策略热点任务复跑复核入口 `scripts/recheck_policy_pair_tasks.py`
  - 已新增环境基线快照入口 `scripts/snapshot_env_baseline.py`
  - 已增强 `scripts/analyze_duration_regressions.py --env-baseline`
  - 已增强 `scripts/scaffold_semi_real_task.py`
    - 当 issue 文本只给 Python 符号名时，会尝试自动推断目标模块路径
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
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v69.json --run-label realissuev69`
- challenge 任务集流水线：
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v69.json --run-label challengev69`
- 候选批量导入：
  - `python scripts/import_issue_batch.py --input benchmarks/example_issue_batch.txt`
- 时延回归分析：
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev31_001.json --improved-batch-summary logs/summaries/batch_run_realissuev32_001.json --run-label realissuev32`
- 环境基线快照：
  - `python scripts/snapshot_env_baseline.py --repetitions 10 --output-dir logs/env_baselines`
- 带环境漂移扣除的时延分析：
  - `python scripts/analyze_duration_regressions.py --baseline-batch-summary logs/summaries/batch_run_realissuev65r3_001.json --improved-batch-summary logs/summaries/batch_run_realissuev66r2_001.json --run-label realissuev66r2 --env-baseline logs/env_baselines/env_baseline_xxx.json`
- trace 热点分析：
  - `python scripts/analyze_trace_hotspots.py --baseline-batch-summary logs/summaries/batch_run_realissuev31_001.json --improved-batch-summary logs/summaries/batch_run_realissuev32_001.json --run-label realissuev32`
- 单任务历史时延分析：
  - `python scripts/analyze_task_history.py --task-dir logs/trajectories/task_040 --output-dir logs/summaries`
- 热点任务集合历史分析：
  - `python scripts/analyze_task_history_cohort.py --task-id task_034 --task-id task_036 --task-id task_038 --task-id task_040 --cohort-label run_tests_hotspots_v32 --output-dir logs/summaries`

## 当前正式任务规模

- 正式 `semi_real` 真实 issue 任务数：`66`
- 当前正式任务来源生态数：`16`
- 当前正式 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`
- 当前 challenge manifest：
  - `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- 当前 challenge 说明文档：
  - `docs/challenge_set.md`
- 当前 challenge shortlist：
  - `docs/challenge_shortlist.md`
- 当前 challenge sourcing brief：
  - `docs/challenge_sourcing_brief_a3.md`
- 当前冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_40_v1.json`
- 当前最大 frozen 集合：`40`

## 当前候选池状态

- `accepted = 69`
- `imported = 0`
- `screened = 0`
- `blocked = 0`
- `completed` 为评测口径上的动态派生状态，不直接写回候选文件
- 当前候选池总量是 `69`
- 当前 `69` 条 accepted 候选中：
  - `66` 条已在正式 manifest
  - `3` 条已在 challenge manifest
- 当前仍在候选推进链路中的条目有：
  - 暂无已 ready 但未纳入任何 manifest 的 challenge 条目
- `fsspec/filesystem_spec#979` 已进一步生成 draft semi_real：
  - `benchmarks/tasks/task_122.json`
  - `benchmarks/repos/fsspec_unstrip_protocol_repo`
  - 当前已补成 ready 口径 semi_real，候选状态已推进到 `accepted`
  - 当前已纳入正式 manifest，正式任务总数推进到 `61`
  - 已确认：`improved_v63` 对带 bug 的 `task_122` 失败，`improved_v64` 单任务修复成功
  - 已完成 `improved_v64` 的正式集、`frozen_20`、`frozen_40` 最小验证
  - 已完成 `improved_v64` 的 `frozen_20 / frozen_40` 稳定性复跑
  - 当前口径是：功能三线继续全绿，且复跑口径稳定；`frozen_40` 均值回落到 `0.5432`
- `agronholm/anyio#1109` 已推进到 `accepted`
  - 已生成并纳入正式任务：
    - `benchmarks/tasks/task_123.json`
    - `benchmarks/repos/anyio_taskgroup_reentry_repo`
  - 已确认：
    - `improved_v64` 单任务失败
    - `improved_v65` 单任务成功
  - 已完成 `improved_v65` 的正式集、`frozen_20`、`frozen_40` 最小验证
  - 已完成 `improved_v65` 的 `frozen_20 / frozen_40` stability recheck
  - 当前口径是：第 `62` 条正式任务已正式接入，新增 `agronholm/anyio` 生态，三线功能继续全绿，冻结集稳定性复跑为 `stable`
- `agronholm/anyio#1111` 已推进到 `accepted`
  - 已生成并纳入正式任务：
    - `benchmarks/tasks/task_124.json`
    - `benchmarks/repos/anyio_cancellation_spin_repo`
  - 已把 repo 从 TODO 脚手架补成 ready 口径，并保持基准 repo 带 bug
  - 已确认：
    - `improved_v65` 单任务失败
    - `improved_v66` 单任务成功
  - 已完成：
    - `improved_v66` 的正式集、`frozen_20`、`frozen_40` 最小验证
  - 当前口径是：
    - 第 `63` 条正式任务已正式接入
    - `v66` 完成扩容验证后曾暴露性能回升
    - `v68` 通过更保守的 pytest runtime 裁剪，已把正式集与冻结集耗时重新拉回
    - 当前 `frozen_20 / frozen_40` 的 `v68` stability recheck 结论都为 `stable`
- `agronholm/anyio#1113` 已推进到 `accepted`
  - 已生成：
    - `benchmarks/tasks/task_125.json`
    - `benchmarks/repos/anyio_check_cancelled_repo`
  - 已确认 `--from-candidate` 自动推断现在能把：
    - `from_thread.check_cancelled`
    - 还原成 `anyio/from_thread.py`
  - 当前口径是：
    - 候选已推进到 `accepted`
    - 已纳入正式 manifest，成为第 `64` 条正式任务
    - 已验证：
      - `improved_v68` 单任务失败
      - `improved_v69` 单任务成功
    - 已完成：
      - 正式集 `64 / 64`
      - `frozen_20` `20 / 20`
      - `frozen_40` `40 / 40`
    - 已完成 stability recheck：
      - `frozen_20 mean = 0.5665`
      - `frozen_40 mean = 0.5555`
      - 两条冻结集结论都为 `stable`
    - 下一步应继续观察平均耗时回升，并补一轮时延定位
- `agronholm/anyio#82` 已推进到 `accepted`
  - 已生成：
    - `benchmarks/tasks/task_128.json`
    - `benchmarks/repos/anyio_82_repo`
  - 已把 repo 补成 ready 口径最小并发回归任务
  - 已验证：
    - `improved_v70` 单任务失败
    - `improved_v71` 单任务成功
  - 当前口径是：
    - 已纳入正式 manifest，成为第 `65` 条正式任务
    - `v71r1` 首轮曾因继承链漏接导致大面积 `Premature Finish`
    - 当前 `v71r2` 已恢复正式集、`frozen_20`、`frozen_40` 三线全绿
- `agronholm/anyio#88` 已继续推进到人工筛选通过阶段
  - 当前口径是：
    - 状态从 `imported` 推进到 `screened`
    - 随后又继续生成了：
      - `benchmarks/tasks/task_129.json`
      - `benchmarks/repos/anyio_88_repo`
    - 并已进一步补成 ready 口径：
      - 正常路径 `1` 条通过
      - 目标 asyncio 路径 `1` 条失败
    - 当前已从 `screened` 继续推进到 `accepted`
    - 当前阶段应视为：
      - `accepted_ready_not_in_any_manifest`
  - 这意味着当前并发题族至少有两条仍在活跃推进：
    - `anyio#82`：`accepted + in_formal_manifest + task_128`
    - `anyio#88`：`accepted + ready + task_129`
- `samuelcolvin/watchfiles#266` 已推进到 `accepted`
  - 已确认 `--dry-run` 的自动推断在修正 URL 噪声后可以稳定落到：
    - `watchfiles/main.py`
    - `tests/test_main.py`
  - 已进一步生成并补齐本地 ready semi-real：
    - `benchmarks/tasks/task_126.json`
    - `benchmarks/repos/watchfiles_266_repo`
  - 当前口径是：
    - 候选已完成从 `screened -> accepted`
    - `task_126` 已是可运行 semi-real 回归任务
  - 当前未纳入正式 manifest，但已纳入 challenge manifest
  - 已验证：
    - `python scripts/run_single_task.py --task benchmarks/tasks/task_126.json --policy optimization/policy_versions/improved_v69.json`
- `samuelcolvin/watchfiles#110` 已推进到 `accepted`
  - 已生成并补齐：
    - `benchmarks/tasks/task_127.json`
    - `benchmarks/repos/watchfiles_110_repo`
  - 当前口径是：
    - 已压成 ready semi-real 回归任务
    - 当前基准 repo 测试失败，符合 challenge hard case 预期
    - `improved_v69` 单任务当前失败
    - 已纳入 challenge manifest，成为第 `2` 条 challenge 题
      - 当前单任务运行结果为 `success`
      - 但由于 repo 当前已是 ready 口径，不再是“带失败基线的正式扩容题”，因此更适合作为 challenge 展示题
  - 当前更准确的下一步是：
    - 继续作为 challenge 题观察代表性
    - 重新 sourcing 第 `3` 条 challenge 候选

候选来源文件：

- `benchmarks/real_world_candidates.json`
- 当前新导入但尚未落地的重点候选主要来自：
  - `samuelcolvin/watchfiles`

## 最新评测结论

### 0. 当前最新扩容对比

- 对比：`improved_v68 -> improved_v69`
- 任务集：`63 -> 64` 条
- 结果：
  - `success_count: 63 -> 64`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - 正式集 compare 口径 `average_duration_sec: 0.5424 -> 0.5656`

说明：

- `v69` 成功把 `task_125` 接入正式集，并保持正式集功能全绿
- `frozen_20` 与 `frozen_40` 也都继续保持 `100%`
- `v69` 的 `frozen_20 / frozen_40` stability recheck 也都为 `stable`
- 但平均耗时相对 `v68` 有回升：
  - `frozen_20: 0.5609 -> 0.5975`
  - `frozen_40: 0.5589 -> 0.5861`
- 因此当前更准确的口径应是：
  - `v69` 是当前最新扩容成功版本
  - 功能侧三线全绿
  - 性能侧仍需继续复核，再决定是否把它升格为新的稳定叙事锚点

补充诊断：

- `v68 -> v69` 的正式集公共 `63` 条任务平均增量已确认是 `+0.0241s`
- `frozen_20` 公共 `20` 条任务平均增量是 `+0.0366s`
- `frozen_40` 公共 `40` 条任务平均增量是 `+0.0272s`
- 当前最可信的两条回升来源是：
  - `run_tests`
    - 正式集 trace 总增量 `+0.8885s`
  - `search_code`
    - 正式集 trace 总增量 `+0.5797s`
- 这说明：
  - 回升不是只由新增 `task_125` 单题拉高
  - 也不是单纯重复 `v66` 时的 pytest 问题
  - 下一步应同时沿 `run_tests` 与 `search_code` 两条线继续下钻
- `search_code` 专项定位已进一步确认：
  - 公共 `63` 条任务里，`63 / 63` 的查询签名完全一致
  - 其中 `56 / 63` 个任务是在“查询不变”的情况下出现回升
  - `search_code` 总增量 `+0.5797s` 里，有 `+0.5614s` 来自第一条搜索
- 这说明当前更像是搜索执行层的冷启动 / 抖动问题，而不是 query 生成策略变了
- 但后续冷启动 / 热启动基准又给出一个重要反证：
  - `task_123` 与 `task_119` 的单独基准都没有复现 `+20ms ~ +60ms` 级别回升
  - 冷 / 热差异都只有亚毫秒级
- 因此当前又新增了一条更直接的复核入口：
  - `scripts/recheck_policy_pair_tasks.py`
  - 它会对同一批热点任务重复运行两套策略
  - 同时汇总：
    - 总耗时
    - `search_code_total_duration_sec`
    - `run_tests_total_duration_sec`
- 这条入口现在也已经拿到了第一轮真实结果：
  - `logs/summaries/policy_pair_recheck_v68_v69_hotspots_001.json`
  - 热点任务：`task_123 / task_119 / task_097 / task_034`
  - `average_duration_delta_sec = -0.0149`
  - `average_search_code_delta_sec = -0.0095`
  - `average_run_tests_delta_sec = -0.0041`
  - `reproduced_search_code_task_count = 0 / 4`
  - `reproduced_run_tests_task_count = 1 / 4`
- 因此当前更稳妥的口径应更新为：
  - `search_code` 是一个已定位到的可疑线索
  - 但当前热点任务复跑没有支持它是稳定主因
  - 下一步应把 `search_code` 降级为次要线索
  - 并把 `run_tests` 重新升为 `v70` 主攻方向
- 当前又补了一轮更细的拆分版真实复跑：
  - `logs/summaries/policy_pair_recheck_v68_v69_hotspots_split_001.json`
  - `average_run_tests_delta_sec = -0.018`
  - `average_run_tests_first_delta_sec = -0.0117`
  - `average_run_tests_second_delta_sec = -0.0064`
- 这说明在当前环境里：
  - `run_tests` 总体也没有复现回升
  - 如果继续深挖，第一次 `run_tests` 更值得优先关注
- 为了支撑这条 `v70` 主线，当前又补齐了一步关键基础设施：
  - `scripts/benchmark_pytest_phases.py`
  - `scripts/benchmark_pytest_importtime.py`
  - `scripts/benchmark_pytest_plugin_variants.py`
  - 现在都可以直接接 `policy` 参数，按真实策略版本复跑
- 同时也补了更省上下文的 compare 入口：
  - `scripts/compare_pytest_policy_pair.py`
  - 它可以直接比较同一任务下：
    - `pytest phases`
    - `pytest importtime`
    两份策略版 summary
- 当前首轮真实 compare 已确认：
  - `task_123` 的 phase / importtime 差异量级都不大
  - `task_119` 的 phase / importtime 差异基本接近噪声
- 当前第二轮真实 compare 也已补齐：
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
- 因此当前更准确的口径应继续更新为：
  - `task_097` 与 `task_034` 给出的信号并不一致
  - 现阶段还不能把 `v68 -> v69` 的回升归结为单一稳定主因
  - `collect` 链路仍然是最值得继续扩样本验证的方向
  - 当前证据仍不足以支持“直接为了 `v70` 改 runtime 实现”
- 为了减少后续手工读单题 compare JSON 的成本，当前又新增：
  - `scripts/analyze_pytest_policy_pair_cohort.py`
  - 它会直接聚合同类型的多任务策略版 compare 结果
- 当前 4 任务真实 cohort 聚合结果是：
  - phase：
    - `average_pytest_startup_over_python_delta_sec = -0.0139`
    - `average_collect_over_pytest_startup_delta_sec = +0.0118`
    - `average_full_over_collect_delta_sec = +0.0054`
    - `collect_slower_task_count = 2 / 4`
    - `full_slower_task_count = 3 / 4`
  - importtime：
    - `average_collect_wall_delta_sec = +0.0026`
    - `average_collect_import_self_delta_us = +1197`
    - `collect_wall_slower_task_count = 2 / 4`
    - `collect_import_self_higher_task_count = 2 / 4`
- 因此当前更准确的口径又收紧了一步：
  - phase 聚合下 `collect` 仍然值得继续优先观察
  - 但 importtime 聚合仍接近噪声，暂时不支持“稳定 import 链恶化”的说法
  - 现阶段更适合继续扩样本，而不是直接产出 `v70`
- 为了继续降低后续追踪成本，当前又新增：
  - `scripts/run_pytest_policy_pair_matrix.py`
  - 它会批量串起：
    - `pytest phases benchmark`
    - `pytest importtime benchmark`
    - 单任务 `compare`
    - phase / importtime 两条 `cohort`
- 当前 4 任务真实 matrix 结果是：
  - phase 聚合：
    - `average_pytest_startup_over_python_delta_sec = +0.0101`
    - `average_collect_over_pytest_startup_delta_sec = -0.0235`
    - `average_full_over_collect_delta_sec = +0.0159`
    - `startup_slower_task_count = 4 / 4`
    - `collect_slower_task_count = 0 / 4`
    - `full_slower_task_count = 3 / 4`
  - importtime 聚合：
    - `average_collect_wall_delta_sec = -0.0047`
    - `average_collect_import_self_delta_us = +1672`
    - `collect_wall_slower_task_count = 1 / 4`
    - `collect_import_self_higher_task_count = 2 / 4`
- 因此当前更准确的口径再次更新为：
  - 当前更完整编排下，`collect` 没有表现出“跨任务普遍更慢”
  - 反而是 `startup` 与 `full run` 更值得继续观察
  - `importtime` 聚合整体也没有支持稳定恶化
  - 现阶段更适合继续扩样本与重复验证，而不是急着产出 `v70`
- 当前又补了一轮更贴近历史时延回升来源的真实 matrix：
  - 任务集合：`task_034 / task_036 / task_038 / task_040`
  - 对应产物：
    - `pytest_policy_pair_matrix_v68_v69_run_tests_hotspots_matrix_001.json`
    - `pytest_policy_pair_phases_cohort_v68_v69_run_tests_hotspots_matrix_phase_001.json`
    - `pytest_policy_pair_importtime_cohort_v68_v69_run_tests_hotspots_matrix_importtime_001.json`
- 当前这轮历史热点集合的聚合结果是：
  - phase：
    - `average_pytest_startup_over_python_delta_sec = +0.004`
    - `average_collect_over_pytest_startup_delta_sec = -0.0047`
    - `average_full_over_collect_delta_sec = -0.0152`
    - `startup_slower_task_count = 2 / 4`
    - `collect_slower_task_count = 2 / 4`
    - `full_slower_task_count = 1 / 4`
  - importtime：
    - `average_collect_wall_delta_sec = +0.0024`
    - `average_collect_import_self_delta_us = +8255`
    - `collect_wall_slower_task_count = 1 / 4`
    - `collect_import_self_higher_task_count = 3 / 4`
- 因此当前最准确的口径继续收敛为：
  - 当前并不存在一个已经稳定站住的单主因
  - `startup / collect / full run` 三条线在不同样本集合上仍会互相拉扯
  - `importtime` 有一定偏正，但证据还不够强
  - 继续扩样本与重复 matrix，仍然比直接做 `v70` 更稳妥
- 为了避免继续靠人工心算三轮 matrix，当前又新增：
  - `scripts/analyze_pytest_policy_pair_matrix_set.py`
  - 它会聚合多轮 matrix summary，直接输出跨集合 aggregate
- 当前三轮 matrix 的总聚合结果是：
  - `average_startup_delta_sec = +0.0051`
  - `average_collect_delta_sec = -0.0089`
  - `average_full_delta_sec = -0.0023`
  - `average_collect_wall_delta_sec = +0.0032`
  - `average_collect_import_self_delta_us = +6506.3333`
  - `startup_positive_matrix_count = 3 / 3`
  - `collect_positive_matrix_count = 1 / 3`
  - `full_positive_matrix_count = 1 / 3`
  - `collect_import_positive_matrix_count = 3 / 3`
- 因此当前最准确的口径再次更新为：
  - 跨三轮 matrix，唯一稳定偏正的是 `pytest startup`
  - `collect` 与 `full run` 都没有呈现稳定正向
  - `importtime` 有一定偏正，但更像次级观察项
  - 如果还继续做性能主线，下一步应优先盯 `pytest startup`
  - 如果后续 1 到 2 轮 matrix 仍不能继续强化这一判断，就该暂时切回 A 线扩题

### 0.1 上一轮主版本对比

- 对比：`improved_v66 -> improved_v68`
- 任务集：`63 -> 63` 条
- 结果：
  - `success_count: 63 -> 63`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - 正式集 compare 口径 `average_duration_sec: 0.5514 -> 0.5424`

说明：

- `v66` 的性能回升已经被进一步定位到 `run_tests` 的 subprocess / pytest collection 链路
- `v67` 试图通过关闭 `debugging + unraisableexception + threadexception` 插件回收耗时，但会让大量 unittest 类任务在 `_pytest.debugging` 的 `trace` 选项路径上报错，因此被判定为无效优化方向
- `v68` 继续保留 `v66` 的修复能力，只额外追加 `-p no:threadexception`
- 当前更准确的口径是：
  - `v68` 在不改变功能结果的前提下，相对 `v66` 把正式集平均耗时拉回了 `0.009s`
  - 因而它已经成为当前更可信的候选版本

### 0.1 当前最新冻结集观察

- `improved_v68` `frozen_20` compare：
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `average_duration_sec: 0.5867 -> 0.5609`
- `improved_v68` `frozen_40` compare：
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `average_duration_sec: 0.5732 -> 0.5589`
- 当前稳定 streak：
  - 仍为 `8`

说明：

- `v68` 在固定集合上没有功能回归
- 且相对 `v66`，两条冻结集平均耗时都已经回落
- 已完成 stability recheck：
  - `frozen_20`
    - mean = `0.5617`
    - std = `0.0166`
    - conclusion = `stable`
  - `frozen_40`
    - mean = `0.5529`
    - std = `0.0031`
    - conclusion = `stable`
- 当前更可信的下一步已经从“继续解释 v66 为什么慢”切到：
  - 以 `v69` 作为当前最新扩容版本继续做稳定性与性能复核
  - 同时保留 `v67` 作为一次失败的 runtime 裁剪反例

### 1. 当前最新扩容对比

- 对比：`improved_v57 -> improved_v58`
- 任务集：`54 -> 55` 条
- 结果：
  - `success_count: 54 -> 55`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - 正式集 compare 口径 `average_duration_sec: 0.523 -> 0.5234`

说明：

- 这说明 `improved_v58` 已成功把正式真实任务集从 `54` 条推进到 `55` 条
- 新增任务是 `task_111`，来源于 `pallets/click#3362`
- 功能上这一轮仍然保持 `100%` 成功率与 `100%` 测试通过率
- 复跑口径下当前正式集平均耗时只轻微波动了 `0.0004s`
- 这说明这轮不只是扩题成功，还顺带修复了 `v58r1` 中暴露出的 `task_109` 继承链漏接问题

### 2. 当前最新冻结集观察

- `improved_v58` `frozen_20` compare：
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `average_duration_sec: 0.5385 -> 0.5506`
- `improved_v58` `frozen_40` compare：
  - `success_rate = 1.0`
  - `test_pass_rate = 1.0`
  - `average_duration_sec: 0.5437 -> 0.5294`
- 当前稳定 streak：
  - 仍为 `8`

说明：

- `v58` 在固定集合上没有功能回归
- 它在 `frozen_20` 上相对 `v57` 只有 `0.0121s` 的轻微波动
- 它在 `frozen_40` 上相对 `v57` 反而回落了 `0.0143s`
- 当前 `0.5294` 仍低于 `improved_v32` 基线阈值 `0.5514`
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
- `v57` `frozen_40` 对比：
  - `logs/summaries/batch_compare_frozen40_step12_002.json`
  - `average_duration_sec: 0.5293 -> 0.5437`

说明：

- `v57` 继续证明了扩题链路稳定可用
- 当前最强证据表明：新题扩容后功能稳定，而且 `frozen_40` 性能已经重新落回长期阈值以内
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

- 顺着已经跑通的 A2/C 线，继续把新生态候选往正式任务推进
- 保持 `watchfiles#266 / task_126` 作为独立 challenge 题，不污染正式主集口径
- challenge 线当前状态：
  - `task_126` 是当前唯一 challenge 题
  - 本地 challenge shortlist 已清空
  - 下一条 challenge 候选需要重新 sourcing
  - challenge 找题入口已单独收口到 `docs/challenge_sourcing_brief_a3.md`
- 保持 `frozen_40` 的稳定性门控与 maturity 审计持续可复用，但当前主缺口已经从“达成 60 条”切到“扩新来源并把导入链路产品化”

### `improved_v53`

- 来源：`python-poetry/tomlkit#505`
- 新增任务：`task_101`
- 结论：
  - 扩容成功，正式任务数推进到 `50`
  - 功能继续保持全绿
  - 但正式集与 `frozen_20` 平均耗时相对 `v52` 再次回升
  - 因此当前仍不能把它视为新的稳定基线
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
- 当前最新状态是：规模侧已经达到 `63 / 60`，稳定性侧 `frozen_40 streak = 8` 已满足长期目标；新的实际缺口转为继续扩新来源、补齐并发与文件路径类题型，并把候选导入链路继续收口
- 持续把“扩容对比”和“冻结同集合对比”成对保留

### `improved_v54`

- 来源：`python-poetry/tomlkit#295`
- 新增任务：`task_103`
- 结论：
  - 扩容成功，正式任务数推进到 `51`
  - 正式集与 `frozen_20` 继续保持全绿
  - 相对 `v53`，正式集 `average_duration_sec: 0.7143 -> 0.6544`
  - 相对 `v53`，`frozen_20` `average_duration_sec: 0.7361 -> 0.6697`
  - 但由于还没有补 `frozen_40` 同集合验证，所以当前仍不能把它视为新的稳定基线
- 这一轮还暴露了一个重要过程性经验：
  - `v54r1` 首轮批量评测曾因为 patcher 继承链条件漏掉 `improved_v54` 而大面积回归
  - 修复继承链后，`v54r2` 已恢复到正式集与 `frozen_20` 双 `100%`
- 当前主线口径应更新为：
  - 稳定基线仍是 `improved_v50`
  - 最新扩容版本是 `improved_v54`
  - 正式任务数是 `51`
  - `frozen_40 streak` 仍是 `8`

### `improved_v55`

- 来源：`pytest-dev/pytest#14189`
- 新增任务：`task_105`
- 结论：
  - 扩容成功，正式任务数推进到 `52`
  - 正式集与 `frozen_20` 继续保持全绿
  - 首轮时延对比有回升，但复跑后正式集 `average_duration_sec: 0.6544 -> 0.6551`
  - 复跑后 `frozen_20` `average_duration_sec: 0.6697 -> 0.6835`
  - 因此这轮更准确的口径是“功能稳定扩容，性能轻微波动但已收敛”
  - 但由于还没有补 `frozen_40` 同集合验证，所以当前仍不能把它视为新的稳定基线
- 当前主线口径应更新为：
  - 稳定基线仍是 `improved_v50`
  - 最新扩容版本是 `improved_v55`
  - 正式任务数是 `52`
  - `frozen_40 streak` 仍是 `8`

### `improved_v56`

- 来源：`python-poetry/tomlkit#430`
- 新增任务：`task_107`
- 结论：
  - 扩容成功，正式任务数推进到 `53`
  - 正式集、`frozen_20`、`frozen_40` 复跑口径继续保持全绿
  - 正式集 `average_duration_sec: 0.6551 -> 0.5237`
  - `frozen_20` `average_duration_sec: 0.6835 -> 0.5313`
  - `frozen_40` `average_duration_sec: 0.6527 -> 0.5293`
  - `v56r1` 首轮曾暴露出 `task_105` 的继承链漏接问题，但 `v56r2` 已修复并恢复全量通过
  - 当前 `frozen_40` 已重新低于长期阈值 `0.5514`
- 当前主线口径应更新为：
  - 稳定基线仍是 `improved_v50`
  - 最新扩容版本是 `improved_v56`
  - 正式任务数是 `53`
  - `frozen_40 streak` 仍是 `8`

### `improved_v57`

- 来源：`pypa/packaging#1231`
- 新增任务：`task_109`
- 结论：
  - 扩容成功，正式任务数推进到 `54`
  - 正式集、`frozen_20`、`frozen_40` 复跑口径继续保持全绿
  - 正式集 `average_duration_sec: 0.5237 -> 0.523`
  - `frozen_20` `average_duration_sec: 0.5313 -> 0.5385`
  - `frozen_40` `average_duration_sec: 0.5293 -> 0.5437`
  - `v57r1` 首轮先后暴露出两处继承链漏接：老规则集合遗漏 `v57`，以及 `v56` 的单元素 key 规则未继续继承到 `v57`
  - `v57r2 / v57r3` 修复后已恢复正式集 `54 / 54`、`frozen_20` `20 / 20` 与 `frozen_40` `40 / 40`
  - 当前 `frozen_40` 继续低于长期阈值 `0.5514`
- 当前主线口径应更新为：
  - 稳定基线仍是 `improved_v50`
  - 最新扩容版本是 `improved_v57`
  - 正式任务数是 `54`
  - `frozen_40 streak` 仍是 `8`

## 建议冷启动顺序

如果后续由新的会话继续推进，建议先读：

1. `docs/project_memory.md`
2. `docs/next_actions.md`
3. `docs/candidate_shortlist.md`
4. `docs/benchmark_registry.md`
5. `docs/results.md`
6. `docs/optimization_log.md`

## 2026-06-14 当前补充记忆

- 当前 `agronholm/anyio#88` 已形成更强证据：
  - `task_129` 已是 `accepted + ready`
  - `improved_v69` 单任务失败
  - `improved_v70` 单任务成功
  - 因此它已完成正式扩容所需的直接质量证明
- 当前 `task_129` 已正式纳入 manifest：
  - 正式任务数已从 `64` 推进到 `65`
  - `refresh_035` 已记录：
    - `formal_task_count +1`
    - `challenge_accepted_ready_not_in_any_manifest_count -1`
- 当前 `improved_v70` 已完成最小正式验证：
  - 正式集 `65 / 65`
  - `frozen_20` `20 / 20`
  - `frozen_40` `40 / 40`
- 当前更准确的性能口径是：
  - 正式集平均耗时相对 `v69` 回升：
    - `0.5656 -> 0.5924`
  - `frozen_20` 平均耗时相对 `v69` 回落：
    - `0.5975 -> 0.5803`
  - `frozen_40` 平均耗时相对 `v69` 回落：
    - `0.5861 -> 0.5582`
- 因此当前 `improved_v70` 的定位应是：
  - 最新扩容成功版本
  - 已过三线最小功能验证
  - 首轮 stability recheck 后，`frozen_40` 已是 `stable`
  - `frozen_20` 在 5 次复跑下也已进一步收敛为 `stable`
  - 但是否直接替代现有主稳定叙事锚点，仍建议结合后续真实扩容继续观察
- 当前 `agronholm/anyio#82` 也已从纯脚手架继续推进：
  - `task_128` 已是 `accepted + in_formal_manifest`
  - 已完成：
    - `improved_v70` 单任务失败
    - `improved_v71` 单任务成功
    - `v71r2` 正式集、`frozen_20`、`frozen_40` 三线最小验证
    - `v71` 的 `frozen_20 / frozen_40` stability recheck
  - 因此它已经不再是候选验证题，而是当前最新一条正式扩容证据
  - 当前稳定性口径：
    - `frozen_20 mean = 0.5727`
    - `frozen_20 std = 0.0177`
    - `frozen_20 conclusion = stable`
    - `frozen_40 mean = 0.5637`
    - `frozen_40 std = 0.0099`
    - `frozen_40 conclusion = stable`

## 2026-06-14 当前补充记忆（latest 校准）

- latest roadmap tracking 已推进到：
  - `roadmap_tracking_refresh_042`
  - headline：
    - `roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK`
- 当前最新口径应统一为：
  - 正式真实任务：`66`
  - challenge 任务：`3`
  - 生态数：`16`
  - 候选池：`69`
  - `accepted = 69`
  - `screened = 0`
  - `imported = 0`
- 当前 challenge 集已经是：
  - `task_126 / samuelcolvin/watchfiles#266`
  - `task_127 / samuelcolvin/watchfiles#110`
  - `task_130 / samuelcolvin/watchfiles#169`
- 因此 challenge 线的当前下一步不再是补第 `3` 条，而是：
  - `重新 sourcing 第 4 条 challenge 候选`
- 当前 `improved_v71` 仍是最新扩容成功版本：
  - 正式集、`frozen_20`、`frozen_40` 三线最小验证通过
  - `frozen_20 / frozen_40` stability recheck 都为 `stable`
- 当前最该保持的主线顺序仍是：
  - 继续扩正式真实 issue
  - 独立补第 `4` 条 challenge hard case
  - 若外部 sourcing 暂时受阻，再继续围绕 `run_tests` 做性能证据下钻

## 2026-06-14 当前补充记忆（refresh_043 导航校准）

- latest tracking 已继续推进到：
  - `roadmap_tracking_refresh_043`
- 这轮 refresh 虽然仍属于：
  - `refresh_outcome = no_material_change`
- 但导航层已经不再退化成泛化 `active_track`
- 当前 latest 输出已明确收敛为：
  - `history_advice.recommended_focus = challenge_track`
  - `action_board top priority = challenge_track`
  - `status_card top_priority_track = challenge_track`
  - `first_action = 重新 sourcing 第 4 条 challenge 候选`
- 这意味着后续如果只是先读 latest：
  - 已经能直接恢复当前最合适的主线
  - 不需要再先人工判断“这轮到底应该优先 challenge、formal 还是 performance”

## 2026-06-14 当前补充记忆（refresh_045 优先级稳态）

- latest tracking 已继续推进到：
  - `roadmap_tracking_refresh_045`
- 当前要特别记住的一点不是数字变化，而是导航行为变化：
  - 即使 `history_advice_category` 已回到 `monitor_and_continue`
  - 只要当前仍满足：
    - challenge 已有 `3` 条
    - shortlist 为空
    - `next_action = 重新 sourcing 第 4 条 challenge 候选`
  - latest `action_board / status_card` 仍会继续把：
    - `challenge_track`
    放在第一优先级
- 当前 latest 的第一条可执行命令已经是：
  - `python scripts/search_candidate_issues.py --query bug --target-family "文件路径与 IO" --limit 10 --run-label challenge_a4`
- 这意味着后续续做时：
  - 即使没有新的规模变化
  - 也不需要再先手工把优先级从 performance 拉回 challenge

## 2026-06-14 当前补充记忆（refresh_047 认证前置条件显性化）

- latest tracking 已继续推进到：
  - `roadmap_tracking_refresh_047`
- 当前 latest 的真实含义不是“challenge 已经没必要优先”
- 而是：
  - `history_advice_category = stalled_tracking`
  - 但 challenge 第 `4` 条候选缺口仍然最具体
  - 且 live sourcing 已确认首先卡在 GitHub 认证，而不是候选本身质量
- 当前最重要的新事实是：
  - `gh auth status` 显示：
    - `GITHUB_TOKEN` 无效
    - keyring 中的 `wangd237` 账号存在，但不是当前 active account
- 因此 latest 现在把第一条命令收口成：
  - `gh auth status`
- 随后的 challenge 命令链才是：
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4`
- 这意味着后续真正要做的不是猜“该不该继续 challenge”
- 而是：
  - 先恢复 challenge 搜题的认证前置条件
  - 再继续第 `4` 条 challenge 候选 sourcing

## 2026-06-14 当前补充记忆（认证解析已修复，当前主阻塞转为外网访问限制）

- `search_candidate_issues.py` 的认证解析现在已增强：
  - 当环境变量里的 `GITHUB_TOKEN` 明显无效时
  - 会优先尝试去掉环境污染后回退到 `gh auth token / keyring`
- 这意味着当前 challenge 搜题脚本已经不再被“坏 env token”直接卡死
- 在 `GITHUB_TOKEN='invalid-token'` 的真实复核下：
  - 已不再返回 `401 Bad credentials`
  - 当前重新收敛到的阻塞是：
    - `dial tcp ... access a socket in a way forbidden by its access permissions`
- 因此现在更准确的 handoff 结论是：
  - 认证解析问题已部分修复
  - 当前主阻塞已转为当前执行层对 GitHub API 的外网访问限制

## 2026-06-14 当前补充记忆（refresh_049 文案与 handoff 语义收口）

- latest tracking 已继续推进到：
  - `roadmap_tracking_refresh_049`
- 这轮没有改变主线判断：
  - `formal_task_count = 66`
  - `challenge_task_count = 3`
  - `ecosystem_count = 16`
  - `frozen_40_streak = 8`
  - `top_priority_track = challenge_track`
- 这轮真正修正的是 latest 文案口径：
  - `top_priority_reason`
  - 已从：
    - `首先卡在 GitHub 认证前置条件`
  - 收口为：
    - `首先卡在外部访问前置条件`
- 这样做的原因是：
  - challenge 搜题脚本对坏 `GITHUB_TOKEN` 的鲁棒性已经增强
  - 当前 live sourcing 的第一层真实阻塞更接近：
    - 当前执行层对 GitHub API 的外网访问限制
  - 因此如果后续只读 latest：
    - 不会再误以为“认证修复”仍然是唯一最先要做的工程问题
- 当前更准确的 challenge 续做顺序应记为：
  - `gh auth status`
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4`
  - 如果仍失败，优先记录新的 live 阻塞证据，再 refresh

## 2026-06-14 当前补充记忆（challenge 认证桥接继续收紧，真实阻塞稳定落到外网层）

- 这轮对第 `4` 条 challenge 候选重新做了 live 复核
- 当前更细的真实链路已经确认：
  - `gh auth status` 在清掉坏 `GITHUB_TOKEN` 后可恢复正常
  - 当前 active account 为：
    - `wangd237 (keyring)`
  - 但 `gh auth token` 在这台机器上仍返回：
    - `no oauth token found for github.com`
- 这意味着：
  - `gh 已登录`
  - 但 token 不一定可被当前进程直接导出
- 因此 `search_candidate_issues.py` 现在已继续加固为：
  - 如果能解析到 token，就显式注入 `GITHUB_TOKEN`
  - 如果解析不到 token，但 `gh` 已登录：
    - 也允许直接走 `gh` 当前会话
    - 不再在脚本内部提前报“无法获取 GitHub 认证 token”
- 这轮真实复核后，challenge live sourcing 的错误已稳定收敛为：
  - `gh search issues 失败：Post "https://api.github.com/graphql": dial tcp ... connectex: An attempt was made to access a socket in a way forbidden by its access permissions.`
- 因此当前最准确的 handoff 结论进一步收紧为：
  - challenge 搜题脚本的认证桥接层已不再是第一阻塞
  - 当前第一阻塞稳定落在：
    - 当前执行层对 GitHub API 的 socket / 外网访问限制

## 2026-06-14 当前补充记忆（challenge 本地认证准备度已进入 roadmap tracking）

- `snapshot_roadmap_status.py` 现在会额外生成：
  - `challenge_status.local_auth_readiness`
- `refresh_roadmap_tracking.py` 现在会把这组信号继续暴露到：
  - `roadmap_status_card_latest_refresh.md`
  - `roadmap_action_board_latest_refresh.md`
  - `roadmap_status_refresh_*.md`
- 当前这组 readiness 的作用不是替代 live sourcing：
  - 而是让 latest 直接说明 challenge 搜题当前本地卡在哪一层
- `refresh_051` 的一个重要现实观察是：
  - latest 已能直接显示：
    - `challenge_auth_env_token_present`
    - `challenge_auth_env_token_looks_valid`
    - `challenge_auth_gh_logged_in`
    - `challenge_auth_token_exportable`
    - `challenge_auth_preferred_search_mode`
- 当前真实 latest 显示：
  - `env token present = True`
  - `env token looks valid = True`
  - `gh logged in = False`
  - `preferred_search_mode = env_token`
- 这说明：
  - 常驻环境里当前残留了一个“形状上像 GitHub token”的环境变量
  - 它会影响 challenge 搜题的默认认证路径判断
- 因此后续只要 latest 看到：
  - `challenge_auth_preferred_search_mode = env_token`
  - 同时 live sourcing 仍失败
  - 就应优先考虑：
    - 先清理当前 shell 的 `GITHUB_TOKEN`
    - 再复核 `gh auth status / gh auth token / search_candidate_issues.py`

## 2026-06-14 当前补充记忆（refresh_052：challenge 动作建议已开始消费 readiness）

- `refresh_052` 开始，challenge 线的 `action board / status card` 不再只是展示 readiness 字段
- 而是已经根据：
  - `challenge_auth_preferred_search_mode`
  自动调整第一条动作与第一条命令
- 当前真实 latest 显示：
  - `preferred_search_mode = env_token`
  - 因此 `first_command` 已自动收口为：
    - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
- 这意味着 latest 已从：
  - “告诉你有哪些状态字段”
  进一步推进到：
  - “根据这些状态字段直接编排下一步动作”
- 因此后续如果 challenge 本地 readiness 变化为：
  - `gh_session_fallback`
  - 或 `gh_auth_token`
  - latest 的第一条命令也应随之切换，而不是继续固定写死

## 2026-06-14 当前补充记忆（refresh_054：challenge readiness 已正式进入 delta 与 history）

- 这一轮不是再新增展示字段，而是把 challenge 本地认证准备度真正接进：
  - `changed_fields`
  - `delta.field_changes`
  - `history/progress_track`
- `refresh_roadmap_tracking.py` 当前已把以下字段纳入高信号比较集合：
  - `challenge_auth_env_token_present`
  - `challenge_auth_env_token_looks_valid`
  - `challenge_auth_gh_logged_in`
  - `challenge_auth_token_exportable`
  - `challenge_auth_preferred_search_mode`
- 这意味着后续如果 readiness 发生变化：
  - latest 不只会在展示层看到字段值变化
  - 还会在 tracking 语义层被正式识别为一轮 challenge 线推进
- 本轮同时补齐了对应测试口径：
  - `test_refresh_roadmap_tracking_marks_no_material_change_when_latest_is_unchanged`
  - 已同步把 stub 的 `local_auth_readiness` 补全
  - 避免“上一份 latest 有 readiness、当前 stub 没有”导致的伪变化
- 本轮验证结果：
  - `python -m pytest tests/test_refresh_roadmap_tracking.py tests/test_snapshot_roadmap_status.py tests/test_search_candidate_issues.py tests/test_validate_challenge_shortlist.py -q`
  - `42 passed`
- 本轮 refresh：
  - `roadmap_tracking_refresh_054`
- 当前 `refresh_054` 仍是：
  - `no_material_change`
- 这不是 readiness 接线无效：
  - 而是当前真实 latest 与上一份 latest 的 readiness 状态完全一致
  - 因而被正确判定为“状态延续”
- 因此当前更准确的 handoff 结论是：
  - readiness 已经具备“进入 history/decision”的能力
  - 接下来只有当本地认证状态真的变化时，才应期待它打断当前的 `no_material_change streak`

## 2026-06-14 当前补充记忆（challenge 第 4 条任务正式接入）

- `watchfiles#215` 已从 ready challenge 草稿继续推进到：
  - `accepted`
  - `task_131`
  - `benchmarks/repos/watchfiles_215_repo`
  - `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- 这意味着当前 challenge manifest 已从：
  - `3 -> 4`
- 当前 challenge 四题分别是：
  - `task_126`
  - `task_127`
  - `task_130`
  - `task_131`
- `task_131` 当前的边界价值是：
  - 用最小固定事件序列表达 `vim` 风格保存时，单文件 watch 把 `Remove(File)` 错当真实删除
  - 从而补齐现有 watchfiles challenge 集里“编辑器保存语义”这一条边界维度
- 因此 challenge 线的下一步已从：
  - “继续把 `watchfiles#215` 压成 ready”
  变为：
  - “跑 challenge 四题全链路评测，并重新 sourcing 第 5 条候选”

## 2026-06-14 当前补充记忆（challenge 第 5 条候选 sourcing 外部阻塞已前移）

- 当前 `search_candidate_issues.py` 的 challenge 搜题认证链又补强了一步：
  - 当 shell 里残留“看起来像 GitHub token、但实际无效”的 `GITHUB_TOKEN` 时
  - 脚本现在不会直接停在第一层 401
  - 而是会继续尝试：
    - `gh` keyring token
    - `gh session fallback`
- 对应新增测试已通过：
  - `python -m pytest tests/test_search_candidate_issues.py -q`
  - `14 passed`
- 这意味着 challenge 第 `5` 条候选当前最真实的外部阻塞，已经从：
  - `bad token / auth fallback 不够稳`
  前移为：
  - `本地代理 http://127.0.0.1:7890 不可达`
- 当前真实错误形态是：
  - `proxyconnect tcp: dial tcp 127.0.0.1:7890: connectex: No connection could be made because the target machine actively refused it`
- 因此后续如果继续做第 `5` 条 challenge 候选 sourcing：
  - 不应再先怀疑脚本认证回退链
  - 而应优先检查：
    - 当前 shell 是否仍注入了代理变量
    - `127.0.0.1:7890` 代理是否真的在运行
    - 或者是否应直接移除代理变量后再试

## 2026-06-14 当前补充记忆（refresh_056：第 4 条 challenge 候选已恢复）

- 当前 challenge live sourcing 已不再卡在外网访问：
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - 之后执行 `search_candidate_issues.py`
  - 已成功拿到 `samuelcolvin/watchfiles` 的 10 条候选
- 本轮最终选择恢复到 shortlist 的候选是：
  - `samuelcolvin/watchfiles#215`
  - 标题：
    - `Problems when using vim - Remove(File) event when saving the file`
- 当前它已经完成：
  - 导入候选池
  - `screened`
  - 写入 `docs/challenge_shortlist.md`
- 同时修正了一处 tracking 口径脱节：
  - `docs/challenge_shortlist.md` 真实使用的是：
    - `## 当前最值得补的 challenge 候选`
  - `validate_challenge_shortlist.py` 之前只识别：
    - `## 下一条最值得补的 challenge 候选`
  - 这会导致 shortlist 文档里明明已有候选，snapshot 仍读成 `0`
- 当前已把 shortlist 解析改成兼容两种标题
- 并新增测试：
  - `test_extract_candidate_issue_refs_supports_current_candidate_section_heading`
- 当前验证结果：
  - `python -m pytest tests/test_validate_challenge_shortlist.py tests/test_snapshot_roadmap_status.py tests/test_refresh_roadmap_tracking.py tests/test_search_candidate_issues.py -q`
  - `43 passed`
- 当前真实 latest：
  - `roadmap_tracking_refresh_056`
  - `challenge_shortlist_candidate_count = 1`
  - `challenge_next_candidate_issue_ref = samuelcolvin/watchfiles#215`
  - `refresh_outcome = progress`
  - `top_priority_track = challenge_track`
- 因此当前 roadmap 的 challenge 线已从：
  - “空 shortlist + 连续 no_material_change”
  恢复为：
  - “已有第 4 条明确候选 + latest 重新回到 challenge 主线”

## 2026-06-14 当前补充记忆（refresh_059：watchfiles#215 已进入 screened_with_task）

- `watchfiles#215` 已继续从“仅 shortlist 候选”推进到：
  - `task_131`
  - `benchmarks/repos/watchfiles_215_repo`
  - 当前候选阶段：
    - `screened_with_task`
- 当前脚手架状态是：
  - `repo_scaffold_status = needs_manual_completion`
  - 也就是：
    - 已有本地 semi-real repo 与 task 外壳
    - 但还没有补成 ready 口径回归题
- 本轮同时修正了一处 tracking 语义问题：
  - 之前 `screened_with_task_count +1` 会被 latest 误偏向 formal 线
  - 现在已新增：
    - `challenge_status.shortlist_screened_with_task_count`
  - 用来表达：
    - shortlist 里的 challenge 候选里，有多少条已经进入本地脚手架阶段
- 当前真实 latest：
  - `roadmap_tracking_refresh_059`
  - `challenge_shortlist_candidate_count = 1`
  - `challenge_shortlist_screened_with_task_count = 1`
  - `next_candidate_issue_ref = samuelcolvin/watchfiles#215`
  - `top_priority_track = challenge_track`
- 因此当前 challenge 线又向前推进了一档：
  - 不再只是“找到了第 4 条候选”
  - 而是“第 4 条候选已经有本地 repo，可以继续压成 ready challenge 草稿”

## 2026-06-14 当前补充记忆（refresh_066：rich#2411 已进入 accepted + ready + not_in_manifest）

- `Textualize/rich#2411` 已从“仅 shortlist 候选”继续推进到：
  - `task_132`
  - `benchmarks/repos/rich_windows_rule_repo`
  - `accepted + ready + not_in_manifest`
- 当前压缩口径已经固定为：
  - 不依赖真实 Windows / PowerShell / 控制台环境
  - 只用显式 `encoding` 的 fake stream 覆盖 `Console.rule()` / `Console.print("─")`
  - 在 `cp1252 / ascii` 等 legacy 编码路径上稳定降级为 `-`
  - 在 `utf-8` 路径上仍保留 Unicode 横线
- 当前验证结果：
  - `python -m pytest benchmarks/repos/rich_windows_rule_repo/tests/test_console.py -q`
  - `3 passed`
- 当前真实 tracking：
  - `roadmap_tracking_refresh_066`
  - `accepted_candidate_count = 71`
  - `screened_candidate_count = 0`
  - `challenge_accepted_ready_not_in_any_manifest_count = 1`
  - `next_candidate_issue_ref = Textualize/rich#2411`
- 这意味着 challenge 第 `5` 条候选当前不再只是“待脚手架评估”
  - 而是已经具备进入 challenge manifest 决策阶段的本地 ready 证据

## 2026-06-14 当前补充记忆（refresh_067：rich#2411 已正式接入 challenge manifest）

- `Textualize/rich#2411` 已从 ready challenge 候选继续推进到：
  - `accepted`
  - `task_132`
  - `benchmarks/repos/rich_windows_rule_repo`
  - `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- 这意味着当前 challenge manifest 已从：
  - `4 -> 5`
- 当前 challenge 五题分别是：
  - `task_126`
  - `task_127`
  - `task_130`
  - `task_131`
  - `task_132`
- `task_132` 当前的边界价值是：
  - 用 Windows-like legacy 编码输出流稳定表达 box-drawing 字符在控制台写出路径上的安全降级
  - 从而补上现有 challenge 集里“控制台编码 / 字符降级”这一条平台边界维度
- 当前 challenge 五题评测已跑通：
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v71.json --run-label challengev71_r5`
- 当前真实 tracking：
  - `roadmap_tracking_refresh_067`
  - `challenge_task_count = 5`
  - `accepted_in_challenge_manifest_count = 5`
  - `shortlist_candidate_count = 0`
  - `next_action = 重新 sourcing 第 6 条 challenge 候选`

## 2026-06-14 当前补充记忆（refresh_068：第 6 条 challenge 候选已恢复为 rich#2457）

- 当前第 `6` 条 challenge 候选已经不再为空
- 最新恢复出来的是：
  - `Textualize/rich#2457`
  - 标题：
    - `[BUG] Console(no_color=True) does not work on Windows 10`
- 当前它已经完成：
  - 导入 candidate 池
  - `screened`
  - 写入 `docs/challenge_shortlist.md`
- 当前它在 pipeline 中的真实阶段是：
  - `screened_without_task`
- 当前真实 latest：
  - `roadmap_tracking_refresh_068`
  - `candidate_count = 72`
  - `screened_candidate_count = 1`
  - `challenge_shortlist_candidate_count = 1`
  - `challenge_next_candidate_issue_ref = Textualize/rich#2457`
  - `next_action = 优先评估 challenge 候选 Textualize/rich#2457`
- 因此当前 roadmap 的 challenge 线已从：
  - “五题 manifest 已落地，下一条候选为空”
  恢复为：
  - “已有第 6 条明确候选，下一步进入脚手架评估”

## 2026-06-14 当前补充记忆（refresh_069：rich#2457 已正式接入 challenge manifest）

- `Textualize/rich#2457` 已从 screened challenge 候选继续推进到：
  - `accepted`
  - `task_133`
  - `benchmarks/repos/rich_windows_no_color_repo`
  - `benchmarks/manifests/real_issue_tasks_challenge_v1.json`
- 当前压缩口径已经固定为：
  - 不依赖真实 Windows 控制台
  - 只保留 `legacy_windows=True + vt=False` 的最小平台分支
  - `no_color=True` 时不应再输出 Windows 样式标记
  - 相邻 `no_color=False` 路径仍保留样式能力
- 当前新增策略版本：
  - `optimization/policy_versions/improved_v72.json`
  - 新增规则：优先让 legacy Windows 分支先遵守 `no_color`
- 当前关键验证：
  - `python -m pytest benchmarks/repos/rich_windows_no_color_repo/tests/test_console.py -q`
    - 基线 `1 failed, 2 passed`
  - `python -m pytest tests/test_patcher_rich_v72.py -q`
    - `1 passed`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_133.json --policy optimization/policy_versions/improved_v72.json`
    - `final_status = success`
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v72.json --run-label challengev72_r6`
    - `success_rate = 0.5`
    - `test_pass_rate = 0.5`
- 当前真实 tracking：
  - `roadmap_tracking_refresh_069`
  - `challenge_task_count = 6`
  - `accepted_in_challenge_manifest_count = 6`
  - `shortlist_candidate_count = 0`
  - `next_action = 重新 sourcing 第 7 条 challenge 候选`
- 这意味着 challenge 线当前已从：
  - “评估第 6 条候选能否落地”
  继续推进到：
  - “六题 manifest 已落地，下一条候选重新变为空，需要继续 sourcing”

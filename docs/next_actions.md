# 下一步行动清单

本文件只记录“可以直接做的下一步”，避免每次续做时重新从长历史里推理。

## 口径校准

- 2026-06-13 已确认：
  - `improved_v68` 与 `improved_v69` 的 `pytest_additional_flags` 完全相同
  - 两者当前 runtime 配置等价
- 因此当前所有 `v68 / v69` 的 `pytest phases / importtime / matrix / matrix-set` 结果：
  - 应优先解释为 `runtime-equivalent noise probe`
  - 不应继续直接当作“runtime flags 差异实验”的主证据
- 后续如果继续使用这条线：
  - 目的应是观察噪声、稳定性和环境敏感性
  - 只有构造出真正 runtime 不同的 policy pair 后，才重新升格为 runtime 对照主线
- 已补一轮“复用旧真实日志、重生校准产物”：
  - `logs/summaries/pytest_policy_pair_phases_cohort_v68_v69_hotspots_phase_calibrated_001.json`
  - `logs/summaries/pytest_policy_pair_importtime_cohort_v68_v69_hotspots_importtime_calibrated_001.json`
  - `logs/summaries/pytest_policy_pair_matrix_set_v68_v69_triage_calibrated_001.json`
- 已进一步把这套动作固化成单脚本入口：
  - `scripts/rebuild_pytest_policy_pair_calibrated_views.py`
  - 对应总索引产物：
    - `logs/summaries/pytest_policy_pair_calibrated_view_v68_v69_hotspots_001.json`
- 已新增 semi-real 接入阶段审计入口：
  - `scripts/audit_semi_real_pipeline.py`
  - 最新真实审计：
    - `logs/summaries/semi_real_pipeline_audit_phase6_001.json`
  - 当前关键信号：
    - `formal_candidate_count = 66`
    - `accepted_in_challenge_manifest = 3`
    - `watchfiles#169` 已完成 challenge 接入：
      - `samuelcolvin/watchfiles#169`
      - 当前 issue 级判题已把目标文件收敛到：`watchfiles/main.py`、`tests/test_main.py`
      - 当前已进一步进入：`accepted + ready + task_130 + in_challenge_manifest`
    - `screened_with_task` 现在也应视为一类高价值推进信号：
      - 代表候选已不只是“人工筛过”
      - 而是已经进入本地 semi-real 任务脚手架阶段
- 其中最关键的新校准字段是：
  - `runtime_equivalent_matrix_count = 3`
- 说明当前 triage 用到的三轮 matrix 都属于同 runtime 配置下的噪声探针
- 当前如果需要快速恢复 roadmap 全局状态，可运行：
  - `python scripts/snapshot_roadmap_status.py --run-label roadmap`
  - 它会把 maturity、challenge、candidate、frozen 等关键状态收口成一份状态快照
- 当前如果需要一键刷新 roadmap 跟踪产物，可运行：
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 它会顺序刷新：
    - `validate_tasks`
    - `audit_semi_real_pipeline`
    - `analyze_benchmark_maturity`
    - `snapshot_roadmap_status`
  - 刷新后优先看稳定入口：
    - `logs/summaries/roadmap_tracking_latest_refresh.json`
    - `logs/summaries/roadmap_tracking_latest_refresh.md`
  - 当前 latest 还会额外带一层轻量 delta：
    - `previous_latest_summary_json_path`
    - `changed_fields`
    - `delta.field_changes`
    - `refresh_outcome`
    - `history_overview`
  - 因此续做时可以先看 latest，再决定是：
    - 继续扩正式集
    - 继续补 challenge sourcing
    - 还是只是在追踪链路上刷新但没有实质变化
  - 如果只是想一眼看结论，优先读：
    - `refresh_outcome.category`
    - `refresh_outcome.summary`
  - 如果你想最快从 latest markdown 跳到下一层入口，优先看：
    - `Outputs`
    - `## Fast Paths`
  - 现在 latest 已经会显式挂出：
    - `history_summary_json_path / md_path`
    - `action_board_json_path / md_path`
    - `status_card_json_path / md_path`
  - 如果这轮推进主要发生在候选筛选链路而不是正式 manifest：
    - 也要优先看 latest 里的
      - `screened_candidate_count`
      - `screened_with_task_count`
      - `imported_candidate_count`
      - `challenge_shortlist_candidate_count`
      - `challenge_next_candidate_issue_ref`
  - 因此通常不需要再去日志目录里手工翻文件名
  - 如果想看最近几轮 refresh 是连续推进、连续无变化，还是开始出现回退信号，优先看：
    - `logs/summaries/roadmap_tracking_history_latest_refresh.json`
    - `logs/summaries/roadmap_tracking_history_latest_refresh.md`
  - history latest 现在还会直接给出：
    - `advice.category`
    - `advice.summary`
    - `advice.recommended_actions`
  - 当前还新增了一层“短暂停顿记忆”：
    - 如果最近一轮是 `no_material_change`
    - 但距离最近一次 `progress` 仍在很短窗口内
    - `history_advice` 会继续返回：
      - `keep_momentum`
      - 并继承最近一次 `progress_track`
    - 这样 handoff 时不会因为一轮空转就立刻丢掉主线
  - 当 `recent_no_material_change_streak` 很长时，优先按 advice 切回真正的主线动作，而不是继续只跑 refresh
  - 但要注意这个窗口是有限的：
    - 以当前真实 latest `roadmap_tracking_refresh_029` 为例
    - `recent_no_material_change_streak = 3`
    - 因此 advice 已合理回到 `monitor_and_continue`
    - 说明现在更需要新的实质推进，而不是继续靠 refresh 维持 momentum
  - 如果只想看一个“当前该做什么”的总入口，直接看：
    - `logs/summaries/roadmap_action_board_latest_refresh.json`
    - `logs/summaries/roadmap_action_board_latest_refresh.md`
  - 当前如果 action board 把 performance 线排到第 `1` 优先级：
    - 不要先只跑 refresh
    - 优先按它给出的顺序先补：
      - `env baseline`
      - `duration compare`
    - 然后再回到 refresh 做状态收口
  - 现在 refresh 已经能把这类 performance 证据识别成高信号推进：
    - 不再只靠 `formal_task_count / candidate_count` 这类规模字段
    - `performance_status` 更新也会进入 `changed_fields`
  - 现在即使随后一轮 refresh 没有新增证据：
    - latest handoff 也不会退回泛化 `active_track`
    - 而会继续保留最近一次 progress 所属的主线
  - 如果只想先用最小信息恢复上下文，直接看：
    - `logs/summaries/roadmap_status_card_latest_refresh.json`
    - `logs/summaries/roadmap_status_card_latest_refresh.md`
  - status card 现在不只保留正式集 / 冻结集状态，也会直接给出：
    - `candidate`
    - `screened`
    - `screened_with_task`
    - `imported`
    - challenge shortlist 当前是否已有下一候选
  - action board 现在已经把：
    - 优先级
    - 下一步动作
    - 推荐命令
    - 推荐文档入口
    - 完成信号
    - 回到 refresh 的触发点
    - refresh 后应重点观察的 tracking 信号
    收口到同一个地方

## 当前最高优先级

### 0. 用 maturity 审计结果驱动后续推进

目标：

- 让每轮推进都直接对应 `Benchmark Maturity v1` 的量化缺口
- 避免每次续做都重新手工盘点规模、生态覆盖和 frozen 进度

完成标准：

- 每次重要更新后至少补一轮：
  - `python -m scripts.analyze_benchmark_maturity --run-label maturity`
- 至少同步最新审计结果到：
  - `docs/project_memory.md`
  - `docs/optimization_log.md`

当前状态：

- 已新增 `scripts/analyze_benchmark_maturity.py`
- 最新审计结果：
  - 正式任务数：`66 / 60`
  - 来源生态数：`16 / 6`
  - frozen 集合：`40 / 40`
  - `frozen_40` 连续版本：`8 / 5`

### 1. 以 `frozen_20` 作为后续策略升级的固定基线

目标：

- 后续每新增一个 `improved_vXX`
- 都优先在 `real_issue_tasks_frozen_20_v1.json` 上补一轮同集合评测

完成标准：

- baseline / improved 使用完全相同的 `20` 条任务
- 至少保留 `1` 份 compare 报告
- 报告里明确记录成功率、测试通过率和 taxonomy 变化

### 2. 继续扩新来源，并在 `60+` 基础上扩容正式任务

目标：

- 从新的候选来源中持续补充高质量 issue
- 形成新的 `task_121` 之后的后续编号任务
- 继续扩充正式真实任务集

完成标准：

- 单轮至少新增 `1` 到 `3` 条正式任务
- 优先补足还没覆盖或覆盖较薄的仓库来源
- 新任务进入 `benchmarks/manifests/real_issue_tasks.json`
- 扩容后仍保持任务集整体稳定

当前状态：

- 当前高优先级 shortlist 已重新建立
- 已新增缺陷覆盖分析脚本：
  - `scripts/analyze_defect_coverage.py`
- 已生成当前可信 gap report：
  - `logs/summaries/defect_coverage_v2_gap_analysis_002.md`
- 已新增 A2 找题 brief：
  - `docs/issue_sourcing_brief_a2.md`
- 已新增半自动候选搜索脚本：
  - `scripts/search_candidate_issues.py`
- 已增强 semi_real 脚手架入口：
  - `scripts/scaffold_semi_real_task.py --from-candidate`
  - `scripts/scaffold_semi_real_task.py --dry-run`
- 候选状态机已切到最小版：
  - `imported -> screened -> accepted -> completed`
  - `screened -> blocked`
- 已完成状态机相关脚本收口：
  - `scripts/validate_tasks.py` 已按新状态校验 candidate
  - `scripts/import_issue_batch.py` 已改用 `draft_task_count` 输出口径
  - `scripts/run_real_issue_eval.py` 已能在汇总中动态派生 `completed`
- 已补齐搜索结果接入候选池的入口：
  - `scripts/import_search_results.py`
  - 可把 `candidate_search_*.json` 直接导入 `real_world_candidates.json`
- 已修正 candidate search 的基础启发式去噪：
  - 代码块与 URL 不再直接参与 family / risk 推断
  - 文本/编码/wrapping 类 issue 的命中质量更高
- 已补 A2 定向搜索入口：
  - `search_candidate_issues.py --target-family 并发与协程`
  - `search_candidate_issues.py --target-family "文件路径与 IO"`
- 已增强候选筛选入口：
  - `scripts/screen_candidate.py` 支持按状态批量逐条筛选
  - 默认最适合清理 `imported` 候选池
- `real_issue_tasks_frozen_40_v1.json` 已正式创建
- 当前已经累计到 `frozen_40 streak = 8`
- 当前已经完成 `task_109 / improved_v57` 的功能扩容，并已补齐正式集、`frozen_20`、`frozen_40` 三线验证
- 当前已经完成 `task_111 / improved_v58` 的正式集、`frozen_20`、`frozen_40` 三线验证，并补强结构化 issue 导入链路
- 当前已经完成 `task_113 / improved_v59` 的正式集、`frozen_20`、`frozen_40` 三线验证
- 当前已经完成 `task_115 / improved_v60` 的正式集、`frozen_20`、`frozen_40` 三线验证
- 当前已经完成 `task_117 / improved_v61` 的正式集、`frozen_20`、`frozen_40` 三线验证
- 当前已经完成 `task_119 / improved_v62` 的正式集验证，并在 `frozen_20`、`frozen_40` 上确认功能继续全绿
- 当前已经完成 `task_121 / improved_v63` 的正式集、`frozen_20`、`frozen_40` 三线验证
- 当前 `v63` 在 `frozen_40` 上的绝对耗时是 `0.5594`，仍高于 `improved_v32` 阈值 `0.5514`
- 正式任务数 `60` 的规模目标已经达成
- `v63r3` 已把 `frozen_40` 复跑口径拉回 `0.5454`，重新低于长期阈值 `0.5514`
- 下一轮重点可以从“补齐 Benchmark Maturity v1”切换到“在 v1 已达成的前提下继续扩题、扩来源并提升自动化治理能力”
- 当前最自然的后续动作是：
  - `task_123` 已纳入正式 manifest，`improved_v65` 的正式集 / frozen 集最小验证与 stability recheck 已完成
  - `v65` 当前更准确的结论是“扩容成功、三线无回归、冻结集稳定性复跑 stable、平均耗时相对 v64 小幅改善”
  - 候选池当前真实状态是 `accepted=64 / screened=1 / imported=0`
  - `anyio#1111` 已推进到 `accepted`，并已生成并纳入正式任务 `task_124 + anyio_cancellation_spin_repo`
  - 已确认：
    - `improved_v65` 在 `task_124` 上单任务失败
    - `improved_v66` 在 `task_124` 上单任务成功
  - `improved_v66` 已完成正式集 / `frozen_20` / `frozen_40` 三线最小验证
  - 已完成针对 `v66` 的时延定位：
    - 主增量集中在 `run_tests` 的 subprocess / pytest collection 链路
  - `improved_v67` 已作为失败实验被否证：
    - 关闭 `debugging + unraisableexception + threadexception` 会触发 `_pytest.debugging` 的 `trace` 选项错误
  - `improved_v68` 已确认：
    - 正式集 `63 / 63`
    - `frozen_20` `20 / 20`
    - `frozen_40` `40 / 40`
    - 相对 `v66`，正式集 `0.5514 -> 0.5424`
    - 相对 `v66`，`frozen_20` `0.5867 -> 0.5609`
    - 相对 `v66`，`frozen_40` `0.5732 -> 0.5589`
    - `frozen_20 / frozen_40` stability recheck 均为 `stable`
  - `improved_v69` 已确认：
    - 正式集 `64 / 64`
    - `frozen_20` `20 / 20`
    - `frozen_40` `40 / 40`
    - `frozen_20 / frozen_40` stability recheck 均为 `stable`
    - 但平均耗时相对 `v68` 有所回升，因此当前最优先动作是补时延定位，而不是直接继续扩题
  - 下一步优先切回：
    - 以 `v69` 作为当前最新扩容版本继续推进
    - 优先先做 `v68 -> v69` 时延定位，再决定是否做 `v70`
    - `samuelcolvin/watchfiles#266` 已推进到 `accepted`，并已落本地 ready semi-real：
      - `benchmarks/tasks/task_126.json`
      - `benchmarks/repos/watchfiles_266_repo`
    - 当前更准确的下一步是：
      - 先放入独立 challenge manifest 持续观察
      - 如后续代表性证据更强，再决定是否纳入正式 manifest
  - 继续把 A2 扩来源重点保持在 `并发与协程` 与 `文件路径与 IO`
  - `agronholm/anyio#1113` 已经完成：
    - `accepted`
    - `task_125`
    - `benchmarks/repos/anyio_check_cancelled_repo`
    - `improved_v68` 单任务失败 / `improved_v69` 单任务成功 / 正式接入
  - `agronholm/anyio#82` 已继续推进到：
    - `screened + 已生成脚手架`
    - `task_128`
    - `benchmarks/repos/anyio_82_repo`
  - `agronholm/anyio#88` 也已继续推进到：
    - `accepted + ready`
    - `task_129`
    - `benchmarks/repos/anyio_88_repo`
  - 当前这条新推进意味着：
    - `accepted_ready_not_in_any_manifest_count` 现在也应成为 refresh 可见的高信号变化
    - A 线现在可以继续二选一：
      - 把 `task_128` 收敛成 ready bug repo
      - 或对 `task_129` 直接做单任务修复验证，再决定是否纳入正式 manifest
  - 当前下一步已明确切到：
    - 对 `v68 -> v69` 的耗时回升补一轮定位
    - 再决定是否需要 `v70` 做性能回收
  - `v68 -> v69` 的时延定位现已补齐：
    - 正式集公共 `63` 条任务平均增量：`+0.0241s`
    - `frozen_20` 公共 `20` 条任务平均增量：`+0.0366s`
    - `frozen_40` 公共 `40` 条任务平均增量：`+0.0272s`
    - 正式集 trace 顶层工具主增量：
      - `run_tests = +0.8885s`
      - `search_code = +0.5797s`
  - 因此下一步进一步收窄为：
    - 先补 `run_tests` 与 `search_code` 的细分定位
    - 再决定是否做只回收性能、不扩题的 `improved_v70`
  - `search_code` 细分定位也已补齐：
    - 公共 `63` 条任务 `63 / 63` 查询签名完全一致
    - 其中 `56 / 63` 个任务是在查询不变时仍然变慢
    - `search_code` 总增量 `+0.5797s` 中，有 `+0.5614s` 来自第一条搜索
  - 因此 `search_code` 这条线的下一步也已明确：
    - 优先做冷启动 / 热启动基准
    - 再决定是否需要评估 `rg` 或缓存式搜索实现
  - `search_code` 冷启动 / 热启动基准现已补齐：
    - `task_123` 与 `task_119` 单独实验都没有复现大幅回升
    - 当前更像 batch run 上下文噪声，而不是 search_code 函数本体稳定变慢
  - 已补对应复核入口：
    - `scripts/recheck_policy_pair_tasks.py`
  - 所以下一步进一步收窄为：
    - 先重跑少量热点任务复核 `v68 / v69` 差异
    - 如果不能稳定复现，就把 `run_tests` 重新升为 `v70` 主攻方向
  - 推荐先跑：
    - `task_123`
    - `task_119`
    - `task_097`
    - `task_034`
  - 推荐命令：
    - `python scripts/recheck_policy_pair_tasks.py --task benchmarks/tasks/task_123.json --task benchmarks/tasks/task_119.json --task benchmarks/tasks/task_097.json --task benchmarks/tasks/task_034.json --baseline-policy optimization/policy_versions/improved_v68.json --improved-policy optimization/policy_versions/improved_v69.json --repetitions 3 --run-label v68_v69_hotspots`
  - 当前这轮真实复核结果也已补齐：
    - `logs/summaries/policy_pair_recheck_v68_v69_hotspots_001.json`
  - 结论：
    - `average_duration_delta_sec = -0.0149`
    - `average_search_code_delta_sec = -0.0095`
    - `average_run_tests_delta_sec = -0.0041`
    - `reproduced_search_code_task_count = 0 / 4`
    - `reproduced_run_tests_task_count = 1 / 4`
  - 因此当前更稳妥的下一步已经更新为：
    - 把 `search_code` 回升降级为次要线索
    - 把 `run_tests` 重新升为 `v70` 主攻方向
  - 现在又进一步补了一轮拆分版复核：
    - `logs/summaries/policy_pair_recheck_v68_v69_hotspots_split_001.json`
  - 新结论：
    - `average_run_tests_delta_sec = -0.018`
    - `average_run_tests_first_delta_sec = -0.0117`
    - `average_run_tests_second_delta_sec = -0.0064`
  - 因此下一步应更聚焦：
    - 优先沿第一次 `run_tests` 对应的 pre-test / collect 链路下钻
    - 第二次 `run_tests` 作为次级观察项保留
  - 已补环境基线快照入口：
    - `scripts/snapshot_env_baseline.py`
    - 默认会对 `python -c "pass"` 与 `python -m pytest --version` 做重复采样
  - 已增强时延分析入口：
    - `scripts/analyze_duration_regressions.py --env-baseline`
    - 当环境快照包含 comparison 段时，会额外输出 `env_adjusted_common_average_delta_sec`

### 3. 用时延分析脚本定位最近的系统性变慢

目标：

- 基于 `scripts/analyze_duration_regressions.py`
- 持续比较相邻两轮 batch run 的公共任务耗时变化
- 找出是少数热点任务异常，还是整组任务普遍变慢

完成标准：

- 至少保留 `1` 份扩容集时延分析报告
- 至少保留 `1` 份 `frozen_20` 时延分析报告
- 在优化日志里明确记录 top regressions 和后续假设
- 至少保留 `1` 份 trace 热点分析报告，确认主要热点工具
- 至少保留 `1` 份单任务历史时延分析报告，确认热点任务是稳定变慢还是高方差抖动
- 至少保留 `1` 份热点任务集合历史分析报告，确认回升是否具有群体一致性
- 至少保留 `1` 份环境基线快照，帮助区分环境漂移和真实策略回归
- 至少把新候选保持在 “imported -> screened -> accepted -> ready -> 单任务验证 -> 正式接入” 的连续推进节奏，而不是回到只找题不落地
- 已完成一轮 `v68 -> v69` 的 batch 时延 compare 与 trace 热点分析
- 当前下一步应优先补：
  - 热点任务 `v68 / v69` 小规模重跑复核
  - 热点任务历史分布复核
  - 必要时再补带环境快照的 compare 口径

### 5. 继续下钻 pytest 启动与 collection 开销

目标：

- 在已经确认 workspace copy 不是主因之后
- 继续定位 `run_tests` 命令执行链里到底是哪一段在回升
- 尽量把“猜测 pytest 变慢”变成可复现、可比较的实验结论

完成标准：

- 至少保留 `1` 份针对 pytest 启动或 collection 的细分实验报告
- 明确比较首次运行与重复运行差异
- 尽量区分命令执行、import/collection、摘要提取三类开销
- 在优化日志里明确记录“已排除项”和“当前最可信主因”

当前状态：

- 已完成一轮 `pytest` 分阶段细分实验
- 已确认热点任务的主要额外开销位于 `pytest` 启动与 `collect-only`
- 已完成一轮 `pytest importtime` 细分实验
- 已确认 `collect-only` 阶段稳定多出 `37` 个模块和约 `20898us` import self time
- 已完成一轮 `pytest` 插件变体细分实验
- 已确认 `_001` 样本受命令拼接 bug 污染
- 已用 `_002` 样本修正结论：`minimal_safe_plugins` 可稳定减少约 `31.7ms`、`5853us` import self time 和 `22` 个模块
- 已用 `_003` 样本继续拆出 `debug_exception_plugins`
- 已确认 `debug_exception_plugins` 单独可稳定减少约 `23.5ms`
- 已用 `_004` 样本继续拆成单插件
- 已确认 `unraisableexception_only` 单独可稳定减少约 `28.2ms`
- 已确认 `threadexception_only` 没有稳定收益
- 已把 `pytest` 分阶段 / importtime / 插件变体诊断脚本补成支持 `--policy`
- 这意味着后续可以直接按策略版本复跑：
  - `scripts/benchmark_pytest_phases.py --policy ...`
  - `scripts/benchmark_pytest_importtime.py --policy ...`
  - `scripts/benchmark_pytest_plugin_variants.py --policy ...`
- 已新增同任务双策略摘要 compare 入口：
  - `scripts/compare_pytest_policy_pair.py`
- 已新增多任务双策略 compare cohort 汇总入口：
  - `scripts/analyze_pytest_policy_pair_cohort.py`
- 已新增多任务策略版 pytest 一键编排入口：
  - `scripts/run_pytest_policy_pair_matrix.py`
- 已完成 `v51` 的环境级复跑校验
- 已确认同环境下 `improved_v50` 的 `frozen_40` 也从 `0.5410` 回升到 `0.6616`
- 当前更应优先排查环境或 `run_tests` 执行链路整体漂移，而不是直接把回升归因到新 patch 规则
- 当前 `search_code` 已被热点任务复跑降级后，下一步应优先用上述三条脚本直接比较：
  - `improved_v68`
  - `improved_v69`
  - 后续 `improved_v70`
- 当前已补第一轮真实 compare：
  - `pytest_policy_pair_task123_phase_v68_v69_001.json`
  - `pytest_policy_pair_task123_importtime_v68_v69_001.json`
  - `pytest_policy_pair_task119_phase_v68_v69_001.json`
  - `pytest_policy_pair_task119_importtime_v68_v69_001.json`
- 当前结论：
  - `task_123` phase 侧差异都很小，最明显的是 `full_first_minus_repeated_delta_sec = +0.0341`
  - `task_123` importtime 侧 `collect_wall_delta_sec = -0.0007`，但 `collect_import_self_delta_us = +5753`
  - `task_119` phase / importtime 差异都接近噪声级
  - 因此当前证据仍不足以支持“直接为 v70 改 runtime 实现”
- 当前第二轮真实 compare 也已补齐：
  - `pytest_policy_pair_task097_phase_v68_v69_001.json`
  - `pytest_policy_pair_task097_importtime_v68_v69_001.json`
  - `pytest_policy_pair_task034_phase_v68_v69_001.json`
  - `pytest_policy_pair_task034_importtime_v68_v69_001.json`
- 新结论：
  - `task_097` phase 侧表现为：
    - `pytest_startup_over_python_delta_sec = -0.0051`
    - `collect_over_pytest_startup_delta_sec = +0.0114`
    - `full_over_collect_delta_sec = +0.0098`
  - `task_097` importtime 侧表现为：
    - `collect_wall_delta_sec = -0.0182`
    - `collect_import_self_delta_us = -12204`
    - `collect_unique_module_delta = 0`
  - `task_034` phase 侧表现为：
    - `pytest_startup_over_python_delta_sec = -0.0539`
    - `collect_over_pytest_startup_delta_sec = +0.0446`
    - `full_over_collect_delta_sec = +0.0093`
  - `task_034` importtime 侧表现为：
    - `collect_wall_delta_sec = +0.0277`
    - `collect_import_self_delta_us = +14898`
    - `collect_unique_module_delta = 0`
  - 四任务合起来的更稳妥口径已经更新为：
    - `v68 / v69` 之间暂时看不到单一、稳定、跨任务一致的主因
    - `collect` 链路仍然是当前最值得继续积累证据的方向
    - 现阶段仍不应仅凭这组证据直接做 `v70` runtime 改动
- 当前又进一步补了 4 任务 cohort 聚合：
  - `pytest_policy_pair_phases_cohort_v68_v69_hotspots_phase_001.json`
  - `pytest_policy_pair_importtime_cohort_v68_v69_hotspots_importtime_001.json`
- cohort 聚合后的新口径：
  - phase 聚合：
    - `average_pytest_startup_over_python_delta_sec = -0.0139`
    - `average_collect_over_pytest_startup_delta_sec = +0.0118`
    - `average_full_over_collect_delta_sec = +0.0054`
    - `collect_slower_task_count = 2 / 4`
    - `full_slower_task_count = 3 / 4`
  - importtime 聚合：
    - `average_collect_wall_delta_sec = +0.0026`
    - `average_collect_import_self_delta_us = +1197`
    - `collect_wall_slower_task_count = 2 / 4`
    - `collect_import_self_higher_task_count = 2 / 4`
  - 因此当前最稳妥的判断进一步更新为：
    - `collect` 在 phase 聚合上仍偏正向变慢，值得继续盯住
    - 但 importtime 聚合整体仍接近噪声，不支持把回升直接归因成稳定的 import 链恶化
    - 下一步应继续扩样本，而不是立即做 `v70` runtime 回收版本
- 当前又补了一轮一键编排 matrix 真实结果：
  - `pytest_policy_pair_matrix_v68_v69_hotspots_matrix_001.json`
  - `pytest_policy_pair_phases_cohort_v68_v69_hotspots_matrix_phase_001.json`
  - `pytest_policy_pair_importtime_cohort_v68_v69_hotspots_matrix_importtime_001.json`
- 这轮更完整编排下的新口径是：
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
  - 因此当前最稳妥的判断再次更新为：
    - “collect 普遍变慢”这条假设在当前更完整编排下没有站稳
    - 当前更像是 `pytest startup` 与 `full run` 比 `collect` 更值得继续观察
    - `importtime` 聚合整体没有支持稳定恶化
    - 现阶段仍不应急着直接做 `v70`
- 当前又补了一轮“历史 run_tests 热点集合” matrix：
  - `pytest_policy_pair_matrix_v68_v69_run_tests_hotspots_matrix_001.json`
  - `pytest_policy_pair_phases_cohort_v68_v69_run_tests_hotspots_matrix_phase_001.json`
  - `pytest_policy_pair_importtime_cohort_v68_v69_run_tests_hotspots_matrix_importtime_001.json`
- 这轮历史热点集合的新口径是：
  - phase 聚合：
    - `average_pytest_startup_over_python_delta_sec = +0.004`
    - `average_collect_over_pytest_startup_delta_sec = -0.0047`
    - `average_full_over_collect_delta_sec = -0.0152`
    - `startup_slower_task_count = 2 / 4`
    - `collect_slower_task_count = 2 / 4`
    - `full_slower_task_count = 1 / 4`
  - importtime 聚合：
    - `average_collect_wall_delta_sec = +0.0024`
    - `average_collect_import_self_delta_us = +8255`
    - `collect_wall_slower_task_count = 1 / 4`
    - `collect_import_self_higher_task_count = 3 / 4`
  - 因此当前最稳妥的判断又进一步收敛为：
    - 在历史热点集合上，`startup / collect / full run` 三条线都没有形成足够稳定的单主因
    - `importtime` 有一定偏正，但仍不足以支撑“稳定系统级恶化”
    - 现阶段更适合继续扩样本或重复 matrix，而不是直接做 `v70`
- 当前又补了一层跨三轮 matrix 的总聚合：
  - `pytest_policy_pair_matrix_set_v68_v69_triage_001.json`
  - 它汇总了：
    - `v68_v69_hotspots_matrix`
    - `v68_v69_run_tests_hotspots_matrix`
    - `v68_v69_control_group_matrix`
- 跨集合聚合后的新口径是：
  - `average_startup_delta_sec = +0.0051`
  - `average_collect_delta_sec = -0.0089`
  - `average_full_delta_sec = -0.0023`
  - `average_collect_wall_delta_sec = +0.0032`
  - `average_collect_import_self_delta_us = +6506.3333`
  - `startup_positive_matrix_count = 3 / 3`
  - `collect_positive_matrix_count = 1 / 3`
  - `full_positive_matrix_count = 1 / 3`
  - `collect_import_positive_matrix_count = 3 / 3`
- 因此当前最稳妥的结论再次更新为：
  - 如果性能主线还要继续追因，第一优先级应从 `collect` 切到 `pytest startup`
  - `collect` 不再适合作为当前主线嫌疑点
  - `importtime` 更适合保留为次级观察项，而不是直接定责主因
  - 若再补 1 到 2 轮 matrix 后趋势不再强化，就应暂时把性能主线降权，切回 A 线扩题
- 已完成 `v56` 的正式集、`frozen_20`、`frozen_40` 验证及复跑
- 已确认 `v56` 相对 `v55` 在功能上继续无回归
- 已确认复跑口径下正式集 `0.6551 -> 0.5237`、`frozen_20` `0.6835 -> 0.5313`、`frozen_40` `0.6527 -> 0.5293`
- 说明这轮不只是扩容成功，还把固定 `40` 条集合重新拉回长期阈值以内
- 已完成一轮 `pytest importtime` 分组分析
- 已确认新增 import 开销主要落在 `pytest_optional_plugins / windows_ctypes / xml_stack / terminal_chain`
- 已新增 `improved_v36`，在 `improved_v35` 基础上补充 `packaging wheel compressed tag order` 修复规则
- 已在 `frozen_20` 上验证 `improved_v36`：`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5402 -> 0.5386`
- 已在正式 `33` 条任务集上验证 `improved_v36`：`success_count = 32 -> 33`、`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.535 -> 0.5312`
- 已新增 `improved_v37`，在 `improved_v36` 基础上补充 `tomlkit boolean(True)` 布尔字面量修复规则
- 已在 `frozen_20` 上验证 `improved_v37`：`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5386 -> 0.5687`
- 已在正式 `34` 条任务集上验证 `improved_v37`：`success_count = 33 -> 34`、`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5312 -> 0.6038`
- 已新增 `improved_v38`，在 `improved_v37` 基础上补充 `OutOfOrderTableProxy.pop()` 删除同步规则
- 已在 `frozen_20` 上验证 `improved_v38`：`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5687 -> 0.5427`
- 已在正式 `35` 条任务集上验证 `improved_v38`：`success_count = 34 -> 35`、`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.6038 -> 0.553`
- 已新增 `improved_v39`，在 `improved_v38` 基础上补充 super table 下 dotted key 父级前缀保留规则
- 已在 `frozen_20` 上验证 `improved_v39`：`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5427 -> 0.5443`
- 已在正式 `36` 条任务集上验证 `improved_v39`：`success_count = 35 -> 36`、`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.553 -> 0.5453`
- 已新增 `improved_v40`，在 `improved_v39` 基础上补充 AsyncLoopContext.__repr__ 的 async 表示层修复规则
- 已在 `frozen_20` 上验证 `improved_v40`：`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5443 -> 0.5682`
- 已在正式 `37` 条任务集上验证 `improved_v40`：`success_count = 36 -> 37`、`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5453 -> 0.5717`
- 已新增 `improved_v41`，在 `improved_v40` 基础上补充 jinja indent 首行空白与 `blank=False` 交互规则
- 已在 `frozen_20` 上验证 `improved_v41`：`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5682 -> 0.5185`
- 已在正式 `38` 条任务集上验证 `improved_v41`：`success_count = 37 -> 38`、`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5717 -> 0.5173`
- 已新增 `improved_v42`，在 `improved_v41` 基础上补充 tomlkit dotted inline table 后续键值换行规则
- 已在 `frozen_20` 上验证 `improved_v42`：`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5185 -> 0.5186`
- 已在正式 `39` 条任务集上验证 `improved_v42`：`success_count = 38 -> 39`、`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.5173 -> 0.5157`
- 当前可以把 `v42` 视为继续扩容与创建 `frozen_40` 的候选基线

### 4. 持续清理候选池

目标：

- 维持当前 `imported` 候选不过度堆积
- 从新的来源补充候选后，继续及时收敛
- 尽量把高质量候选推进为 `accepted`
- 把明显不适合的候选明确标为 `blocked`

完成标准：

- 候选池里“高优先级但未决”的 issue 数量持续下降
- `docs/candidate_shortlist.md` 始终只保留最值得推进的少量候选

## 建议执行顺序

1. 先看 `docs/candidate_shortlist.md`
2. 用 `scripts/import_issue_batch.py` 导入一批新来源 issue
3. 从新来源里确认下一条要推进的 issue
4. 生成 draft task 和 semi_real repo
5. 补 patch 规则与 policy
6. 跑单任务分辨测试
7. 跑扩容对比
8. 再用 `frozen_20` 跑同集合 compare
9. 用 `scripts/analyze_duration_regressions.py` 补一轮时延分析
10. 用 `scripts/analyze_trace_hotspots.py` 补一轮 trace 热点分析
11. 用 `scripts/analyze_task_history.py` 下钻热点任务历史分布
12. 用 `scripts/analyze_task_history_cohort.py` 汇总热点任务集合
13. 用 `scripts/benchmark_run_tests_modes.py` 和 `scripts/analyze_run_tests_mode_cohort.py` 排除 workspace copy 假设
14. 继续拆 pytest import / collection 的内部差异、平台链路与解释器抖动
15. 继续扩真实 issue 正式任务，在当前 `64` 条基础上优先补薄弱生态与缺陷类型
16. 继续在 `real_issue_tasks_frozen_40_v1.json` 上维持连续无回归证据，不让现有 `streak = 8` 回退
17. 视情况继续拆 `unraisableexception + debugging` 的组合边界，但优先级低于 benchmark maturity 主线
18. 跑一轮 `python -m scripts.analyze_benchmark_maturity --run-label maturity` 更新量化缺口
19. 最后同步 `README.md`、`GUIDE.md`、`docs/results.md`、`docs/optimization_log.md`

## 当前推荐下一阶段动作

优先级建议：

1. 扩新来源，补下一批 GitHub issue 候选
2. 以 `improved_v69` 作为当前最新扩容版本继续推进，同时把 `improved_v50` 保留为 `frozen_40` 长期对比锚点，并把 `improved_v68` 保留为上一轮性能更优参考
3. 在继续扩题的同时，观察后续版本能否持续守住当前已经恢复的 `frozen_40` 长期阈值与 stability 结论

补充说明：

- 当前 `tomlkit#440` 已经落地为 `task_079`
- 当前 `tomlkit#504` 已经落地为 `task_081`
- 当前 `packaging#1204` 已经落地为 `task_083`
- 当前 `pydantic#13257` 已经落地为 `task_085`
- 当前 `tomlkit#439` 已经落地为 `task_087`
- 当前 `jinja#2165` 已经落地为 `task_089`
- 当前 `packaging#1240` 已经落地为 `task_091`
- 当前 `click#3572` 已经落地为 `task_093`
- 当前 `click#3125` 已经落地为 `task_095`
- 当前 `click#3571` 已经落地为 `task_097`
- 当前 `jinja#2108` 已经落地为 `task_099`
- 当前 `tomlkit#505` 已经落地为 `task_101`
- 当前 `tomlkit#295` 已经落地为 `task_103`
- 当前 `pytest#14189` 已经落地为 `task_105`
- 当前 `tomlkit#430` 已经落地为 `task_107`
- 当前 `packaging#1231` 已经落地为 `task_109`
- 当前新的候选库存已清空高优先级存量，后续应继续把新增候选从 `imported` 及时收敛到 `screened / blocked`
- 当前最新落地状态已经推进到正式 `64` 条，且 `v69` 已完成正式集全绿、冻结集功能验证与 stability recheck，但仍需继续补性能定位
- 当前已补一轮更直接的 frozen 对比证据：
  - `logs/summaries/duration_compare_frozen40_v68_v69_001.json`
  - 当前 `common_average_delta_sec = 0.0272`
  - top regression 任务当前优先可看：
    - `task_050`
    - `task_034`
    - `task_022`
- 当前 `roadmap_tracking_refresh_026` 已验证：
  - 新的 performance 证据补充会触发 `refresh_outcome = progress`
  - 而不是继续被吞成 `no_material_change`
- 当前 `roadmap_tracking_refresh_027` 已验证：
  - 虽然本轮回到 `no_material_change`
  - 但 latest `action_board / status_card` 仍保留：
    - `performance_track`
  - 因此后续续做不会丢失正在推进的主线
- 因此下一轮更应该优先“在 v1 已达成的前提下继续扩新来源、扩正式任务规模，并把同版复跑与性能复核纳入常规流程”，而不是再把“达到 60 条”当作主目标
- 当前扩容优先级已明确调整为：
  - `并发与协程`
  - `文件路径与 IO`
  - 其次是来自新生态的 `继承、优先级与控制流`
- challenge 线当前建议的下一步是：
  - `watchfiles#110` 已从 `screened` 推进到：
    - `task_127`
    - `benchmarks/repos/watchfiles_110_repo`
    - `accepted_in_challenge_manifest`
  - challenge manifest 当前已扩到 `2` 条：
    - `task_126`
    - `task_127`
  - 当前更准确的下一步已经变成：
    - 继续观察 `task_127` 与 `task_130` 是否长期保持 hard case 价值
    - 重新 sourcing 第 `4` 条 challenge 候选

详细理由见：

- `docs/candidate_shortlist.md`
- `docs/challenge_shortlist.md`
- `docs/challenge_sourcing_brief_a3.md`

## 不建议现在优先碰的方向

- 需要大量框架语义判断的问题
- 更像规范解释争议的问题
- 可能要跨多个文件或多个子系统联动的问题
- 明显依赖真实仓库运行环境的大问题

## 每轮完成后要同步的最小清单

- `benchmarks/tasks/`
- `benchmarks/repos/`
- `benchmarks/manifests/`
- `optimization/policy_versions/`
- `logs/summaries/`
- `scripts/import_issue_batch.py`
- `scripts/analyze_duration_regressions.py`
- `scripts/analyze_trace_hotspots.py`
- `scripts/analyze_task_history.py`
- `scripts/analyze_task_history_cohort.py`
- `scripts/recheck_policy_pair_tasks.py`
- `scripts/benchmark_run_tests_modes.py`
- `scripts/analyze_run_tests_mode_cohort.py`
- `scripts/benchmark_pytest_phases.py`
- `scripts/analyze_pytest_phase_cohort.py`
- `scripts/benchmark_pytest_importtime.py`
- `scripts/analyze_pytest_importtime_cohort.py`
- `scripts/benchmark_pytest_plugin_variants.py`
- `scripts/analyze_pytest_plugin_variant_cohort.py`
- `scripts/analyze_pytest_importtime_groups.py`
- `README.md`
- `GUIDE.md`
- `docs/results.md`
- `docs/case_studies.md`
- `docs/optimization_log.md`

## 当前最新优先动作（2026-06-14）

- `task_128` 已形成：
  - `improved_v70` 单任务失败
  - `improved_v71` 单任务成功
- 当前也已完成：
  - `task_128` 纳入正式 manifest
  - `improved_v71` 的正式集 / `frozen_20` / `frozen_40` 最小验证
- 因此当前最值得做的第一顺位动作已经更新为：
  - 当前这一步已完成
  - `improved_v71` 的 `frozen_20 / frozen_40` stability recheck 都已补齐为 `stable`
  - 下一步转为继续扩新真实 issue 或补第 `4` 条 challenge 候选

- 当前需要记住的性能口径：
  - 正式集 `average_duration_sec: 0.5924 -> 0.5617`
  - `frozen_20: 0.5803 -> 0.5974`
  - `frozen_40: 0.5582 -> 0.5794`
  - 因此当前不是简单的“全面变慢”或“全面变快”
  - 而是：
    - 扩容成功
    - 正式集回落
    - 冻结集回升
    - 需要用 stability recheck 把信号再压实

- 当前需要额外记住的一条过程性教训：
  - `v71r1` 首轮曾因 patcher 继承链漏接出现大面积 `Premature Finish`
  - 当前已在 `app/agent/patcher.py` 中把 `v71` 继续接回 `v59 -> v43` 的旧规则链
  - `v71r2` 已恢复三线全绿
  - 这说明后续每次新增策略版本后，仍要把“旧规则继承链是否完整”作为第一类回归风险

- 当前 stability recheck 已补齐：
  - `frozen_20`
    - `mean = 0.5727`
    - `std = 0.0177`
    - `conclusion = stable`
  - `frozen_40`
    - `mean = 0.5637`
    - `std = 0.0099`
    - `conclusion = stable`
- 因此当前更准确的 `v71` 定位应更新为：
  - 最新扩容成功版本
  - 已完成三线最小验证
  - 冻结集稳定性复跑也已达 `stable`
  - 但冻结集相对 `v70` 的平均耗时仍有回升，后续应继续观察性能侧是否需要单独收敛

- 当前第二顺位动作：
  - 刷新 tracking / maturity / README 口径
  - 重点确认：
    - 正式任务数 `66`
    - 候选池 `accepted = 69`
    - latest refresh headline 已更新为：
      - `roadmap: formal=66 challenge=3 eco=16 frozen=40 streak=8 validation=OK`

- 当前第三顺位动作：
  - 重新 sourcing 第 `4` 条 challenge 候选
  - 优先看：
    - 并发与协程
    - 文件路径与 IO
    - 新生态的继承 / 控制流边界题

- 当前又新增一轮性能证据：
  - `logs/env_baselines/env_baseline_20260613T182156280991Z.json`
    - `mean_of_means_sec = 0.0815`
  - `logs/summaries/duration_compare_frozen40_v70_v71_001.json`
    - `common_average_delta_sec = +0.0212`
  - `logs/summaries/duration_compare_frozen20_v70_v71_001.json`
    - `common_average_delta_sec = +0.0171`
- 当前又新增一轮热点证据：
  - `logs/summaries/trace_hotspots_frozen40v71r2_001.json`
    - `run_tests delta_total_duration_sec = +0.9079`
  - `logs/summaries/trace_hotspots_frozen20v71r2_001.json`
    - `run_tests delta_total_duration_sec = +0.3933`
- 因此当前更准确的性能口径又收紧为：
  - `v71` 相对 `v70` 在两条冻结集上都存在正向回升
  - 且这轮回升的主增量仍然落在 `run_tests`
  - 且这轮并不是“没有新证据”的状态
  - 下一步可以继续围绕这些新 compare 产物做 refresh 收口和后续下钻

## 当前补充动作（2026-06-14 refresh_049）

- latest tracking 已更新到：
  - `roadmap_tracking_refresh_049`
- 当前 first priority 仍然是：
  - `challenge_track`
  - `重新 sourcing 第 4 条 challenge 候选`
- 但需要记住：
  - latest 的阻塞文案已经不再是：
    - `GitHub 认证前置条件`
  - 而是更准确的：
    - `外部访问前置条件`
- 因此后续最稳妥的第一组动作是：
  - `gh auth status`
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4`
- 如果仍然失败：
  - 不要只重复 refresh
  - 优先把新的 live 错误形态记录到 `docs/project_memory.md` 与 `docs/optimization_log.md`

## 当前补充动作（2026-06-14 challenge auth fallback）

- `search_candidate_issues.py` 现在已经补了新的 fallback：
  - 即使 `gh auth token` 拿不到 token
  - 也会继续尝试直接走当前已登录的 `gh` 会话
- 这意味着当前 challenge 线最前面的脚本阻塞已经继续后移
- 现在如果再次执行：
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4`
- 更可能看到的不是认证报错，而是：
  - GitHub API 外网访问 / socket 权限错误
- 因此当前最准确的下一步分叉是：
  - 如果执行环境可访问 GitHub API，就继续导入与筛选 challenge 候选
  - 如果仍被 socket 层挡住，就把这份阻塞继续视为 challenge 线当前第一外部前置条件

## 当前补充动作（2026-06-14 refresh_051 challenge readiness）

- latest tracking 现在已经会直接显示 challenge 本地认证准备度
- 续做 challenge 线前，先看：
  - `logs/summaries/roadmap_status_card_latest_refresh.md`
  - `logs/summaries/roadmap_action_board_latest_refresh.md`
- 当前重点字段是：
  - `challenge_auth_env_token_present`
  - `challenge_auth_env_token_looks_valid`
  - `challenge_auth_gh_logged_in`
  - `challenge_auth_token_exportable`
  - `challenge_auth_preferred_search_mode`
- 当前 `refresh_051` 的直接观察是：
  - `preferred_search_mode = env_token`
  - 且 `gh_logged_in = False`
- 这意味着后续如果 challenge 搜题继续失败：
  - 第一反应不应只是“再试一次”
  - 而应先清理当前 shell 的 `GITHUB_TOKEN`
  - 再复核 `gh auth status`
  - 再决定是走 `env_token` 还是 `gh_session_fallback`

## 当前补充动作（2026-06-14 refresh_052 challenge command routing）

- latest 现在不只是显示 `challenge_auth_preferred_search_mode`
- 它已经开始根据这个字段自动调整 `first_command`
- 当前 `refresh_052` 的真实 latest 是：
  - `preferred_search_mode = env_token`
  - `first_command = Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
- 因此当前 challenge 线最稳妥的开局顺序已进一步收口为：
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - `gh auth status`
  - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4`

## 当前补充动作（2026-06-14 refresh_054 challenge readiness delta/history）

- challenge readiness 现在已经不只是 latest 展示字段
- 它已正式进入：
  - `changed_fields`
  - `delta.field_changes`
  - `history/progress_track`
- 这意味着后续如果本地认证状态真的变化：
  - refresh 应该能够直接把它识别成 challenge 线信号
  - 而不是继续只显示字段、却不影响 tracking 结论
- 当前 `refresh_054` 仍然是：
  - `no_material_change`
- 直接原因不是接线失败：
  - 而是 `refresh_053 -> refresh_054` 期间
  - `challenge_auth_*` 这组 readiness 字段没有发生真实变化
- 因此下一步最值得做的不是继续空跑 refresh：
  - 而是触发一轮真实的 challenge 认证/外部访问状态变化
  - 然后再回来看 readiness 是否成功打断当前 streak
- 当前最推荐的最小动作顺序仍是：
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - `gh auth status`
  - `python scripts/search_candidate_issues.py --repo samuelcolvin/watchfiles --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_a4`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

## 当前补充动作（2026-06-14 refresh_056 第 4 条 challenge 候选恢复）

- 当前第 4 条 challenge 候选已经不再为空
- 最新恢复出来的是：
  - `samuelcolvin/watchfiles#215`
- 当前它已完成：
  - 导入 candidate 池
  - `screened`
  - 写入 `docs/challenge_shortlist.md`
- 当前 latest 已明确显示：
  - `challenge_shortlist_candidate_count = 1`
  - `challenge_next_candidate_issue_ref = samuelcolvin/watchfiles#215`
  - `top_priority_track = challenge_track`
- 因此接下来最自然的动作已经从“继续找第 4 条候选”切换成：
  - 优先评估 `watchfiles#215` 是否能压成稳定本地 challenge semi-real
- 推荐下一步顺序：
  - `gh issue view 215 --repo samuelcolvin/watchfiles`
  - `python scripts/scaffold_semi_real_task.py --from-candidate samuelcolvin_watchfiles_issue_215 --dry-run`
  - 如 dry-run 合理，再继续生成本地脚手架
  - 完成后再 `python scripts/refresh_roadmap_tracking.py --run-label refresh`

## 当前补充动作（2026-06-14 refresh_059 challenge 候选已进入 task 脚手架）

- `watchfiles#215` 当前已经不再只是 shortlist 文档上的候选
- 它已进入：
  - `task_131`
  - `benchmarks/repos/watchfiles_215_repo`
  - `screened_with_task`
- 当前更自然的下一步已从“继续找候选”切换成：
  - 把 `task_131` 从 `needs_manual_completion` 往 `ready` 推进
- 推荐顺序：
  - 先补 `watchfiles/main.py` 的最小事件归并逻辑
  - 再把 `tests/test_main.py` 从 TODO 模板压成 1 到 3 条稳定回归测试
  - 跑 `python -m pytest benchmarks/repos/watchfiles_215_repo/tests/test_main.py -q`
  - 如通过，再考虑是否推进为 challenge ready 草稿
  - 最后 `python scripts/refresh_roadmap_tracking.py --run-label refresh`

## 当前补充动作（2026-06-14 challenge 第 4 条任务已接入）

- `watchfiles#215` 当前已经不再只是 ready 草稿
- 它已继续推进到：
  - `accepted`
  - `task_131`
  - `in_challenge_manifest`
- 因此当前最自然的下一步已从：
  - “继续把 `task_131` 压成 ready”
  切换成：
  - “跑四题 challenge 集评测并重新 sourcing 第 5 条候选”
- 当前推荐顺序：
  - `python scripts/validate_challenge_shortlist.py`
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v71.json --run-label challengev71_r4`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
  - 再根据 latest 的 `next_action` 与 `challenge_shortlist_candidate_count` 决定是否立即进入第 `5` 条候选 sourcing

## 当前补充动作（2026-06-14 challenge 第 5 条候选 sourcing）

- 当前 `search_candidate_issues.py` 的认证回退链已补强：
  - 坏 `GITHUB_TOKEN` 不再是第一阻塞点
  - 现在会继续尝试 keyring token 与 `gh session fallback`
- 因此当前第 `5` 条 challenge 候选 sourcing 的最新真实阻塞已变成：
  - 本地代理 `http://127.0.0.1:7890` 不可达
- 当前最推荐的最小排障顺序是：
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - `Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue`
  - `Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue`
  - `gh auth status`
  - `python scripts/search_candidate_issues.py --repo Textualize/rich --query bug --target-family "文件路径与 IO" --state closed --labels bug --limit 10 --run-label challenge_b1_rich`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`
- 如果仍然失败：
  - 优先把新的网络 / DNS / socket 错误形态继续写入 `project_memory` 与 `optimization_log`
  - 不要退回只重复空跑 refresh

## 当前补充动作（2026-06-14 `rich#2411` 已进入 ready 决策阶段）

- `Textualize/rich#2411` 当前已经不再只是 shortlist 候选
- 它已继续推进到：
  - `task_132`
  - `benchmarks/repos/rich_windows_rule_repo`
  - `accepted + ready + not_in_manifest`
- 当前 `refresh_066` 已明确显示：
  - `accepted_candidate_count = 71`
  - `screened_candidate_count = 0`
  - `challenge_accepted_ready_not_in_any_manifest_count = 1`
- 因此当前最自然的下一步已从：
  - “继续评估是否能压成脚手架”
  切换成：
  - “决定是否把 `task_132` 接入 challenge manifest”
- 当前推荐顺序：
  - `python -m pytest benchmarks/repos/rich_windows_rule_repo/tests/test_console.py -q`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_132.json --policy optimization/policy_versions/improved_v71.json`
  - 如单任务表现符合 challenge 展示预期，再把 `task_132` 加入 `real_issue_tasks_challenge_v1.json`
  - 然后 `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v71.json --run-label challengev71_r5`
  - 最后 `python scripts/refresh_roadmap_tracking.py --run-label refresh`

## 当前补充动作（2026-06-14 `rich#2411` 已正式成为第 5 条 challenge 任务）

- `Textualize/rich#2411` 当前已经不再只是 ready 候选
- 它已继续推进到：
  - `accepted`
  - `task_132`
  - `in_challenge_manifest`
- 当前 `refresh_067` 已明确显示：
  - `challenge_task_count = 5`
  - `accepted_in_challenge_manifest_count = 5`
  - `shortlist_candidate_count = 0`
  - `next_action = 重新 sourcing 第 6 条 challenge 候选`
- 因此当前最自然的下一步已从：
  - “决定是否把 `task_132` 接入 challenge manifest”
  切换成：
  - “维护 challenge 五题集合，并继续扩第 6 条 challenge 候选”
- 当前推荐顺序：
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - `Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue`
  - `Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue`
  - `gh auth status`
  - `python scripts/search_candidate_issues.py --query bug --target-family "文件路径与 IO" --limit 10 --run-label challenge_a6`
  - `python scripts/import_search_results.py --search-result <candidate_search_json> --recommendation high --limit 3`
  - `python scripts/screen_candidate.py --status imported --limit 3`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

## 当前补充动作（2026-06-14 第 6 条 challenge 候选已恢复为 `rich#2457`）

- `Textualize/rich#2457` 当前已经不再只是临时搜索结果
- 它已进入：
  - `candidate_id = Textualize_rich_issue_2457`
  - `screened`
  - `docs/challenge_shortlist.md`
- 当前 `refresh_068` 已明确显示：
  - `candidate_count = 72`
  - `screened_candidate_count = 1`
  - `challenge_shortlist_candidate_count = 1`
  - `challenge_next_candidate_issue_ref = Textualize/rich#2457`
- 因此当前最自然的下一步已从：
  - “重新 sourcing 第 6 条 challenge 候选”
  切换成：
  - “优先评估 `rich#2457` 是否适合进入脚手架阶段”
- 当前推荐顺序：
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - `gh issue view 2457 --repo Textualize/rich`
  - `python scripts/scaffold_semi_real_task.py --from-candidate Textualize_rich_issue_2457 --dry-run`
  - 如 dry-run 合理，再生成本地脚手架
  - 完成后 `python scripts/refresh_roadmap_tracking.py --run-label refresh`

## 当前补充动作（2026-06-14 `rich#2457` 已正式成为第 6 条 challenge 任务）

- `Textualize/rich#2457` 当前已经不再只是 screened 候选
- 它已继续推进到：
  - `accepted`
  - `task_133`
  - `benchmarks/repos/rich_windows_no_color_repo`
  - `in_challenge_manifest`
- 当前 `refresh_069` 已明确显示：
  - `challenge_task_count = 6`
  - `accepted_in_challenge_manifest_count = 6`
  - `shortlist_candidate_count = 0`
  - `next_action = 重新 sourcing 第 7 条 challenge 候选`
- 当前缩题口径已经固定为：
  - 不依赖真实 Windows 10 / cmd.exe / Cmder
  - 只保留 `legacy_windows=True + vt=False` 这条最小平台语义分支
  - 用 `no_color=True` 是否仍错误输出 Windows 样式标记来表达原 issue
- 当前验证结果：
  - `python -m pytest benchmarks/repos/rich_windows_no_color_repo/tests/test_console.py -q`
    - 基线 `1 failed, 2 passed`
  - `python -m pytest tests/test_patcher_rich_v72.py -q`
    - `1 passed`
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_133.json --policy optimization/policy_versions/improved_v72.json`
    - `final_status = success`
  - `python scripts/run_challenge_eval.py --policy optimization/policy_versions/improved_v72.json --run-label challengev72_r6`
    - `task_count = 6`
    - `success_rate = 0.5`
    - `test_pass_rate = 0.5`
- 因此当前最自然的下一步已从：
  - “优先评估 `rich#2457` 是否适合进入脚手架阶段”
  切换成：
  - “重新 sourcing 第 7 条 challenge 候选，并继续观察六题 challenge 集的 hard-case 价值”
- 当前推荐顺序：
  - `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue`
  - `gh auth status`
  - `python scripts/search_candidate_issues.py --query bug --target-family "文件路径与 IO" --limit 10 --run-label challenge_a7`
  - `python scripts/import_search_results.py --search-result <candidate_search_json> --recommendation high --limit 3`
  - `python scripts/screen_candidate.py --status imported --limit 3`
  - `python scripts/refresh_roadmap_tracking.py --run-label refresh`

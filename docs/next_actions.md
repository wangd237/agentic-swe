# 下一步行动清单

本文件只记录“可以直接做的下一步”，避免每次续做时重新从长历史里推理。

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
  - 正式任务数：`52 / 60`
  - 来源生态数：`13 / 6`
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

### 2. 继续扩新来源并扩容正式任务，朝 `40+` 再到 `60+`

目标：

- 从新的候选来源中持续补充高质量 issue
- 形成新的 `task_105` 之后的后续编号任务
- 继续扩充正式真实任务集

完成标准：

- 单轮至少新增 `1` 到 `3` 条正式任务
- 优先补足还没覆盖或覆盖较薄的仓库来源
- 新任务进入 `benchmarks/manifests/real_issue_tasks.json`
- 扩容后仍保持任务集整体稳定

当前状态：

- 当前高优先级 shortlist 仍为空
- `real_issue_tasks_frozen_40_v1.json` 已正式创建
- 当前已经累计到 `frozen_40 streak = 8`
- 当前已经完成 `task_105 / improved_v55` 的功能扩容，但这轮仍暂未进入新的稳定 streak
- 下一轮重点应继续扩新来源，并在保持当前 `frozen_40` 稳定性的前提下继续把正式任务数从 `52` 推向 `60+`

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
- 已完成 `v51` 的环境级复跑校验
- 已确认同环境下 `improved_v50` 的 `frozen_40` 也从 `0.5410` 回升到 `0.6616`
- 当前更应优先排查环境或 `run_tests` 执行链路整体漂移，而不是直接把回升归因到新 patch 规则
- 已完成 `v55` 的正式集与 `frozen_20` 验证及复跑
- 已确认 `v55` 相对 `v54` 在功能上继续无回归
- 已确认复跑口径下正式集 `0.6544 -> 0.6551`、`frozen_20` `0.6697 -> 0.6835`
- 说明这轮主要是轻微性能波动，而不是明显恶化
- 但由于还没有补 `frozen_40` 同集合验证，所以暂时仍不能把 `v55` 计入新的稳定版本证据
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

- 维持当前 `to_review = 0`
- 从新的来源补充候选后，继续及时收敛
- 尽量把高质量候选推进为 `accepted`
- 把明显不适合的候选明确标为 `rejected`

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
15. 继续扩真实 issue 正式任务，把总数从 `40` 推向 `60`
16. 继续在 `real_issue_tasks_frozen_40_v1.json` 上累计连续 `5` 个策略版本的固定集合无回归证据
17. 视情况继续拆 `unraisableexception + debugging` 的组合边界，但优先级低于 benchmark maturity 主线
18. 跑一轮 `python -m scripts.analyze_benchmark_maturity --run-label maturity` 更新量化缺口
19. 最后同步 `README.md`、`GUIDE.md`、`docs/results.md`、`docs/optimization_log.md`

## 当前推荐下一阶段动作

优先级建议：

1. 扩新来源，补下一批 GitHub issue 候选
2. 以 `improved_v50` 为当前稳定基线继续扩正式任务数，同时把 `v51 / v52 / v53 / v54 / v55` 记为“扩容成功、性能恢复中”
3. 继续对 pytest import/collection、首次运行与重复运行差异做更细实验，优先把 `frozen_40` 拉回长期阈值

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
- 当前新的候选库存已清空高优先级存量，`to_review = 0`
- 当前最新 maturity 审计已经推进到 `52 / 60`
- 因此下一轮更应该优先“扩新来源 + 继续恢复 frozen40 性能 + 再决定谁是下一版稳定 streak”，而不是继续停留在候选筛选阶段

详细理由见：

- `docs/candidate_shortlist.md`

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

# 下一步行动清单

本文件只记录“可以直接做的下一步”，避免每次续做时重新从长历史里推理。

## 当前最高优先级

### 1. 以 `frozen_20` 作为后续策略升级的固定基线

目标：

- 后续每新增一个 `improved_vXX`
- 都优先在 `real_issue_tasks_frozen_20_v1.json` 上补一轮同集合评测

完成标准：

- baseline / improved 使用完全相同的 `20` 条任务
- 至少保留 `1` 份 compare 报告
- 报告里明确记录成功率、测试通过率和 taxonomy 变化

### 2. 继续扩容 1 到 2 条正式任务

目标：

- 从新的候选来源中再补充 `1` 到 `2` 条高质量 issue
- 形成新的 `task_062` 或后续编号任务
- 继续扩充正式真实任务集

完成标准：

- 单任务能区分旧策略失败 / 新策略成功
- 新任务进入 `benchmarks/manifests/real_issue_tasks.json`
- 扩容后仍保持任务集整体稳定

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
- 已完成一轮 `pytest importtime` 分组分析
- 已确认新增 import 开销主要落在 `pytest_optional_plugins / windows_ctypes / xml_stack / terminal_chain`
- 已新增 `improved_v33`，通过 policy 注入 `-p no:unraisableexception`
- 已在热点 4 任务上验证 `improved_v33`：平均总耗时 `-0.002s`，成功率保持 `1.0`
- 已在 `frozen_20` 上验证 `improved_v33`：`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.6774 -> 0.5379`
- 已在正式 `30` 条任务集上验证 `improved_v33`：`success_rate = 1.0`、`test_pass_rate = 1.0`、`average_duration_sec = 0.6778 -> 0.5423`
- 当前可以把 `v33` 视为后续扩容与 `frozen_40` 的候选基线推进

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
3. 确认下一条要推进的 issue
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
15. 继续扩真实 issue 正式任务，优先朝 `40+` 再到 `60+` 推进
16. 构建 `frozen_40`，并开始累计连续 `5` 个策略版本的固定集合无回归证据
17. 视情况继续拆 `unraisableexception + debugging` 的组合边界，但优先级低于 benchmark maturity 主线
18. 最后同步 `README.md`、`GUIDE.md`、`docs/results.md`、`docs/optimization_log.md`

## 当前推荐下一条 issue 候选

优先级建议：

1. 扩新来源，补下一批 GitHub issue 候选
2. 以 `improved_v33` 为候选基线，继续扩正式任务数并构建 `frozen_40`
3. 继续对 pytest import/collection、首次运行与重复运行差异做更细实验，但服务于后续版本在 `frozen_40` 上的连续无回归

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

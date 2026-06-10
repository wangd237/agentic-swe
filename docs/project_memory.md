# 项目记忆卡

本文件用于在新会话或长间隔续做时，快速恢复项目上下文。

目标不是替代完整文档，而是提供一个高密度、低冗余的冷启动入口。

## 当前阶段

- 当前阶段：`Phase 6 - 优化系统`
- 当前最新策略：`improved_v22`
- 当前主分支最近重要能力：
  - 已完成 `20` 条真实 issue 派生 `semi_real` 正式任务
  - 已补齐第 `3` 组冻结同集合评测证据：`frozen_20`
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
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v22.json --run-label realissuev22`

## 当前正式任务规模

- 正式 `semi_real` 真实 issue 任务数：`20`
- 当前正式 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`
- 当前冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`

## 当前候选池状态

- `accepted = 20`
- `drafted = 1`
- `to_review = 9`

候选来源文件：

- `benchmarks/real_world_candidates.json`

## 最新评测结论

### 1. 最新扩容对比

- 对比：`improved_v21 -> improved_v22`
- 任务集：`19 -> 20` 条
- 结果：
  - `success_count: 19 -> 20`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_steps: 9.3158 -> 9.25`
  - `average_duration_sec: 0.5743 -> 0.5552`

说明：

- 这组结果证明我们已经把正式真实任务集稳定扩容到 `20` 条
- 扩容后依旧保持 `100%` 成功率和 `100%` 测试通过率
- 这一组仍属于扩容对比，主要说明“规模扩大后依旧稳定”

### 2. 当前最新冻结同集合证据

- 对比：`improved_v21 -> improved_v22`
- 任务集：固定 `20` 条
- 结果：
  - `success_rate: 0.95 -> 1.0`
  - `test_pass_rate: 0.95 -> 1.0`
  - `average_steps: 9.25 -> 9.25`
  - `average_duration_sec: 0.5536 -> 0.5569`
  - `Premature Finish: 1 -> 0`

说明：

- 这是当前第 `3` 组真正可解释为“策略改进”的冻结同集合证据
- 关键变化任务是 `task_046`
- 虽然平均耗时轻微回升，但成功率和错误标签显著改善

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

## 最近三轮优化结论

### `improved_v20`

- 覆盖场景：CLI `resolve_command` 在 `cmd is None` 时的异常回落
- 新增任务：`task_042`
- 同时补齐冻结 `18` 条任务的同集合对比

### `improved_v21`

- 覆盖场景：`MM.YYYY` 月年格式在点号分隔场景下的 parser 回落
- 新增任务：`task_044`
- 真实任务集扩容到 `19` 条

### `improved_v22`

- 覆盖场景：single-label hostname 应被视为合法 hostname
- 新增任务：`task_046`
- 同时补齐冻结 `20` 条任务的同集合对比

## 接下来最值得做的事

- 围绕 `frozen_20` 继续积累后续版本的同集合对比证据
- 从 `to_review` 中优先推进 `pypa/packaging#810`、`dateutil/dateutil#1191`、`python-jsonschema/jsonschema#1328`
- 持续把“扩容对比”和“冻结同集合对比”成对保留

## 建议冷启动顺序

如果后续由新的会话继续推进，建议先读：

1. `docs/project_memory.md`
2. `docs/next_actions.md`
3. `docs/candidate_shortlist.md`
4. `docs/benchmark_registry.md`
5. `docs/results.md`
6. `docs/optimization_log.md`

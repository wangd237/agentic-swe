# 项目记忆卡

本文件用于在新会话或长间隔续做时，快速恢复项目上下文。

目标不是替代完整文档，而是提供一个高密度、低冗余的冷启动入口。

## 当前阶段

- 当前阶段：`Phase 6 - 优化系统`
- 当前最新策略：`improved_v20`
- 当前主分支最近重要能力：
  - 已完成 18 条真实 issue 派生 `semi_real` 任务
  - 已补齐 2 组冻结同集合评测
  - 已形成追加式优化记录与 GitHub 自动推送节奏

## 当前核心链路

项目当前已经稳定具备这条主线：

`Task -> Agent Run -> Logging -> Evaluation -> Optimization -> Re-run`

对应入口：

- 单任务运行：
  - `python scripts/run_single_task.py --task benchmarks/tasks/task_001.json`
- 批量运行：
  - `python scripts/run_batch.py`
- 真实 issue 任务集流水线：
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v20.json --run-label realissuev20`

## 当前正式任务规模

- 正式 `semi_real` 真实 issue 任务数：`18`
- 当前正式 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`
- 当前冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`

## 当前候选池状态

- `accepted = 18`
- `drafted = 1`
- `to_review = 11`

候选来源文件：

- `benchmarks/real_world_candidates.json`

## 最新评测结论

### 1. 最新扩容对比

- 对比：`improved_v19 -> improved_v20`
- 任务集：`17 -> 18` 条
- 结果：
  - `success_count: 17 -> 18`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_steps: 9.3529 -> 9.3889`
  - `average_duration_sec: 0.6026 -> 0.5823`

说明：

- 这组结果证明我们可以继续扩容任务集，同时维持 `100%` 成功率
- 这一轮平均耗时优于上一轮，但平均步数略有回升
- 它仍属于扩容对比，因此不能单独说明策略本身一定更强

### 2. 当前最新冻结同集合证据

- 对比：`improved_v19 -> improved_v20`
- 任务集：固定 18 条
- 结果：
  - `success_rate: 0.9444 -> 1.0`
  - `test_pass_rate: 0.9444 -> 1.0`
  - `average_steps: 9.3889 -> 9.3889`
  - `average_duration_sec: 0.5736 -> 0.5713`
  - `Premature Finish: 1 -> 0`

说明：

- 这是当前第二组真正可解释为“策略改进”的冻结同集合证据
- 关键变化任务是 `task_042`

## 最新新增任务

- `task_041`
  - 类型：`real_issue`
  - 来源：`pallets/click#2402`
- `task_042`
  - 类型：`semi_real`
  - repo：`click_alias_repo`
  - 首个通过版本：`improved_v20`
  - 缺陷类型：`cmd is None` 时的 CLI 命令解析异常回落

## 最近三轮优化结论

### `improved_v18`

- 覆盖场景：integer-valued `multipleOf` 浮点数应按数学整数处理
- 新增任务：`task_038`

### `improved_v19`

- 覆盖场景：Requirement extra 在复合 marker 中的字符串规范化
- 新增任务：`task_040`

### `improved_v20`

- 覆盖场景：CLI `resolve_command` 在 `cmd is None` 时的异常回落
- 新增任务：`task_042`
- 同时补齐冻结 18 条任务的同集合对比

## 接下来最值得做的事

- 从 `to_review` 中再挑 1 条高质量 issue，推进到 `task_043 / task_044`
- 当正式任务数到 20 条时，固化下一组冻结 manifest
- 持续把“扩容对比”和“冻结同集合对比”成对保留

## 建议冷启动顺序

如果后续由新的会话继续推进，建议先读：

1. `docs/project_memory.md`
2. `docs/next_actions.md`
3. `docs/candidate_shortlist.md`
4. `docs/benchmark_registry.md`
5. `docs/results.md`
6. `docs/optimization_log.md`

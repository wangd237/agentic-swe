# 项目记忆卡

本文件用于在新会话或长间隔续做时，快速恢复项目上下文。

目标不是替代完整文档，而是提供一个高密度、低冗余的冷启动入口。

## 当前阶段

- 当前阶段：`Phase 6 - 优化系统`
- 当前最新策略：`improved_v18`
- 当前主分支最近重要能力：
  - 已完成 16 条真实 issue 派生 `semi_real` 任务
  - 已补齐 1 组冻结同集合评测
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
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v18.json --run-label realissuev18`

## 当前正式任务规模

- 正式 `semi_real` 真实 issue 任务数：`16`
- 当前正式 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`
- 当前冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`

## 当前候选池状态

- `accepted = 16`
- `drafted = 1`
- `to_review = 13`

候选来源文件：

- `benchmarks/real_world_candidates.json`

## 最新评测结论

### 1. 最新扩容对比

- 对比：`improved_v17 -> improved_v18`
- 任务集：`15 -> 16` 条
- 结果：
  - `success_count: 15 -> 16`
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_steps: 9.2667 -> 9.1875`
  - `average_duration_sec: 0.5887 -> 0.5649`

说明：

- 这组结果证明我们可以继续扩容任务集，同时维持 `100%` 成功率
- 并且这次平均步数和平均耗时都优于上一轮
- 但它仍不是冻结同集合对比，因此不能单独说明策略本身一定更强

### 2. 当前冻结同集合证据

- 对比：`improved_v16 -> improved_v17`
- 任务集：固定 15 条
- 结果：
  - `success_rate: 0.9333 -> 1.0`
  - `test_pass_rate: 0.9333 -> 1.0`
  - `average_steps: 9.2667 -> 9.2667`
  - `average_duration_sec: 0.5926 -> 0.5906`
  - `Premature Finish: 1 -> 0`

说明：

- 这是目前第一组真正可解释为“策略改进”的冻结同集合证据
- 关键变化任务是 `task_036`

## 最新新增任务

- `task_037`
  - 类型：`real_issue`
  - 来源：`python-jsonschema/jsonschema#1159`
- `task_038`
  - 类型：`semi_real`
  - repo：`jsonschema_multipleof_repo`
  - 首个通过版本：`improved_v18`
  - 缺陷类型：integer-valued `multipleOf` 浮点数数值语义

## 最近三轮优化结论

### `improved_v16`

- 覆盖场景：mixed-type extras 排序时的 `TypeError` 兜底
- 新增任务：`task_034`

### `improved_v17`

- 覆盖场景：hostname 格式检查在空字符串场景下回落为普通校验失败
- 新增任务：`task_036`
- 同时补齐冻结 15 条任务的同集合对比

### `improved_v18`

- 覆盖场景：integer-valued `multipleOf` 浮点数应按数学整数处理
- 新增任务：`task_038`
- 在 16 条正式任务集上继续保持 `100%` 成功率

## 接下来最值得做的事

- 从 `to_review` 中再挑 1 条高质量 issue，推进到 `task_039 / task_040`
- 当正式任务数到 18 或 20 条时，固化下一组冻结 manifest
- 持续把“扩容对比”和“冻结同集合对比”成对保留

## 建议冷启动顺序

如果后续由新的会话继续推进，建议先读：

1. `docs/project_memory.md`
2. `docs/next_actions.md`
3. `docs/candidate_shortlist.md`
4. `docs/benchmark_registry.md`
5. `docs/results.md`
6. `docs/optimization_log.md`

# 项目记忆卡

本文件用于在新会话或长间隔续做时，快速恢复项目上下文。

目标不是替代完整文档，而是提供一个高密度、低冗余的冷启动入口。

## 当前阶段

- 当前阶段：`Phase 6 - 优化系统`
- 当前最新策略：`improved_v32`
- 当前主分支最近重要能力：
  - 已完成 `30` 条真实 issue 派生 `semi_real` 正式任务
  - 已在 `frozen_20` 上补齐一轮 `improved_v31 -> improved_v32` 无回归验证
  - 已把当前高优先级 `to_review` 候选池清零
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
  - `python scripts/run_real_issue_eval.py --manifest benchmarks/manifests/real_issue_tasks.json --policy optimization/policy_versions/improved_v32.json --run-label realissuev32`

## 当前正式任务规模

- 正式 `semi_real` 真实 issue 任务数：`30`
- 当前正式 manifest：
  - `benchmarks/manifests/real_issue_tasks.json`
- 当前冻结 manifest：
  - `benchmarks/manifests/real_issue_tasks_frozen_15_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_18_v1.json`
  - `benchmarks/manifests/real_issue_tasks_frozen_20_v1.json`

## 当前候选池状态

- `accepted = 30`
- `drafted = 0`
- `to_review = 0`

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

- 对比：`improved_v31 -> improved_v32`
- 任务集：固定 `20` 条
- 结果：
  - `success_rate: 1.0 -> 1.0`
  - `test_pass_rate: 1.0 -> 1.0`
  - `average_steps: 9.25 -> 9.25`
  - `average_duration_sec: 0.6122 -> 0.6774`

说明：

- 这是当前最新的一轮 `frozen_20` 无回归验证
- 说明新增 profile 布局继承规则没有破坏已有 `20` 条固定任务
- 当前最近一组真正带来同集合成功率提升的证据仍然是 `improved_v21 -> improved_v22`

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
- 当前高优先级 `to_review` 已清零，下一步应扩新来源并定位近期耗时回升原因
- 持续把“扩容对比”和“冻结同集合对比”成对保留

## 建议冷启动顺序

如果后续由新的会话继续推进，建议先读：

1. `docs/project_memory.md`
2. `docs/next_actions.md`
3. `docs/candidate_shortlist.md`
4. `docs/benchmark_registry.md`
5. `docs/results.md`
6. `docs/optimization_log.md`

# 下一步行动清单

本文件只记录“可以直接做的下一步”，避免每次续做时重新从长历史里推理。

## 当前最高优先级

### 1. 继续扩容 1 条正式任务

目标：

- 从 `to_review` 候选里再挑 1 条高质量 issue
- 形成新的 `task_043` 草稿和 `task_044` 可运行 `semi_real`
- 新增 `improved_v21`

完成标准：

- 单任务能区分旧策略失败 / 新策略成功
- 新任务进入正式 manifest
- 跑一轮扩容对比

### 2. 规划 `frozen_20`

目标：

- 在正式任务数到 20 条后，固化下一组冻结 manifest
- 建议命名方向：
  - `real_issue_tasks_frozen_20_v1.json`

完成标准：

- baseline / improved 使用完全相同的任务列表
- 至少保留 1 份同集合 compare 报告

### 3. 持续清理候选池

目标：

- 把 `to_review = 11` 继续收敛
- 尽量把高质量候选推进为 `accepted`
- 把明显不适合的候选明确标为 `rejected`

完成标准：

- 候选池里“高优先级但未决”的 issue 数量持续下降

## 建议执行顺序

1. 先看 `docs/candidate_shortlist.md`
2. 确认下一条要推进的 issue
3. 生成 draft task 和 semi_real repo
4. 补 patch 规则与 policy
5. 跑单任务分辨测试
6. 跑扩容对比
7. 当任务数达到 20 条时，再补 `frozen_20` compare
8. 最后同步 `README.md`、`GUIDE.md`、`docs/results.md`、`docs/optimization_log.md`

## 当前推荐下一条 issue 候选

优先级建议：

1. `dateutil/dateutil#384`
2. `python-jsonschema/jsonschema#1162`
3. `pypa/packaging#810`
4. `dateutil/dateutil#1191`
5. `python-jsonschema/jsonschema#1328`

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
- `README.md`
- `GUIDE.md`
- `docs/results.md`
- `docs/case_studies.md`
- `docs/optimization_log.md`

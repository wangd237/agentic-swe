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

- 从剩余 `to_review` 候选里再挑 `1` 到 `2` 条高质量 issue
- 形成新的 `task_049 / task_050` 或后续编号任务
- 继续扩充正式真实任务集

完成标准：

- 单任务能区分旧策略失败 / 新策略成功
- 新任务进入 `benchmarks/manifests/real_issue_tasks.json`
- 扩容后仍保持任务集整体稳定

### 3. 持续清理候选池

目标：

- 把 `to_review = 8` 继续收敛
- 尽量把高质量候选推进为 `accepted`
- 把明显不适合的候选明确标为 `rejected`

完成标准：

- 候选池里“高优先级但未决”的 issue 数量持续下降
- `docs/candidate_shortlist.md` 始终只保留最值得推进的少量候选

## 建议执行顺序

1. 先看 `docs/candidate_shortlist.md`
2. 确认下一条要推进的 issue
3. 生成 draft task 和 semi_real repo
4. 补 patch 规则与 policy
5. 跑单任务分辨测试
6. 跑扩容对比
7. 再用 `frozen_20` 跑同集合 compare
8. 最后同步 `README.md`、`GUIDE.md`、`docs/results.md`、`docs/optimization_log.md`

## 当前推荐下一条 issue 候选

优先级建议：

1. `dateutil/dateutil#1191`
2. `python-jsonschema/jsonschema#1328`
3. `python-jsonschema/jsonschema#1125`
4. `simonw/sqlite-utils#159`
5. `pydantic/pydantic#9582`

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

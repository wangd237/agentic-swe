# 下一步行动清单

本文件只记录当前真正应该做的下一步。项目目标是服务 AI Agent 实习投递，因此所有行动都必须增强 LLM coding agent 的展示价值。

## 1. 当前口径

- 主角：OpenAI-compatible LLM coding agent。
- 证据：真实 issue 派生任务、trace/result/patch、测试验证、case study。
- 底座：benchmark、harness、规则版 baseline、frozen set、stability recheck。
- 暂缓：继续堆规则版任务、继续扩 benchmark 数量、继续深挖 maturity / 性能追踪。

## 2. 当前最高优先级

### P0：跑 1 条更复杂的 LLM Agent 任务

目标：补齐作品集中“不是只会简单单文件修复”的证据。

候选方向：

- 跨文件修复；
- 更长上下文；
- 需要先读测试再定位实现；
- 允许失败，但必须能形成清晰 `incomplete_reason`。

完成标准：

- 使用 `scripts/run_issue_agent.py` 真实运行；
- 产物写入 `logs/trajectories/<task_id>/<run_id>/`；
- `result.json` 有明确 `final_status`；
- 成功时有 `patch.diff`；
- 失败或边界时有明确 `incomplete_reason`。

### P1：更新 Agent 案例文档

跑完下一条代表任务后，同步：

- [docs/agent_eval_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_eval_summary.md)
- [docs/agent_case_studies.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_case_studies.md)
- 必要时同步 README 的小样本结果表。

写 case study 时优先讲：

- agent 读了什么；
- 为什么选择改这个文件；
- patch 的关键判断；
- 测试如何验证；
- 如果失败，失败原因是什么。

### P2：把失败分类变成展示资产

当前 `result.json` 已支持：

- `no_patch`
- `failed_tests`
- `max_iterations`
- `no_tests_run`
- `unverified_patch`

下一步要把这些分类汇总成一小段说明，放到 agent eval 或 case study 中。重点不是羞于失败，而是证明这个 agent 项目有真实边界和可审计性。

## 3. 可执行命令

选定更复杂任务后，运行一条 LLM agent 任务：

```bash
python scripts/run_issue_agent.py --task benchmarks/tasks/<task_id>.json --policy optimization/policy_versions/llm_deepseek_minimal.json
```

运行聚焦测试：

```bash
python -m pytest tests/test_llm_agent.py tests/test_write_file.py -q --basetemp .pytest_tmp_next_step
```

查看某次运行结果：

```bash
Get-Content logs/trajectories/<task_id>/<run_id>/result.json
```

## 4. 暂时不要优先做

- 不要把“新增正式 benchmark 数量”作为主目标。
- 不要继续围绕 `improved_v*` 规则版 patcher 做大迭代。
- 不要把 pytest 性能复核当成当前主线。
- 不要先做 UI、多 agent、训练增强。
- 不要把 DeepSeek 写死进 agent 代码；LLM provider 要保持 OpenAI-compatible 抽象。

## 5. 每轮完成后同步清单

每次完成一条重要 agent run 后，至少检查：

- README 是否需要更新小样本数字；
- `docs/agent_eval_summary.md` 是否记录新 run；
- `docs/agent_case_studies.md` 是否需要新增案例；
- `docs/v2_roadmap.md` 的下一步是否仍准确；
- 是否需要提交并推送。

## 6. 当前推荐下一步

选择一条比现有 5 条主样本更复杂的任务，用 LLM agent 真实跑一遍。不要为了成功率挑太简单的题；现在最缺的是可讲述的 agent 决策过程。

# 下一步行动清单

本文件只记录当前真正应该做的下一步。项目目标是服务 AI Agent 实习投递，因此所有行动都必须增强 LLM coding agent 的展示价值。

## 1. 当前口径

- 主角：OpenAI-compatible LLM coding agent。
- 证据：真实 issue 派生任务、trace/result/patch、测试验证、case study。
- 底座：benchmark、harness、规则版 baseline、frozen set、stability recheck。
- 暂缓：继续堆规则版任务、继续扩 benchmark 数量、继续深挖 maturity / 性能追踪。

## 2. Week Target 交付物

当前短期目标以 [docs/weekTarget.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/weekTarget.md) 为准：把项目推到“可以放进简历 + 面试中打开给人看”的状态。

### 交付物 1：LLM Agent 样本扩到 ≥25 条

目标：从当前 `5` 条主样本 + `2` 条扩展成功 + `1` 条边界 incomplete，扩到至少 `25` 条真实 LLM agent run。

要求：

- 必须包含至少 `3` 条 challenge 边界题；
- 每跑完约 `5` 条就停下来抽检 diff；
- 成功不能只看 `final_status`，还要确认 patch 合理；
- failure / boundary 要记录 `incomplete_reason`，并尽量覆盖至少 `2` 种不同 reason。

### 交付物 2：Case Study 扩到 ≥4 条

当前要优先把已有成功 run 写清楚，不必等新增 25 条全部跑完。建议详写：

- `task_010`
- `task_024`
- `task_016`
- `task_093`

每条必须包含关键步骤序列、agent 决策关键点、patch 核心改动、验证结果。

### 交付物 3：README 指标表真实化

README 的 Agent 能力表必须只写真实跑出来的数字，并和 [docs/agent_eval_summary.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/agent_eval_summary.md) 保持一致。

### 交付物 4：项目一键可跑 + `.env.example`

面试官 clone 后应能快速理解：

- 如何安装依赖；
- 如何配置 OpenAI-compatible provider；
- 如何运行一条 LLM agent 任务。

## 3. 当前已完成 / 待完成

| 交付物 | 当前状态 | 下一步 |
| --- | --- | --- |
| 样本 ≥25 | 已完成，当前 `33` 条已记录 run | 继续保持抽检，不再盲目刷成功 |
| ≥3 条 challenge | 已完成，当前 `7` 条 challenge / boundary run | 后续重点转为失败 reason 多样性 |
| `incomplete_reason` | 已完成，当前已有 `no_patch` 和 `max_iterations` | 后续可继续补 `failed_tests`，但 week target 已达标 |
| case study ≥4 | 已完成首版 | 可再挑 `task_126/128/133` 补复杂案例 |
| README 指标 | 已完成首版 | 后续随新增失败样本刷新 |
| `.env.example` | 已完成首版 | 与 README 快速开始保持一致 |

## 4. 失败分类

- `no_patch`
- `failed_tests`
- `max_iterations`
- `no_tests_run`
- `unverified_patch`

## 5. 可执行命令

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

## 6. 暂时不要优先做

- 不要把“新增正式 benchmark 数量”作为主目标。
- 不要继续围绕 `improved_v*` 规则版 patcher 做大迭代。
- 不要把 pytest 性能复核当成当前主线。
- 不要先做 UI、多 agent、训练增强。
- 不要把 DeepSeek 写死进 agent 代码；LLM provider 要保持 OpenAI-compatible 抽象。

## 7. 每轮完成后同步清单

每次完成一条重要 agent run 后，至少检查：

- README 是否需要更新小样本数字；
- `docs/agent_eval_summary.md` 是否记录新 run；
- `docs/agent_case_studies.md` 是否需要新增案例；
- `docs/v2_roadmap.md` 的下一步是否仍准确；
- 是否需要提交并推送。

# 下一步行动清单

本文件只记录当前真正应该做的下一步。项目目标以 [docs/weekTarget.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/weekTarget.md) 为准：把 LLM coding agent 打磨到实习/面试可展示，而不是继续扩 benchmark 数量。

## 1. 当前阶段

当前处于 **Target 2：多模型规模化验证**。

已完成：

- Target 1 压力测试：14 条 hard task，12/14 success，产出 [docs/stress_test_report.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/stress_test_report.md)。
- 多模型 runner / aggregator 基础设施。
- DeepSeek frozen_40 最新基线：`40/40` completed，`39/40` success，success rate `0.975`。
- 基于 `task_032` trace 落地 scratch-file guard，避免 `debug.py/tmp.py/scratch.py/probe.py` 这类无法执行的临时调试文件污染 patch 或消耗迭代。
- 当前 interim comparison： [docs/model_comparison.md](/E:/My_Projects/agentic-software-engineering-roadmap/docs/model_comparison.md)。

尚未完成：

- Kimi frozen_40。
- GLM frozen_40。
- 三模型正式交集分析。
- 至少 5 条失败 case 的 trace 级根因分析。
- Target 2 最终版 `docs/model_comparison.md` 和本地 `docs/agent_evolution.md` 收口。

## 2. 当前事实

| 项 | 状态 |
| --- | --- |
| DeepSeek policy | ready |
| Kimi policy | ready, waiting for key |
| GLM policy | ready, waiting for key |
| `.env` 当前 key | only `DEEPSEEK_API_KEY` |
| Target 2 completed pairs | `40/120` |
| Target 2 验收线 | `>=100` completed `(task, model)` pairs |

当前 `.env` 还缺：

- `KIMI_API_KEY`
- `GLM_API_KEY`

Kimi/GLM base URL 和 model 已在 policy 中给出默认值，因此只要 key 到位，preflight 就能继续。

## 3. 下一步命令

Kimi key 到位后：

```powershell
python scripts\run_multi_model_eval.py --manifest benchmarks\manifests\real_issue_tasks_frozen_40_v1.json --policy optimization\policy_versions\llm_kimi_minimal.json --output-dir logs\summaries --run-label target2_kimi_frozen40 --max-workers 1 --retries 0
```

GLM key 到位后：

```powershell
python scripts\run_multi_model_eval.py --manifest benchmarks\manifests\real_issue_tasks_frozen_40_v1.json --policy optimization\policy_versions\llm_glm_minimal.json --output-dir logs\summaries --run-label target2_glm_frozen40 --max-workers 1 --retries 0
```

三模型都跑完后，用最新三个 summary 生成正式报告：

```powershell
python scripts\aggregate_model_comparison.py --summary logs\summaries\multi_model_eval_target2_deepseek_frozen40_scratch_guard_001_001.json --summary <kimi_summary.json> --summary <glm_summary.json> --output-dir logs\summaries --run-label target2_three_model --docs-output docs\model_comparison.md
```

## 4. 暂时不要优先做

- 不加新 benchmark 任务。
- 不继续刷 DeepSeek 单模型成功率，除非是为了验证明确的 harness/prompt 改进。
- 不回到规则版 `improved_v*` 主线。
- 不做 Anthropic/Claude API 适配。
- 不做 Web UI、LangGraph、multi-agent 或 reflection。
- 不把 DeepSeek 写进 agent 代码；继续保持 OpenAI-compatible 抽象。

## 5. 每轮完成后检查

- `pytest -q` 是否通过。
- `docs/model_comparison.md` 是否反映最新真实 run。
- 本地 `docs/agent_evolution.md` 是否追加设计演进记录。
- `git status` 是否干净，且 `docs/agent_evolution.md` 仍不被 Git 追踪。
